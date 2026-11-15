// 1. Backend URL
const BACKEND_URL = 'http://127.0.0.1:8000/chat';

// 2. Grab HTML elements from the page
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const actionButtons = document.querySelectorAll('.action-btn');

// 3. Conversation memory list
const chatHistory = [];


// 4. Helper function to make AI text look clean and turn **text** into real Bold text
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


// 5. Function to create a chat bubble and put it on the screen
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


// 6. Function to fill the input box with Nigerian Meta Ads templates
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


// 7. Function to clear the chat and start fresh
function startNewChat() {
    chatHistory.length = 0;
    chatBox.innerHTML = '';
    addMessageToScreen(
        "New chat started! Click one of the quick tools below or tell me about the Nigerian campaign you are working on.",
        "ai"
    );
}


// 8. Function that sends the user's message AND chat history to Python
async function sendMessageToBackend(userText) {
    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userText,
                history: chatHistory
            })
        });

        const data = await response.json();
        return data.reply;

    } catch (error) {
        console.error('Error connecting to backend:', error);
        return 'Error: Could not reach the Python backend. Make sure uvicorn is running on port 8000!';
    }
}


// 9. Main function that runs when you click Send or press Enter
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


// 10. Connect all buttons to their functions
sendBtn.addEventListener('click', handleSendMessage);
newChatBtn.addEventListener('click', startNewChat);

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
