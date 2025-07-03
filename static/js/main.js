let isDemo = false;
    const widget      = document.getElementById('chatWidget');
    const demoBtn     = document.getElementById('demoToggle');
    const minimizeBtn = document.getElementById('minimizeBtn');
    const form        = document.getElementById('chatForm');
    const input       = document.getElementById('inputMsg');
    const messages    = document.getElementById('messages');

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
      // show user
      const u = document.createElement('div');
      u.className = 'chat-message user';
      u.textContent = text;
      messages.appendChild(u);
      input.value = '';
      messages.scrollTop = messages.scrollHeight;
      // pick endpoint
      const url = isDemo ? '/api/demo-chat' : '/api/chat';
      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({user_id:'web_user',message:text})
        });
        const {reply} = await res.json();
        const b = document.createElement('div');
        b.className = 'chat-message bot';
        b.textContent = reply;
        messages.appendChild(b);
        messages.scrollTop = messages.scrollHeight;
      } catch(err) {
        console.error(err);
      }
    });