import os
from dotenv import load_dotenv
from groq import Groq


from backend.rag_engine import retrieve_relevant_knowledge

load_dotenv()

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


def score_model_intelligence(model_name: str) -> int:
    name = model_name.lower()

    if any(k in name for k in ["70b", "120b", "maverick", "llama-4", "kimi", "qwen3-32b", "gpt-oss"]):
        return 100

    if any(k in name for k in ["32b", "27b", "17b", "scout", "compound", "mixtral"]):
        return 80

    if any(k in name for k in ["gemma2-9b", "8b"]):
        return 50

    return 10


def get_ranked_chat_models(client) -> list:
    models_response = client.models.list()
    all_models = [model.id for model in models_response.data]

    blocked_words = ["whisper", "guard", "tts", "orpheus", "playai", "embed", "allam", "vision"]

    valid_models = []
    for model_name in all_models:
        name_lower = model_name.lower()
        if not any(bad_word in name_lower for bad_word in blocked_words):
            valid_models.append(model_name)

    valid_models.sort()
    valid_models.sort(key=score_model_intelligence, reverse=True)

    return valid_models


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
                    frequency_penalty=0.7,
                    max_tokens=1800
                )
                reply_text = response.choices[0].message.content
                return reply_text
            except Exception as model_error:
                last_error = str(model_error)
                continue

        return f"AI Error: None of the models succeeded. Last error: {last_error}"

    except Exception as error:
        return f"AI Error: {str(error)}"
