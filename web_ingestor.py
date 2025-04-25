import requests
from bs4 import BeautifulSoup
from memory_manager import add_document

def clean_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)

def ingest_web_url(url, category="web_learning"):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    content = clean_text(response.text)
    metadata = {"source": url, "category": category}
    add_document(content, metadata)
    return "✅ Website content ingested."
