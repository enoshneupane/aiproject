from openai import OpenAI
from dotenv import load_dotenv
import os
import sys

def test_api_key():
    print("Running API key test...")
    
    # Load environment variables
    load_dotenv()
    
    # Get the API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return False
    
    print(f"Found API key starting with: {api_key[:10]}...")
    
    try:
        # Initialize the client
        client = OpenAI(api_key=api_key)
        
        # Make a simple test request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=10
        )
        
        # Check if we got a successful response
        if response and response.choices and len(response.choices) > 0:
            print("SUCCESS: API key is valid")
            print(f"Response: {response.choices[0].message.content}")
            return True
        else:
            print("ERROR: No proper response received")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_api_key()
    sys.exit(0 if success else 1) 