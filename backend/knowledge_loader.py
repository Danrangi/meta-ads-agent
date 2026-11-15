import os

# 1. Find the exact path to our 'backend/knowledge' folder
# Why: Using os.path makes sure this works on Windows, Mac, and Render servers without breaking.
CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_FOLDER = os.path.join(CURRENT_FOLDER, "knowledge")


# 2. Function to read all notes inside the 'backend/knowledge' folder
def load_expert_knowledge() -> str:
    # If the folder doesn't exist yet, return an empty string so the server doesn't crash
    if not os.path.exists(KNOWLEDGE_FOLDER):
        return ""

    combined_notes = []

    # Loop through every file inside the backend/knowledge folder
    for filename in sorted(os.listdir(KNOWLEDGE_FOLDER)):
        # Only read text (.txt) or markdown (.md) files
        if filename.endswith(".md") or filename.endswith(".txt"):
            file_path = os.path.join(KNOWLEDGE_FOLDER, filename)
            
            # Open the file safely using UTF-8 encoding (so emojis and symbols work)
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if content:
                    combined_notes.append(content)

    # Join all knowledge files together with a clean blank line between them
    return "\n\n".join(combined_notes)
