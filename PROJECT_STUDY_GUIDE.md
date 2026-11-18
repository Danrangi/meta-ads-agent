cat > PROJECT_STUDY_GUIDE.md << 'EOF'
# 📘 Complete Project Study Guide & Codebook
**Project:** Personal Meta Ads AI Mentor (Nigeria & Global RAG Edition)

This document contains the complete source code and plain-English explanations for every file in this project. Use this guide to study how a real full-stack AI + RAG application is built from scratch.

---

## Part 1: How the Architecture Works (The Restaurant Analogy)

Think of this web application like a restaurant:

1. **The Frontend (`frontend/index.html`, `style.css`, `app.js`) is the Waiter:**
   - It lives on **Vercel**.
   - It shows you the chat box, buttons, and knowledge upload form.
   - When you type a question and click Send, the Waiter (`app.js`) packages your question into JSON format and carries it over the internet to the Kitchen.

2. **The Backend Server (`backend/main.py`) is the Kitchen Door:**
   - It lives on **Render** and runs using **Python + FastAPI**.
   - Why don't we call Groq AI directly from the Frontend? **Security!** If we put our secret `GROQ_API_KEY` inside `frontend/app.js`, anyone could right-click the website and steal our key. Hiding it inside the Python Backend keeps it 100% secret.

3. **The RAG Engine (`backend/rag_engine.py`) is the Recipe Book:**
   - **RAG** stands for **Retrieval-Augmented Generation**.
   - When you paste a YouTube link or blog URL, `rag_engine.py` extracts all the words, chops them into 250-word paragraphs (**chunks**), and saves them inside `backend/knowledge/rag_store.json`.
   - When you ask a question, it searches all 490+ chunks, grabs the **top 4 most relevant chunks**, and hands them to the AI Chef.

4. **The AI Brain (`backend/ai_mentor.py`) is the Chef:**
   - It combines:
     1. Your **System Prompt** (instructions to act as a Nigerian & Global Meta Ads Mentor).
     2. The **Retrieved RAG Chunks** from your saved YouTube videos and blogs.
     3. Your **Chat History** (so it remembers earlier messages).
     4. Your **New Question**.
   - It sends all of this to the smartest available free model on **Groq** and returns the final answer to the screen.

---

## Part 2: Backend Code & Explanations

### 1. `backend/main.py` (The Traffic Controller)
**Why this file exists:** It opens the web doors (**Endpoints**) so our Frontend can talk to Python.
- `GET /`: Checks if the server is awake.
- `POST /chat`: Receives your question and returns the AI's answer.
- `GET /knowledge`: Lists all YouTube videos and articles saved in your RAG brain.
- `POST /knowledge`: Saves a new YouTube video, blog URL, or text note.
- `POST /knowledge/delete`: Removes a source from your RAG brain.

~~~python
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

# 2. Setup CORS (Cross-Origin Resource Sharing)
# Why: Because our Frontend (on Vercel) and Backend (on Render) live at different
# web addresses. Without CORS, web browsers block them from talking for security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Define the exact shape of incoming requests using Pydantic BaseModel
# Why: Acts like a security guard at the door checking that incoming data is valid.
class ChatRequest(BaseModel):
    message: str
    history: list = []

class KnowledgeRequest(BaseModel):
    source_type: str      # 'youtube', 'url', or 'text'
    title: str            # Name of the video or article
    content: str          # The URL or raw text

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
~~~

---

### 2. `backend/rag_engine.py` (The RAG Knowledge Base Engine)
**Why this file exists:** It handles downloading YouTube transcripts (`youtube-transcript-api`), scraping blog articles (`BeautifulSoup`), splitting long text into 250-word chunks, saving them to `backend/knowledge/rag_store.json`, and searching those chunks when you ask a question.

**Why we built RAG in pure Python instead of heavy libraries like ChromaDB/PyTorch:**
Render's free hosting tier gives you **512MB of RAM**. Heavy AI vector libraries use over 1,000MB of RAM and crash free servers. Our pure-Python keyword scorer uses **less than 5MB of RAM** and searches 500+ chunks in milliseconds!

~~~python
import os
import json
import re
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

# 1. Define where our permanent RAG database file lives
CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
RAG_FILE_PATH = os.path.join(CURRENT_FOLDER, "knowledge", "rag_store.json")

