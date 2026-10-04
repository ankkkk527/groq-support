let currentChatId = null;
let chats = {};

function generateId() {
    return 'chat_' + Date.now();
}

function getCurrentTime() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' +
           now.getMinutes().toString().padStart(2, '0');
}

function saveChatsList() {
    localStorage.setItem('anvar_ai_chats', JSON.stringify(chats));
}

function loadChatsList() {
    const saved = localStorage.getItem('anvar_ai_chats');
    if (saved) chats = JSON.parse(saved);
}

function renderChatList() {
    const chatList = document.getElementById('chatList');
    chatList.innerHTML = '';
    const keys = Object.keys(chats).reverse();
    keys.forEach(id => {
        const btn = document.createElement('button');
        btn.className = 'chat-item' + (id === currentChatId ? ' active' : '');
        btn.textContent = chats[id].title || 'Yangi suhbat';
        btn.onclick = () => loadChat(id);
        chatList.appendChild(btn);
    });
}

function newChat() {
    currentChatId = generateId();
    chats[currentChatId] = { title: 'Yangi suhbat', messages: [] };
    saveChatsList();
    renderChatList();
    const messages = document.getElementById('messages');
    messages.innerHTML = '';
    addMessage('assistant', 'Salom! Men Anvar AI yordamchisiman. Har qanday savol bering!', false);
}

function loadChat(id) {
    currentChatId = id;
    const messages = document.getElementById('messages');
    messages.innerHTML = '';
    chats[id].messages.forEach(m => {
        addMessage(m.role, m.content, false);
    });
    renderChatList();
}

function addMessage(role, text, save = true) {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.innerHTML = text.replace(/\n/g, '<br>') + '<div class="time">' + getCurrentTime() + '</div>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    if (save && currentChatId) {
        chats[currentChatId].messages.push({ role, content: text });
        if (role === 'user' && chats[currentChatId].title === 'Yangi suhbat') {
            chats[currentChatId].title = text.substring(0, 30);
        }
        saveChatsList();
        renderChatList();
    }
}

function showTyping() {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'typing';
    div.id = 'typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById('typing');
    if (typing) typing.remove();
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    if (!message) return;

    addMessage('user', message);
    input.value = '';
    input.style.height = 'auto';
    showTyping();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentChatId, message: message })
        });
        const data = await response.json();
        removeTyping();
        addMessage('assistant', data.reply);
    } catch (error) {
        removeTyping();
        addMessage('assistant', 'Xatolik yuz berdi. Qaytadan urinib ko\'ring.');
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('hidden');
}

document.getElementById('userInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

document.getElementById('userInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js');
}

window.onload = function() {
    loadChatsList();
    if (Object.keys(chats).length === 0) {
        newChat();
    } else {
        const lastId = Object.keys(chats)[Object.keys(chats).length - 1];
        loadChat(lastId);
    }
    renderChatList();
};
