const chatStreamContainer = document.querySelector('.chat-stream-container');
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const themeToggleBtn = document.getElementById('themeToggleBtn');
const chatSessionsList = document.getElementById('chatSessionsList');

// Sidebar Drawer Elements (Mobile & Responsive)
const sidebar = document.getElementById('sidebar');
const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');

function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
}

function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
}

if (sidebarToggleBtn) sidebarToggleBtn.addEventListener('click', openSidebar);
if (sidebarCloseBtn) sidebarCloseBtn.addEventListener('click', closeSidebar);
if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeSidebar);

// Desktop Sidebar Toggle (Smooth Collapse / Expand)
const appLayout = document.querySelector('.app-layout');
const desktopSidebarCollapseBtn = document.getElementById('desktopSidebarCollapseBtn');
const desktopSidebarExpandBtn = document.getElementById('desktopSidebarExpandBtn');

// Restore saved desktop sidebar preference
if (localStorage.getItem('ebm_desktop_sidebar_collapsed') === 'true') {
    if (appLayout) appLayout.classList.add('sidebar-collapsed');
}

function setDesktopSidebarCollapsed(collapsed) {
    if (!appLayout) return;
    appLayout.classList.toggle('sidebar-collapsed', collapsed);
    localStorage.setItem('ebm_desktop_sidebar_collapsed', collapsed ? 'true' : 'false');
}

if (desktopSidebarCollapseBtn) {
    desktopSidebarCollapseBtn.addEventListener('click', () => setDesktopSidebarCollapsed(true));
}
if (desktopSidebarExpandBtn) {
    desktopSidebarExpandBtn.addEventListener('click', () => setDesktopSidebarCollapsed(false));
}

