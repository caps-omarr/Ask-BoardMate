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

function escapeAttr(text) {
    if (!text) return '';
    return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Carousel Generator
function generateCarouselHtml(slides) {
    if (!slides || slides.length === 0) return '';
    const carouselId = 'carousel_' + Math.random().toString(36).substr(2, 9);

    if (slides.length === 1) {
        const s = slides[0];
        return `
            <div class="chat-photo-card" onclick="openPhotoModal('${s.url}', '${escapeAttr(s.alt)}')">
                <img src="${s.url}" alt="${escapeAttr(s.alt)}" loading="lazy" class="photo-card-img" />
                <div class="photo-card-badge">📷 1 Photo</div>
            </div>
        `;
    }

    const slidesHtml = slides.map((s, idx) => `
        <div class="carousel-slide ${idx === 0 ? 'active' : ''}">
            <img src="${s.url}" alt="${escapeAttr(s.alt)}" loading="lazy" class="carousel-img" onclick="openPhotoModal('${s.url}', '${escapeAttr(s.alt)}')" />
        </div>
    `).join('');

    const dotsHtml = slides.map((_, idx) => `
        <span class="carousel-dot ${idx === 0 ? 'active' : ''}" onclick="goToCarouselSlide('${carouselId}', ${idx})"></span>
    `).join('');

    return `
        <div class="chat-carousel" id="${carouselId}" data-index="0" data-total="${slides.length}">
            <div class="carousel-track">
                ${slidesHtml}
            </div>
            <button type="button" class="carousel-prev" aria-label="Previous photo" onclick="moveCarousel('${carouselId}', -1)">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
            </button>
            <button type="button" class="carousel-next" aria-label="Next photo" onclick="moveCarousel('${carouselId}', 1)">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
            <div class="carousel-counter">
                📷 <span class="carousel-current">1</span> / <span>${slides.length}</span>
            </div>
            <div class="carousel-dots">
                ${dotsHtml}
            </div>
        </div>
    `;
}

// Global Carousel Navigation
window.moveCarousel = function(carouselId, delta) {
    const carousel = document.getElementById(carouselId);
    if (!carousel) return;
    const total = parseInt(carousel.getAttribute('data-total') || '1', 10);
    let index = parseInt(carousel.getAttribute('data-index') || '0', 10);

    index = (index + delta + total) % total;
    carousel.setAttribute('data-index', index);

    const slides = carousel.querySelectorAll('.carousel-slide');
    slides.forEach((slide, idx) => {
        slide.classList.toggle('active', idx === index);
    });

    const dots = carousel.querySelectorAll('.carousel-dot');
    dots.forEach((dot, idx) => {
        dot.classList.toggle('active', idx === index);
    });

    const counter = carousel.querySelector('.carousel-current');
    if (counter) counter.textContent = (index + 1);
};

window.goToCarouselSlide = function(carouselId, targetIndex) {
    const carousel = document.getElementById(carouselId);
    if (!carousel) return;
    const total = parseInt(carousel.getAttribute('data-total') || '1', 10);
    if (targetIndex < 0 || targetIndex >= total) return;

    carousel.setAttribute('data-index', targetIndex);

    const slides = carousel.querySelectorAll('.carousel-slide');
    slides.forEach((slide, idx) => {
        slide.classList.toggle('active', idx === targetIndex);
    });

    const dots = carousel.querySelectorAll('.carousel-dot');
    dots.forEach((dot, idx) => {
        dot.classList.toggle('active', idx === targetIndex);
    });

    const counter = carousel.querySelector('.carousel-current');
    if (counter) counter.textContent = (targetIndex + 1);
};

// Lightbox Modal
window.openPhotoModal = function(url, alt) {
    let modal = document.getElementById('photoLightbox');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'photoLightbox';
        modal.className = 'photo-lightbox';
        modal.innerHTML = `
            <div class="lightbox-backdrop" onclick="closePhotoModal()"></div>
            <div class="lightbox-content">
                <button type="button" class="lightbox-close" onclick="closePhotoModal()" aria-label="Close photo preview">&times;</button>
                <img id="lightboxImg" src="" alt="" />
                <div id="lightboxCaption" class="lightbox-caption"></div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    const img = modal.querySelector('#lightboxImg');
    const cap = modal.querySelector('#lightboxCaption');
    img.src = url;
    img.alt = alt || 'Boarding house photo';
    cap.textContent = alt || '';
    modal.classList.add('open');
};

window.closePhotoModal = function() {
    const modal = document.getElementById('photoLightbox');
    if (modal) modal.classList.remove('open');
};

// Markdown Formatter with Carousel Support
function formatMarkdown(text) {
    if (!text) return '';

    // Normalize line breaks
    let raw = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    // Storage for carousel placeholders
    const carousels = [];

    // 1. Explicit :::carousel ... ::: blocks
    raw = raw.replace(/:::carousel([\s\S]*?):::/gi, (match, inner) => {
        const slides = [];
        const imgRegex = /!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g;
        let m;
        while ((m = imgRegex.exec(inner)) !== null) {
            slides.push({ alt: m[1] || 'Boarding House Photo', url: m[2] });
        }
        if (slides.length === 0) {
            const urlRegex = /(https?:\/\/[^\s<)]+)/g;
            while ((m = urlRegex.exec(inner)) !== null) {
                slides.push({ alt: 'Boarding House Photo', url: m[1] });
            }
        }
        if (slides.length === 0) return '';
        const token = `__CAROUSEL_PLACEHOLDER_${carousels.length}__`;
        carousels.push(generateCarouselHtml(slides));
        return `\n${token}\n`;
    });

    // 2. Consecutive markdown images ![alt](url) -> group into carousel
    const consecutiveImgRegex = /(?:!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)\s*)+/g;
    raw = raw.replace(consecutiveImgRegex, (match) => {
        const slides = [];
        const singleRegex = /!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g;
        let m;
        while ((m = singleRegex.exec(match)) !== null) {
            slides.push({ alt: m[1] || 'Boarding House Photo', url: m[2] });
        }
        if (slides.length === 0) return match;
        const token = `__CAROUSEL_PLACEHOLDER_${carousels.length}__`;
        carousels.push(generateCarouselHtml(slides));
        return `\n${token}\n`;
    });

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

        // Check for carousel placeholder
        const carouselMatch = trimmed.match(/^__CAROUSEL_PLACEHOLDER_(\d+)__$/);
        if (carouselMatch) {
            closeList();
            const idx = parseInt(carouselMatch[1], 10);
            html += carousels[idx] || '';
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

    // In case placeholders remained inside paragraphs, replace them globally
    for (let i = 0; i < carousels.length; i++) {
        const token = `__CAROUSEL_PLACEHOLDER_${i}__`;
        html = html.replace(new RegExp(token, 'g'), carousels[i]);
    }

    return html;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendMessage(text, isUser = false, save = true) {
    // Remove welcome hero once chat starts
    const hero = document.getElementById('welcomeHero');
    if (hero) hero.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    if (!isUser) {
        const authorHeader = document.createElement('div');
        authorHeader.className = 'bot-author-header';
        authorHeader.innerHTML = `
            <span class="bot-avatar-badge">🏠</span>
            <span class="bot-author-name">Ask-BoardMate</span>
        `;
        msgDiv.appendChild(authorHeader);
    }

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

    if (save) {
        savedUiMessages.push({ text, isUser });
        if (savedUiMessages.length > 50) savedUiMessages = savedUiMessages.slice(-50);
        try {
            localStorage.setItem('ebm_chat_ui_messages', JSON.stringify(savedUiMessages));
        } catch (e) {}
    }
}

function showTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message bot-message';
    indicatorDiv.id = 'typingIndicator';

    const authorHeader = document.createElement('div');
    authorHeader.className = 'bot-author-header';
    authorHeader.innerHTML = `
        <span class="bot-avatar-badge">🏠</span>
        <span class="bot-author-name">Ask-BoardMate</span>
    `;
    indicatorDiv.appendChild(authorHeader);

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

// Session & Conversational Memory Management
let currentSessionId = localStorage.getItem('ebm_session_id');
if (!currentSessionId) {
    currentSessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
    localStorage.setItem('ebm_session_id', currentSessionId);
}

let conversationHistory = [];
try {
    const savedHist = localStorage.getItem('ebm_conversation_history');
    if (savedHist) conversationHistory = JSON.parse(savedHist);
} catch (e) {
    conversationHistory = [];
}

let savedUiMessages = [];
try {
    const savedUi = localStorage.getItem('ebm_chat_ui_messages');
    if (savedUi) savedUiMessages = JSON.parse(savedUi);
} catch (e) {
    savedUiMessages = [];
}

// Render Claude-Style Welcome Hero with Suggestion Chips
function renderWelcomeHero() {
    chatMessages.innerHTML = `
        <div class="welcome-hero" id="welcomeHero">
            <div class="hero-glyph">🏠</div>
            <div class="hero-pill">TPC Student Housing Assistant</div>
            <h2 class="hero-title">How can I help you find housing today?</h2>
            <p class="hero-subtitle">Ask about accredited boarding houses in Talibon, Bohol, compare rental rates, check curfews, or view property photos.</p>
            
            <div class="suggestion-grid">
                <button type="button" class="suggestion-chip" onclick="sendSuggestedPrompt('Show me photos of Torres Boarding House')">
                    <span class="chip-icon">📷</span>
                    <span>Photos of Torres Boarding House</span>
                </button>
                <button type="button" class="suggestion-chip" onclick="sendSuggestedPrompt('What boarding houses are under ₱1,000 per month?')">
                    <span class="chip-icon">💰</span>
                    <span>Dorms under ₱1,000/month</span>
                </button>
                <button type="button" class="suggestion-chip" onclick="sendSuggestedPrompt('Which boarding houses allow female students only?')">
                    <span class="chip-icon">👩</span>
                    <span>Female-only dorms near TPC</span>
                </button>
                <button type="button" class="suggestion-chip" onclick="sendSuggestedPrompt('How many total boarding houses are in Talibon?')">
                    <span class="chip-icon">📍</span>
                    <span>Explore all 15 accredited houses</span>
                </button>
            </div>
        </div>
    `;
}

// Global Suggestion Handler
window.sendSuggestedPrompt = function(promptText) {
    if (!messageInput) return;
    messageInput.value = promptText;
    chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
};

// Initial view: restore saved messages or display welcome hero
if (savedUiMessages && savedUiMessages.length > 0) {
    chatMessages.innerHTML = '';
    savedUiMessages.forEach(m => {
        appendMessage(m.text, m.isUser, false);
    });
} else {
    renderWelcomeHero();
}

// Textarea Auto-Resize & Keyboard Enter handling
if (messageInput) {
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        }
    });
}

// "New Chat" / Reset Session Button
const newChatBtn = document.getElementById('newChatBtn');
if (newChatBtn) {
    newChatBtn.addEventListener('click', async () => {
        if (confirm("Start a new chat session? This will clear your current conversation history.")) {
            if (isGenerating) {
                stopGeneration();
            }

            try {
                await fetch('/api/chat/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: currentSessionId })
                });
            } catch (e) {}

            currentSessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
            localStorage.setItem('ebm_session_id', currentSessionId);

            conversationHistory = [];
            savedUiMessages = [];
            localStorage.removeItem('ebm_conversation_history');
            localStorage.removeItem('ebm_chat_ui_messages');

            renderWelcomeHero();
            messageInput.value = '';
            messageInput.style.height = 'auto';
            messageInput.focus();
        }
    });
}

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

    // Append user query to UI and persist
    appendMessage(query, true, true);
    messageInput.value = '';
    messageInput.style.height = 'auto';

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
                session_id: currentSessionId,
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
        if (conversationHistory.length > 20) {
            conversationHistory = conversationHistory.slice(-20);
        }
        try {
            localStorage.setItem('ebm_conversation_history', JSON.stringify(conversationHistory));
        } catch (e) {}
        
        appendMessage(replyText, false, true);

    } catch (err) {
        removeTypingIndicator();
        if (err.name === 'AbortError') {
            console.log('Response generation stopped by user.');
            return;
        }
        appendMessage("Unable to connect to the housing server. Please check your connection and try again.", false, true);
        console.error(err);
    } finally {
        setGeneratingState(false);
        messageInput.focus();
    }
});



