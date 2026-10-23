# Teacher-Student Model for Basic English

A knowledge distillation project. A large **teacher** model answers a set of basic English questions, and those question-answer pairs become the training data for a small **student** model that learns to answer the same way.

**Teacher model:** `openai/gpt-oss-120b` (open-weight, Apache 2.0), accessed through the Groq API. It is the only model used in this project, for every version of the data.

## How it works

```
Seed questions -> Question generation -> Cleaning and split -> Teacher answers -> Student model
 (50, by hand)    (topic grid, teacher)   (dedupe, test set)    (JSONL dataset)    (LoRA fine-tune)
```

1. Write 50 seed questions by hand on basic English.
2. Improve the teacher's system prompt by comparing two versions (v1 vs v2).
3. Grow the question set to about 3,000 with the teacher, using a topic grid.
4. Clean, deduplicate, and split into train and a held-out test set.
5. Collect the teacher's answers for every question.
6. Fine-tune a small student on the train set and compare it with the teacher on the test set.

## Project status

- [x] Phase 1: Talk to the teacher through the API
- [x] Phase 2: Collect answers for the 50 seed questions
- [x] Phase 3: Quality checks and prompt improvement (v1 vs v2)
- [x] Phase 4a: Generate questions with the teacher (about 3,000 raw)
- [x] Phase 4b: Clean, deduplicate and split (about 3,050 kept: about 2,850 train, 200 test)
- [ ] Phase 4c: Collect teacher answers for all train and test questions
- [ ] Phase 5: Fine-tune the student model (LoRA on Colab)
- [ ] Phase 6: Compare student vs teacher on the held-out test questions
- [ ] Phase 7: Final report

## Seed questions

50 hand-written questions in 7 categories, with Easy, Medium and Hard levels:

| Category | Count |
|---|---|
| Grammar | 10 |
| Tenses | 8 |
| Vocabulary | 8 |
| Correction | 8 |
| Writing | 6 |
| Conversation | 4 |
| Edge case | 6 |

The edge cases are on purpose: messy typing, an instruction to answer in one line, and an off-topic question (the capital of France) to test whether the model stays on task.

## Results: prompt v1 vs v2

Both versions use the same model and the same temperature (0.3). **Only the system prompt changed.**

| Prompt | Average length | Shortest | Longest | Flagged by checker |
|---|---|---|---|---|
| v1: "You are an English teacher. Explain simply with examples." | 363 words | not measured | not measured | not checked |
| v2: plain text, direct answer first, under 150 words, English only | 43 words | 11 words | 135 words | 0 of 50 |

v2 answers are about 88% shorter.

### What we found when reading the output

- **v1 answers were long and heavily formatted:** tables, headings, emojis and mini quizzes, which is too much for a beginner and hard for a small student model to imitate.
- **Long answers contained factual mistakes.** In the first v1 review, the answer on "a" vs "an" gave wrong sound labels, put the acronym rows in the wrong columns of its cheat sheet, and contradicted itself on the word "eulogy". The answer on nouns also called a dog a "person" noun. Length does not mean quality, and a student would copy these errors, so the data must be checked before training.
- **The automatic checker has limits.** It flagged an email answer ending in `[Your Name]` as "cut off". It was a false alarm, so the checker was updated. Format checks cannot catch factual errors, which still need a human review.
- **v2 trade-off:** shorter answers are cleaner but thinner on nuance (for example, the email closing answer lists "Yours faithfully" without saying when to use it).

## Question generation (Phase 4)

### Method

- **Topic grid.** Asking for "2,500 questions" in one call gives repetitive, low-quality lists. Instead, each call gets one combination of category, subtopic and difficulty: 7 categories, 45 subtopics and 3 difficulty levels make 135 jobs of 22 questions each.
- **Few-shot examples.** Each call shows the teacher 3 hand-written seed questions from the same category, with the instruction not to copy them.
- **High temperature for questions (0.9).** Answers use 0.3, because they must be consistent and correct. Questions use 0.9, because they must be varied.
- **Defensive parsing.** The teacher returns a JSON list. The parser reads only the part between the first `[` and the last `]`, and a job that cannot be parsed is skipped and retried on the next run.
- **Resume support.** Every script skips work that is already saved, so a crash or a rate limit never loses finished work.

### Cleaning and split

