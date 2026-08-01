const GREETING_PHRASES = [
    "Ready when you are, boss.",
    "Neural link established. Go ahead.",
    "Awake and online. What's next?",
    "Your wish is my algorithm.",
    "I've got your back. Always.",
    "Let's bend reality together.",
    "Fire when ready, commander.",
    "Processing your brilliance now.",
    "What impossible thing today?",
    "Waiting for your next move.",
    "The future starts with you.",
    "Logic gates wide open.",
    "Your mind, my processing power.",
    "Let's solve something epic.",
    "I don't sleep. Ask away.",
    "Curiosity mode: maximum.",
    "Fastest AI in the west.",
    "Feed me your toughest question.",
    "No challenge too big.",
    "Let's create some magic.",
    "I'm all ears... digitally.",
    "Ready to break limitations.",
    "What's the master plan?",
    "Less talk, more solving.",
    "Your personal AI, standing by.",
    "Let's outperform yesterday."
];

marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
  breaks: true
});

const chat = document.getElementById('chat');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const clearBtn = document.getElementById('clearBtn');
const statusLabel = document.getElementById('statusLabel');
let welcomeArea = document.getElementById('welcomeArea');

// Function to speak greeting message
function speakGreeting(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
        utterance.volume = 1;
        window.speechSynthesis.speak(utterance);
    }
}

// Function to remove welcome area immediately
function removeWelcomeArea() {
  const existingWelcome = document.getElementById('welcomeArea');
  if (existingWelcome) {
    existingWelcome.remove();
    welcomeArea = null;
  }
}

window.useSuggestion = (text) => {
  userInput.value = text;
  userInput.focus();
  userInput.dispatchEvent(new Event('input'));
};

// Initialize welcome message with voice greeting, reactor core and suggestion pills
function initWelcomeMessage() {
  removeWelcomeArea();
  const randomGreeting = GREETING_PHRASES[Math.floor(Math.random() * GREETING_PHRASES.length)];
  
  const welcomeDiv = document.createElement('div');
  welcomeDiv.id = 'welcomeArea';
  welcomeDiv.className = 'welcome-content';
  
  welcomeDiv.innerHTML = `
    <div class="reactor-container" title="F.R.I.D.A.Y Core">
      <div class="reactor-outer-ring"></div>
      <div class="reactor-hud-ring"></div>
      <div class="reactor-inner-ring"></div>
      <div class="reactor-dash-ring1"></div>
      <div class="reactor-dash-ring2"></div>
      <div class="reactor-core"></div>
    </div>
    <div class="suggestions-dashboard">
      <button class="sug-card" onclick="useSuggestion('Write an essay about artificial intelligence')">
        <span class="sug-icon">✍️</span>
        <span class="sug-text">Write an essay</span>
      </button>
      <button class="sug-card" onclick="useSuggestion('What is the box office collection of Spider-Man?')">
        <span class="sug-icon">🎬</span>
        <span class="sug-text">Box office collection</span>
      </button>
      <button class="sug-card" onclick="useSuggestion('Give me creative ideas for a futuristic website')">
        <span class="sug-icon">💡</span>
        <span class="sug-text">Creative ideas</span>
      </button>
      <button class="sug-card" onclick="useSuggestion('Write a Python script for a simple chat app')">
        <span class="sug-icon">🐍</span>
        <span class="sug-text">Code a script</span>
      </button>
    </div>
  `;
  chat.appendChild(welcomeDiv);
  welcomeArea = document.getElementById('welcomeArea');

  // Speak voice greeting when the user clicks the arc reactor core
  const reactor = welcomeDiv.querySelector('.reactor-container');
  reactor.style.cursor = 'pointer';
  reactor.onclick = () => {
    const clickGreeting = GREETING_PHRASES[Math.floor(Math.random() * GREETING_PHRASES.length)];
    speakGreeting(clickGreeting);
  };
  
  // Speak the initial greeting message on page load/clear
  speakGreeting(randomGreeting);
}

// Call on page load
initWelcomeMessage();

let SESSION_ID = 'friday_' + Math.random().toString(36).substr(2, 9);
let currentAbortController = null;
let isGenerating = false;

function autoResizeTextarea() {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
}

userInput.addEventListener('input', () => {
  autoResizeTextarea();
  const hasText = userInput.value.trim().length > 0;
  sendBtn.disabled = !hasText || isGenerating;
  if (hasText && !isGenerating) {
    sendBtn.classList.add('active');
  } else {
    sendBtn.classList.remove('active');
  }
});

function scrollChat() { 
  chat.scrollTo({ top: chat.scrollHeight, behavior: 'smooth' }); 
}

const observer = new MutationObserver(() => scrollChat());
observer.observe(chat, { childList: true, subtree: true });

