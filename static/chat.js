const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const themeToggleBtn = document.getElementById('themeToggleBtn');

// Theme Management (Light / Dark mode toggle)
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('ebm-theme', theme);
}

// Initial theme detection from localStorage or system preference
const savedTheme = localStorage.getItem('ebm-theme');
if (savedTheme) {
    applyTheme(savedTheme);
} else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    applyTheme('dark');
} else {
    applyTheme('light');
}

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
    });
}

// Simple Markdown Formatter
function formatMarkdown(text) {
    if (!text) return '';
    
    // Escape HTML tags to prevent XSS
    let escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Bold: **text**
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // URLs to clickable links
    const urlPattern = /(https?:\/\/[^\s]+)/g;
    escaped = escaped.replace(urlPattern, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');

    // Convert newlines to breaks or bullet points
    const lines = escaped.split('\n');
    let html = '';
    let inList = false;

    for (let line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            if (!inList) {
                html += '<ul>';
                inList = true;
            }
            html += `<li>${trimmed.substring(2)}</li>`;
        } else if (/^\d+\.\s/.test(trimmed)) {
            if (!inList) {
                html += '<ol>';
                inList = true;
            }
            html += `<li>${trimmed.replace(/^\d+\.\s/, '')}</li>`;
        } else {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            if (trimmed.length > 0) {
                html += `<p>${trimmed}</p>`;
            }
        }
    }

    if (inList) {
        html += '</ul>';
    }

    return html;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendMessage(text, isUser = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (isUser) {
        contentDiv.textContent = text;
    } else {
        contentDiv.innerHTML = formatMarkdown(text);
    }

    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function showTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message bot-message';
    indicatorDiv.id = 'typingIndicator';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    indicatorDiv.appendChild(contentDiv);
    chatMessages.appendChild(indicatorDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = messageInput.value.trim();
    if (!query) return;

    // Append user query
    appendMessage(query, true);
    messageInput.value = '';
    messageInput.disabled = true;
    sendBtn.disabled = true;

    showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        removeTypingIndicator();

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const data = await response.json();
        appendMessage(data.answer || "I could not find an answer for that inquiry.");

    } catch (err) {
        removeTypingIndicator();
        appendMessage("Unable to connect to the housing server. Please check your connection and try again.");
        console.error(err);
    } finally {
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    }
});
