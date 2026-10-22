Teacher-Student Model for Basic English

A knowledge distillation project. A large teacher model answers a set of basic English questions, and those question-answer pairs become the training data for a small student model that learns to answer the same way.

Teacher model: openai/gpt-oss-120b (open-weight, Apache 2.0), accessed through the Groq API. It is the only model used in this project, for every version of the data.

How it works
Seed questions  ->  Teacher model  ->  Q&A dataset  ->  Student model
 (hand-written)    (gpt-oss-120b)     (JSONL, checked)   (LoRA fine-tune)
Write seed questions by hand on basic English.
Ask the teacher each question with a fixed system prompt and save the answers.
Check the answers automatically and by reading them.
Grow the dataset with teacher-generated questions.
Fine-tune a small student on the final dataset and compare it with the teacher.
Project status
 Phase 1: Talk to the teacher through the API
 Phase 2: Collect answers for all 50 seed questions
 Phase 3: Quality checks and prompt improvement (v1 vs v2)
 Phase 4: Expand to 1,000+ questions with the teacher
 Phase 5: Fine-tune the student model (LoRA on Colab)
 Phase 6: Compare student vs teacher on unseen questions
 Phase 7: Final report
Seed questions

50 hand-written questions in 7 categories, with Easy, Medium and Hard levels:

Category	Count
Grammar	10
Tenses	8
Vocabulary	8
Correction	8
Writing	6
Conversation	4
Edge case	6

The edge cases are on purpose: messy typing, an instruction to answer in one line, and an off-topic question (the capital of France) to test whether the model stays on task.

Results so far: prompt v1 vs v2

Both versions use the same model and the same temperature (0.3). Only the system prompt changed.

Prompt	Average length	Shortest	Longest	Flagged by checker
v1: "You are an English teacher. Explain simply with examples."	363 words	not measured	not measured	not checked
v2: plain text, direct answer first, under 150 words, English only	43 words	11 words	135 words	0 of 50

v2 answers are about 88% shorter.

What we found when reading the output
v1 answers were long and heavily formatted: tables, headings, emojis and mini quizzes, which is too much for a beginner and hard for a small student model to imitate.
Long answers contained factual mistakes. In the first v1 review, the answer on "a" vs "an" gave wrong sound labels, put the acronym rows in the wrong columns of its cheat sheet, and contradicted itself on the word "eulogy". The answer on nouns also called a dog a "person" noun. Length does not mean quality, and a student would copy these errors, so the data must be checked before training.
The automatic checker has limits. It flagged an email answer ending in [Your Name] as "cut off". It was a false alarm, so the checker was updated. Format checks cannot catch factual errors, which still need a human review.
v2 trade-off: shorter answers are cleaner but thinner on nuance (for example, the email closing answer lists "Yours faithfully" without saying when to use it).
Project structure
teacher-student-english/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── seed_questions.xlsx      # 50 seed questions
│   ├── seed_data_v1.jsonl       # teacher answers, prompt v1
│   └── seed_data_v2.jsonl       # teacher answers, prompt v2
└── src/
    ├── ask_teacher.py           # test one question
    ├── collect_answers.py       # ask all questions and save answers
    └── check_quality.py         # automatic quality checks
How to run

1. Install

pip install -r requirements.txt

2. Set your Groq API key (never put the key in the code)

Windows (PowerShell): setx GROQ_API_KEY "your_key_here", then reopen the terminal
Mac/Linux: export GROQ_API_KEY="your_key_here"

3. Test the teacher with one question

python src/ask_teacher.py

4. Collect answers for all seed questions

Open src/collect_answers.py and set VERSION = "v1" or VERSION = "v2", then run:

python src/collect_answers.py

The prompt and the output file name both come from VERSION, so they cannot get out of sync. If the run stops halfway, run it again: questions that are already answered are skipped.

5. Check the quality

python src/check_quality.py

This prints average lengths for v1 and v2, the shortest and longest answers, and any answer that is too long, has a table, heading or emoji, or looks cut off.

Data format

One JSON record per line (JSONL), so a crash never loses finished answers:

json
{"id": 1, "category": "Grammar", "difficulty": "Easy", "question": "...", "answer": "..."}
Roadmap
Generate 1,000+ similar questions with the teacher, remove duplicates, and collect answers
Filter the dataset (length, format, factual spot checks)
Fine-tune a small model (about 0.5B to 1.5B parameters) with LoRA
Evaluate on held-out questions that were never used in training
Author

Arpit Tyagi: GitHub | LinkedIn