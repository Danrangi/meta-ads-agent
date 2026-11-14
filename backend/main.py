from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. Create our FastAPI application
# Why: This 'app' object is the core of our backend server.
app = FastAPI(title="Meta Ads AI Mentor Backend")

# 2. Setup CORS (Cross-Origin Resource Sharing)
# Why: Because our Frontend (on Vercel or our browser) and Backend (on Render)
# live at different web addresses. Without this block, your web browser will 
# block them from talking to each other for security reasons.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows our frontend to connect from anywhere
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, etc.
    allow_headers=["*"],
)

# 3. Define the shape of an incoming chat message
# Why: This acts like a security guard at the door. It makes sure that whenever
# the frontend sends data to our backend, it MUST include a 'message' as text (str).
class ChatRequest(BaseModel):
    message: str


# 4. Health Check Endpoint (GET /)
# Why: When we deploy to Render later, we want a simple URL we can visit in our
# browser just to confirm the Python server is awake and running properly.
@app.get("/")
def check_server_status():
    return {"status": "online", "message": "Meta Ads AI Backend is running!"}


# 5. Chat Endpoint (POST /chat)
# Why: This is the main door where our frontend will send the user's question
# and wait for the AI's response.
@app.post("/chat")
def chat_with_mentor(request: ChatRequest):
    # Grab the text message that the user typed in the frontend
    user_message = request.message

    # For right now, before we add the AI key, we return a test reply from Python
    # Why: We test the connection step-by-step. If this works, we know Python works!
    reply_text = f"Python Backend received your message: '{user_message}'. Next step: connecting Groq AI!"

    # Send the reply back to the frontend as a clean dictionary (JSON)
    return {"reply": reply_text}
