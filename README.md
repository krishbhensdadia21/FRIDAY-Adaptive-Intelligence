# 🤖 F.R.I.D.A.Y — Adaptive Intelligence AI Assistant

F.R.I.D.A.Y is an advanced AI assistant built using Flask, Groq LLMs, Wikipedia search, and real-time web search.

It combines:
- 🧠 LLM reasoning
- 📖 Wikipedia factual retrieval
- 🌐 Real-time web search
- 🎤 Voice input
- 💎 Modern glassmorphism UI
- ⚡ Fast responses powered by Groq

Inspired by the intelligent assistant concept from Iron Man.

---

# ✨ Features

## 🧠 Intelligent Query Routing
F.R.I.D.A.Y automatically classifies user queries into:
- Historical / factual questions
- Real-time web questions
- Conversational & reasoning tasks

Then routes them to the best answering pipeline.

---

## 📖 Wikipedia Integration
Uses multi-strategy Wikipedia retrieval:
- Topic extraction
- Search fallback
- Disambiguation handling
- Context-based answer generation

---

## 🌐 Real-Time Web Search
Integrated with:
- Serper.dev API
- DuckDuckGo fallback

Used for:
- Live news
- Sports
- Stock prices
- Recent events
- Current information

---

## 💬 Modern AI Chat UI
Features:
- Glassmorphism design
- Syntax-highlighted code blocks
- Copy code button
- Typing animation
- Mobile responsive layout
- AI/User avatars
- Dynamic greeting system

---

## 🎤 Voice Features
- Speech recognition input
- AI greeting voice synthesis
- Hands-free interaction

---

# 🛠️ Tech Stack

## Backend
- Python
- Flask
- Groq API
- Wikipedia API
- Requests

## Frontend
- HTML5
- CSS3
- JavaScript
- Marked.js
- Highlight.js

---

# 📂 Project Structure

```bash
FRIDAY-AI/
│
├── Friday.py
├── .env
├── requirements.txt
├── README.md
│
├── static/
│   ├── style.css
│   ├── script.js
│   ├── user.png
│   └── robot.png
│
└── index.html
```

---

# ⚙️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/FRIDAY-AI.git
cd FRIDAY-AI
```

---

## 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3️⃣ Create .env File

Create a `.env` file in root directory:

```env
GROQ_API_KEY=your_groq_api_key
SERPER_API_KEY=your_serper_api_key
PORT=5000
```

---

## 4️⃣ Run Application

```bash
python Friday.py
```

Open:

```bash
http://localhost:5000
```

---

# 🔐 Environment Variables

| Variable | Description |
|---|---|
| GROQ_API_KEY | Groq API Key |
| SERPER_API_KEY | Serper Search API Key |
| PORT | Flask server port |

---

# 🧠 AI Pipeline Architecture

```text
User Query
    ↓
Intent Classification
    ↓
┌──────────────────────┐
│ factual_wiki         │ → Wikipedia Pipeline
│ factual_web          │ → Web Search Pipeline
│ conversational       │ → LLM Pipeline
└──────────────────────┘
    ↓
Response Generation
    ↓
Frontend Rendering
```

---

# 📸 UI Highlights

- Dark futuristic interface
- AI-powered response badges
- Responsive design
- Smooth animations
- ChatGPT-inspired input system

---

# 🚀 Future Improvements

- Streaming responses
- Persistent database memory
- Multi-agent reasoning
- Image generation
- File uploads
- Vector database integration
- RAG architecture
- Local LLM support
- Authentication system

---

# ⚠️ Security Notes

Never upload:
- `.env`
- API keys
- Tokens
- Credentials

Add this to `.gitignore`:

```gitignore
.env
__pycache__/
venv/
```

---

# 📜 License

This project is for educational and research purposes.

---

# 👨‍💻 Author

Developed by Krish Patel

---

# ⭐ Support

If you like this project:
- Star the repository
- Fork the project
- Contribute improvements

---

# 🔥 F.R.I.D.A.Y

> “Ready when you are, boss.”
