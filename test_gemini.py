import os
from google import genai

key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
model = os.environ.get("REDGREEN_MODEL", "gemini-2.0-flash")
client = genai.Client(api_key=key)
resp = client.models.generate_content(model=model, contents="Reply with exactly: OK")
print("Model replied:", resp.text)
