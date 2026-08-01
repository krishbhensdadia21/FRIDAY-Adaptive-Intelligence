from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from groq import Groq
import wikipedia
import requests
import json
import re
import os
import time
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — set your keys here or via environment variables
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# In-memory conversation history keyed by session_id
conversation_store = {}

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY — call Groq cleanly
# ─────────────────────────────────────────────────────────────────────────────
def groq(messages, model="llama-3.3-70b-versatile", temperature=0, max_tokens=400, stream=False):
    """Thin wrapper around Groq chat completions."""
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
    )


def groq_text(messages, model="llama-3.3-70b-versatile", temperature=0, max_tokens=400):
    resp = groq(messages, model=model, temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — INTENT CLASSIFIER
# Decides what kind of answer this question needs.
# ─────────────────────────────────────────────────────────────────────────────
def classify_intent(query: str) -> str:
    """
    Returns one of:
      factual_wiki   — can be answered from Wikipedia
      factual_web    — needs live web data (prices, scores, news, box office, current events)
      conversational — chat / opinion / creative / reasoning
    """
    result = groq_text([
        {
            "role": "system",
            "content": (
                "Classify the user query into EXACTLY ONE of these categories:\n"
                "- factual_wiki  : historical facts, biographies, science, geography, definitions, events before 2023\n"
                "- factual_web   : current prices, live scores, today's news, recent movies/shows, box office, stock prices, weather, anything needing real-time or recent data\n"
                "- conversational: opinions, creative writing, jokes, math, coding help, general reasoning, small talk\n\n"
                "Reply with ONLY the category label, nothing else."
            ),
        },
        {"role": "user", "content": query},
    ], max_tokens=10)

    result = result.lower()
    if "wiki" in result:
        return "factual_wiki"
    if "web" in result:
        return "factual_web"
    return "conversational"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2a — WIKIPEDIA SEARCH (robust, multi-strategy)
# ─────────────────────────────────────────────────────────────────────────────
def extract_topic(query: str) -> str:
    return groq_text([
        {
            "role": "system",
            "content": (
                "Extract the core search topic from the query.\n"
                "Rules:\n"
                "- Return ONLY the topic/entity name\n"
                "- Preserve exact punctuation (colons, hyphens)\n"
                "- Keep proper nouns and titles exactly as stated\n"
                "- Do NOT include question words or filler\n"
                "- Max 10 words\n\n"
                "Examples:\n"
                "  'Who is Elon Musk?' → 'Elon Musk'\n"
                "  'Tell me about the French Revolution' → 'French Revolution'\n"
                "  'Box office of Dhurandhar: The Revenge?' → 'Dhurandhar: The Revenge'\n"
                "  'What year was the Taj Mahal built?' → 'Taj Mahal'"
            ),
        },
        {"role": "user", "content": query},
    ], max_tokens=30)


def wikipedia_search(query: str) -> str | None:
    topic = extract_topic(query)
    print(f"[Wiki] Topic: {topic}")

    def try_page(title):
        try:
            page = wikipedia.page(title, auto_suggest=True)
            content = page.summary + "\n\n" + page.content[:6000]
            return content
        except wikipedia.exceptions.DisambiguationError as e:
            for opt in e.options[:4]:
                try:
                    page = wikipedia.page(opt, auto_suggest=False)
                    return page.summary + "\n\n" + page.content[:6000]
                except Exception:
                    continue
        except Exception:
            return None

    def answer_from_content(content):
        if not content:
            return None
        return groq_text([
            {
                "role": "system",
                "content": (
                    "You are a precise answering assistant.\n"
                    "Answer the QUESTION using ONLY the TEXT provided.\n"
                    "Rules:\n"
                    "- Be direct and accurate\n"
                    "- Include specific numbers, dates, names from the text\n"
                    "- Keep answer under 120 words\n"
                    "- If the text doesn't contain the answer, reply: NOT_FOUND"
                ),
            },
            {
                "role": "user",
                "content": f"TEXT:\n{content}\n\nQUESTION: {query}",
            },
        ], max_tokens=200)

    # Strategy A: direct
    content = try_page(topic)
    if content:
        ans = answer_from_content(content)
        if ans and "NOT_FOUND" not in ans:
            return ans

    # Strategy B: wikipedia search → top results
    try:
        results = wikipedia.search(topic, results=6)
        for r in results:
            content = try_page(r)
            if content:
                ans = answer_from_content(content)
                if ans and "NOT_FOUND" not in ans:
                    return ans
    except Exception:
        pass

    # Strategy C: simplified topic
    simplified = re.sub(
        r'\b(box office|cast|director|plot|release date|budget|collection|gross|earnings|review|rating|wiki|wikipedia)\b',
        '', topic, flags=re.IGNORECASE
    ).strip()
    if simplified and simplified != topic:
        content = try_page(simplified)
        if content:
            ans = answer_from_content(content)
            if ans and "NOT_FOUND" not in ans:
                return ans

    return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2b — WEB SEARCH (Serper.dev or DuckDuckGo fallback)
# ─────────────────────────────────────────────────────────────────────────────
def web_search(query: str) -> str | None:
    """Search the web for real-time data. Uses Serper if key available, else DuckDuckGo."""
    snippets = []

    # ── Try Serper.dev (best quality, 2500 free/month) ────────────────
    if SERPER_API_KEY:
        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": query, "num": 6},
                timeout=8,
            )
            data = resp.json()

            # Answer box (instant answer)
            if data.get("answerBox"):
                ab = data["answerBox"]
                answer = ab.get("answer") or ab.get("snippet") or ab.get("snippetHighlighted")
                if answer:
                    snippets.append(f"[Direct Answer]: {answer}")

            # Organic results
            for item in data.get("organic", [])[:5]:
                title   = item.get("title", "")
                snippet = item.get("snippet", "")
                if snippet:
                    snippets.append(f"{title}: {snippet}")

            # Knowledge graph
            kg = data.get("knowledgeGraph", {})
            if kg.get("description"):
                snippets.insert(0, f"[Knowledge Graph]: {kg['description']}")

        except Exception as e:
            print(f"[Serper] Error: {e}")

    # ── DuckDuckGo fallback (no key needed) ───────────────────────────
    if not snippets:
        try:
            resp = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
                timeout=6,
            )
            data = resp.json()
            if data.get("AbstractText"):
                snippets.append(data["AbstractText"])
            for topic in data.get("RelatedTopics", [])[:4]:
                if isinstance(topic, dict) and topic.get("Text"):
                    snippets.append(topic["Text"])
        except Exception as e:
            print(f"[DuckDuckGo] Error: {e}")

    if not snippets:
        return None

    context = "\n".join(snippets[:6])
    print(f"[Web] Context length: {len(context)} chars")

    answer = groq_text([
        {
            "role": "system",
            "content": (
                "You are a precise answering assistant with access to web search results.\n"
                "Answer the QUESTION using the SEARCH RESULTS provided.\n"
                "Rules:\n"
                "- Be direct and specific\n"
                "- Include exact figures, names, dates from the results\n"
                "- If results are insufficient, use your knowledge but say so\n"
                "- Keep answer under 150 words\n"
                f"- Today's date: {datetime.now().strftime('%d %B %Y')}"
            ),
        },
        {
            "role": "user",
            "content": f"SEARCH RESULTS:\n{context}\n\nQUESTION: {query}",
        },
    ], max_tokens=250)

    return answer


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2c — PURE LLM (conversational + math + code + reasoning)
# ─────────────────────────────────────────────────────────────────────────────
def llm_answer(query: str, history: list, intent: str) -> str:
    today = datetime.now().strftime("%d %B %Y")

    system = f"""You are F.R.I.D.A.Y — a brilliant, friendly AI assistant.
Today's date: {today}

Rules:
- Answer ANY question directly and helpfully
- For math: show working step-by-step
- For code: write clean, working code with comments
- For creative tasks: be imaginative and detailed
- For opinions: be thoughtful but balanced
- Keep answers concise but complete (under 200 words unless code/creative)
- Never refuse a reasonable question
- If unsure about recent events, say "As of my knowledge cutoff..." but still answer"""

    messages = [{"role": "system", "content": system}]

    # Add last 6 turns of history for context
    for turn in history[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    messages.append({"role": "user", "content": query})

    return groq_text(messages, temperature=0.5, max_tokens=600)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — MASTER PIPELINE
# Runs the right strategy and falls back gracefully
# ─────────────────────────────────────────────────────────────────────────────
def answer_query(query: str, history: list) -> dict:
    intent = classify_intent(query)
    print(f"[Pipeline] Intent: {intent} | Query: {query[:60]}")

    source = "llm"
    answer = None

    if intent == "factual_wiki":
        answer = wikipedia_search(query)
        if answer:
            source = "wikipedia"
        else:
            # Fallback: try web search
            answer = web_search(query)
            if answer:
                source = "web"

    elif intent == "factual_web":
        answer = web_search(query)
        if answer:
            source = "web"
        else:
            # Fallback: Wikipedia might have something
            answer = wikipedia_search(query)
            if answer:
                source = "wikipedia"

    # Final fallback: pure LLM for everything
    if not answer:
        answer = llm_answer(query, history, intent)
        source = "llm"

    return {"answer": answer, "source": source, "intent": intent}


# ─────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data        = request.get_json()
        user_msg    = data.get('message', '').strip()
        session_id  = data.get('session_id', 'default')

        if not user_msg:
            return jsonify({'error': 'No message provided'}), 400

        # Load/init conversation history
        if session_id not in conversation_store:
            conversation_store[session_id] = []
        history = conversation_store[session_id]

        # Get answer
        result = answer_query(user_msg, history)

        # Save to history
        history.append({"role": "user",      "content": user_msg})
        history.append({"role": "assistant",  "content": result["answer"]})

        # Trim history to last 20 turns
        if len(history) > 20:
            conversation_store[session_id] = history[-20:]

        return jsonify({
            'response': result["answer"],
            'source':   result["source"],
            'intent':   result["intent"],
            'status':   'success'
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_history():
    data       = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    conversation_store.pop(session_id, None)
    return jsonify({'status': 'cleared'})


@app.route('/api/trending', methods=['GET'])
def get_trending():
    """Returns the current trending theme dynamically (e.g. spiderman, batman, or default)"""
    try:
        prompt = (
            "What is the top trending blockbuster or superhero movie in theaters right now as of August 2026?\n"
            "Format your answer as a JSON object with two keys:\n"
            "  'movie': The title of the movie\n"
            "  'theme': One of 'spiderman', 'batman', 'superman', 'ironman', or 'default'\n\n"
            "Provide ONLY the raw JSON block, nothing else."
        )
        response_text = groq_text([{"role": "user", "content": prompt}], max_tokens=100)
        match = re.search(r'\{.*?\}', response_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return jsonify(data)
    except Exception as e:
        print(f"[ERROR] Failed to fetch trending: {e}")
    return jsonify({"movie": "Spider-Man", "theme": "spiderman"})


# ─────────────────────────────────────────────────────────────────────────────
# FRONTEND — Serve separated HTML/CSS/JS files
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images)"""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"\n{'='*50}")
    print(f"  F.R.I.D.A.Y Advanced AI Assistant")
    print(f"  Running at http://localhost:{port}")
    print(f"  Wikipedia Search | Web Search | LLM")
    print(f"  Voice Input: ON | AI Voice: Greeting Only")
    print(f"{'='*50}\n")
    app.run(debug=True, port=port)