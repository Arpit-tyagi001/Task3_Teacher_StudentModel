import json
import re

V1_FILE = "seed_data_v1.jsonl"
V2_FILE = "seed_data_v2.jsonl"
MAX_WORDS = 200


def load_records(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def avg_words(records):
    total = sum(len(r["answer"].split()) for r in records)
    return total / len(records)


def check_answer(answer):
    problems = []

    words = len(answer.split())
    if words > MAX_WORDS:
        problems.append(f"too long ({words} words)")

    if re.search(r"^\s*\|", answer, re.MULTILINE):
        problems.append("has a table")

    if re.search(r"^\s*#{1,6}\s", answer, re.MULTILINE):
        problems.append("has a heading")

    if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", answer):
        problems.append("has an emoji")

    if answer.strip()[-1] not in ".!?\"')”’]":
        problems.append("may be cut off")

    return problems


v1 = load_records(V1_FILE)
v2 = load_records(V2_FILE)

print(f"v1: {len(v1)} answers, average {avg_words(v1):.0f} words")
print(f"v2: {len(v2)} answers, average {avg_words(v2):.0f} words")
lengths = [len(r["answer"].split()) for r in v2]
print(f"v2 shortest: {min(lengths)} words, longest: {max(lengths)} words")
print()

flagged = 0
for r in v2:
    problems = check_answer(r["answer"])
    if problems:
        flagged += 1
        print(f"ID {r['id']}: " + ", ".join(problems))

print()
print(f"{flagged} of {len(v2)} answers flagged")