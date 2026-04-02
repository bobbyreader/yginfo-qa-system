(function() {
    const CONFIG = {
        apiBase: 'http://localhost:8000',
        tenantId: 'default',
        channel: 'webchat',
        userId: 'user_' + Math.random().toString(36).substr(2, 9),
        sessionId: null,
    };

    let messagesEl, inputEl, sendBtn;

    function init(config) {
        Object.assign(CONFIG, config);
        CONFIG.sessionId = 'session_' + Date.now();

        messagesEl = document.getElementById('yg-messages');
        inputEl = document.getElementById('yg-input');
        sendBtn = document.getElementById('yg-send');

        inputEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    window.YGWidget = { init };

    function toggleWidget() {
        const widget = document.getElementById('yg-widget');
        const isMin = widget.classList.toggle('minimized');
        const toggle = document.getElementById('yg-toggle');
        toggle.textContent = isMin ? '−' : '−';
        messagesEl.style.display = isMin ? 'none' : 'block';
        document.getElementById('yg-input-area').style.display = isMin ? 'none' : 'flex';
    }
    window.toggleWidget = toggleWidget;

    async function sendMessage() {
        const text = inputEl.value.trim();
        if (!text) return;

        addMessage('user', text);
        inputEl.value = '';
        sendBtn.disabled = true;

        try {
            const resp = await fetch(`${CONFIG.apiBase}/api/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tenant_id: CONFIG.tenantId,
                    channel: CONFIG.channel,
                    user_id: CONFIG.userId,
                    session_id: CONFIG.sessionId,
                    message: text,
                }),
            });

            const data = await resp.json();

            addMessage('assistant', data.reply);

            if (data.recommendations && data.recommendations.length > 0) {
                const recEl = document.createElement('div');
                recEl.className = 'message assistant';
                recEl.innerHTML = '<small>推荐问题：</small><br>' +
                    data.recommendations.map(r => `<a href="javascript:void(0)" onclick="YGWidget.send('${r}')">${r}</a>`).join('<br>');
                messagesEl.appendChild(recEl);
            }
        } catch (err) {
            addMessage('assistant', '抱歉，服务出了点问题，请稍后再试。');
        } finally {
            sendBtn.disabled = false;
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
    }
    window.YGWidget.send = sendMessage;

    function addMessage(role, text) {
        const el = document.createElement('div');
        el.className = `message ${role}`;
        el.textContent = text;
        messagesEl.appendChild(el);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }
})();