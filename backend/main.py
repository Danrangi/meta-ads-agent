from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our AI Mentor function
from backend.ai_mentor import ask_meta_ads_mentor

# 1. Create our FastAPI application
app = FastAPI(title="Meta Ads AI Mentor Backend")

# 2. Setup CORS so our frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Define what an incoming request from the frontend looks like
# Why we added 'history': This list holds the previous messages in the chat
# so the AI can remember context when you ask follow-up questions.
class ChatRequest(BaseModel):
    message: str
    history: list = []


# 4. Health Check Endpoint (GET /)
@app.get("/")
def check_server_status():
    return {"status": "online", "message": "Meta Ads AI Backend is running!"}


# 5. Chat Endpoint (POST /chat)
@app.post("/chat")
def chat_with_mentor(request: ChatRequest):
    user_message = request.message
    chat_history = request.history

    # Send both the new question AND the conversation history to our AI Mentor
    ai_reply = ask_meta_ads_mentor(user_message, chat_history)

    return {"reply": ai_reply}
