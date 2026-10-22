import os
import json
import time
import pandas as pd
from groq import Groq

MODEL = "openai/gpt-oss-120b"

PROMPTS = {
    "v1": "You are an English teacher. Explain simply with examples.",
    "v2": (
        "You are a friendly English teacher for beginners. "
        "Answer in plain text only: no tables, no emojis, no headings. "
        "Start with a direct answer in one or two sentences, then give 2 or 3 short examples. "
        "Keep the answer under 150 words, unless the user asks you to write something long, "
        "like a letter or a paragraph, then keep it under 200 words. "
        "If the question is not about English, politely say that you can only help with English. "
        "If the user asks for a specific length or format, follow it exactly."
    ),
}

# The ONLY line you change to switch between versions
VERSION = "v1"

SYSTEM_PROMPT = PROMPTS[VERSION]
INPUT_FILE = "seed_questions.xlsx"
OUTPUT_FILE = f"seed_data_{VERSION}.jsonl"

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def ask_teacher(question):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def load_done_ids():
    done = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:  # "r" = read
            for line in f:
                done.add(json.loads(line)["id"])
    return done


print(f"Running {VERSION} -> {OUTPUT_FILE}")

df = pd.read_excel(INPUT_FILE, sheet_name="Seed Questions")
done_ids = load_done_ids()

with open(OUTPUT_FILE, "a", encoding="utf-8") as f:  # "a" = append
    for _, row in df.iterrows():
        qid = int(row["ID"])
        if qid in done_ids:
            continue

        question = row["Question"]
        print(f"[{qid}/{len(df)}] {question}")

        try:
            answer = ask_teacher(question)
        except Exception as e:
            print("   failed:", e)
            time.sleep(5)
            continue

        record = {
            "id": qid,
            "category": row["Category"],
            "difficulty": row["Difficulty"],
            "question": question,
            "answer": answer,
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        time.sleep(2)

print("Done")