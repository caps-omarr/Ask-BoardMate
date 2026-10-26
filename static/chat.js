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

// Markdown Formatter
function formatMarkdown(text) {
    if (!text) return '';
    
    // Normalize line breaks
    let raw = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    // Escape HTML tags to prevent XSS
    let escaped = raw
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Bold: **text**
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Markdown links: [title](url)
    escaped = escaped.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // Standalone URLs (not inside quotes/attributes)
    escaped = escaped.replace(/(?<!href=")(https?:\/\/[^\s<)]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');

    const lines = escaped.split('\n');
    let html = '';
    let currentList = null; // 'ul' or 'ol'

    function closeList() {
        if (currentList) {
            html += `</${currentList}>`;
            currentList = null;
        }
    }

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        let trimmed = line.trim();

        if (!trimmed) {
            closeList();
            continue;
        }

        // Horizontal divider: --- or --------------------
        if (/^[-*_]{3,}$/.test(trimmed)) {
            closeList();
            html += '<hr class="chat-divider">';
            continue;
        }

        // Headings: ###, ##, #
        const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
        if (headingMatch) {
            closeList();
            const level = headingMatch[1].length;
            const tag = level <= 2 ? 'h3' : 'h4';
            html += `<${tag} class="chat-heading">${headingMatch[2]}</${tag}>`;
            continue;
        }

        // Unordered list item (- or *)
        if (/^[-*]\s+/.test(trimmed)) {
            if (currentList !== 'ul') {
                closeList();
                html += '<ul class="chat-list">';
                currentList = 'ul';
            }
            html += `<li>${trimmed.replace(/^[-*]\s+/, '')}</li>`;
            continue;
        }

        // Numbered list item (1. 2.)
        const numMatch = trimmed.match(/^(\d+)\.\s+(.+)$/);
        if (numMatch) {
            if (currentList !== 'ol') {
                closeList();
                html += '<ol class="chat-list">';
                currentList = 'ol';
            }
            html += `<li>${numMatch[2]}</li>`;
            continue;
        }

        // Regular paragraph text
        closeList();
        html += `<p class="chat-p">${trimmed}</p>`;
    }

    closeList();
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

const conversationHistory = [];
let currentAbortController = null;
let isGenerating = false;

function setGeneratingState(generating) {
    isGenerating = generating;
    if (generating) {
        sendBtn.classList.add('stop-mode');
        sendBtn.setAttribute('title', 'Stop response');
        sendBtn.setAttribute('aria-label', 'Stop response');
    } else {
        sendBtn.classList.remove('stop-mode');
        sendBtn.setAttribute('title', 'Send message');
        sendBtn.setAttribute('aria-label', 'Send message');
        currentAbortController = null;
    }
}

function stopGeneration() {
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
    }
    removeTypingIndicator();
    setGeneratingState(false);
}

// Clicking the button while generating stops the active response
sendBtn.addEventListener('click', (e) => {
    if (isGenerating) {
        e.preventDefault();
        e.stopPropagation();
        stopGeneration();
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = messageInput.value.trim();
    if (!query) return;

    // If currently generating a previous response and user submits a new prompt,
    // cancel the in-flight response and start the new one immediately
    if (isGenerating) {
        stopGeneration();
    }

    // Append user query to UI
    appendMessage(query, true);
    messageInput.value = '';

    // Keep message input clickable and focused so user can type freely
    messageInput.focus();

    showTypingIndicator();
    setGeneratingState(true);

    currentAbortController = new AbortController();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: currentAbortController.signal,
            body: JSON.stringify({
                query: query,
                history: conversationHistory.slice(-10) // keep last 10 turns
            })
        });

        removeTypingIndicator();

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const data = await response.json();
        const replyText = data.answer || "I could not find an answer for that inquiry.";
        
        // Record in conversation history for multi-turn context
        conversationHistory.push({ role: 'user', content: query });
        conversationHistory.push({ role: 'assistant', content: replyText });
        
        appendMessage(replyText);

    } catch (err) {
        removeTypingIndicator();
        if (err.name === 'AbortError') {
            console.log('Response generation stopped by user.');
            return;
        }
        appendMessage("Unable to connect to the housing server. Please check your connection and try again.");
        console.error(err);
    } finally {
        setGeneratingState(false);
        messageInput.focus();
    }
});

