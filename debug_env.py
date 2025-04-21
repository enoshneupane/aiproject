from dotenv import load_dotenv
import os

print("===== BEFORE LOADING .env =====")
env_var = os.getenv("OPENAI_API_KEY")
print(f"API Key: {env_var if env_var else 'Not found'}")

print("\n===== LOADING .env FILE =====")
load_dotenv(verbose=True)

print("\n===== AFTER LOADING .env =====")
env_var = os.getenv("OPENAI_API_KEY")
print(f"API Key: {env_var[:10]}... (length: {len(env_var) if env_var else 0})")

# Try to read the file directly
print("\n===== READING .env FILE DIRECTLY =====")
try:
    with open(".env", "r") as f:
        content = f.read().strip()
        print(f"File content: {content[:10]}... (length: {len(content)})")
        
        # Parse the file manually
        for line in content.split('\n'):
            if line.startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip()
                print(f"Parsed key: {key[:10]}... (length: {len(key)})")
except Exception as e:
    print(f"Error reading file: {str(e)}") 