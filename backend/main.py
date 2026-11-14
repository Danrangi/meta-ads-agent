from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our new AI Mentor function from our ai_mentor.py file
from backend.ai_mentor import ask_meta_ads_mentor

# 1. Create our FastAPI application
app = FastAPI(title="Meta Ads AI Mentor Backend")

# 2. Setup CORS so our frontend HTML file is allowed to talk to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Define what an incoming request from the frontend must look like
class ChatRequest(BaseModel):
    message: str


# 4. Health Check Endpoint (GET /)
@app.get("/")
def check_server_status():
    return {"status": "online", "message": "Meta Ads AI Backend is running!"}


# 5. Chat Endpoint (POST /chat)
@app.post("/chat")
def chat_with_mentor(request: ChatRequest):
    # Grab the question you typed in the chat box
    user_message = request.message

    # Send your question to our Groq AI Mentor and get the expert response
    ai_reply = ask_meta_ads_mentor(user_message)

    # Send the AI's response back to the frontend chat screen
    return {"reply": ai_reply}
