const widget = document.getElementById('chatWidget');
const minimizeBtn = document.getElementById('minimizeBtn');
const form = document.getElementById('chatForm');
const input = document.getElementById('inputMsg');
const messages = document.getElementById('messages');
const quickRepliesContainer = document.createElement('div');
quickRepliesContainer.className = 'quick-replies';
messages.parentNode.insertBefore(quickRepliesContainer, form);

const typingIndicator = document.createElement('div');
typingIndicator.className = 'typing-indicator';
typingIndicator.innerHTML = '<span></span><span></span><span></span>';

// Function to add a message to the chat
function addMessage(sender, text) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-message ${sender}`;

  const avatar = document.createElement('div');
  avatar.className = `chat-avatar ${sender}`;
  avatar.textContent = sender === 'user' ? 'You' : 'AI';

  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble';
  bubble.textContent = text;

  if (sender === 'user') {
    msgDiv.appendChild(bubble);
    msgDiv.appendChild(avatar);
  } else {
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
  }
  messages.appendChild(msgDiv);
  messages.scrollTop = messages.scrollHeight;
}

// Function to show/hide typing indicator
function showTypingIndicator(show) {
  if (show) {
    messages.appendChild(typingIndicator);
    messages.scrollTop = messages.scrollHeight;
  } else {
    if (messages.contains(typingIndicator)) {
      messages.removeChild(typingIndicator);
    }
  }
}

// Function to add quick replies
function addQuickReplies(replies) {
  quickRepliesContainer.innerHTML = '';
  replies.forEach(reply => {
    const btn = document.createElement('button');
    btn.className = 'quick-reply-btn';
    btn.textContent = reply;
    btn.addEventListener('click', () => {
      input.value = reply;
      quickRepliesContainer.innerHTML = ''; // Clear quick replies immediately
      form.dispatchEvent(new Event('submit'));
    });
    quickRepliesContainer.appendChild(btn);
  });
}

// Proactive welcome message
window.addEventListener('load', () => {
  setTimeout(() => {
    addMessage('bot', 'Hello! How can I assist you today? Feel free to ask me anything about AIChatFlows.');
    addQuickReplies([
      'What are your features?',
      'How much does it cost?',
      'Tell me about automation.'
    ]);
  }, 1000);
});

// Minimize / restore
minimizeBtn.addEventListener('click', () => {
  widget.classList.toggle('minimized');
});

// Send message
form.addEventListener('submit', async e => {
  e.preventDefault();
  console.log('Form submit event triggered.');
  const text = input.value.trim();
  if (!text) return;

  addMessage('user', text);
  input.value = '';
  quickRepliesContainer.innerHTML = ''; // Clear quick replies after sending
  showTypingIndicator(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({user_id:'web_user',message:text})
    });
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const data = await res.json();
    showTypingIndicator(false);
    
    if (data.reply) {
      addMessage('bot', data.reply);
    } else {
      addMessage('bot', 'I received your message but couldn\'t generate a response. Please try again.');
    }

  } catch(err) {
    console.error('Chat error:', err);
    showTypingIndicator(false);
    
    let errorMessage;
    if (err.message.includes('NetworkError') || err.message.includes('Failed to fetch')) {
      errorMessage = 'Connection error. Please check your internet connection and try again.';
    } else if (err.message.includes('HTTP 5')) {
      errorMessage = 'Server error. Our AI assistant is temporarily unavailable. Please try again in a few minutes.';
    } else if (err.message.includes('HTTP 4')) {
      errorMessage = 'Request error. Please try rephrasing your message.';
    } else {
      errorMessage = 'Oops! Something went wrong. Please try again later.';
    }
    
    addMessage('bot', errorMessage);
  }
});

// Keyboard shortcuts
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    form.dispatchEvent(new Event('submit'));
  }
});

// Auto-resize textarea
input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 120) + 'px';
});

console.log('main.js loaded.');
console.log('Form element:', form);