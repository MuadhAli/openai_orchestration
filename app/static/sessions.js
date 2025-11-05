/**
 * Session Management for ChatGPT Web UI
 */

// Session management variables
let currentSessionId = null;
let sessions = [];

// Initialize session management when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initSessionManagement();
});

function initSessionManagement() {
    console.log('Initializing session management...');
    
    // Bind events
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const newSessionBtn = document.getElementById('new-session-btn');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    if (newSessionBtn) {
        newSessionBtn.addEventListener('click', createNewSession);
    }
    
    // Load initial data
    loadSessions();
}

function toggleSidebar() {
    const sidebar = document.getElementById('session-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

async function loadSessions() {
    try {
        console.log('Loading sessions...');
        const response = await fetch('/api/sessions');
        if (response.ok) {
            const data = await response.json();
            sessions = data.sessions || [];
            console.log(`Loaded ${sessions.length} sessions`);
            
            // If no sessions exist, create a default one
            if (sessions.length === 0) {
                console.log('No sessions found, creating default session...');
                await createDefaultSession();
                return; // loadSessions will be called again after creating default session
            }
            
            renderSessions();
            
            // Auto-select first session if none selected
            if (!currentSessionId && sessions.length > 0) {
                console.log('Auto-selecting first session...');
                selectSession(sessions[0].id);
            }
        } else {
            console.error('Failed to load sessions:', response.statusText);
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
        // If loading fails, try to create a default session
        await createDefaultSession();
    }
}

async function createDefaultSession() {
    try {
        console.log('Creating default session...');
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: 'Default Chat'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Default session created:', data.id);
            // Reload sessions after creating default
            await loadSessions();
        } else {
            console.error('Failed to create default session:', response.statusText);
        }
    } catch (error) {
        console.error('Error creating default session:', error);
    }
}

function renderSessions() {
    const sessionList = document.getElementById('session-list');
    if (!sessionList) {
        console.warn('Session list element not found');
        return;
    }
    
    sessionList.innerHTML = '';
    
    if (sessions.length === 0) {
        sessionList.innerHTML = `
            <div style="text-align: center; color: var(--text-secondary, #666); padding: 2rem;">
                <p>No sessions yet</p>
                <small>Create your first session to get started!</small>
            </div>
        `;
        return;
    }
    
    sessions.forEach(session => {
        const sessionItem = document.createElement('div');
        sessionItem.className = 'session-item';
        sessionItem.dataset.sessionId = session.id;
        
        if (session.id === currentSessionId) {
            sessionItem.classList.add('active');
        }
        
        sessionItem.innerHTML = `
            <div class="session-info">
                <div class="session-name">${escapeHtml(session.name)}</div>
                <div class="session-preview">${escapeHtml(session.last_message || 'No messages yet')}</div>
            </div>
            <div class="session-actions">
                <button class="session-delete" onclick="deleteSession('${session.id}')" aria-label="Delete session">×</button>
            </div>
        `;
        
        // Add click event for session selection
        sessionItem.addEventListener('click', (e) => {
            if (!e.target.classList.contains('session-delete')) {
                selectSession(session.id);
            }
        });
        
        sessionList.appendChild(sessionItem);
    });
    
    console.log(`Rendered ${sessions.length} sessions`);
}

async function createNewSession() {
    try {
        console.log('Creating new session...');
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: `New Chat`
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('New session created:', data.id);
            await loadSessions();
            selectSession(data.id);
            showSuccessMessage('New chat created!');
        } else {
            throw new Error('Failed to create session');
        }
    } catch (error) {
        console.error('Error creating session:', error);
            showErrorMessage('Failed to create new chat. Please try again.');
    }
}

async function selectSession(sessionId) {
    console.log('Selecting session:', sessionId);
    currentSessionId = sessionId;
    
    // Update UI
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const selectedItem = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
    
    // Update the main chat app if it exists
    if (window.chatApp) {
        window.chatApp.currentSessionId = sessionId;
        await loadSessionMessages(sessionId);
    }
    
    // Close sidebar on mobile after selection
    const sidebar = document.getElementById('session-sidebar');
    if (sidebar && window.innerWidth <= 768) {
        sidebar.classList.remove('open');
    }
}

async function loadSessionMessages(sessionId) {
    try {
        console.log('Loading messages for session:', sessionId);
        const response = await fetch(`/api/sessions/${sessionId}/messages`);
        if (response.ok) {
            const data = await response.json();
            console.log(`Loaded ${data.messages.length} messages`);
            
            // Clear current messages
            if (window.chatApp) {
                window.chatApp.clearMessages();
                
                // Add messages
                data.messages.forEach(message => {
                    window.chatApp.addMessageWithAnimation(message.role, message.content);
                });
                
                if (data.messages.length === 0) {
                    window.chatApp.clearMessages();
                }
            }
        } else {
            console.error('Failed to load session messages:', response.statusText);
        }
    } catch (error) {
        console.error('Failed to load session messages:', error);
    }
}

async function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this chat?')) {
        return;
    }
    
    try {
        console.log('Deleting session:', sessionId);
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadSessions();
            
            // If deleted session was current, select another or clear
            if (currentSessionId === sessionId) {
                if (sessions.length > 0) {
                    selectSession(sessions[0].id);
                } else {
                    currentSessionId = null;
                    if (window.chatApp) {
                        window.chatApp.clearMessages();
                    }
                }
            }
            
            showSuccessMessage('Chat deleted successfully!');
        } else {
            throw new Error('Failed to delete session');
        }
    } catch (error) {
        console.error('Error deleting session:', error);
        showErrorMessage('Failed to delete chat. Please try again.');
    }
}

function showSuccessMessage(message) {
    console.log('Success:', message);
    if (window.chatApp && window.chatApp.showSuccessToast) {
        window.chatApp.showSuccessToast(message);
    } else {
        // Fallback: show alert
        alert(message);
    }
}

function showErrorMessage(message) {
    console.error('Error:', message);
    if (window.chatApp && window.chatApp.showErrorModal) {
        window.chatApp.showErrorModal(message);
    } else {
        // Fallback: show alert
        alert('Error: ' + message);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export for use by main chat app
window.sessionManager = {
    currentSessionId: () => currentSessionId,
    loadSessions,
    selectSession,
    createNewSession: async () => {
        await createNewSession();
        return currentSessionId;
    }
};

console.log('Session management script loaded');