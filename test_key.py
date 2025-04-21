from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Warning: No API key found. Please set OPENAI_API_KEY in your .env file.")
    exit(1)

print(f"Testing API key starting with: {api_key[:10]}...")

# Initialize the client
client = OpenAI(api_key=api_key)

try:
    # Try a simple completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, this is a test message."}]
    )
    print("\nAPI Response:", response.choices[0].message.content)
    print("\nAPI test successful!")
except Exception as e:
    print("\nError:", str(e))
    print("\nThis suggests the API key might not be valid for OpenAI's services.") 