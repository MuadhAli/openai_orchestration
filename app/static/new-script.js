// Simple, clean chat application
class ChatApp {
    constructor() {
        this.currentChatId = null;
        this.chats = [];
        this.isLoading = false;
        
        this.initElements();
        this.bindEvents();
        
        // Initialize routing
        this.initRouting();
        
        console.log('ChatApp initialized');
    }
    
    initRouting() {
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (e) => {
            this.handleRouteChange();
        });
        
        // Handle initial route
        this.handleRouteChange();
    }
    
    async handleRouteChange() {
        const path = window.location.pathname;
        
        // Route: /new - Show welcome/new chat interface
        if (path === '/new' || path === '/') {
            // Clear current chat selection but don't create new one yet
            this.currentChatId = null;
            this.clearMessages();
            await this.loadChats();
            this.renderChats();
        }
        // Route: /chat/{session_id} - Load specific chat
        else if (path.startsWith('/chat/')) {
            const sessionId = path.replace('/chat/', '').split('?')[0]; // Remove query params
            if (sessionId) {
                await this.loadChats();
                // Only load if it's different from current
                if (sessionId !== this.currentChatId) {
                    await this.selectChat(sessionId);
                }
            } else {
                this.redirectToNew();
            }
        }
        // Default: Redirect to new chat
        else {
            this.redirectToNew();
            await this.handleRouteChange(); // Recursive call after redirect
        }
    }
    
    updateURL(sessionId) {
        if (sessionId) {
            const newPath = `/chat/${sessionId}`;
            if (window.location.pathname !== newPath) {
                window.history.pushState({ sessionId }, '', newPath);
            }
        } else {
            this.redirectToNew();
        }
    }
    
    redirectToNew() {
        if (window.location.pathname !== '/new' && window.location.pathname !== '/') {
            window.history.pushState({}, '', '/new');
        }
    }

    initElements() {
        this.chatForm = document.getElementById('chat-form');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.messagesArea = document.getElementById('messages-area');
        this.chatList = document.getElementById('chat-list');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.charCounter = document.getElementById('char-counter');
        this.welcomeMessage = document.getElementById('welcome-message');
        this.sidebar = document.getElementById('sidebar');
        this.overlay = document.getElementById('overlay');
        this.mobileMenuBtn = document.getElementById('mobile-menu-btn');
    }

    bindEvents() {
        // Form submission
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Input events
        this.messageInput.addEventListener('input', () => this.handleInput());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // New chat button
        this.newChatBtn.addEventListener('click', () => {
            this.redirectToNew();
            this.createNewChat();
        });
        
        // Mobile menu
        this.mobileMenuBtn.addEventListener('click', () => this.toggleSidebar());
        this.overlay.addEventListener('click', () => this.closeSidebar());
    }

    handleInput() {
        const length = this.messageInput.value.length;
        this.charCounter.textContent = `${length} / 4000`;
        this.sendBtn.disabled = length === 0 || this.isLoading;
        this.autoResize();
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSubmit(e);
        }
    }

    autoResize() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        // Ensure we have a chat
        if (!this.currentChatId) {
            await this.createNewChat();
        }

        this.isLoading = true;
        this.sendBtn.disabled = true;

        // Add user message
        this.addMessage('user', message);
        
        // Clear input
        this.messageInput.value = '';
        this.handleInput();

        // Show typing indicator
        const typingId = this.showTyping();

        try {
            const response = await fetch(`/api/sessions/${this.currentChatId}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTyping(typingId);
            
            // Add AI response
            this.addMessage('assistant', data.assistant_message.content);
            
            // Refresh chat list to show updated session name (for first message)
            await this.loadChats();

        } catch (error) {
            console.error('Chat error:', error);
            this.removeTyping(typingId);
            this.addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        } finally {
            this.isLoading = false;
            this.handleInput();
        }
    }

    addMessage(role, content) {
        // Remove welcome message if it exists
        if (this.welcomeMessage && this.welcomeMessage.style.display !== 'none') {
            this.welcomeMessage.style.display = 'none';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = `avatar ${role}`;
        avatar.textContent = role === 'user' ? 'U' : 'AI';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format markdown content
        const formattedContent = this.formatMessageContent(content);
        messageContent.innerHTML = formattedContent;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.messagesArea.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessageContent(content) {
        if (!content) return '';
        
        // Escape HTML to prevent XSS attacks
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Split into lines for better processing
        const lines = formatted.split(/\n/);
        const processedLines = [];
        let inList = false;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            
            // Check if this is a list item (starts with - or * followed by space)
            const listMatch = trimmed.match(/^([\-*])\s+(.+)$/);
            
            if (listMatch) {
                // Start a list if we're not in one
                if (!inList) {
                    if (processedLines.length > 0) {
                        processedLines.push('<br>');
                    }
                    processedLines.push('<ul>');
                    inList = true;
                }
                
                // Process the list item content (handle markdown inside)
                let itemContent = listMatch[2];
                
                // Apply markdown formatting to the item content
                itemContent = this.applyMarkdown(itemContent);
                
                processedLines.push(`<li>${itemContent}</li>`);
            } else {
                // End list if we were in one
                if (inList) {
                    processedLines.push('</ul>');
                    inList = false;
                }
                
                // Process regular line (not a list item)
                if (trimmed) {
                    const markdownContent = this.applyMarkdown(trimmed);
                    processedLines.push(markdownContent);
                    if (i < lines.length - 1) {
                        processedLines.push('<br>');
                    }
                } else if (i < lines.length - 1) {
                    // Empty line
                    processedLines.push('<br>');
                }
            }
        }
        
        // Close any open list
        if (inList) {
            processedLines.push('</ul>');
        }
        
        return processedLines.join('');
    }
    
    applyMarkdown(text) {
        let formatted = text;
        
        // Markdown formatting: **bold** (double asterisks) - must be done first
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Markdown formatting: __bold__ (double underscores) - must be done first
        formatted = formatted.replace(/__(.*?)__/g, '<strong>$1</strong>');
        
        // Markdown formatting: `code` (backticks) - before italic to avoid conflicts
        formatted = formatted.replace(/`([^`]+?)`/g, '<code>$1</code>');
        
        // Markdown formatting: *italic* (single asterisk)
        // Only match if not part of a bold pattern (already processed)
        // Use a simple approach: match single asterisks that aren't next to another asterisk
        formatted = formatted.replace(/(^|[^*])\*([^*]+?)\*([^*]|$)/g, '$1<em>$2</em>$3');
        
        // Markdown formatting: _italic_ (single underscore)
        // Only match if not part of a bold pattern
        formatted = formatted.replace(/(^|[^_])_([^_]+?)_([^_]|$)/g, '$1<em>$2</em>$3');
        
        return formatted;
    }

    showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar assistant';
        avatar.textContent = 'AI';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'message-content';
        
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        typingContent.appendChild(typingIndicator);
        typingDiv.appendChild(avatar);
        typingDiv.appendChild(typingContent);
        
        this.messagesArea.appendChild(typingDiv);
        this.scrollToBottom();
        
        return 'typing-indicator';
    }

    removeTyping(typingId) {
        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }
    }

    scrollToBottom() {
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
    }

    async loadChats() {
        try {
            const response = await fetch('/api/sessions');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.chats = data.sessions || [];
            this.renderChats();
            
            // Only auto-select if we don't have a current chat and no route
            if (!this.currentChatId && window.location.pathname === '/new') {
                if (this.chats.length === 0) {
                    await this.createNewChat();
                } else {
                    // Don't auto-select, let user choose or create new
                    this.showWelcome();
                }
            }
        } catch (error) {
            console.error('Failed to load chats:', error);
        }
    }

    renderChats() {
        this.chatList.innerHTML = '';
        
        this.chats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            if (chat.id === this.currentChatId) {
                chatItem.classList.add('active');
            }
            
            const chatName = document.createElement('div');
            chatName.className = 'chat-name';
            chatName.textContent = chat.name || 'New Chat';
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.textContent = '×';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                this.deleteChat(chat.id);
            };
            
            chatItem.appendChild(chatName);
            chatItem.appendChild(deleteBtn);
            
            chatItem.onclick = () => this.selectChat(chat.id);
            
            this.chatList.appendChild(chatItem);
        });
    }

    async createNewChat() {
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'New Chat' })
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            this.currentChatId = data.id;
            
            await this.loadChats();
            this.clearMessages();
            
            // Update URL to reflect new chat
            this.updateURL(this.currentChatId);
            
            console.log('New chat created:', this.currentChatId);
        } catch (error) {
            console.error('Failed to create new chat:', error);
        }
    }

    async selectChat(chatId) {
        // Don't update if already selected
        if (this.currentChatId === chatId) {
            return;
        }
        
        this.currentChatId = chatId;
        this.renderChats();
        await this.loadChatMessages(chatId);
        this.closeSidebar();
        
        // Update URL without reloading page
        this.updateURL(chatId);
    }

    async loadChatMessages(chatId) {
        try {
            const response = await fetch(`/api/sessions/${chatId}/messages`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.clearMessages();
            
            if (data.messages.length === 0) {
                this.showWelcome();
            } else {
                data.messages.forEach(msg => {
                    this.addMessage(msg.role, msg.content);
                });
            }
        } catch (error) {
            console.error('Failed to load chat messages:', error);
        }
    }

    async deleteChat(chatId) {
        if (!confirm('Delete this chat?')) return;
        
        try {
            const response = await fetch(`/api/sessions/${chatId}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            // If we deleted the current chat, redirect to new chat
            if (chatId === this.currentChatId) {
                this.currentChatId = null;
                this.redirectToNew();
                await this.createNewChat();
            } else {
                await this.loadChats();
            }
        } catch (error) {
            console.error('Failed to delete chat:', error);
        }
    }

    clearMessages() {
        this.messagesArea.innerHTML = '';
        this.showWelcome();
    }

    showWelcome() {
        this.messagesArea.innerHTML = `
            <div class="welcome-message" id="welcome-message">
                <h2>👋 Welcome to ChatGPT</h2>
                <p>Start a conversation by typing a message below.</p>
            </div>
        `;
        this.welcomeMessage = document.getElementById('welcome-message');
    }

    toggleSidebar() {
        this.sidebar.classList.toggle('open');
        this.overlay.classList.toggle('show');
    }

    closeSidebar() {
        this.sidebar.classList.remove('open');
        this.overlay.classList.remove('show');
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});