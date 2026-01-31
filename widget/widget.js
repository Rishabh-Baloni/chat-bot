(function() {
    'use strict';
    
    // Widget configuration - can be overridden by user
    window.ChatbotConfig = window.ChatbotConfig || {};
    
    const DEFAULT_CONFIG = {
        apiBaseUrl: 'https://chat-bot-hizj.onrender.com',
        buttonText: '💬',
        headerText: 'AI Assistant',
        placeholder: 'Type your message...',
        sendButtonText: 'Send',
        maxMessageLength: 2000,
        rateLimitDelay: 1000,
        position: 'bottom-right', // bottom-right, bottom-left, top-right, top-left
        theme: 'default', // default, dark, light
        showTypingIndicator: true,
        coldStartMessage: 'Starting up... This may take a moment on first use.',
        version: '1.0.0'
    };
    
    // Merge user config with defaults
    const WIDGET_CONFIG = { ...DEFAULT_CONFIG, ...window.ChatbotConfig };
    
    let sessionId = null;
    let isOpen = false;
    let lastMessageTime = 0;
    let isProcessing = false;
    let isColdStart = true;
    
    // Security: Generate secure session ID
    function generateSessionId() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return 'session_' + Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('') + '_v' + WIDGET_CONFIG.version;
    }
    
    // Security: Sanitize user input
    function sanitizeInput(input) {
        if (!input || typeof input !== 'string') return '';
        
        if (input.length > WIDGET_CONFIG.maxMessageLength) {
            input = input.substring(0, WIDGET_CONFIG.maxMessageLength);
        }
        
        input = input.replace(/[<>"'&]/g, function(match) {
            const entities = {
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;',
                '&': '&amp;'
            };
            return entities[match];
        });
        
        return input.trim();
    }
    
    // Rate limiting
    function canSendMessage() {
        const now = Date.now();
        if (now - lastMessageTime < WIDGET_CONFIG.rateLimitDelay) {
            return false;
        }
        lastMessageTime = now;
        return true;
    }
    
    // Get position classes
    function getPositionClasses() {
        const positions = {
            'bottom-right': 'bottom-right',
            'bottom-left': 'bottom-left',
            'top-right': 'top-right',
            'top-left': 'top-left'
        };
        return positions[WIDGET_CONFIG.position] || 'bottom-right';
    }
    
    // Create widget HTML
    function createWidget() {
        const positionClass = getPositionClasses();
        const themeClass = `theme-${WIDGET_CONFIG.theme}`;
        
        const widgetHTML = `
            <div id="chatbot-widget" class="${positionClass} ${themeClass}">
                <div id="chat-button" class="chat-button">
                    ${WIDGET_CONFIG.buttonText}
                </div>
                <div id="chat-window" class="chat-window" style="display: none;">
                    <div class="chat-header">
                        <span>${WIDGET_CONFIG.headerText}</span>
                        <div class="header-info">
                            <span class="version">v${WIDGET_CONFIG.version}</span>
                            <button id="close-chat" class="close-button">×</button>
                        </div>
                    </div>
                    <div id="chat-messages" class="chat-messages"></div>
                    <div class="chat-input-container">
                        <input type="text" id="chat-input" placeholder="${WIDGET_CONFIG.placeholder}" maxlength="${WIDGET_CONFIG.maxMessageLength}" />
                        <button id="send-button">${WIDGET_CONFIG.sendButtonText}</button>
                    </div>
                    <div class="chat-status" id="chat-status" style="display: none;"></div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }
    
    // Add message to chat
    function addMessage(message, isUser = false, isError = false, isSystem = false) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        
        let className = 'message ';
        if (isUser) {
            className += 'user-message';
        } else if (isError) {
            className += 'error-message';
        } else if (isSystem) {
            className += 'system-message';
        } else {
            className += 'bot-message';
        }
        
        messageDiv.className = className;
        messageDiv.textContent = sanitizeInput(message);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Show status message
    function showStatus(message, isError = false) {
        const statusDiv = document.getElementById('chat-status');
        statusDiv.textContent = message;
        statusDiv.className = `chat-status ${isError ? 'error' : 'info'}`;
        statusDiv.style.display = 'block';
        
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
    
    // Send message to backend with retry logic
    async function sendMessage(message, retryCount = 0) {
        if (!sessionId) {
            sessionId = generateSessionId();
        }
        
        const maxRetries = 2;
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);
            
            const response = await fetch(`${WIDGET_CONFIG.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.status === 429) {
                throw new Error('Rate limit exceeded. Please wait a moment.');
            }
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error (${response.status}): ${errorText}`);
            }
            
            const data = await response.json();
            
            if (!data.response) {
                throw new Error('Invalid response format');
            }
            
            // Handle version compatibility
            if (data.version && data.version !== WIDGET_CONFIG.version) {
                console.warn(`Widget version ${WIDGET_CONFIG.version} may be incompatible with API version ${data.version}`);
            }
            
            // Mark cold start as complete
            if (isColdStart) {
                isColdStart = false;
            }
            
            return data.response;
            
        } catch (error) {
            console.error('Chat error:', error);
            
            if (error.name === 'AbortError') {
                return 'Request timed out. Please try again.';
            }
            
            if (retryCount < maxRetries && !error.message.includes('Rate limit')) {
                await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
                return sendMessage(message, retryCount + 1);
            }
            
            if (error.message.includes('Rate limit')) {
                return 'Please wait a moment before sending another message.';
            }
            
            return 'Sorry, I encountered an error. Please try again later.';
        }
    }
    
    // Toggle chat window
    function toggleChat() {
        const chatWindow = document.getElementById('chat-window');
        const chatButton = document.getElementById('chat-button');
        
        isOpen = !isOpen;
        
        if (isOpen) {
            chatWindow.style.display = 'flex';
            chatButton.style.display = 'none';
            document.getElementById('chat-input').focus();
        } else {
            chatWindow.style.display = 'none';
            chatButton.style.display = 'flex';
        }
    }
    
    // Handle message sending with queue
    async function handleSendMessage() {
        const input = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        const message = sanitizeInput(input.value);
        
        if (!message) return;
        
        if (!canSendMessage()) {
            showStatus('Please wait before sending another message', true);
            return;
        }
        
        input.disabled = true;
        sendButton.disabled = true;
        
        addMessage(message, true);
        input.value = '';
        
        // Show appropriate loading message
        let loadingMessage = 'Typing...';
        if (isColdStart) {
            loadingMessage = WIDGET_CONFIG.coldStartMessage;
        }
        
        if (WIDGET_CONFIG.showTypingIndicator) {
            addMessage(loadingMessage, false, false, true);
            const messages = document.getElementById('chat-messages');
            const typingMessage = messages.lastElementChild;
            
            try {
                const response = await sendMessage(message);
                typingMessage.remove();
                addMessage(response, false);
            } catch (error) {
                typingMessage.remove();
                addMessage('Service temporarily unavailable. Please try again in a moment.', false, true);
            }
        } else {
            try {
                const response = await sendMessage(message);
                addMessage(response, false);
            } catch (error) {
                addMessage('Service temporarily unavailable. Please try again in a moment.', false, true);
            }
        }
        
        input.disabled = false;
        sendButton.disabled = false;
        input.focus();
    }
    
    // Initialize widget
    function initWidget() {
        createWidget();
        
        document.getElementById('chat-button').addEventListener('click', toggleChat);
        document.getElementById('close-chat').addEventListener('click', toggleChat);
        document.getElementById('send-button').addEventListener('click', handleSendMessage);
        
        document.getElementById('chat-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });
        
        // Welcome message
        setTimeout(() => {
            addMessage('Hello! How can I help you today?', false);
        }, 500);
    }
    
    // Load CSS with version support
    function loadCSS() {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `${WIDGET_CONFIG.apiBaseUrl}/widget/widget.css?v=${WIDGET_CONFIG.version}`;
        link.onerror = function() {
            console.warn('Failed to load widget CSS');
        };
        document.head.appendChild(link);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            loadCSS();
            initWidget();
        });
    } else {
        loadCSS();
        initWidget();
    }
    
})();