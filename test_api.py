from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
print(f"Testing API key: {api_key[:10]}...")

# Initialize the client
client = OpenAI(api_key=api_key)

try:
    # Make a simple API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=10
    )
    print("API call successful!")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error:", str(e)) 