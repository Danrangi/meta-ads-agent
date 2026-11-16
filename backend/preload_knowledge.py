import time
from backend.rag_engine import add_knowledge_source

# Retry just the 5 resources that timed out on the first pass
RETRY_RESOURCES = [
    {
        "source_type": "youtube",
        "title": "Ben Heath – If I Started Facebook Ads in 2026",
        "content": "https://www.youtube.com/watch?v=crId74rHjuA"
    },
    {
        "source_type": "youtube",
        "title": "How To Run Meta Ads In Nigeria – Beginners Big Secrets",
        "content": "https://www.youtube.com/watch?v=3jPqjX7QpK4"
    },
    {
        "source_type": "url",
        "title": "How to Run Facebook Ads in Nigeria – Beginner’s Guide 2026",
        "content": "https://sellevo.ng/blog/how-to-run-facebook-ads-in-nigeria-beginner-s-guide-2026"
    },
    {
        "source_type": "url",
        "title": "Meta Targeting in Nigeria – How to Stop Wasting Ad Spend",
        "content": "https://bizmartek.com.ng/meta-ads-targeting/"
    },
    {
        "source_type": "url",
        "title": "Facebook Ads Cost in Nigeria 2026 – Budget & VAT Guide",
        "content": "https://digitaladsreach.com/facebook-ads-cost-in-nigeria/"
    }
]

def retry_skipped():
    print("🔄 Retrying the 5 timed-out resources with a polite 4-second pause...\n")
    for item in RETRY_RESOURCES:
        print(f"Loading: {item['title']}...")
        try:
            result = add_knowledge_source(item["source_type"], item["title"], item["content"])
            print(f"   ✅ Saved! ({result['chunks_added']} chunks added)")
        except Exception as error:
            print(f"   ⚠️ Still unavailable ({error})")
        time.sleep(4)

if __name__ == "__main__":
    retry_skipped()
