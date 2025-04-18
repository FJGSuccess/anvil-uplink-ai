import os
import io
import csv
import json
import fitz  # PyMuPDF
import anvil.server
import requests
import mimetypes
from PIL import Image
import pytesseract
from openai import OpenAI
from anvil.google.drive import app_files

# ✅ Anvil Uplink Key
anvil.server.connect("server_PHCQQZWPSVM25CEAVZVC5QQP-I7XBYA5TZTZ5PIRM")

# ✅ API Keys via Environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

@anvil.server.callable
def extract_user_data_from_file(file):
    file_bytes = file.get_bytes()
    mime_type, _ = mimetypes.guess_type(file.name)
    extracted_text = ""

    if mime_type == "application/pdf":
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        extracted_text = "\n".join([page.get_text() for page in doc])
    elif mime_type in ["image/jpeg", "image/png"]:
        image = Image.open(io.BytesIO(file_bytes))
        extracted_text = pytesseract.image_to_string(image)
    else:
        raise Exception("Unsupported file type. Please upload a PDF or image.")

    prompt = f"""
    Based on the following extracted content, create structured data for a brand strategy:

    CONTENT:
    {extracted_text}

    Return the result as JSON with keys:
    - brand_kit (logo, colors[], fonts[])
    - niche (name, subniches[], transformation, tone)
    - avatar (demographics, pain_points[], goals[], beliefs[], objections[])
    - offer (name, price, format, promise, pillars[], faqs[])
    After the JSON, include a human-readable summary preview of the strategy.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    reply_text = response.choices[0].message.content

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
    prompt = f"""
    You are a top-tier social media strategist.

    Create {num_posts} {content_type.lower()} post(s) for {platform} based on:

    Brand: {user_data.get("brand_kit")}
    Niche: {user_data.get("niche")}
    Avatar: {user_data.get("avatar")}
    Offer: {user_data.get("offer")}

    Each post must include:
    - Text
    - CTA (call to action)
    - Hashtags
    - AI Image Prompt

    Return as JSON list with keys: text, cta, hashtags, image_prompt
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return []

@anvil.server.callable
def export_posts_to_drive(posts):
    csv_data = "Platform,Text,CTA,Hashtags,Image Prompt\n"
    for row in posts:
        csv_data += ",".join(
            ['"{}"'.format(str(field).replace('"', "'")) for field in [
                row.get("platform", ""),
                row.get("text", ""),
                row.get("cta", ""),
                row.get("hashtags", ""),
                row.get("image_prompt", "")
            ]]
        ) + "\n"

    file = app_files.anviluploads.create_file("social_posts.csv", csv_data.encode("utf-8"))
    return file.get_url()

@anvil.server.callable
def get_pexels_images(prompts, per_prompt=3):
    headers = {"Authorization": PEXELS_API_KEY}
    images_by_prompt = []

    for prompt in prompts:
        response = requests.get(
            f"https://api.pexels.com/v1/search",
            params={"query": prompt, "per_page": per_prompt},
            headers=headers
        )
        if response.status_code == 200:
            items = response.json().get("photos", [])
            images = [
                {
                    "prompt": prompt,
                    "url": item["src"]["medium"],
                    "photographer": item["photographer"],
                    "photo_page": item["url"]
                }
                for item in items
            ]
            images_by_prompt.append(images)
        else:
            images_by_prompt.append([])

    return images_by_prompt

anvil.server.wait_forever()
