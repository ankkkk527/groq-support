const userId = 'user_' + Math.random().toString(36).substr(2, 9);

function getCurrentTime() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' +
           now.getMinutes().toString().padStart(2, '0');
}

function addMessage(role, text) {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.innerHTML = text + '<div class="time">' + getCurrentTime() + '</div>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
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
    showTyping();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, message: message })
        });
        const data = await response.json();
        removeTyping();
        addMessage('assistant', data.reply);
    } catch (error) {
        removeTyping();
        addMessage('assistant', 'Xatolik yuz berdi. Qaytadan urinib koring.');
    }
}

document.getElementById('userInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' \&\& !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

window.onload = function() {
    addMessage('assistant', 'Salom! Men Groq Support yordamchisiman. Groq haqida savollaringiz bormi? Yordam berishga tayyorman! 😊');
};
