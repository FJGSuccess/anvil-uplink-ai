import os
from memory_manager import add_document
import fitz  # PyMuPDF for PDFs
from docx import Document as DocxDocument

def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file_path):
    doc = DocxDocument(file_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    return text

def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text

def load_documents_from_folder(folder_path, category="general"):
    for file_name in os.listdir(folder_path):
        ext = os.path.splitext(file_name)[-1].lower()
        file_path = os.path.join(folder_path, file_name)
        text = ""

        if ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        elif ext == ".docx":
            text = extract_text_from_docx(file_path)
        elif ext == ".txt":
            text = extract_text_from_txt(file_path)

        if text:
            add_document(text, {"filename": file_name, "category": category})
