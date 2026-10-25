# UrduExplainBench

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23592500.svg)](https://doi.org/10.5281/zenodo.23592500)

A small benchmark for checking how well language models explain school science and maths in Urdu compared with English.

Every topic comes from Pakistan's Grade 6 to 10 textbooks (Punjab Curriculum and Textbook Board), and every Urdu explanation is paired with an English one written from the same prompt. Native Urdu speakers, one of them a working Urdu-medium teacher, scored each explanation by hand.

Built by Sheraz Hassan as a student researcher at the Center for Language Engineering (CLE), Al-Khawarizmi Institute of Computer Science (KICS), University of Engineering and Technology (UET) Lahore.

## Why I made this

I grew up in a village near Vehari, and later spent time tutoring kids from families who couldn't afford extra help. Most of them were learning in Urdu. So when AI tutors started being pitched as the fix for students like them, I wanted to know whether that holds up in the language they actually study in. Most Urdu benchmarks use multiple-choice questions, which show what a model knows, not whether it can explain something to a twelve-year-old the way their textbook does. So I built this: the same topics and the same prompts in Urdu and English, checked by people who read and teach Urdu.

## What's in here

| File | What it contains |
|---|---|
| `data/topics.csv` | The 30 topics, with subject, grade, and the English and Urdu topic names |
| `data/prompts.csv` | The exact prompt sent to each model in each language |
| `data/textbook_mapping.csv` | Which textbook, unit and pages each topic comes from |
| `data/reference_entries.md` | What the textbook teaches for each topic, used to judge factual errors |
| `data/rubric.md` | The scoring guide the raters used (five dimensions, 1 to 5) |
| `data/ratings.csv` | Every human rating, with raters anonymized as R1 to R3 |
| `data/accuracy_labels.csv` | Factual-accuracy label for each rated explanation (0 none, 1 minor, 2 major) |
| `data/outputs_all_runs.csv` | All 720 model outputs from four separate runs |
| `data/output_characteristics.csv` | Things measured automatically for every output: length, tokens per word, foreign script, English glosses, raw LaTeX |
| `scripts/generate.py` | Generates explanations with the same settings as the study |
| `scripts/reproduce_results.py` | Recomputes the main results from the files above |

## At a glance

- 30 topics: 10 physics, 10 chemistry and biology, 10 mathematics, Grades 6 to 10
- 3 models: GPT-4o, Llama-3.3-70B-Instruct, Llama-3.1-8B-Instruct
- 180 rated explanations (30 topics × 3 models × English and Urdu)
- 5 scoring dimensions: conceptual clarity, grade-appropriateness, pedagogical structure, terminology, language quality
- 3 native Urdu raters, scoring both languages of each pair
- 4 generation runs, 720 outputs in total, for checking whether failures repeat

## What it found

- Urdu explanations scored about a point lower than English on a 5-point scale (gap −0.97, 95% CI about −1.15 to −0.79), for every model, rater and subject.
- The biggest drops were in language quality, clarity and terminology.
- No difference was detected between Llama-3.3-70B and the much smaller Llama-3.1-8B in Urdu.
- Across four runs, Llama-3.3-70B slipped Devanagari or Chinese characters into 25% of its Urdu answers (Llama-3.1-8B 2.5%, GPT-4o none) and kept most of its Urdu answers well below the requested length.

`results/expected_results.txt` shows the output of `reproduce_results.py`. Bootstrap confidence intervals can shift by about 0.01 from run to run.

## Using it

**To test another model:** run `scripts/generate.py` on `data/prompts.csv` (set your API keys as environment variables first; the script explains how), then score the outputs with `data/rubric.md`. Rate both languages of each pair with the same person, so differences in how strict raters are don't affect the comparison.

**To check the numbers:**

```
pip install -r requirements.txt
python3 scripts/reproduce_results.py
```

## Things to keep in mind

- It's small: 30 hand-picked topics, three models, three raters. Treat results as trends.
- Rater agreement was moderate (Krippendorff's alpha 0.58, below the usual 0.667), and agreement on grade-appropriateness was at chance.
- Only the first run was rated by people. Runs 2 to 4 were used for the automatic checks.
- The reference entries and accuracy labels reflect one person's reading of the textbooks.
- The terminology scores follow how Urdu-medium textbooks actually write: English terms in Urdu script for science, Urdu terms for maths. See `data/rubric.md`.

## Models and dates

Run 1 (rated) was generated on 5 August 2026 through the OpenAI API (GPT-4o, which resolved to `gpt-4o-2024-08-06`) and the Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`). Groq retired both Llama models on 16 August 2026, so runs 2 to 4 (11 October 2026) used the same open-weight models through OpenRouter. Settings for every run: temperature 0.3, up to 2,000 output tokens, no system prompt.

## License

Code is MIT licensed. Data is CC BY 4.0, so you can use it with credit. Model outputs remain subject to the providers' terms, and textbook material is summarised or quoted briefly for research purposes.

## Citation

If you use this, please cite:

> Hassan, S. (2026). *UrduExplainBench: Urdu vs English explanation quality on Pakistan's Grade 6–10 curriculum* (Version 1.0.0) [Data set]. https://doi.org/10.5281/zenodo.23592500

The accompanying paper, "Where Language Models Fail Urdu-Medium Students: A Curriculum-Anchored Evaluation of Science and Mathematics Explanations", is currently under review.

## Thanks

To Prof. Dr. Sarmad Hussain and the Center for Language Engineering at KICS, UET Lahore, for supervising and supporting this work; to Ms Tahira Rizwan for her mentorship; to the three volunteer raters for their careful work; and to the Urdu-medium teacher who corrected the terminology rubric before rating began.