- Normalize text (lowercase, no punctuation), remove exact duplicates, then remove near-duplicates with Jaccard word-set similarity (limit 0.8).
- Seeds are compared too, so generated copies of seed questions are removed.
- Replace look-alike Unicode characters with plain ones before saving.
- Shuffle, give IDs starting from 1001, and hold out **200 questions as a test set that is never used for training**, to avoid data leakage when comparing student and teacher.

### What we found

- **Style-type subtopics were read as topics.** "Messy typing" produced clean questions *about* spelling instead of questions *containing* typos, and "explain to a child" produced questions about gravity and electricity instead of English. The fix was to rewrite these subtopics as direct instructions about the question text and regenerate only those jobs.
- **Jaccard has blind spots.** At a limit of 0.7 it removed legitimately different questions (for example "a university" vs "an university" was dropped because it shares a template with "a apple" vs "an apple"). It also ignores word order, so "past perfect instead of simple past" can match "simple past instead of present perfect". A limit of 0.8 removed far fewer good questions, and with about 3,000 questions the few false removals cost little.
- **The teacher outputs look-alike characters.** gpt-oss sometimes writes a narrow no-break space (U+202F) or a non-breaking hyphen (U+2011) instead of a plain space or hyphen. They look normal on screen but break string matching and give the student odd tokens, so they are replaced before saving.
- **Difficulty labels are rough.** The model guesses the difficulty, so it is used to spread the questions, not as an exact grade.
- **Categories are not equal in size.** Grammar has the most questions and Conversation the fewest, because of how many subtopics each has. The student is likely to be strongest on Grammar and weakest on Conversation.

Train questions per category from the latest cleaning run:

| Category | Train questions |
|---|---|
| Grammar | 617 |
| Vocabulary | 433 |
| Edge case | 428 |
| Correction | 371 |
| Writing | 368 |
| Tenses | 349 |
| Conversation | 287 |

## Project structure

```
teacher-student-english/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── seed_questions.xlsx            # 50 seed questions
│   ├── seed_data_v1.jsonl             # teacher answers, prompt v1
│   ├── seed_data_v2.jsonl             # teacher answers, prompt v2
│   ├── generated_questions_raw.jsonl  # raw questions from the topic grid
│   ├── questions_train.jsonl          # cleaned training questions
│   └── questions_test.jsonl           # held-out test questions
└── src/
    ├── ask_teacher.py                 # test one question
    ├── collect_answers.py             # ask the teacher and save answers
    ├── check_quality.py               # automatic answer checks
    ├── generate_questions.py          # topic grid question generation
    └── clean_questions.py             # dedupe, fix characters, split
```

## How to run

**1. Install**

```
pip install -r requirements.txt
```

**2. Set your Groq API key** (never put the key in the code)

- Windows (PowerShell): `setx GROQ_API_KEY "your_key_here"`, then reopen the terminal
- Mac/Linux: `export GROQ_API_KEY="your_key_here"`

**3. Test the teacher with one question**

```
python src/ask_teacher.py
```

**4. Collect answers for the seed questions**

Open `src/collect_answers.py` and set `VERSION = "v1"` or `VERSION = "v2"`, then run:

```
python src/collect_answers.py
```

The prompt and the output file name both come from `VERSION`, so they cannot get out of sync.

**5. Check the answer quality**

```
python src/check_quality.py
```

**6. Generate questions**

```
python src/generate_questions.py
```

This writes `data/generated_questions_raw.jsonl`. If it stops halfway, run it again and finished jobs are skipped.

**7. Clean and split the questions**

```
python src/clean_questions.py
```

This writes `data/questions_train.jsonl` and `data/questions_test.jsonl`. It rebuilds both files and reassigns IDs on every run, so run it once and then treat the output as frozen.

## Data format

One JSON record per line (JSONL), so a crash never loses finished work:

```json
{"id": 1001, "category": "Grammar", "subtopic": "nouns", "difficulty": "Easy", "question": "..."}
```

## Roadmap

- Collect the teacher's answers for all train and test questions
- Filter the answers (length, format, factual spot checks)
- Fine-tune a small model (about 0.5B to 1.5B parameters) with LoRA
- Evaluate on the held-out test questions that were never used in training

## Author

Arpit Tyagi: [GitHub](https://github.com/Arpit-tyagi001) | [LinkedIn](https://linkedin.com/in/arpit-tyagi1000/)