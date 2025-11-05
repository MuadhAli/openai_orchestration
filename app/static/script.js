/**
 * ChatGPT Web UI - Frontend JavaScript
 * Handles chat functionality, API communication, and user interactions
 */

class ChatApp {
    constructor() {
        // DOM elements
        this.chatForm = document.getElementById('chat-form');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.messagesContainer = document.getElementById('messages-container');
        this.loadingIndicator = document.getElementById('loading-indicator');
        this.newChatButton = document.getElementById('new-chat-btn');
        this.charCounter = document.getElementById('char-counter');
        
        // Error modal elements
        this.errorModal = document.getElementById('error-modal');
        this.errorMessage = document.getElementById('error-message');
        this.closeErrorModal = document.getElementById('close-error-modal');
        this.retryButton = document.getElementById('retry-button');
        this.dismissError = document.getElementById('dismiss-error');
        
        // Success toast elements
        this.successToast = document.getElementById('success-toast');
        this.successMessage = document.getElementById('success-message');
        
        // Session sidebar elements
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        this.sessionSidebar = document.getElementById('session-sidebar');
        this.sessionList = document.getElementById('session-list');
        this.newSessionButton = document.getElementById('new-session-btn');
        
        // Document upload elements
        this.uploadButton = document.getElementById('upload-document-btn');
        this.uploadModal = document.getElementById('upload-modal');
        this.closeUploadModal = document.getElementById('close-upload-modal');
        this.uploadForm = document.getElementById('upload-form');
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.fileInfo = document.getElementById('file-info');
        this.uploadSubmit = document.getElementById('upload-submit');
        this.cancelUpload = document.getElementById('cancel-upload');
        this.documentsContainer = document.getElementById('documents-container');
        
        // App state
        this.currentSessionId = null;
        this.isLoading = false;
        this.lastFailedMessage = null;
        
        // Initialize the app
        this.init();
    }
    
    /**
     * Initialize the chat application
     */
    init() {
        console.log('Initializing ChatApp...');
        
        // Check critical elements
        if (!this.messageInput) {
            console.error('Message input not found! ID: message-input');
        }
        if (!this.sendButton) {
            console.error('Send button not found! ID: send-button');
        }
        if (!this.charCounter) {
            console.error('Char counter not found! ID: char-counter');
        }
        
        this.bindEvents();
        this.updateSendButtonState();
        this.updateCharCounter();
        this.focusInput();
        
        // Integrate with session manager
        if (window.sessionManager) {
            this.currentSessionId = window.sessionManager.currentSessionId();
        }
        
        console.log('ChatApp initialized successfully');
    }
    