// Theme Management (Light / Dark mode toggle with icon-only button)
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('ebm-theme', theme);
    if (themeToggleBtn) {
        themeToggleBtn.setAttribute('title', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
        themeToggleBtn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    }
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
                <div class="photo-card-badge">1 Photo</div>
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
                <span class="carousel-current">1</span> / <span>${slides.length} Photos</span>
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

// Reliable Smooth Scroll to Bottom for Chat Stream
function scrollToBottom(smooth = true) {
    if (!chatStreamContainer) return;
    if (smooth) {
        chatStreamContainer.scrollTo({
            top: chatStreamContainer.scrollHeight,
            behavior: 'smooth'
        });
    } else {
        chatStreamContainer.scrollTop = chatStreamContainer.scrollHeight;
    }
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
            <span class="bot-author-name">Ask BoardMate</span>
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
    scrollToBottom(true);

    // Re-scroll when any images/carousels finish loading
    const imgs = msgDiv.querySelectorAll('img');
    imgs.forEach(img => {
        if (!img.complete) {
            img.addEventListener('load', () => scrollToBottom(true), { once: true });
        }
    });

    if (save) {
        const session = getCurrentSession();
        if (session) {
            session.messages.push({ text, isUser });
            if (session.messages.length > 50) session.messages = session.messages.slice(-50);
            session.updatedAt = Date.now();
            saveSessionsToStorage();
        }
    }
}

function showTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message bot-message';
    indicatorDiv.id = 'typingIndicator';

    const authorHeader = document.createElement('div');
    authorHeader.className = 'bot-author-header';
    authorHeader.innerHTML = `
        <span class="bot-author-name">Ask BoardMate</span>
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
    scrollToBottom(true);
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// ==========================================================================
// Multi-Session Chat Management (Claude & ChatGPT Style)
// ==========================================================================
let allSessions = [];
try {
    const stored = localStorage.getItem('ebm_chat_sessions');
    if (stored) allSessions = JSON.parse(stored);
} catch (e) {
    allSessions = [];
}

// Migrate legacy single session if present
if (allSessions.length === 0) {
    let oldUi = [];
    try { oldUi = JSON.parse(localStorage.getItem('ebm_chat_ui_messages') || '[]'); } catch (e) {}
    let oldHist = [];
    try { oldHist = JSON.parse(localStorage.getItem('ebm_conversation_history') || '[]'); } catch (e) {}
    if (oldUi.length > 0) {
        const firstUser = oldUi.find(m => m.isUser);
        const title = firstUser ? (firstUser.text.length > 28 ? firstUser.text.substring(0, 28) + '...' : firstUser.text) : 'Previous Chat';
        allSessions.push({
            id: localStorage.getItem('ebm_session_id') || ('sess_' + Date.now()),
            title: title,
            updatedAt: Date.now(),
            messages: oldUi,
            history: oldHist
        });
        saveSessionsToStorage();
    }
}

let currentSessionId = localStorage.getItem('ebm_active_session_id');
if (!currentSessionId || !allSessions.some(s => s.id === currentSessionId)) {
    if (allSessions.length > 0) {
        currentSessionId = allSessions[0].id;
    } else {
        const initialSess = createNewSession();
        allSessions.push(initialSess);
        currentSessionId = initialSess.id;
        saveSessionsToStorage();
    }
    localStorage.setItem('ebm_active_session_id', currentSessionId);
}

function createNewSession() {
    return {
        id: 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
        title: 'New chat',
        updatedAt: Date.now(),
        messages: [],
        history: []
    };
}

function getCurrentSession() {
    let s = allSessions.find(item => item.id === currentSessionId);
    if (!s) {
        s = createNewSession();
        allSessions.unshift(s);
        currentSessionId = s.id;
        localStorage.setItem('ebm_active_session_id', currentSessionId);
        saveSessionsToStorage();
    }
    return s;
}

function saveSessionsToStorage() {
    try {
        localStorage.setItem('ebm_chat_sessions', JSON.stringify(allSessions));
    } catch (e) {}
}

function renderSessionsList() {
    if (!chatSessionsList) return;
    chatSessionsList.innerHTML = '';

    if (allSessions.length === 0) {
        chatSessionsList.innerHTML = '<li class="empty-sessions-hint">No saved chats yet. Start a conversation!</li>';
        return;
    }

    allSessions.forEach(s => {
        const li = document.createElement('li');
        li.className = 'session-item-wrap';
        const isActive = s.id === currentSessionId;

        const btn = document.createElement('button');
        btn.className = `session-item ${isActive ? 'active' : ''}`;
        btn.setAttribute('aria-label', `Open chat: ${s.title}`);
        btn.innerHTML = `
            <span class="session-item-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
            </span>
            <span class="session-item-title">${escapeAttr(s.title || 'New chat')}</span>
        `;
        btn.addEventListener('click', () => switchSession(s.id));

        const delBtn = document.createElement('button');
        delBtn.className = 'session-delete-btn';
        delBtn.setAttribute('title', 'Delete chat');
        delBtn.setAttribute('aria-label', `Delete chat: ${s.title}`);
        delBtn.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
        `;
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSession(s.id);
        });

        li.appendChild(btn);
        li.appendChild(delBtn);
        chatSessionsList.appendChild(li);
    });
}

function switchSession(sessionId) {
    if (sessionId === currentSessionId) {
        closeSidebar();
        return;
    }
    if (isGenerating) {
        stopGeneration();
    }
    currentSessionId = sessionId;
    localStorage.setItem('ebm_active_session_id', currentSessionId);
    closeSidebar();
    loadActiveSessionUi();
    renderSessionsList();
    if (messageInput) messageInput.focus();
}

function deleteSession(sessionId) {
    const idx = allSessions.findIndex(s => s.id === sessionId);
    if (idx === -1) return;

    allSessions.splice(idx, 1);
    saveSessionsToStorage();

    if (sessionId === currentSessionId) {
        if (allSessions.length > 0) {
            currentSessionId = allSessions[0].id;
        } else {
            const newS = createNewSession();
            allSessions.push(newS);
            currentSessionId = newS.id;
            saveSessionsToStorage();
        }
        localStorage.setItem('ebm_active_session_id', currentSessionId);
        loadActiveSessionUi();
    }
    renderSessionsList();
}

function loadActiveSessionUi() {
    const session = getCurrentSession();
    chatMessages.innerHTML = '';
    if (session.messages && session.messages.length > 0) {
        session.messages.forEach(m => {
            appendMessage(m.text, m.isUser, false);
        });
        scrollToBottom(false);
    } else {
        renderWelcomeHero();
    }
}

