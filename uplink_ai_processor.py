import os
import anvil.server
from openai import OpenAI

from memory_manager import query_memory, add_document
from doc_loader import load_documents_from_folder
from google_drive_sync import sync_books
from web_ingestor import ingest_web_url

anvil.server.connect(os.getenv("ANVIL_UPLINK_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@anvil.server.callable
def ask_ai(prompt):
    try:
        memory_context = query_memory(prompt)
        full_prompt = f"Relevant business context:\n{memory_context}\n\nUser: {prompt}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an intelligent assistant named Sorte. Respond using the company's knowledge and voice."},
                {"role": "user", "content": full_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

@anvil.server.callable
def update_knowledgebase():
    try:
        sync_books()
        load_documents_from_folder("knowledge_base", category="business_model")
        return "✅ Knowledge base updated from Google Drive."
    except Exception as e:
        return f"⚠️ Sync error: {str(e)}"

@anvil.server.callable
def ingest_web_article(url, category="web_learning"):
    try:
        result = ingest_web_url(url, category)
        return result
    except Exception as e:
        return f"⚠️ Web ingestion error: {str(e)}"

anvil.server.wait_forever()
