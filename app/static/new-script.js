// Simple, clean chat application
class ChatApp {
    constructor() {
        this.currentChatId = null;
        this.chats = [];
        this.isLoading = false;
        
        this.initElements();
        this.bindEvents();
        this.loadChats();
        
        console.log('ChatApp initialized');
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
        this.newChatBtn.addEventListener('click', () => this.createNewChat());
        
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
        messageContent.textContent = content;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.messagesArea.appendChild(messageDiv);
        this.scrollToBottom();
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
            
            if (this.chats.length === 0) {
                await this.createNewChat();
            } else {
                this.renderChats();
                this.selectChat(this.chats[0].id);
            }
        } catch (error) {
            console.error('Failed to load chats:', error);
            await this.createNewChat();
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
            
            console.log('New chat created:', this.currentChatId);
        } catch (error) {
            console.error('Failed to create new chat:', error);
        }
    }

    async selectChat(chatId) {
        this.currentChatId = chatId;
        this.renderChats();
        await this.loadChatMessages(chatId);
        this.closeSidebar();
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

            // If we deleted the current chat, create a new one
            if (chatId === this.currentChatId) {
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