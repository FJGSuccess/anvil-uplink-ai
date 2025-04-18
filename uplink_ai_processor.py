import anvil.server
import openai
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import io
import mimetypes
import os
import requests
import anvil.google.drive
from anvil.google.drive import app_files
from openai import OpenAI
from datetime import datetime

anvil.server.connect("server_PHCQQZWPSVM25CEAVZVC5QQP-I7XBYA5TZTZ5PIRM")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

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

    print("📄 Extracted text:", extracted_text[:500])

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
    print("🤖 GPT Response:\n", reply_text[:500])

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
You are a top-tier social media strategist.

Create {num_posts} high-performing social media post(s) for {platform}.
Type: {content_type}

Brand: {brand}
Niche: {niche}
Ideal Client Avatar: {avatar}
Offer: {offer}

Each post should include:
- A hook (first line that grabs attention)
- 2–4 sentences of valuable content
- A CTA (call to action)

Tailor it to match {platform}'s style, tone, and ideal formatting (e.g. short for Twitter, vertical focus for TikTok, caption-rich for Instagram, professional for LinkedIn).

Return each post as a plain text block. No titles or extra formatting.
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    full_text = response.choices[0].message.content.strip()
    posts = full_text.split("\n\n")[:num_posts]

    return [{
        "platform": platform,
        "text": post,
        "cta": "Tap the link in bio to learn more!",
        "hashtags": "#example #strategy #growth",
        "image_prompt": f"{platform} visual with high engagement and style"
    } for post in posts]

@anvil.server.callable
def export_posts_to_drive(generated_posts):
    headers = ["Platform", "Post Text", "CTA", "Hashtags", "Image Prompt"]
    rows = [[
        post.get("platform", ""),
        post.get("text", ""),
        post.get("cta", ""),
        post.get("hashtags", ""),
        post.get("image_prompt", "")
    ] for post in generated_posts]

    csv_data = ",".join(f'"{header}"' for header in headers) + "\n"
    for row in rows:
        csv_data += ",".join('"' + field.replace('"', "'") + '"' for field in row) + "\n"

    filename = f"social_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file = anvil.BlobMedia("text/csv", csv_data.encode("utf-8"), name=filename)
    anvil.google.drive.app_files.folder.add_file(file)
    return filename

@anvil.server.callable
def get_pexels_images(prompts, per_prompt=3):
    all_results = []
    headers = {"Authorization": PEXELS_API_KEY}
    base_url = "https://api.pexels.com/v1/search"

    for prompt in prompts:
        response = requests.get(base_url, params={"query": prompt, "per_page": per_prompt}, headers=headers)
        if response.status_code == 200:
            photos = response.json().get("photos", [])
            image_urls = [{"url": p["src"]["large"], "alt": p["alt"], "link": p["url"]} for p in photos]
            all_results.append({"prompt": prompt, "images": image_urls})
        else:
            print("❌ Failed to fetch images for prompt:", prompt)
            all_results.append({"prompt": prompt, "images": []})

    return all_results

anvil.server.wait_forever()