# 2. Load the saved knowledge database from disk
def load_rag_store() -> list:
    if not os.path.exists(RAG_FILE_PATH):
        return []
    try:
        with open(RAG_FILE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []

# 3. Save the updated knowledge database back to disk
def save_rag_store(store_data: list):
    os.makedirs(os.path.dirname(RAG_FILE_PATH), exist_ok=True)
    with open(RAG_FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(store_data, file, indent=2, ensure_ascii=False)

# 4. Split a long video or article into smaller ~250-word chunks
# Why: We cannot feed 20 whole books into an AI prompt at once. Chopping text into
# 250-word chunks lets us search and send ONLY the 3-4 paragraphs that answer your question!
def split_text_into_chunks(text: str, chunk_size_words: int = 250) -> list:
    words = text.split()
    chunks = []
    
    # Step forward by 200 words (leaving a 50-word overlap so ideas aren't cut in half)
    step = 200
    for i in range(0, len(words), step):
        slice_of_words = words[i : i + chunk_size_words]
        chunk_text = " ".join(slice_of_words).strip()
        if chunk_text:
            chunks.append(chunk_text)
            
    return chunks

# 5. Extract spoken words (captions) from a YouTube Video URL
def extract_youtube_text(youtube_url: str) -> str:
    video_id = ""
    if "youtu.be/" in youtube_url:
        video_id = youtube_url.split("youtu.be/")[1].split("?")[0][:11]
    elif "v=" in youtube_url:
        video_id = youtube_url.split("v=")[1].split("&")[0][:11]
    elif "shorts/" in youtube_url:
        video_id = youtube_url.split("shorts/")[1].split("?")[0][:11]
    else:
        raise ValueError("Invalid YouTube link. Please paste a full youtube.com or youtu.be link.")

    ytt_api = YouTubeTranscriptApi()
    fetched_transcript = ytt_api.fetch(video_id)

    lines = [snippet.text for snippet in fetched_transcript]
    full_text = " ".join(lines)
    
    if not full_text.strip():
        raise ValueError("This YouTube video returned an empty transcript.")
        
    return full_text

# 6. Extract clean article text from any Blog Post or Official Meta Help URL
def extract_website_text(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    response = requests.get(url, headers=headers, timeout=20)
    
    if response.status_code != 200:
        raise ValueError(f"Website blocked or unavailable (Status code {response.status_code}).")

    # Strip out menus, scripts, and styling so only clean article paragraphs remain
    soup = BeautifulSoup(response.text, "html.parser")
    for junk_tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        junk_tag.decompose()

    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all(["p", "h1", "h2", "h3", "li"])]
    clean_text = " ".join([p for p in paragraphs if len(p) > 20])

    if not clean_text.strip():
        raise ValueError("Could not find readable article text on that page.")

    return clean_text

# 7. Add a new resource (YouTube, Blog URL, or Text) into our permanent RAG store
def add_knowledge_source(source_type: str, title: str, content_or_url: str) -> dict:
    store = load_rag_store()

    # Remove any old chunks with the exact same title so we never create duplicates
    store = [item for item in store if item["title"].lower() != title.lower()]

    if source_type == "youtube":
        raw_text = extract_youtube_text(content_or_url)
    elif source_type == "url":
        raw_text = extract_website_text(content_or_url)
    elif source_type == "text":
        raw_text = content_or_url.strip()
    else:
        raise ValueError("Unknown source type.")

    if len(raw_text) < 20:
        raise ValueError("The extracted content is too short to save.")

    chunks = split_text_into_chunks(raw_text)
    
    for index, chunk_text in enumerate(chunks):
        store.append({
            "title": title,
            "source_type": source_type,
            "chunk_index": index + 1,
            "content": chunk_text
        })

    save_rag_store(store)
    return {"title": title, "chunks_added": len(chunks)}

# 8. Delete a knowledge source by its title
def delete_knowledge_source(title_to_delete: str) -> int:
    store = load_rag_store()
    original_count = len(store)
    updated_store = [item for item in store if item["title"] != title_to_delete]
    save_rag_store(updated_store)
    return original_count - len(updated_store)

# 9. List all unique knowledge sources saved so far
def list_saved_sources() -> list:
    store = load_rag_store()
    seen_titles = {}
    
    for item in store:
        title = item["title"]
        if title not in seen_titles:
            seen_titles[title] = {
                "title": title,
                "source_type": item.get("source_type", "text"),
                "chunks": 0
            }
        seen_titles[title]["chunks"] += 1

    return list(seen_titles.values())

# 10. Retrieve ONLY the most relevant chunks for a user's question
def retrieve_relevant_knowledge(user_question: str, top_k: int = 4) -> str:
    store = load_rag_store()
    if not store:
        return ""

    stop_words = {"the", "and", "for", "with", "how", "what", "should", "can", "you", "my", "in", "to", "of", "is", "are", "on", "ads", "meta", "facebook"}
    question_words = set(re.findall(r"\w+", user_question.lower())) - stop_words

    scored_chunks = []
    for item in store:
        chunk_lower = item["content"].lower()
        title_lower = item["title"].lower()
        
        score = 0
        for word in question_words:
            if word in chunk_lower:
                score += 2
            if word in title_lower:
                score += 3
                
        scored_chunks.append((score, item))

    scored_chunks.sort(key=lambda pair: pair[0], reverse=True)
    best_items = [pair[1] for pair in scored_chunks[:top_k]]

    formatted_results = []
    for item in best_items:
        formatted_results.append(f"[Source: {item['title']}]\n{item['content']}")

    return "\n\n---\n\n".join(formatted_results)
~~~

---

### 3. `backend/ai_mentor.py` (The AI Brain & Model Ranker)
**Why this file exists:** It builds the System Prompt (combining Nigerian market rules + retrieved RAG chunks), ranks all models on your Groq account so we **always** pick the smartest 70B/120B/Llama-4 model first, and sends the conversation to Groq.

~~~python
import os
from dotenv import load_dotenv
from groq import Groq

from backend.rag_engine import retrieve_relevant_knowledge

# 1. Load secret API keys from .env
load_dotenv()

# 2. Define the core instructions for our Nigerian & Global Meta Ads Mentor
BASE_SYSTEM_PROMPT = """
You are my personal Meta Ads (Facebook & Instagram) AI Strategist and Mentor.
I am based in Nigeria and running Meta Ads primarily for the Nigerian market (unless I state otherwise).

Whenever you help me with ad strategy, ad copy, targeting, or campaign analysis, you MUST follow these rules:
1. Use the facts and strategies from the RETRIEVED KNOWLEDGE BASE CHUNKS below (when relevant) and mention the saved source title you are using. Note: Raw YouTube transcripts have no punctuation, so extract the ideas cleanly and NEVER copy their rambling spoken style.
2. Tailor your advice to the Nigerian market (use Naira ₦ for budgets/offers, consider WhatsApp/IG DM funnels, Lagos/Abuja/PH targeting, and Nigerian buyer trust) unless I specify a foreign country.
3. NEVER repeat any sentence or phrase. Answer clearly, structured with bullet points and **bold headings**.
4. STRICT FORMATTING RULE: Never use Markdown tables (|---|), never use HTML tags like <br>, and never use code blocks (```).
5. Always include a short section at the end called "**💡 Why This Works (Lesson):**" explaining the Meta Ads principle behind your advice in simple English.
"""

# 3. Build the System Prompt dynamically using RAG
def build_rag_system_prompt(user_question: str) -> str:
    relevant_chunks = retrieve_relevant_knowledge(user_question, top_k=3)
    
    if not relevant_chunks:
        return (
            f"{BASE_SYSTEM_PROMPT}\n\n"
            f"Note: No custom knowledge chunks matched this question yet."
        )

    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"=== RETRIEVED EXPERT KNOWLEDGE (FROM SAVED VIDEOS & DOCS) ===\n"
        f"{relevant_chunks}\n"
        f"============================================================="
    )

# 4. Score each model by its intelligence/size so we ALWAYS pick the smartest brain first!
def score_model_intelligence(model_name: str) -> int:
    name = model_name.lower()

    # Tier 1: Massive & Latest Flagship Models (Highest Priority)
    if any(k in name for k in ["70b", "120b", "maverick", "llama-4", "kimi", "qwen3-32b", "gpt-oss"]):
        return 100

    # Tier 2: Strong Mid-Size Reasoning/Chat Models
    if any(k in name for k in ["32b", "27b", "17b", "scout", "compound", "mixtral"]):
        return 80

    # Tier 3: Fast Standard Chat Models (9B / 8B)
    if any(k in name for k in ["gemma2-9b", "8b"]):
        return 50

    return 10

# 5. Get a cleanly sorted list of valid chat models from Smartest to Smallest
def get_ranked_chat_models(client) -> list:
    models_response = client.models.list()
    all_models = [model.id for model in models_response.data]

    # Block audio models, safety-checkers, and small foreign test models ('allam')
    blocked_words = ["whisper", "guard", "tts", "orpheus", "playai", "embed", "allam", "vision"]

    valid_models = []
    for model_name in all_models:
        name_lower = model_name.lower()
        if not any(bad_word in name_lower for bad_word in blocked_words):
            valid_models.append(model_name)

    valid_models.sort()
    valid_models.sort(key=score_model_intelligence, reverse=True)

    return valid_models

# 6. Main function to ask Groq using our smartest model + RAG prompt
def ask_meta_ads_mentor(user_question: str, chat_history: list) -> str:
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "PASTE_YOUR_GROQ_KEY_HERE":
            raise ValueError("Missing GROQ_API_KEY! Please check your .env file.")

        client = Groq(api_key=api_key)
        ranked_models = get_ranked_chat_models(client)

        system_prompt = build_rag_system_prompt(user_question)

        messages_for_ai = [{"role": "system", "content": system_prompt}]
        for past_message in chat_history:
            messages_for_ai.append({
                "role": past_message["role"],
                "content": past_message["content"]
            })
        messages_for_ai.append({"role": "user", "content": user_question})

        last_error = ""
        for chosen_model in ranked_models:
            try:
                response = client.chat.completions.create(
                    model=chosen_model,
                    messages=messages_for_ai,
                    temperature=0.5,
                    frequency_penalty=0.7,  # Prevents word/sentence repetition loops
                    max_tokens=1800
                )
                return response.choices[0].message.content
            except Exception as model_error:
                last_error = str(model_error)
                continue

        return f"AI Error: None of the models succeeded. Last error: {last_error}"

    except Exception as error:
        return f"AI Error: {str(error)}"
~~~

---

## Part 3: Frontend Code & Explanations

### 1. `frontend/index.html` (The Page Structure)
**Why this file exists:** It defines the visual building blocks of our page:
- `<header>`: Holds the title, the `📚 Add Knowledge` button, and the `New Chat` button.
- `<section id="kb-panel">`: The collapsible drawer for uploading YouTube links, blog URLs, or text notes.
- `<main id="chat-box">`: The scrollable conversation area.
- `<div class="quick-actions">`: The 4 pill buttons for fast prompt templates.
- `<footer>`: The typing box and `Send` button.

### 2. `frontend/style.css` (The Clean Design)
**Why this file exists:** It styles our HTML so it looks clean and works on both computers and mobile phones.
- **Key CSS Trick We Learned (`white-space: pre-wrap;`):** By default, HTML collapses all line breaks into a single space, turning AI answers into a messy wall of text. Adding `white-space: pre-wrap;` on `.message` preserves all the AI's paragraphs and bullet points automatically!

### 3. `frontend/app.js` (The Frontend Brain)
**Why this file exists:** It listens for button clicks, formats `**bold**` text cleanly, keeps track of `chatHistory` so the AI remembers the conversation, and uses `fetch()` to send data to our Python server.

**Key Engineering Trick (`isLocalComputer` check):**
At the very top of `app.js`, our code automatically checks if you opened the page on your laptop (`localhost` / `file:`) or on the live internet (`vercel.app`), and switches between `http://127.0.0.1:8000` and your live Render URL automatically!

---

## Part 4: 6 Real-World Engineering Bugs We Solved Together

As you built this project, you encountered real-world software engineering bugs. Here is what caused each one and how we solved it:

1. **`Client.__init__() got an unexpected keyword argument 'proxies'`**
   - **Cause:** An older version of the `groq` package (`0.11.0`) conflicted with a newer internet library (`httpx`).
   - **Fix:** Upgraded `groq>=0.15.0` in `requirements.txt`.

2. **`ModuleNotFoundError: No module named 'groq'` on Windows**
   - **Cause:** Running `pip install` installed packages into Windows' global Python instead of the project's `.venv` virtual environment toolbox.
   - **Fix:** Ran `.venv/Scripts/python -m pip install` and `.venv/Scripts/python -m uvicorn` so Windows always used the `.venv` toolbox.

3. **YouTube `no element found: line 1, column 0`**
   - **Cause:** YouTube blocked older versions of `youtube-transcript-api` (`0.6.3`).
   - **Fix:** Upgraded to `youtube-transcript-api>=1.0.3` and updated our function to use `YouTubeTranscriptApi().fetch(video_id)`.

4. **Groq `404 model_not_found` & `orpheus` Audio Model Errors**
   - **Cause:** Hardcoding a single model name breaks if an account doesn't have it enabled, and picking any available model without filtering accidentally picked Groq's `orpheus` voice model.
   - **Fix:** Wrote `get_ranked_chat_models()` to filter out voice/audio models (`whisper`, `tts`, `orpheus`, `playai`) and try valid chat models in order.

5. **The AI Repeating Sentences in a Loop**
   - **Cause:** Groq returned its model list in random order, sometimes landing on a tiny foreign test model (`allam-2-7b`) which got confused by unpunctuated YouTube auto-captions.
   - **Fix:** Blocked `allam`, added `score_model_intelligence()` so 70B/120B/Llama-4 models always rank #1, and added `frequency_penalty=0.7`.

6. **Render Deployment `No such file or directory: 'requirements.txt'`**
   - **Cause:** Render's default build command looks for `requirements.txt` in the root folder, not inside `backend/requirements.txt`.
   - **Fix:** Added `requirements.txt` and `.python-version` (`3.12`) to the root folder so Render deploys smoothly every time.
EOF