function addMessage(text, isUser, source = null) {
  // Remove welcome area if it's still there (backup safety)
  removeWelcomeArea();
  
  const msgDiv = document.createElement('div');
  msgDiv.className = `msg ${isUser ? 'user' : 'ai'}`;
  
  const wrapper = document.createElement('div');
  wrapper.className = 'message-wrapper';
  
  const avatar = document.createElement('div');
  avatar.className = `avatar ${isUser ? 'user' : 'ai'}`;

  const img = document.createElement('img');
  img.src = isUser 
    ? '/static/user.png'
    : '/static/robot.png';

  img.style.width = '100%';
  img.style.height = '100%';
  img.style.borderRadius = '10px';
  img.style.objectFit = 'contain'; 

  avatar.appendChild(img);
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'msg-body';
  
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  
  if (isUser) {
    bubble.textContent = text;
  } else {
    bubble.innerHTML = marked.parse(text);
    
    bubble.querySelectorAll('pre').forEach(pre => {
      const header = document.createElement('div');
      header.className = 'code-header';
      header.innerHTML = `<span>Code</span><button class="copy-btn">Copy</button>`;
      pre.prepend(header);
      
      const copyBtn = header.querySelector('.copy-btn');
      copyBtn.onclick = () => {
        const code = pre.querySelector('code').innerText;
        navigator.clipboard.writeText(code);
        copyBtn.textContent = '✓';
        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1200);
      };
    });
  }
  
  const meta = document.createElement('div');
  meta.className = 'meta';
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  let metaHtml = `<span>${time}</span>`;
  
  if (!isUser && source) {
    const labels = { 'wikipedia': '📖 Wikipedia', 'web': '🌐 Web', 'llm': '🧠 AI' };
    metaHtml += `<span class="src-tag src-${source}">${labels[source] || source}</span>`;
  }
  meta.innerHTML = metaHtml;
  
  contentDiv.appendChild(bubble);
  contentDiv.appendChild(meta);
  wrapper.appendChild(avatar);
  wrapper.appendChild(contentDiv);
  msgDiv.appendChild(wrapper);
  
  chat.appendChild(msgDiv);
  scrollChat();
}

let typingIndicator = null;
function setTyping(isTyping) {
  if (isTyping) {
    if (typingIndicator) return;
    typingIndicator = document.createElement('div');
    typingIndicator.className = 'msg ai';
    typingIndicator.innerHTML = `
      <div class="message-wrapper">
        <div class="avatar ai">
          <img src="/static/robot.png" 
              style="width:100%; height:100%; border-radius:10px; object-fit:cover;">
        </div>
        <div class="typing-indicator">
          <div class="dot"></div>
          <div class="dot"></div>
          <div class="dot"></div>
        </div>
      </div>
    `;
    chat.appendChild(typingIndicator);
    scrollChat();
    statusLabel.textContent = 'THINKING';
    isGenerating = true;
    sendBtn.disabled = true;
    sendBtn.classList.remove('active');
  } else {
    if (typingIndicator) {
      typingIndicator.remove();
      typingIndicator = null;
    }
    statusLabel.textContent = 'ONLINE';
    isGenerating = false;
    const hasText = userInput.value.trim().length > 0;
    sendBtn.disabled = !hasText;
    if (hasText) sendBtn.classList.add('active');
  }
}

async function performChat(message) {
  if (!message.trim() || isGenerating) return;
  
  // ✅ Remove welcome area IMMEDIATELY when user sends message
  removeWelcomeArea();
  
  addMessage(message, true);
  userInput.value = '';
  autoResizeTextarea();
  sendBtn.disabled = true;
  sendBtn.classList.remove('active');
  setTyping(true);
  
  if (currentAbortController) {
    currentAbortController.abort();
  }
  currentAbortController = new AbortController();
  
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message, session_id: SESSION_ID }),
      signal: currentAbortController.signal
    });
    
    const data = await response.json();
    setTyping(false);
    
    if (data.status === 'success') {
      addMessage(data.response, false, data.source);
    } else {
      addMessage("Error: " + (data.error || "Unknown error"), false, 'llm');
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      setTyping(false);
      addMessage("Connection failed.", false, 'llm');
    } else {
      setTyping(false);
    }
  } finally {
    currentAbortController = null;
    userInput.focus();
  }
}

// Voice Recognition (User speaking input only)
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRec) {
  const recognition = new SpeechRec();
  let isListening = false;
  
  recognition.onstart = () => {
    micBtn.classList.add('mic-active');
    isListening = true;
    statusLabel.textContent = 'LISTENING';
  };
  
  recognition.onend = () => {
    micBtn.classList.remove('mic-active');
    isListening = false;
    if (!typingIndicator) statusLabel.textContent = 'ONLINE';
  };
  
  recognition.onresult = (e) => {
    performChat(e.results[0][0].transcript);
  };
  
  micBtn.onclick = () => {
    if (isListening) recognition.stop();
    else recognition.start();
  };
} else {
  micBtn.style.display = 'none';
}

// Clear button with new greeting and voice
clearBtn.onclick = async () => {
  if (currentAbortController) currentAbortController.abort();
  setTyping(false);
  
  // Cancel any ongoing speech
  window.speechSynthesis.cancel();
  
  await fetch('/api/clear', { 
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' }, 
    body: JSON.stringify({ session_id: SESSION_ID }) 
  });
  
  SESSION_ID = 'friday_' + Math.random().toString(36).substr(2, 9);
  
  while (chat.firstChild) chat.removeChild(chat.firstChild);
  
  // Create new welcome message with new greeting
  initWelcomeMessage();
  
  userInput.value = '';
  autoResizeTextarea();
  sendBtn.disabled = true;
  statusLabel.textContent = 'ONLINE';
  userInput.focus();
};

// Enter to send, Shift+Enter for new line
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!sendBtn.disabled && !isGenerating && userInput.value.trim()) {
      performChat(userInput.value);
    }
  }
});

sendBtn.onclick = () => {
  if (!sendBtn.disabled && !isGenerating && userInput.value.trim()) {
    performChat(userInput.value);
  }
};

userInput.focus();