import anvil.server
import os
from memory_manager import query_memory, add_document
from google_drive_sync import sync_books
from doc_loader import load_documents_from_folder
from web_ingestor import learn_from_url

# Connect to Anvil Uplink securely
anvil.server.connect(os.getenv("ANVIL_SERVER_KEY"))

# Define server-callable functions

@anvil.server.callable
def ask_ai(prompt):
    from llama_index import ServiceContext, VectorStoreIndex
    from llama_index.llms import OpenAI
    from llama_index.embeddings import OpenAIEmbedding

    # Create an OpenAI LLM (automatic from OPENAI_API_KEY in environment)
    service_context = ServiceContext.from_defaults(
        llm=OpenAI(model="gpt-3.5-turbo"),
        embed_model=OpenAIEmbedding()
    )

    # Load the index
    index = VectorStoreIndex.from_persist_dir("./chroma_store")

    query_engine = index.as_query_engine(service_context=service_context)
    response = query_engine.query(prompt)
    return response.response

@anvil.server.callable
def update_knowledgebase():
    try:
        sync_books()  # Pull updated books from Google Drive
        load_documents_from_folder("./knowledgebase", category="knowledgebase")
        return "✅ Knowledge Base Updated Successfully!"
    except Exception as e:
        return f"⚠️ Sync Failed: {str(e)}"

@anvil.server.callable
def ingest_web_article(url, category="web"):
    try:
        content = learn_from_url(url)
        if content:
            add_document(content, {"source": url, "category": category})
            return "✅ Web Article Ingested Successfully!"
        else:
            return "⚠️ No Content Found at URL"
    except Exception as e:
        return f"⚠️ Web Ingestion Failed: {str(e)}"
