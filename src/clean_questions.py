import json
import re
import random
import unicodedata
from collections import Counter
import pandas as pd

RAW_FILE = "data/generated_questions_raw.jsonl"
SEED_FILE = "data/seed_questions.xlsx"
TRAIN_FILE = "data/questions_train.jsonl"
TEST_FILE = "data/questions_test.jsonl"

SIMILARITY_LIMIT = 0.8
MIN_WORDS = 3
MAX_WORDS = 80
TEST_SIZE = 200
FIRST_ID = 1001

# Look-alike characters that some models produce, and their plain replacements
CHAR_FIXES = {
    "\u00a0": " ",   # no-break space
    "\u202f": " ",   # narrow no-break space
    "\u2009": " ",   # thin space
    "\u200a": " ",   # hair space
    "\u2011": "-",   # non-breaking hyphen
    "\u200b": "",    # zero-width space (invisible)
}


def fix_characters(text):
    for bad, good in CHAR_FIXES.items():
        text = text.replace(bad, good)
    return text


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def strip_numbering(text):
    return re.sub(r"^\s*(\d+[\.\)]|[-*•])\s*", "", text).strip()


def jaccard(a, b):
    return len(a & b) / len(a | b)


def load_records(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def save_records(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


raw = load_records(RAW_FILE)
seeds = pd.read_excel(SEED_FILE, sheet_name="Seed Questions")

kept_sets = []
kept_texts = []
seen_exact = set()

# Seeds go in first, so generated copies of them are removed
for q in seeds["Question"]:
    q = fix_characters(q)
    norm = normalize(q)
    seen_exact.add(norm)
    kept_sets.append(set(norm.split()))
    kept_texts.append(q)

kept = []
removed_examples = []
counts = {"too short": 0, "too long": 0, "exact duplicate": 0, "near duplicate": 0}

for r in raw:
    q = strip_numbering(fix_characters(r["question"]))
    norm = normalize(q)
    words = set(norm.split())
    n_words = len(norm.split())

    if n_words < MIN_WORDS:
        counts["too short"] += 1
        continue
    if n_words > MAX_WORDS:
        counts["too long"] += 1
        continue
    if norm in seen_exact:
        counts["exact duplicate"] += 1
        continue

    match = None
    for i, other in enumerate(kept_sets):
        if jaccard(words, other) >= SIMILARITY_LIMIT:
            match = i
            break
    if match is not None:
        counts["near duplicate"] += 1
        if len(removed_examples) < 10:
            removed_examples.append((q, kept_texts[match]))
        continue

    seen_exact.add(norm)
    kept_sets.append(words)
    kept_texts.append(q)
    kept.append({**r, "question": q})

random.seed(42)
random.shuffle(kept)
for number, r in enumerate(kept, start=FIRST_ID):
    r["id"] = number

test = kept[:TEST_SIZE]
train = kept[TEST_SIZE:]
save_records(TRAIN_FILE, train)
save_records(TEST_FILE, test)

print(f"raw questions: {len(raw)}")
for reason, n in counts.items():
    print(f"removed ({reason}): {n}")
print(f"kept: {len(kept)}  ->  train {len(train)}, test {len(test)}")

print("\ntrain questions per category:")
for category, n in Counter(r["category"] for r in train).most_common():
    print(f"  {category}: {n}")

print("\nnon-ASCII characters left in the questions:")
leftover = Counter()
for r in kept:
    for ch in r["question"]:
        if ord(ch) > 127:
            leftover[ch] += 1
if not leftover:
    print("  none")
for ch, n in leftover.most_common():
    print(f"  U+{ord(ch):04X} {unicodedata.name(ch, 'UNKNOWN')}: {n}")

print("\nexamples of removed near-duplicates:")
for removed, original in removed_examples:
    print(f"  REMOVED: {removed}")
    print(f"  KEPT   : {original}\n")