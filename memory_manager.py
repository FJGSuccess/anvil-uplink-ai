import chromadb
from chromadb.config import Settings
from llama_index.storage.index_store.chromadb import ChromaVectorStore
from llama_index import VectorStoreIndex, Document

# Persistent ChromaDB setup
CHROMA_DIR = "./chroma_store"
client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_DIR))
collection = client.get_or_create_collection("sorte_memory")
vector_store = ChromaVectorStore(chroma_collection=collection)
index = VectorStoreIndex.from_vector_store(vector_store)

def add_document(content, metadata):
    doc = Document(text=content, metadata=metadata)
    index.insert(doc)
    index.storage_context.persist()

def remove_by_category(category):
    ids_to_remove = [
        item['id'] for item in collection.get()['metadatas'] if item.get('category') == category
    ]
    for doc_id in ids_to_remove:
        collection.delete(documents=[doc_id])

def query_memory(prompt):
    query_engine = index.as_query_engine()
    result = query_engine.query(prompt)
    return result.response
