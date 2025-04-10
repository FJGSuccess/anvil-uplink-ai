import anvil.server
import openai
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import io
import mimetypes
import os
from openai import OpenAI

anvil.server.connect("server_PHCQQZWPSVM25CEAVZVC5QQP-I7XBYA5TZTZ5PIRM")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@anvil.server.callable
def extract_user_data_from_file(file):
    # Read bytes and determine file type
    file_bytes = file.get_bytes()
    mime_type, _ = mimetypes.guess_type(file.name)

    extracted_text = ""

    if mime_type in ["application/pdf"]:
        # Parse PDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        extracted_text = "\n".join([page.get_text() for page in doc])

    elif mime_type in ["image/jpeg", "image/png"]:
        # OCR image
        image = Image.open(io.BytesIO(file_bytes))
        extracted_text = pytesseract.image_to_string(image)

    else:
        raise Exception("Unsupported file type. Please upload a PDF or image file.")

    print("📄 Extracted text:", extracted_text[:500])  # Debug preview

    # Send to OpenAI to structure it
    prompt = f"""
    Based on the following extracted content, create structured data for a brand strategy:

    CONTENT:
    {extracted_text}

    Return the result as JSON with keys:
    - brand_kit (logo, colors[], fonts[])
    - niche (name, subniches[], transformation, tone)
    - avatar (demographics, pain_points[], goals[], beliefs[], objections[])
    - offer (name, price, format, promise, pillars[], faqs[])
    """

    response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # ← updated
    messages=[{"role": "user", "content": prompt}],
    temperature=0.5,
    )

    reply_text = response.choices[0].message.content
    print("🤖 GPT Response:\n", reply_text[:500])

    import json
    return json.loads(reply_text)

anvil.server.wait_forever()
