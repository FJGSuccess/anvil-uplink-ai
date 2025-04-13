import anvil.server
import openai
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import io
import mimetypes
import os

# ✅ Connect to Anvil using your Uplink key
anvil.server.connect("server_PHCQQZWPSVM25CEAVZVC5QQP-I7XBYA5TZTZ5PIRM")

# ✅ Set your OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

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

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    reply_text = response.choices[0].message["content"]
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

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response.choices[0].message["content"].strip()

@anvil.server.callable
def generate_social_posts(user_data, num_posts, platform, content_type):
    brand = user_data.get("brand_kit", {})
    niche = user_data.get("niche", {})
    avatar = user_data.get("avatar", {})
    offer = user_data.get("offer", {})

    prompt = f"""
You are a top-tier social media strategist.

Create {num_posts} high-performing social media post(s) for {platform} in the format of a {content_type}.

Brand: {brand}
Niche: {niche}
Ideal Client Avatar: {avatar}
Offer: {offer}

Each post should include:
- \"text\": a caption or short-form content block (hook + 2–4 sentence value)
- \"cta\": a call-to-action line
- \"hashtags\": relevant, niche-specific tags
- \"image_prompt\": a visual idea or scene to pair with this post

Return only a list of dictionaries like this:
[
  {{
    \"text\": \"...\",
    \"cta\": \"...\",
    \"hashtags\": \"...\",
    \"image_prompt\": \"...\"
  }},
  ...
]
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    import json
    try:
        return json.loads(response.choices[0].message["content"])
    except Exception as e:
        raise Exception(f"Could not parse GPT response: {e}")

# ✅ Keep this at the bottom to run the Uplink
anvil.server.wait_forever()
