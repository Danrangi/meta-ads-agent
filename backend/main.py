from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.ai_mentor import ask_meta_ads_mentor
from backend.rag_engine import (
    add_knowledge_source,
    list_saved_sources,
    delete_knowledge_source
)

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


# 3. Define the shape of incoming requests
class ChatRequest(BaseModel):
    message: str
    history: list = []


class KnowledgeRequest(BaseModel):
    source_type: str
    title: str
    content: str


class DeleteKnowledgeRequest(BaseModel):
    title: str


# 4. Health Check Endpoint (GET /)
@app.get("/")
def check_server_status():
    return {"status": "online", "message": "Meta Ads AI Backend is running!"}


# 5. Chat Endpoint (POST /chat)
@app.post("/chat")
def chat_with_mentor(request: ChatRequest):
    ai_reply = ask_meta_ads_mentor(request.message, request.history)
    return {"reply": ai_reply}


# 6. List Saved Knowledge Endpoint (GET /knowledge)
@app.get("/knowledge")
def get_knowledge_list():
    sources = list_saved_sources()
    return {"sources": sources}


# 7. Add New Knowledge Endpoint (POST /knowledge)
@app.post("/knowledge")
def upload_knowledge(request: KnowledgeRequest):
    try:
        result = add_knowledge_source(
            source_type=request.source_type,
            title=request.title,
            content_or_url=request.content
        )
        return {
            "status": "success",
            "message": f"Saved '{result['title']}' ({result['chunks_added']} knowledge chunks added!)"
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


# 8. Delete Knowledge Endpoint (POST /knowledge/delete)
@app.post("/knowledge/delete")
def remove_knowledge(request: DeleteKnowledgeRequest):
    removed_count = delete_knowledge_source(request.title)
    return {
        "status": "success",
        "message": f"Deleted '{request.title}' ({removed_count} chunks removed)."
    }
