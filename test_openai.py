from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Warning: No API key found. Please set OPENAI_API_KEY in your .env file.")
    exit(1)

print("API Key:", api_key[:10] + "..." if api_key else "None")

# Initialize the client
client = OpenAI(api_key=api_key)

try:
    # Try a simple completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello!"}]
    )
    print("\nAPI Response:", response.choices[0].message.content)
except Exception as e:
    print("\nError:", str(e)) 