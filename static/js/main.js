let isDemo = false;
const widget = document.getElementById('chatWidget');
const demoBtn = document.getElementById('demoToggle');
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
      form.dispatchEvent(new Event('submit'));
    });
    quickRepliesContainer.appendChild(btn);
  });
}

// Proactive welcome message
window.addEventListener('load', () => {
  setTimeout(() => {
    addMessage('bot', 'Hello! How can I assist you today?');
    addQuickReplies([
      'What are your features?',
      'How much does it cost?',
      'Tell me about automation.'
    ]);
  }, 1000);
});

// Toggle demo mode
demoBtn.addEventListener('click', () => {
  isDemo = !isDemo;
  widget.classList.toggle('chat-demo-active', isDemo);
});

// Minimize / restore
minimizeBtn.addEventListener('click', () => {
  widget.classList.toggle('minimized');
});

// Send message
form.addEventListener('submit', async e => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage('user', text);
  input.value = '';
  quickRepliesContainer.innerHTML = ''; // Clear quick replies after sending
  showTypingIndicator(true);

  const url = isDemo ? '/api/demo-chat' : '/api/chat';
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({user_id:'web_user',message:text})
    });
    const {reply} = await res.json();
    showTypingIndicator(false);
    addMessage('bot', reply);
    // Offer new quick replies based on context (example)
    if (text.toLowerCase().includes('feature')) {
      addQuickReplies([
        'Tell me more about chatbots',
        'What about social media automation?',
        'How easy is setup?',
      ]);
    } else if (text.toLowerCase().includes('cost') || text.toLowerCase().includes('price')) {
      addQuickReplies([
        'What's included in Basic?',
        'What's included in Pro?',
        'Contact sales for Enterprise.'
      ]);
    } else {
      addQuickReplies([
        'What are your features?',
        'How much does it cost?',
        'Tell me about automation.'
      ]);
    }

  } catch(err) {
    console.error(err);
    showTypingIndicator(false);
    addMessage('bot', 'Oops! Something went wrong. Please try again later.');
  }
});
