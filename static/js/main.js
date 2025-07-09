// AIChatFlows - Main JavaScript functionality
// Chat Widget and Interactive Elements

document.addEventListener('DOMContentLoaded', function() {
    // Chat Widget Functionality
    initializeChatWidget();
});

function initializeChatWidget() {
    const chatWidget = document.getElementById('chatWidget');
    const chatForm = document.getElementById('chatForm');
    const inputMsg = document.getElementById('inputMsg');
    const messages = document.getElementById('messages');
    const minimizeBtn = document.getElementById('minimizeBtn');
    const demoToggle = document.getElementById('demoToggle');

    // Check if chat widget elements exist (they're only on the home page)
    if (!chatWidget || !chatForm || !inputMsg || !messages) {
        return; // Not on a page with chat widget
    }

    let isMinimized = false;
    let isDemoMode = false;

    // Demo responses for the chat widget
    const demoResponses = [
        "Thanks for your message! We'd love to help automate your customer service.",
        "Our AI chatbots can handle Instagram DMs, Facebook messages, and more!",
        "Would you like to know more about our Starter or Pro plans?",
        "Feel free to check out our pricing and get started with AIChatFlows!",
        "This is a demo response. In a real setup, our AI would provide personalized answers based on your business."
    ];

    // Initialize messages with welcome message
    addMessage('AIChatFlows', 'Hi! I\'m the AIChatFlows demo bot. Ask me anything about our AI automation services!', 'bot');

    // Handle chat form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = inputMsg.value.trim();
        if (!message) return;

        // Add user message
        addMessage('You', message, 'user');
        inputMsg.value = '';

        // Auto-resize textarea
        inputMsg.style.height = 'auto';

        // Simulate bot response after a short delay
        setTimeout(() => {
            let response;
            if (isDemoMode) {
                response = demoResponses[Math.floor(Math.random() * demoResponses.length)];
            } else {
                response = generateContextualResponse(message);
            }
            addMessage('AIChatFlows', response, 'bot');
        }, 1000 + Math.random() * 1000); // Random delay between 1-2 seconds
    });

    // Handle minimize button
    minimizeBtn.addEventListener('click', function() {
        isMinimized = !isMinimized;
        chatWidget.classList.toggle('minimized', isMinimized);
        
        // Update button icon
        if (isMinimized) {
            minimizeBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/></svg>';
            minimizeBtn.title = 'Expand Chat';
        } else {
            minimizeBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" fill="none"/></svg>';
            minimizeBtn.title = 'Minimize Chat';
        }
    });

    // Handle demo toggle
    demoToggle.addEventListener('click', function() {
        isDemoMode = !isDemoMode;
        
        // Update button appearance
        demoToggle.classList.toggle('active', isDemoMode);
        demoToggle.title = isDemoMode ? 'Disable Demo Mode' : 'Enable Demo Mode';
        
        // Add system message
        const modeText = isDemoMode ? 'Demo mode enabled' : 'Demo mode disabled';
        addMessage('System', modeText, 'system');
    });

    // Auto-resize textarea
    inputMsg.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Handle Enter key (without Shift)
    inputMsg.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
}

function addMessage(sender, text, type) {
    const messages = document.getElementById('messages');
    if (!messages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="sender">${sender}</span>
            <span class="time">${time}</span>
        </div>
        <div class="message-content">${text}</div>
    `;
    
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

function generateContextualResponse(message) {
    const lowerMessage = message.toLowerCase();
    
    // Keywords and responses mapping
    const responses = {
        'price': 'Our Starter plan is $99/month with a $199 setup fee, and our Pro plan is $149/month with a $249 setup fee. Both include AI chatbot automation!',
        'cost': 'Our Starter plan is $99/month with a $199 setup fee, and our Pro plan is $149/month with a $249 setup fee. Both include AI chatbot automation!',
        'plan': 'We offer two main plans: Starter ($99/mo) for Instagram automation, and Pro ($149/mo) which includes TikTok, Facebook, and WhatsApp automation as well.',
        'instagram': 'Yes! Both our plans include Instagram automation. Our AI can respond to DMs, comments, and help with customer service on Instagram.',
        'facebook': 'Facebook automation is included in our Pro plan ($149/mo). We can automate Messenger responses and Facebook page interactions.',
        'tiktok': 'TikTok automation is available with our Pro plan. We can help manage comments and direct messages on TikTok.',
        'whatsapp': 'WhatsApp Business automation is part of our Pro plan. Perfect for customer service and order management.',
        'setup': 'Our setup process is simple! Just fill out our onboarding form, and our team will configure your AI chatbot within 24-48 hours.',
        'demo': 'This is a live demo of our chat interface! In your actual implementation, the AI would be trained on your specific business information.',
        'start': 'Ready to get started? Click the "Get Started" button on any of our plans, or visit our /start page to begin the onboarding process.',
        'help': 'I\'m here to help! Ask me about our pricing, features, setup process, or any questions about AI chatbot automation for your business.',
        'feature': 'Our main features include 24/7 AI chatbots, dynamic social content creation, multi-platform support, and seamless setup with no coding required.',
        'support': 'We provide email support, priority edits, and comprehensive onboarding. Pro plan customers also get SLA guarantees and monthly usage reports.'
    };
    
    // Check for keywords and return appropriate response
    for (const [keyword, response] of Object.entries(responses)) {
        if (lowerMessage.includes(keyword)) {
            return response;
        }
    }
    
    // Default responses for unmatched queries
    const defaultResponses = [
        'That\'s a great question! Our AI chatbots can help automate customer service across Instagram, Facebook, TikTok, and WhatsApp. Would you like to know more about our plans?',
        'Thanks for asking! AIChatFlows specializes in AI-powered customer service automation. We can set up chatbots for your social media platforms in just 24-48 hours.',
        'Interesting! Our AI systems are designed to handle customer questions, process orders, and provide 24/7 support. Check out our pricing to see which plan fits your needs.',
        'Great point! We offer both Starter and Pro plans, with setup handled completely by our team. No coding or technical knowledge required on your end.'
    ];
    
    return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
}

// Smooth scrolling for anchor links
document.addEventListener('click', function(e) {
    if (e.target.matches('a[href^="#"]')) {
        e.preventDefault();
        const targetId = e.target.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
});

// Add loading states for forms
document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.id === 'chatForm') return; // Skip chat form
    
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        
        // Re-enable after 30 seconds as fallback
        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit';
        }, 30000);
    }
});