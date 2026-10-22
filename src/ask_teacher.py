import os
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

response = client.chat.completions.create(model="openai/gpt-oss-120b", messages=[
  {"role": "system", "content": "You are an English Teacher. explain simply with examples."},
  {"role":"user", "content":"What is a Noun?Give 5 examples."},
],temperature=0.3,)

print(response.choices[0].message.content)