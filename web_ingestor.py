import requests
from bs4 import BeautifulSoup

def learn_from_url(url):
    """Fetch content from a URL and extract clean text."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract visible text only (skip scripts, styles)
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text(separator="\n")
        lines = (line.strip() for line in text.splitlines())
        text = "\n".join(line for line in lines if line)

        return text
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None