    /**
     * Bind event listeners to DOM elements
     */
    bindEvents() {
        // Check if elements exist before binding
        if (!this.chatForm || !this.messageInput || !this.sendButton) {
            console.error('Critical DOM elements not found!');
            console.log('chatForm:', this.chatForm);
            console.log('messageInput:', this.messageInput);
            console.log('sendButton:', this.sendButton);
            return;
        }
        
        // Form submission
        this.chatForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Input events
        this.messageInput.addEventListener('input', () => {
            this.updateSendButtonState();
            this.updateCharCounter();
            this.autoResizeTextarea();
        });
        
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // New chat button
        this.newChatButton.addEventListener('click', () => {
            this.createNewChat();
        });
        
        // Session sidebar events
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
        
        if (this.newSessionButton) {
            this.newSessionButton.addEventListener('click', () => this.createNewChat());
        }
        
        // Document upload events
        if (this.uploadButton) {
            this.uploadButton.addEventListener('click', () => this.showUploadModal());
        }
        
        if (this.closeUploadModal) {
            this.closeUploadModal.addEventListener('click', () => this.hideUploadModal());
        }
        
        if (this.uploadArea && this.fileInput) {
            this.uploadArea.addEventListener('click', () => this.fileInput.click());
            this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
            this.uploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        
        if (this.uploadSubmit) {
            this.uploadSubmit.addEventListener('click', () => this.uploadDocument());
        }
        
        if (this.cancelUpload) {
            this.cancelUpload.addEventListener('click', () => this.hideUploadModal());
        }
        
        // Error modal events
        this.closeErrorModal.addEventListener('click', () => this.hideErrorModal());
        this.dismissError.addEventListener('click', () => this.hideErrorModal());
        this.retryButton.addEventListener('click', () => this.retryLastMessage());
        
        // Close modal when clicking outside
        this.errorModal.addEventListener('click', (e) => {
            if (e.target === this.errorModal) {
                this.hideErrorModal();
            }
        });
        
        // Enhanced keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Escape key to close modal
            if (e.key === 'Escape' && this.errorModal.style.display !== 'none') {
                this.hideErrorModal();
            }
            
            // Advanced keyboard shortcuts
            this.handleAdvancedKeyboardShortcuts(e);
        });
    }
    
    /**
     * Handle form submission
     */
    async handleFormSubmit(e) {
        e.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) {
            return;
        }
        
        await this.sendMessage(message);
    }
    
    /**
     * Handle keyboard events in the input field
     */
    handleKeyDown(e) {
        // Enter key to send (without Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleFormSubmit(e);
        }
    }
    
    /**
     * Send a message to the chat API
     */
    async sendMessage(message) {
        try {
            this.setLoading(true);
            this.lastFailedMessage = message;
            
            // Add user message to chat with animation
            this.addMessageWithAnimation('user', message);
            
            // Show typing indicator
            this.showTypingIndicator();
            
            // Clear input
            this.messageInput.value = '';
            this.updateSendButtonState();
            this.updateCharCounter();
            this.autoResizeTextarea();
            
            // Prepare request data
            const requestData = {
                message: message
            };
            
            // Get current session ID from session manager
            let sessionId = window.sessionManager ? window.sessionManager.currentSessionId() : this.currentSessionId;
            
            // If no session exists, create one first
            if (!sessionId) {
                console.log('No session found, creating default session...');
                if (window.sessionManager && window.sessionManager.createNewSession) {
                    await window.sessionManager.createNewSession();
                    // Get the new session ID
                    sessionId = window.sessionManager.currentSessionId();
                    if (!sessionId) {
                        throw new Error('Failed to create session');
                    }
                } else {
                    throw new Error('No session available and cannot create one');
                }
            }
            
            // Make API request to session-specific endpoint
            const endpoint = `/api/sessions/${sessionId}/chat`;
                
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // The new API returns {user_message: {...}, assistant_message: {...}}
            if (!data.assistant_message) {
                throw new Error('No assistant response received');
            }
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add AI response to chat with animation
            this.addMessageWithAnimation('assistant', data.assistant_message.content);
            
            // Clear the failed message since it succeeded
            this.lastFailedMessage = null;
            this.retryCount = 0; // Reset retry count on success
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            
            // Handle connection errors with retry logic
            if (error.message.includes('Failed to fetch')) {
                this.handleConnectionError();
            } else {
                this.showErrorModal(this.getErrorMessage(error));
            }
        } finally {
            this.setLoading(false);
            this.focusInput();
        }
    }
    
    /**
     * Add a message to the chat display (legacy method, use addMessageWithAnimation for better UX)
     */
    addMessage(role, content) {
        this.addMessageWithAnimation(role, content);
    }
    
    /**
     * Set loading state
     */
    setLoading(loading) {
        this.isLoading = loading;
        
        if (loading) {
            this.loadingIndicator.style.display = 'flex';
            this.sendButton.disabled = true;
            this.messageInput.disabled = true;
        } else {
            this.loadingIndicator.style.display = 'none';
            this.sendButton.disabled = false;
            this.messageInput.disabled = false;
            this.updateSendButtonState();
        }
        
        // Scroll to bottom to show loading indicator
        if (loading) {
            this.scrollToBottom();
        }
    }
    
    /**
     * Update send button state based on input
     */
    updateSendButtonState() {
        if (!this.messageInput || !this.sendButton) {
            console.warn('Cannot update send button - elements missing');
            return;
        }
        
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isLoading;
    }
    
    /**
     * Update character counter
     */
    updateCharCounter() {
        if (!this.messageInput || !this.charCounter) {
            console.warn('Cannot update char counter - elements missing');
            return;
        }
        
        const currentLength = this.messageInput.value.length;
        const maxLength = this.messageInput.maxLength || 4000;
        this.charCounter.textContent = `${currentLength} / ${maxLength}`;
        
        // Change color if approaching limit
        if (currentLength > maxLength * 0.9) {
            this.charCounter.style.color = 'var(--error-color, #ff0000)';
        } else if (currentLength > maxLength * 0.8) {
            this.charCounter.style.color = 'var(--warning-color, #ff9800)';
        } else {
            this.charCounter.style.color = 'var(--text-secondary, #666)';
        }
    }
    
    /**
     * Auto-resize textarea based on content
     */
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
    }
    
    /**
     * Enhanced auto-scroll with smooth behavior
     */
    smoothScrollToBottom() {
        const container = this.messagesContainer;
        const isNearBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 100;
        
        // Only auto-scroll if user is near the bottom
        if (isNearBottom) {
            container.scrollTo({
                top: container.scrollHeight,
                behavior: 'smooth'
            });
        }
    }
    
    /**
     * Show typing indicator for better UX
     */
    showTypingIndicator() {
        // Remove existing typing indicator
        this.hideTypingIndicator();
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content typing-content';
        messageContent.innerHTML = `
            <div class="typing-animation">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        typingDiv.appendChild(avatar);
        typingDiv.appendChild(messageContent);
        this.messagesContainer.appendChild(typingDiv);
        
        this.smoothScrollToBottom();
    }
    
    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    /**
     * Enhanced message display with better animations
     */
    addMessageWithAnimation(role, content) {
        // Remove welcome message if it exists
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.opacity = '0';
            setTimeout(() => welcomeMessage.remove(), 300);
        }
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        
        // Create avatar
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? 'U' : 'AI';
        
        // Create message content with enhanced formatting
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format message content (handle line breaks, etc.)
        const formattedContent = this.formatMessageContent(content);
        messageContent.innerHTML = formattedContent;
        
        // Create timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();
        
        // Append elements
        messageContent.appendChild(timestamp);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        // Add to messages container
        this.messagesContainer.appendChild(messageDiv);
        
        // Animate in
        setTimeout(() => {
            messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 50);
        
        // Scroll to bottom
        this.smoothScrollToBottom();
    }
    
    /**
     * Format message content for better display
     */
    formatMessageContent(content) {
        // Convert line breaks to <br> tags
        let formatted = content.replace(/\n/g, '<br>');
        
        // Basic markdown-like formatting
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
        
        return formatted;
    }
    
    /**
     * Enhanced error handling with retry mechanism
     */
    handleConnectionError() {
        const retryCount = this.retryCount || 0;
        const maxRetries = 3;
        
        if (retryCount < maxRetries) {
            this.retryCount = retryCount + 1;
            setTimeout(() => {
                if (this.lastFailedMessage) {
                    this.sendMessage(this.lastFailedMessage);
                }
            }, 1000 * retryCount); // Exponential backoff
        } else {
            this.showErrorModal('Connection failed after multiple attempts. Please check your internet connection.');
            this.retryCount = 0;
        }
    }
    
    /**
     * Save conversation to local storage
     */
    saveConversationToStorage() {
        if (!this.conversationId) return;
        
        const messages = Array.from(this.messagesContainer.querySelectorAll('.message')).map(msg => {
            const role = msg.classList.contains('user') ? 'user' : 'assistant';
            const content = msg.querySelector('.message-content').textContent.replace(/\d{1,2}:\d{2}:\d{2}\s?(AM|PM)?$/, '').trim();
            return { role, content };
        });
        
        const conversation = {
            id: this.conversationId,
            messages: messages,
            timestamp: Date.now()
        };
        
        try {
            localStorage.setItem(`chat_${this.conversationId}`, JSON.stringify(conversation));
        } catch (error) {
            console.warn('Failed to save conversation to localStorage:', error);
        }
    }
    
    /**
     * Load conversation from local storage
     */
    loadConversationFromStorage(conversationId) {
        try {
            const stored = localStorage.getItem(`chat_${conversationId}`);
            if (stored) {
                const conversation = JSON.parse(stored);
                this.clearMessages();
                
                conversation.messages.forEach(msg => {
                    this.addMessageWithAnimation(msg.role, msg.content);
                });
                
                return true;
            }
        } catch (error) {
            console.warn('Failed to load conversation from localStorage:', error);
        }
        return false;
    }
    
    /**
     * Enhanced keyboard shortcuts
     */
    handleAdvancedKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter to send message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            this.handleFormSubmit(e);
        }
        
        // Ctrl/Cmd + K to start new chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.startNewChat();
        }
        
        // Escape to clear input
        if (e.key === 'Escape' && e.target === this.messageInput) {
            this.messageInput.value = '';
            this.updateSendButtonState();
            this.updateCharCounter();
            this.autoResizeTextarea();
        }
    }
    
    /**
     * Scroll chat to bottom (legacy method, use smoothScrollToBottom for better UX)
     */
    scrollToBottom() {
        this.smoothScrollToBottom();
    }
    
    /**
     * Focus the input field
     */
    focusInput() {
        setTimeout(() => {
            this.messageInput.focus();
        }, 100);
    }
    
    /**
     * Create a new chat (same as new session)
     */
    async createNewChat() {
        if (window.sessionManager) {
            await window.sessionManager.createNewSession();
        } else {
            await this.startNewChat();
        }
    }

    /**
     * Start a new chat conversation
     */
    async startNewChat() {
        try {
            // Clear current conversation
            this.conversationId = null;
            this.lastFailedMessage = null;
            
            // Clear messages and show welcome message
            this.clearMessages();
            
            // Create new conversation on server
            const response = await fetch('/api/chat/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to start new conversation');
            }
            
            this.conversationId = data.conversation_id;
            this.showSuccessToast('New conversation started!');
            this.focusInput();
            
        } catch (error) {
            console.error('Error starting new chat:', error);
            this.showErrorModal('Failed to start new conversation. Please try again.');
        }
    }
    
    /**
     * Clear all messages and show welcome message
     */
    clearMessages() {
        this.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">👋</div>
                <h2>Welcome to ChatGPT Web UI</h2>
                <p>Start a conversation by typing a message below. I'm here to help with any questions or tasks you have!</p>
            </div>
        `;
    }
    
    /**
     * Show error modal
     */
    showErrorModal(message) {
        this.errorMessage.textContent = message;
        this.errorModal.style.display = 'flex';
        this.errorModal.setAttribute('aria-hidden', 'false');
        
        // Focus the close button for accessibility
        setTimeout(() => {
            this.closeErrorModal.focus();
        }, 100);
    }
    
    /**
     * Hide error modal
     */
    hideErrorModal() {
        this.errorModal.style.display = 'none';
        this.errorModal.setAttribute('aria-hidden', 'true');
        this.focusInput();
    }
    
    /**
     * Retry the last failed message
     */
    async retryLastMessage() {
        this.hideErrorModal();
        
        if (this.lastFailedMessage) {
            await this.sendMessage(this.lastFailedMessage);
        }
    }
    
    /**
     * Show success toast notification
     */
    showSuccessToast(message) {
        this.successMessage.textContent = message;
        this.successToast.style.display = 'flex';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            this.hideSuccessToast();
        }, 3000);
    }
    
    /**
     * Hide success toast
     */
    hideSuccessToast() {
        this.successToast.style.display = 'none';
    }
    
    /**
     * Get user-friendly error message
     */
    getErrorMessage(error) {
        if (error.message.includes('Failed to fetch')) {
            return 'Unable to connect to the server. Please check your internet connection and try again.';
        } else if (error.message.includes('500')) {
            return 'The server encountered an error. Please try again in a moment.';
        } else if (error.message.includes('400')) {
            return 'Invalid request. Please check your message and try again.';
        } else if (error.message.includes('429')) {
            return 'Too many requests. Please wait a moment before trying again.';
        } else {
            return error.message || 'An unexpected error occurred. Please try again.';
        }
    }
    
    // Session Management Methods
    
    /**
     * Load sessions from the server
     */
    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            if (response.ok) {
                const data = await response.json();
                this.sessions = data.sessions || [];
                this.renderSessions();
                
                // Auto-select first session if none selected
                if (!this.currentSessionId && this.sessions.length > 0) {
                    this.selectSession(this.sessions[0].id);
                }
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }
    
    /**
     * Render sessions in the sidebar
     */
    renderSessions() {
        if (!this.sessionList) return;
        
        this.sessionList.innerHTML = '';
        
        if (this.sessions.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-sessions';
            emptyState.innerHTML = `
                <p>No sessions yet</p>
                <p>Create your first session to get started!</p>
            `;
            this.sessionList.appendChild(emptyState);
            return;
        }
        
        this.sessions.forEach(session => {
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
            sessionItem.dataset.sessionId = session.id;
            
            if (session.id === this.currentSessionId) {
                sessionItem.classList.add('active');
            }
            
            sessionItem.innerHTML = `
                <div class="session-info">
                    <div class="session-name">${session.name}</div>
                    <div class="session-preview">${session.last_message || 'No messages yet'}</div>
                </div>
                <div class="session-actions">
                    <button class="session-delete" data-session-id="${session.id}" aria-label="Delete session">×</button>
                </div>
            `;
            
            // Add click event for session selection
            sessionItem.addEventListener('click', (e) => {
                if (!e.target.classList.contains('session-delete')) {
                    this.selectSession(session.id);
                }
            });
            
            // Add delete event
            const deleteBtn = sessionItem.querySelector('.session-delete');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSession(session.id);
            });
            
            this.sessionList.appendChild(sessionItem);
        });
    }
    
    /**
     * Create a new session
     */
    async createNewSession() {
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: `Chat ${new Date().toLocaleString()}`
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                await this.loadSessions();
                this.selectSession(data.id);
                this.showSuccessToast('New session created!');
            } else {
                throw new Error('Failed to create session');
            }
        } catch (error) {
            console.error('Error creating session:', error);
            this.showErrorModal('Failed to create new session. Please try again.');
        }
    }
    
    /**
     * Select a session
     */
    async selectSession(sessionId) {
        this.currentSessionId = sessionId;
        
        // Update UI
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const selectedItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('active');
        }
        
        // Load session messages
        await this.loadSessionMessages(sessionId);
    }
    
    /**
     * Load messages for a session
     */
    async loadSessionMessages(sessionId) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}/messages`);
            if (response.ok) {
                const data = await response.json();
                this.clearMessages();
                
                data.messages.forEach(message => {
                    this.addMessageWithAnimation(message.role, message.content);
                });
                
                if (data.messages.length === 0) {
                    // Show welcome message for empty sessions
                    this.clearMessages();
                }
            }
        } catch (error) {
            console.error('Failed to load session messages:', error);
        }
    }
    
    /**
     * Delete a session
     */
    async deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this session?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/sessions/${sessionId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                await this.lo

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing ChatApp...');
    
    // Add a small delay to ensure all elements are rendered
    setTimeout(() => {
        window.chatApp = new ChatApp();
    }, 100);
});

// Handle page visibility changes to maintain connection
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.chatApp) {
        // Page became visible, could check connection status here
        console.log('Page became visible');
    }
});

// Handle online/offline events
window.addEventListener('online', () => {
    if (window.chatApp) {
        window.chatApp.showSuccessToast('Connection restored!');
    }
});

window.addEventListener('offline', () => {
    if (window.chatApp) {
        window.chatApp.showErrorModal('You are currently offline. Please check your internet connection.');
    }
});