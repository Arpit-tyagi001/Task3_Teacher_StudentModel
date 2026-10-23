import os
import json
import time
import random
import pandas as pd
from groq import Groq

MODEL = "openai/gpt-oss-120b"
SEED_FILE = "data/seed_questions.xlsx"
OUTPUT_FILE = "data/generated_questions_raw.jsonl"
QUESTIONS_PER_CALL = 22
EXAMPLES_PER_CALL = 3

SUBTOPICS = {
    "Grammar": [
        "nouns",
        "pronouns",
        "verbs",
        "adjectives",
        "adverbs",
        "prepositions",
        "conjunctions",
        "articles (a, an, the)",
        "subject-verb agreement",
        "singular, plural, countable and uncountable nouns",
    ],
    "Tenses": [
        "simple present and present continuous",
        "simple past",
        "present perfect",
        "future forms (will, going to)",
        "past continuous and past perfect",
        "regular and irregular verbs",
    ],
    "Vocabulary": [
        "synonyms",
        "antonyms",
        "commonly confused words",
        "homophones",
        "meanings of everyday words",
        "prefixes and suffixes",
        "common idioms and phrasal verbs",
    ],
    "Correction": [
        "correcting grammar mistakes in sentences",
        "correcting spelling mistakes",
        "fixing punctuation",
        "capital letters",
        "word order in sentences",
        "rewriting sentences to sound more natural",
    ],
    "Writing": [
        "short paragraphs",
        "informal emails and messages",
        "formal emails and letters",
        "applications and requests",
        "describing people, places and events",
        "essay basics (introduction, body, conclusion)",
    ],
    "Conversation": [
        "greetings and introductions",
        "polite requests and offers",
        "everyday situations (shop, hospital, travel)",
        "phone and workplace talk",
        "giving opinions, agreeing and disagreeing",
    ],
    "Edge case": [
        "asking for an English grammar or vocabulary topic to be explained to a specific audience (a young child, a complete beginner, a non-native adult, a grandparent)",
        "messy typing and spelling mistakes in the question itself",
        "questions with a format limit (one line, three points, one word)",
        "explaining a topic to a child or to a different audience",
        "questions that are not about English at all",
        "asking if a common phrase is correct English",
        "questions typed carelessly: the question text itself has typos, missing apostrophes, no capital letters, no punctuation, or text-speak like 'plz' and 'wen'",
    ],
}
DIFFICULTIES = ["Easy", "Medium", "Hard"]

SYSTEM_PROMPT = (
    "You write practice questions for a basic English learning assistant. "
    "Return ONLY a JSON list of strings. Each string is one question or task "
    "that a student might ask. No numbering, no answers, no explanations, "
    "and no text outside the JSON list."
)

client = Groq(api_key=os.environ["GROQ_API_KEY"])
random.seed(42)


def build_jobs():
    jobs = []
    for category, subtopics in SUBTOPICS.items():
        for subtopic in subtopics:
            for difficulty in DIFFICULTIES:
                jobs.append((category, subtopic, difficulty))
    return jobs


def make_user_prompt(category, subtopic, difficulty, examples):
    example_text = "\n".join(f"- {q}" for q in examples)
    return (
        f"Category: {category}\n"
        f"Subtopic: {subtopic}\n"
        f"Difficulty: {difficulty}\n\n"
        f"Write {QUESTIONS_PER_CALL} different questions about this subtopic.\n"
        "Make them clearly different from each other: change the wording, "
        "the sentence structure and the example words used. "
        "Mix short questions with ones that give a small context. "
        "Write the way real students write.\n\n"
        "Here are example questions in the style we want. Do not copy them:\n"
        f"{example_text}\n\n"
        "Return only the JSON list."
    )


def generate(category, subtopic, difficulty, examples):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": make_user_prompt(category, subtopic, difficulty, examples)},
        ],
        temperature=0.9,
    )
    return response.choices[0].message.content


def parse_questions(text):
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        items = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []
    return [q.strip() for q in items if isinstance(q, str) and q.strip()]


def load_done_jobs():
    done = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                done.add((r["category"], r["subtopic"], r["difficulty"]))
    return done


seeds = pd.read_excel(SEED_FILE, sheet_name="Seed Questions")
jobs = build_jobs()
done_jobs = load_done_jobs()
print(f"{len(jobs)} jobs in total, {len(done_jobs)} already done")

with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
    for number, job in enumerate(jobs, start=1):
        if job in done_jobs:
            continue

        category, subtopic, difficulty = job
        pool = seeds[seeds["Category"] == category]["Question"].tolist()
        examples = random.sample(pool, min(EXAMPLES_PER_CALL, len(pool)))

        print(f"[{number}/{len(jobs)}] {category} | {subtopic} | {difficulty}")

        try:
            text = generate(category, subtopic, difficulty, examples)
        except Exception as e:
            print("   failed:", e)
            time.sleep(5)
            continue

        questions = parse_questions(text)
        if not questions:
            print("   could not read the reply, skipping")
            continue

        for q in questions:
            record = {
                "category": category,
                "subtopic": subtopic,
                "difficulty": difficulty,
                "question": q,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()

        print(f"   got {len(questions)} questions")
        time.sleep(2)

print("Done")