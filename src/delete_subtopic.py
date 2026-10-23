import json

OLD = [
    "explaining a topic to a child or to a different audience",
]
path = "data/generated_questions_raw.jsonl"

records = [json.loads(line) for line in open(path, encoding="utf-8")]
kept = [r for r in records if r["subtopic"] not in OLD]

with open(path, "w", encoding="utf-8") as f:
    for r in kept:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"removed {len(records) - len(kept)}, kept {len(kept)}")