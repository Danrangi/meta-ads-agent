cat > README.md << 'EOF'
# 🚀 Personal Meta Ads AI Mentor (Nigeria & Global RAG Edition)

A full-stack AI Strategist, Copywriter, and Tutor built to help plan, write, target, and analyze **Meta (Facebook & Instagram) Ads**—specifically tailored for the **Nigerian market** (Naira ₦ budgets, WhatsApp & Instagram DM funnels, Lagos/Abuja targeting, buyer trust psychology) as well as global best practices.

---

## ✨ Key Features

1. **🧠 Custom RAG Knowledge Base (Retrieval-Augmented Generation):**
   - Pre-loaded with **22+ curated 2026 Meta Ads courses, YouTube transcripts, and Nigerian marketing guides** (~492 searchable chunks).
   - Retrieves only the most relevant expert lessons for each question and cites the source title.
2. **📚 Built-in UI Knowledge Uploader:**
   - Add new **YouTube Videos**, **Blog Posts / Official Meta Docs**, or **Raw Course Notes** directly from the web interface.
3. **🇳🇬 Nigerian Market Intelligence:**
   - Understands realistic Naira (₦) testing budgets, WhatsApp closing scripts, payment/VAT rules, and how to filter out unqualified clickers.
4. **⚡ Quick-Action Prompt Templates:**
   - 1-click templates for **Campaign Strategy**, **3 Ad Copy Variations**, **Targeting & Budget**, and **Campaign Bottleneck Analysis**.
5. **💬 Conversation Memory & Teaching Mode:**
   - Remembers context across follow-up questions and includes a **"💡 Why This Works (Lesson)"** section at the end of every answer so I learn while working.

---

## 🛠️ Tech Stack & Architecture

- **Frontend (Hosted on Vercel):** Plain HTML5, CSS3, and Vanilla JavaScript (Zero heavy frameworks).
- **Backend (Hosted on Render):** Python 3.12 + FastAPI + Uvicorn.
- **AI Engine:** Groq API (Free Tier) with automatic intelligence ranking (`70B` / `Llama-4` / `32B` prioritized) and anti-repetition protection.
- **RAG Engine:** Pure-Python chunking & keyword-scoring retrieval stored in `backend/knowledge/rag_store.json` (lightweight <5MB RAM footprint to run smoothly on Render's 512MB free tier).

---

## 📂 Project Folder Structure

    meta-ads-agent/
    ├── .env                        # Secret API keys (Ignored by Git for security)
    ├── .gitignore                  # Protects .env and .venv from being uploaded to GitHub
    ├── .python-version             # Tells Render to use Python 3.12
    ├── requirements.txt            # Root Python dependencies for Render deployment
    ├── README.md                   # Project documentation
    │
    ├── frontend/                   # Everything the user sees in the browser (Deployed on Vercel)
    │   ├── index.html              # App layout, chat box, quick-action buttons, and RAG upload panel
    │   ├── style.css               # Clean, responsive light-mode styling for desktop and mobile
    │   └── app.js                  # Handles chat history, UI formatting, and API calls to FastAPI
    │
    └── backend/                    # Python server & AI brain (Deployed on Render)
        ├── main.py                 # FastAPI server endpoints (/chat, /knowledge, /knowledge/delete)
        ├── ai_mentor.py            # System prompt, RAG injection, and Groq model selection logic
        ├── rag_engine.py           # Extracts YouTube/Website text, chunks data, and searches rag_store.json
        ├── preload_knowledge.py    # Batch script to import multiple YouTube videos & blogs at once
        ├── requirements.txt        # Backend Python package list
        └── knowledge/
            └── rag_store.json      # Permanent RAG database containing 490+ chunks of Meta Ads wisdom

---

## 💻 How to Run Locally on My Computer (VS Code)

Whenever I want to run and test the project on my Windows laptop:

### 1. Make sure `.env` exists in the main folder:
Create a `.env` file with my secret Groq key:

    GROQ_API_KEY=gsk_your_secret_key_here

### 2. Install or update Python packages inside `.venv`:

    .venv/Scripts/python -m pip install -r requirements.txt

### 3. Start the Python FastAPI Backend:

    .venv/Scripts/python -m uvicorn backend.main:app --reload --port 8000

### 4. Open the Frontend:
Open `frontend/index.html` in any web browser. (It automatically detects local mode and connects to `http://127.0.0.1:8000`).

---

## 📚 How to Add Permanent Knowledge to the RAG Brain

**Important Note on Render Free Tier:**
Render's free servers go to sleep when inactive and reset their disk to whatever is saved on GitHub.

- **Temporary Upload:** Using the **📚 Add Knowledge** button on the live Vercel site saves knowledge for the current active session.
- **Permanent Upload (Saved Forever):**
  1. Run the backend locally on your laptop (`uvicorn`) and add the YouTube link or Blog URL via the **📚 Add Knowledge** button (or run `.venv/Scripts/python -m backend.preload_knowledge`).
  2. This updates `backend/knowledge/rag_store.json` on your computer.
  3. Push the updated `rag_store.json` to GitHub:

         git add backend/knowledge/rag_store.json
         git commit -m "Add new expert knowledge to RAG store"
         git push origin main

  4. Render will automatically redeploy with the new knowledge baked in permanently!

---

## 🌍 Live Deployment Settings (For Future Reference)

### Backend on Render.com (Free Web Service)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variable:** `GROQ_API_KEY` = *(Your Groq API Key)*

### Frontend on Vercel.com (Free Project)
- **Root Directory:** `frontend`
- **Backend Connection:** Set `RENDER_BACKEND_URL` on Line 4 of `frontend/app.js` to your live `.onrender.com` URL (with no trailing slash).
EOF
