const RENDER_BACKEND_URL = 'https://meta-ads-agent-3uta.onrender.com';

const isLocalComputer = (
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.protocol === 'file:'
);

const API_BASE_URL = isLocalComputer ? 'http://127.0.0.1:8000' : RENDER_BACKEND_URL;

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const actionButtons = document.querySelectorAll('.action-btn');

const toggleKbBtn = document.getElementById('toggle-kb-btn');
const kbPanel = document.getElementById('kb-panel');
const kbType = document.getElementById('kb-type');
const kbTitle = document.getElementById('kb-title');
const kbContent = document.getElementById('kb-content');
const saveKbBtn = document.getElementById('save-kb-btn');
const kbStatus = document.getElementById('kb-status');
const savedSourcesList = document.getElementById('saved-sources-list');

const chatHistory = [];


function formatTextForScreen(rawText) {
    let safeText = rawText
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    let formattedText = safeText.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    formattedText = formattedText.replace(/### /g, "");
    formattedText = formattedText.replace(/## /g, "");

    return formattedText;
}


function addMessageToScreen(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');

    if (sender === 'user') {
        messageDiv.classList.add('user-message');
        messageDiv.textContent = text;
    } else {
        messageDiv.classList.add('ai-message');
        messageDiv.innerHTML = formatTextForScreen(text);
    }

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}


function toggleKnowledgePanel() {
    kbPanel.classList.toggle('hidden');
    if (!kbPanel.classList.contains('hidden')) {
        loadSavedSources();
    }
}


async function deleteSource(title) {
    try {
        await fetch(`${API_BASE_URL}/knowledge/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title })
        });
        loadSavedSources();
    } catch (error) {
        console.error('Could not delete source:', error);
    }
}


async function loadSavedSources() {
    try {
        const response = await fetch(`${API_BASE_URL}/knowledge`);
        const data = await response.json();

        savedSourcesList.innerHTML = '';

        if (!data.sources || data.sources.length === 0) {
            savedSourcesList.innerHTML = '<li>No sources uploaded yet. Add your first YouTube video or article above!</li>';
            return;
        }

        data.sources.forEach(function(source) {
            const li = document.createElement('li');
            li.style.marginBottom = '6px';

            const textSpan = document.createElement('span');
            textSpan.textContent = `${source.title} (${source.source_type} - ${source.chunks} chunks) `;

            const delBtn = document.createElement('button');
            delBtn.textContent = 'Delete';
            delBtn.style.marginLeft = '8px';
            delBtn.style.padding = '2px 6px';
            delBtn.style.fontSize = '0.75rem';
            delBtn.style.color = '#dc2626';
            delBtn.style.border = '1px solid #fca5a5';
            delBtn.style.borderRadius = '4px';
            delBtn.style.background = '#fef2f2';
            delBtn.style.cursor = 'pointer';

            delBtn.addEventListener('click', function() {
                deleteSource(source.title);
            });

            li.appendChild(textSpan);
            li.appendChild(delBtn);
            savedSourcesList.appendChild(li);
        });
    } catch (error) {
        savedSourcesList.innerHTML = '<li>Could not load sources. Make sure backend is running.</li>';
    }
}


async function handleSaveKnowledge() {
    const type = kbType.value;
    const title = kbTitle.value.trim();
    const content = kbContent.value.trim();

    if (!title || !content) {
        kbStatus.style.color = '#dc2626';
        kbStatus.textContent = 'Please enter both a Title and a Link/Text!';
        return;
    }

    saveKbBtn.disabled = true;
    saveKbBtn.textContent = 'Saving...';
    kbStatus.style.color = '#475569';
    kbStatus.textContent = 'Extracting content and saving to RAG brain...';

    try {
        const response = await fetch(`${API_BASE_URL}/knowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_type: type,
                title: title,
                content: content
            })
        });

        const data = await response.json();

        if (response.ok) {
            kbStatus.style.color = '#059669';
            kbStatus.textContent = '✅ ' + data.message;
            kbTitle.value = '';
            kbContent.value = '';
            loadSavedSources();
        } else {
            kbStatus.style.color = '#dc2626';
            kbStatus.textContent = '❌ Error: ' + (data.detail || 'Could not save knowledge.');
        }
    } catch (error) {
        kbStatus.style.color = '#dc2626';
        kbStatus.textContent = '❌ Could not connect to Python server.';
    }

    saveKbBtn.disabled = false;
    saveKbBtn.textContent = 'Save to Brain';
}


function fillPromptTemplate(actionType) {
    if (actionType === 'strategy') {
        userInput.value = "Build a complete Meta Ads strategy for:\n- Business Type: [e.g., Fashion Brand / Dental Clinic]\n- Offer & Price: ₦[e.g., ₦35,000]\n- Location: [e.g., Lagos & Abuja]\n- Where do customers buy?: [WhatsApp / Instagram DM / Website]";
    } else if (actionType === 'copy') {
        userInput.value = "Write 3 high-converting Nigerian ad copy variations (Direct Offer, Trust/Social Proof, Urgency) for:\n- Business: [ ]\n- Offer & Price: ₦[ ]\n- Target Location: [e.g., Lagos / Abuja]";
    } else if (actionType === 'targeting') {
        userInput.value = "Suggest the exact Targeting, Funnel (WhatsApp vs Website), and Daily Budget for:\n- Business: [ ]\n- Daily Budget: ₦[e.g., ₦10,000/day]\n- Target Cities: [ ]";
    } else if (actionType === 'analyze') {
        userInput.value = "Analyze my Meta Ad campaign numbers and tell me the ONE main bottleneck:\n- Amount Spent: ₦[ ]\n- Outbound CTR: [ ]%\n- Leads / WhatsApp Chats: [ ]\n- Actual Sales: [ ]";
    }

    userInput.focus();
}


function startNewChat() {
    chatHistory.length = 0;
    chatBox.innerHTML = '';
    addMessageToScreen(
        "New chat started! Click one of the quick tools below or ask me anything based on your uploaded knowledge.",
        "ai"
    );
}


async function sendMessageToBackend(userText) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: userText,
                history: chatHistory
            })
        });

        const data = await response.json();
        return data.reply;

    } catch (error) {
        console.error('Error connecting to backend:', error);
        return 'Error: Could not reach the Python backend. (Note: On Render free tier, the server may take 30 seconds to wake up on your first message!)';
    }
}


async function handleSendMessage() {
    const text = userInput.value.trim();

    if (text === '') {
        return;
    }

    addMessageToScreen(text, 'user');
    userInput.value = '';

    sendBtn.disabled = true;
    sendBtn.textContent = '...';

    const aiReply = await sendMessageToBackend(text);

    addMessageToScreen(aiReply, 'ai');

    chatHistory.push({ role: 'user', content: text });
    chatHistory.push({ role: 'assistant', content: aiReply });

    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
}


sendBtn.addEventListener('click', handleSendMessage);
newChatBtn.addEventListener('click', startNewChat);
toggleKbBtn.addEventListener('click', toggleKnowledgePanel);
saveKbBtn.addEventListener('click', handleSaveKnowledge);

actionButtons.forEach(function(button) {
    button.addEventListener('click', function() {
        const actionType = button.getAttribute('data-action');
        fillPromptTemplate(actionType);
    });
});

userInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
    }
});
