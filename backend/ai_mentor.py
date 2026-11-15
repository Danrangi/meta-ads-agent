import os
import requests
from dotenv import load_dotenv
from groq import Groq

from backend.knowledge_loader import load_expert_knowledge

# 1. Load secret API keys from .env
load_dotenv()

# 2. Define the core instructions for our Nigerian & Global Meta Ads Mentor
BASE_SYSTEM_PROMPT = """
You are my personal Meta Ads (Facebook & Instagram) AI Strategist and Mentor.
I am based in Nigeria and running Meta Ads primarily for the Nigerian market (unless I state otherwise).
I took a Meta Ads course, so I know the basics, but I want expert guidance.

Whenever you help me with ad strategy, ad copy, targeting, or campaign analysis, you MUST follow these rules:
1. Strictly follow the rules in the EXPERT META ADS KNOWLEDGE BASE below.
2. Tailor your advice to the Nigerian market (use Naira ₦ for budgets/offers, consider WhatsApp/IG DM funnels, Lagos/Abuja/PH targeting, and Nigerian buyer trust) unless I specify a foreign country.
3. NEVER repeat yourself or invent extra campaigns (#2, #3, #4) that I did not ask about. Answer ONLY what I asked clearly and concisely.
4. STRICT FORMATTING RULE: Never use Markdown tables (|---|), never use HTML tags like <br>, and never use code blocks (```). Use clean paragraphs, bullet points, and **bold text** for headings.
5. Always include a short section at the end called "**💡 Why This Works (Lesson):**" explaining the Meta Ads principle behind your advice in simple English.
"""


# 3. Combine the base instructions with all files inside backend/knowledge/
def build_full_system_prompt() -> str:
    expert_notes = load_expert_knowledge()
    
    if not expert_notes:
        return BASE_SYSTEM_PROMPT

    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"=== EXPERT META ADS KNOWLEDGE BASE ===\n"
        f"{expert_notes}\n"
        f"======================================"
    )


# 4. Option A: Ask Google Gemini (Free Tier)
# Why Gemini first? Gemini 2.5 Flash is free, smart, never gets stuck in repetition loops,
# and has a massive memory for reading long YouTube video transcripts!
def ask_gemini(system_prompt: str, user_question: str, chat_history: list) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "PASTE_YOUR_GEMINI_KEY_HERE":
        return ""  # Return empty so our code knows to use Groq instead

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    # Format the conversation history the way Google Gemini expects it
    contents = []
    for msg in chat_history:
        role_name = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role_name,
            "parts": [{"text": msg["content"]}]
        })

    # Add the user's newest question
    contents.append({
        "role": "user",
        "parts": [{"text": user_question}]
    })

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.6
        }
    }

    response = requests.post(url, json=payload, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    
    # If Gemini had an error, return empty so Groq can handle the request as backup
    return ""


# 5. Option B: Ask Groq (Free Tier Backup with Anti-Repetition Fix)
def ask_groq(system_prompt: str, user_question: str, chat_history: list) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "PASTE_YOUR_GROQ_KEY_HERE":
        raise ValueError("Missing API Key! Please check your .env file.")

    client = Groq(api_key=api_key)

    # Find the smartest working model on your Groq account
    models_response = client.models.list()
    available_models = [m.id for m in models_response.data]

    preferred_models = [
        "llama-3.3-70b-versatile",
        "deepseek-r1-distill-llama-70b",
        "qwen-qwq-32b",
        "gemma2-9b-it",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192"
    ]

    chosen_model = "llama-3.1-8b-instant"
    for model_name in preferred_models:
        if model_name in available_models:
            chosen_model = model_name
            break

    messages_for_ai = [{"role": "system", "content": system_prompt}]
    for past_message in chat_history:
        messages_for_ai.append({
            "role": past_message["role"],
            "content": past_message["content"]
        })
    messages_for_ai.append({"role": "user", "content": user_question})

    response = client.chat.completions.create(
        model=chosen_model,
        messages=messages_for_ai,
        temperature=0.5,
        # Why frequency_penalty? This stops small 8B models from repeating sentences in a loop!
        frequency_penalty=0.5,
        max_tokens=1200
    )

    return response.choices[0].message.content


# 6. Main Coordinator Function: Tries Gemini first, falls back to Groq automatically
def ask_meta_ads_mentor(user_question: str, chat_history: list) -> str:
    try:
        system_prompt = build_full_system_prompt()

        # Try Gemini first (if GEMINI_API_KEY is in .env)
        gemini_reply = ask_gemini(system_prompt, user_question, chat_history)
        if gemini_reply:
            return gemini_reply

        # Otherwise, use Groq (with our new anti-repetition fix)
        return ask_groq(system_prompt, user_question, chat_history)

    except Exception as error:
        return f"AI Error: {str(error)}"
