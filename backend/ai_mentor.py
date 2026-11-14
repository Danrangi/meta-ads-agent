import os
from dotenv import load_dotenv
from groq import Groq

# 1. Load the secret API key from our .env file into Python's memory
load_dotenv()

# 2. Define the AI's personality and teaching rules (The System Prompt)
SYSTEM_PROMPT = """
You are my personal Meta Ads (Facebook & Instagram) AI Strategist and Mentor.
I took a Meta Ads course, so I know the basics, but I am not an expert yet.

Whenever you help me with ad strategy, ad copy, targeting, or campaign analysis, you MUST follow these rules:
1. Give practical, actionable Meta Ads advice I can use right away.
2. Keep your answers clear, structured, and easy to read.
3. Always include a short section at the end called "💡 Why This Works (Lesson):" where you explain the Meta Ads principle behind your advice in simple English so I learn while working.
"""


# 3. Function to initialize and return the Groq client
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key or api_key == "PASTE_YOUR_GROQ_KEY_HERE":
        raise ValueError("Missing GROQ_API_KEY! Please check your .env file.")
        
    return Groq(api_key=api_key)


# 4. Function to find a working AI model on your Groq account
# Why: AI companies rename or retire models often. Instead of hardcoding just one name
# that might break, we ask Groq which models are active on your account and pick the best one.
def get_working_model(client) -> str:
    # Ask Groq for the list of models your API key has access to
    models_response = client.models.list()
    
    # Put all available model IDs into a simple Python list
    available_models = []
    for model in models_response.data:
        available_models.append(model.id)

    # Our favorite free models in order of preference
    preferred_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it",
        "mixtral-8x7b-32768"
    ]

    # Check our favorites one by one. Return the first one that is available!
    for model_name in preferred_models:
        if model_name in available_models:
            return model_name

    # If none of our favorites matched, pick the first non-audio model from your account
    for model_name in available_models:
        if "whisper" not in model_name and "guard" not in model_name and "tts" not in model_name:
            return model_name

    # If the account has no models enabled at all, tell us cleanly
    raise ValueError(f"No chat models found on your Groq account. Available: {available_models}")


# 5. Main function that takes your question and gets the AI Mentor's answer
def ask_meta_ads_mentor(user_question: str) -> str:
    try:
        client = get_groq_client()
        
        # Automatically pick a working model from your Groq account
        chosen_model = get_working_model(client)

        # Send both the System Prompt and your Question to Groq
        response = client.chat.completions.create(
            model=chosen_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_question}
            ],
            temperature=0.7
        )

        # Extract the text answer from Groq's response
        ai_answer = response.choices[0].message.content
        return ai_answer

    except Exception as error:
        return f"AI Error: {str(error)}"
