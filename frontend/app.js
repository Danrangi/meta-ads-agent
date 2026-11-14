// 1. Store our Backend URL in one place at the top
// Why: Right now, our Python server runs on our own computer (127.0.0.1:8000).
// Later, when we put the backend on Render, we only have to change this ONE line!
const BACKEND_URL = 'http://127.0.0.1:8000/chat';

// 2. Grab the HTML elements from the page so our code can use them
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');


// 3. Function to create a chat bubble and put it on the screen
function addMessageToScreen(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');

    // Give it the blue style for 'user' or gray style for 'ai'
    if (sender === 'user') {
        messageDiv.classList.add('user-message');
    } else {
        messageDiv.classList.add('ai-message');
    }

    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);

    // Always scroll to the bottom so the newest message is visible
    chatBox.scrollTop = chatBox.scrollHeight;
}


// 4. Function that sends the user's message to our Python FastAPI backend
// Why use 'async'? Because talking to a server takes time (especially when AI is thinking).
// 'async/await' tells JavaScript to wait patiently for the answer without freezing the screen.
async function sendMessageToBackend(userText) {
    try {
        // Send the message to Python using a POST request
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: {
                // Tell Python that we are sending data in standard JSON format
                'Content-Type': 'application/json'
            },
            // Pack our message into the exact format Python expects: {"message": "..."}
            body: JSON.stringify({ message: userText })
        });

        // Unpack the JSON reply that Python sent back to us
        const data = await response.json();

        // Return the reply text so we can show it on the screen
        return data.reply;

    } catch (error) {
        // Why do we have a 'catch' block?
        // If you forget to start the Python server, the request will fail.
        // Instead of failing silently, we return a helpful reminder message!
        console.error('Error connecting to backend:', error);
        return 'Error: Could not reach the Python backend. Make sure uvicorn is running on port 8000!';
    }
}


// 5. Main function that runs when you click Send or press Enter
async function handleSendMessage() {
    const text = userInput.value.trim();

    // Stop here if the box is empty so we don't send blank messages
    if (text === '') {
        return;
    }

    // Step A: Show your message on the screen immediately
    addMessageToScreen(text, 'user');

    // Step B: Clear the input box right away so it feels fast and clean
    userInput.value = '';

    // Step C: Disable the Send button while waiting so we don't accidentally send twice
    sendBtn.disabled = true;
    sendBtn.textContent = '...';

    // Step D: Ask our helper function to send the text to Python and wait for the reply
    const aiReply = await sendMessageToBackend(text);

    // Step E: Show Python's reply on the screen
    addMessageToScreen(aiReply, 'ai');

    // Step F: Turn the Send button back on for the next question
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
}


// 6. Connect the Send button and Enter key to our function
sendBtn.addEventListener('click', handleSendMessage);

userInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
    }
});
