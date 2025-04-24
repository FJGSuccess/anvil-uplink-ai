import os
import anvil.server
from openai import OpenAI

# Connect to Anvil Uplink securely using the environment variable
anvil.server.connect(os.getenv("ANVIL_UPLINK_KEY"))

# Initialize OpenAI client using API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@anvil.server.callable
def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a high-end administrative and marketing AI assistant. Keep replies on-brand, confident, and helpful."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Keep the server alive and listening
anvil.server.wait_forever()
