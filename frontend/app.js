// 1. Grab the HTML elements we need to interact with so our code knows where they are
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// 2. This function has one job: create a new message bubble and add it to the screen
function addMessageToScreen(text, sender) {
    // Create a new <div> element in memory
    const messageDiv = document.createElement('div');
    
    // Give it the general 'message' style
    messageDiv.classList.add('message');
    
    // Decide if it should look like a user message (blue, on the right) or AI message (gray, on the left)
    if (sender === 'user') {
        messageDiv.classList.add('user-message');
    } else {
        messageDiv.classList.add('ai-message');
    }
    
    // Put the actual text inside the bubble
    messageDiv.textContent = text;
    
    // Place the new bubble inside the chat box on the screen
    chatBox.appendChild(messageDiv);
    
    // Automatically scroll to the very bottom so you always see the newest message
    chatBox.scrollTop = chatBox.scrollHeight;
}

// 3. This function runs whenever you click the "Send" button
function handleSendMessage() {
    // Get the text you typed, and remove accidental empty spaces at the beginning or end
    const text = userInput.value.trim();
    
    // Why check this? So we don't send empty blank messages if you click Send by mistake
    if (text === '') {
        return;
    }
    
    // Show your message on the screen
    addMessageToScreen(text, 'user');
    
    // Clear the typing box so it is ready for your next question
    userInput.value = '';
    
    // Temporary placeholder reply until we build our Python backend in the next step
    setTimeout(function() {
        addMessageToScreen("I received your message! Soon, I will be connected to our Python backend to give you real Meta Ads advice.", 'ai');
    }, 500);
}

// 4. Listen for clicks on the Send button and run handleSendMessage when clicked
sendBtn.addEventListener('click', handleSendMessage);

// 5. Also allow pressing the "Enter" key to send a message (without holding Shift) for faster chatting
userInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        // Prevent the Enter key from creating a new blank line inside the box
        event.preventDefault();
        handleSendMessage();
    }
});
