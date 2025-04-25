import os
from llama_index.readers.file import PDFReader, DocxReader, TextFileReader
from memory_manager import add_document

SUPPORTED_TYPES = {
    ".pdf": PDFReader(),
    ".docx": DocxReader(),
    ".txt": TextFileReader()
}

def load_documents_from_folder(folder_path, category="general"):
    for file_name in os.listdir(folder_path):
        ext = os.path.splitext(file_name)[-1].lower()
        loader = SUPPORTED_TYPES.get(ext)
        if loader:
            docs = loader.load_data(file_path=os.path.join(folder_path, file_name))
            for doc in docs:
                add_document(doc.text, {"filename": file_name, "category": category})
