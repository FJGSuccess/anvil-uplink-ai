
import anvil.server
import anvil.media
import openai
import os
import requests
import mimetypes
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# Connect to Anvil
anvil.server.connect("server_PHCQQZWPSVM25CEAVZVC5QQP-I7XBYA5TZTZ5PIRM")

# OpenAI Client Setup
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PEXELS_API_KEY = "bveTpyRBwOqHGBk59IGiQQU3JIybHbk9ouM9tTJCLgf0s6HeIraG4MAb"
PEXELS_URL = "https://api.pexels.com/v1/search"

@anvil.server.callable
def extract_user_data_from_file(file):
    file_bytes = file.get_bytes()
    mime_type, _ = mimetypes.guess_type(file.name)
    extracted_text = ""

    if mime_type in ["application/pdf"]:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        extracted_text = "\n".join([page.get_text() for page in doc])
    elif mime_type in ["image/jpeg", "image/png"]:
        image = Image.open(io.BytesIO(file_bytes))
        extracted_text = pytesseract.image_to_string(image)
    else:
        raise Exception("Unsupported file type. Please upload a PDF or image file.")

    prompt = f"""
    Based on the following extracted content, create structured data for a brand strategy:

    CONTENT:
    {extracted_text}

    Return the result as JSON with keys:
    - brand_kit (logo, colors[], fonts[])
    - niche (name, subniches[], transformation, tone)
    - avatar (demographics, pain_points[], goals[], beliefs[], objections[])
    - offer (name, price, format, promise, pillars[], faqs[])
    After the JSON, include a human-readable summary preview of the strategy in paragraph form.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    reply_text = response.choices[0].message.content
    import json
    import re

    match = re.search(r'(\{.*\})(.*)', reply_text, re.DOTALL)
    if match:
        json_data = match.group(1)
        preview = match.group(2).strip()
        data = json.loads(json_data)
        data['preview'] = preview
        return data
    else:
        return json.loads(reply_text)

@anvil.server.callable
def generate_preview_from_user_data(user_data):
    prompt = f"""
    Based on the following user-entered data, create a summary strategy preview.

    BRAND:
    {user_data.get("brand_kit", {})}

    NICHE:
    {user_data.get("niche", {})}

    AVATAR:
    {user_data.get("avatar", {})}

    OFFER:
    {user_data.get("offer", {})}

    Return only a human-readable paragraph preview.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response.choices[0].message.content.strip()

@anvil.server.callable
def generate_social_posts(user_data, num_posts, platform, content_type):
    brand = user_data.get("brand_kit", {})
    niche = user_data.get("niche", {})
    avatar = user_data.get("avatar", {})
    offer = user_data.get("offer", {})

    prompt = f"""
You are a top-tier social media strategist and marketing expert.

Create {num_posts} high-performing {content_type} social media post(s) for {platform}.

Brand: {brand}
Niche: {niche}
Ideal Client Avatar: {avatar}
Offer: {offer}

Each post should include:
- A hook (first line that grabs attention)
- 2–4 sentences of valuable content
- A CTA (call to action)
- A short image prompt (for visuals)

Tailor it to match {platform}'s style and format.

Return the result as a JSON list with keys: text, cta, hashtags, image_prompt.
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    import json
    try:
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        raise Exception("Invalid response format from OpenAI")

@anvil.server.callable
def export_posts_to_drive(posts):
    from anvil.google.drive import app_files
    import csv

    csv_data = "Platform,Text,CTA,Hashtags,Image Prompt\n"
    for post in posts:
        row = [post.get("platform", ""), post.get("text", ""), post.get("cta", ""),
               post.get("hashtags", ""), post.get("image_prompt", "")]
        csv_data += ",".join(f'"{field.replace('"', "'")}"' for field in row) + "\n"

    file = anvil.BlobMedia("text/csv", csv_data.encode("utf-8"), name="posts_export.csv")
    app_files.posts_export_csv = file
    return "Uploaded to Google Drive"

@anvil.server.callable
def get_pexels_images(prompts, per_prompt=3):
    headers = {"Authorization": PEXELS_API_KEY}
    results = {}

    for prompt in prompts:
        params = {
            "query": prompt,
            "per_page": per_prompt
        }
        r = requests.get(PEXELS_URL, headers=headers, params=params)
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            results[prompt] = [{
                "src": p["src"]["medium"],
                "photographer": p["photographer"],
                "url": p["url"]
            } for p in photos]
        else:
            results[prompt] = []

    return results

anvil.server.wait_forever()
