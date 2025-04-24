import anvil.server
import openai
import os

# Connect to Anvil Uplink using your Uplink key (set in Render's environment settings)
anvil.server.connect(os.getenv("ANVIL_UPLINK_KEY"))

# Set your OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

@anvil.server.callable
def ask_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a high-end administrative and marketing AI assistant. Keep replies on-brand, confident, and helpful."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Start listening for incoming Anvil requests
anvil.server.wait_forever()
