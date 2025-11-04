from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # load .env file

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

prompt = "Say hello from inside Docker!"

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
)

print(response.choices[0].message.content)
