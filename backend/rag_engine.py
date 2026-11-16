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
def split_text_into_chunks(text: str, chunk_size_words: int = 250) -> list:
    words = text.split()
    chunks = []
    
    step = 200
    for i in range(0, len(words), step):
        slice_of_words = words[i : i + chunk_size_words]
        chunk_text = " ".join(slice_of_words).strip()
        if chunk_text:
            chunks.append(chunk_text)
            
    return chunks


# 5. Extract spoken words from a YouTube Video URL
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