// Render Claude-Style Welcome Hero with Suggestion Chips
function renderWelcomeHero() {
    chatMessages.innerHTML = `
        <div class="welcome-hero" id="welcomeHero">
            <div class="hero-logo-wrap">
                <img src="/static/askboardmate.png" alt="Ask BoardMate" class="hero-circle-logo">
            </div>
            <div class="hero-pill">TPC Student Housing Assistant</div>
            <h2 class="hero-title">How can I help you find housing today?</h2>
            <p class="hero-subtitle">Ask about accredited boarding houses in Talibon, Bohol, compare rental rates, check curfews, or view property photos.</p>
            
            <div class="suggestion-grid">
                <button type="button" class="suggestion-chip" onclick="sendSuggestedPrompt('Show me photos of Torres Boarding House')">
                    <span>Photos of Torres Boarding House</span>
                </button>
                <button type="button" class="suggestion-chip" onclick="sendSuggestedPrompt('What boarding houses are under ₱1,000 per month?')">
                    <span>Dorms under ₱1,000/month</span>
                </button>
                <button type="button" class="suggestion-chip" onclick="sendSuggestedPrompt('Which boarding houses allow female students only?')">
                    <span>Female-only dorms near TPC</span>
                </button>
                <button type="button" class="suggestion-chip" onclick="sendSuggestedPrompt('How many total boarding houses are in Talibon?')">
                    <span>Explore all 15 accredited houses</span>
                </button>
            </div>
        </div>
    `;
}

// Global Suggestion Handler
window.sendSuggestedPrompt = function(promptText) {
    if (!messageInput || !promptText) return;
    closeSidebar();
    messageInput.value = promptText;
    chatForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
};

// Initial view: restore active session messages and render sessions list
renderSessionsList();
loadActiveSessionUi();

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

// "New Chat" / Create Session Button (Preserves previous chats)
const newChatBtn = document.getElementById('newChatBtn');

function handleNewChat() {
    closeSidebar();
    if (isGenerating) {
        stopGeneration();
    }

    const current = getCurrentSession();
    // If current session is already empty, just stay on it
    if (current && current.messages.length === 0) {
        renderWelcomeHero();
        if (messageInput) {
            messageInput.value = '';
            messageInput.style.height = 'auto';
            messageInput.focus();
        }
        return;
    }

    const newS = createNewSession();
    allSessions.unshift(newS);
    currentSessionId = newS.id;
    localStorage.setItem('ebm_active_session_id', currentSessionId);
    saveSessionsToStorage();

    renderSessionsList();
    renderWelcomeHero();
    if (messageInput) {
        messageInput.value = '';
        messageInput.style.height = 'auto';
        messageInput.focus();
    }
}

if (newChatBtn) {
    newChatBtn.addEventListener('click', handleNewChat);
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

    if (isGenerating) {
        stopGeneration();
    }

    const session = getCurrentSession();

    // Auto-name session from the first prompt
    if (session.messages.length === 0 || session.title === 'New chat') {
        let cleanTitle = query.replace(/[^\w\s\u00C0-\u017F₱-]/gi, '').trim();
        session.title = cleanTitle.length > 26 ? cleanTitle.substring(0, 26) + '...' : (cleanTitle || 'Conversation');
        renderSessionsList();
    }

    // Append user query to UI and persist
    appendMessage(query, true, true);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    messageInput.focus();

    showTypingIndicator();
    setGeneratingState(true);

    currentAbortController = new AbortController();

    try {
        const historyPayload = (session.history || []).slice(-10);
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: currentAbortController.signal,
            body: JSON.stringify({
                session_id: session.id,
                query: query,
                history: historyPayload
            })
        });

        removeTypingIndicator();

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const data = await response.json();
        const replyText = data.answer || "I could not find an answer for that inquiry.";
        
        // Record in conversation history for multi-turn context
        if (!session.history) session.history = [];
        session.history.push({ role: 'user', content: query });
        session.history.push({ role: 'assistant', content: replyText });
        if (session.history.length > 20) {
            session.history = session.history.slice(-20);
        }
        session.updatedAt = Date.now();
        saveSessionsToStorage();
        
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



