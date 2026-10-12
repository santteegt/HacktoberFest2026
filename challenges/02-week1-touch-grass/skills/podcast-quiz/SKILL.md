---
name: podcast-quiz
description: Turn a podcast, YouTube or talk transcript into a short, grounded, spoken-friendly quiz (4 multiple-choice recall questions plus 1 "field link" question to answer outdoors), and grade the learner's spoken answers afterwards. Use this whenever someone wants to be quizzed or tested on something they listened to, wants to check what they retained from an episode, asks for questions or flashcards from a transcript, mentions walking or exercising while learning, or runs the Idea Leash walk app, even if they never say the word "quiz". Every question must cite a verbatim quote from the transcript, and a bundled script checks that.
---

# podcast-quiz

Build a five-question quiz from one transcript, in a form that works when the learner is walking with earbuds and no screen. Then grade their spoken answers.

Why it is built this way: the quiz is read aloud by a text-to-speech voice and answered by ear or by voice, so questions have to be short and answerable without seeing them. The learner trusts the score, so every question has to be traceable to something that was actually said. A small local model writes the questions, so a script, not the model, decides whether a quiz is valid.

## Inputs

- A transcript file (plain text, or SRT/VTT with timestamps; strip the timestamps yourself before quoting).
- Optional: episode title, source URL, speakers, the learner's language.

If the transcript is under about 400 words, say so and make fewer questions only if the verifier allows it with `--min-questions`. Do not pad with invented content.

## Mode 1: generate

If the caller gives you candidate ideas with quotes already checked against the transcript (this happens for long episodes), skip the skimming in step 1 and work from those candidates: one candidate per question, from different sections where you can. Everything else, including the verifier, still applies.

Work in this order. The order matters because quotes are cheap to pick well and expensive to repair later.

1. **Skim for ideas, not facts.** Pick 6 to 8 candidate ideas the speakers actually argue or explain: a claim and its reason, a definition, a mechanism, a trade-off, a surprising example. Spread them across the whole transcript (beginning, middle, end). Skip trivia such as exact prices, dates and numbers unless the number is the point.
2. **Copy one verbatim quote per idea.** 8 to 40 words, copied exactly from the transcript, including its wording. A quote is the evidence for the question, so never fix grammar or merge two sentences.
3. **Choose 5 different ideas**: 4 for recall questions (kind `mc`) and 1 more for the field-link question. Each idea gets its own quote, so no quote is used twice. A recall question has a short question and four short choices, one correct. Wrong choices should be plausible things a listener who half-paid attention might pick, taken from other parts of the same episode or from natural misreadings, never absurd and never "all of the above" or "none of the above". Write all four choices in the same grammatical shape and within about three words of each other in length, because a listener hearing them read aloud will pick the one that sounds most complete.
4. **Write 1 field-link question** (kind `field_link`) from the fifth idea. It asks the learner to connect that idea to something they saw, heard or felt on this walk, or to what the dog did. Name the idea in a few words so it works with no screen, and keep the whole question to 25 words or fewer: this is the question that most often runs long, so count the words and cut. A shape that works: "The [host / guest / speaker] said [idea in under 10 words]. What did you see, hear or feel on your walk that connects to that?" Use the role that fits the transcript (a single-speaker talk has only "the speaker"). Give 3 to 6 `concept_terms`: words or short phrases (including paraphrases) that an answer about that idea would contain. Its `reference_answer` restates the idea in one sentence using words from the quote; any concrete observation that fits the idea counts as a good answer.
5. **Check yourself against the rules below (count the words in every question), then run the verifier** (see Verifying). Fix whatever it reports and run it again. Stop after three rounds; if a quote keeps failing, replace the question, do not edit the quote.
6. **Shuffle the answer positions** with `python scripts/shuffle_choices.py quiz.json`. Do this last, because models put the correct answer in the same slot far too often and a listener who notices stops thinking. Do not try to balance positions by hand.

### Rules for good questions

- Spoken length: question at most 25 words, each choice at most 12 words. Put the distinguishing word early.
- Test understanding ("Why did the guest say X?", "What trade-off did they describe?") more than recall of a detail.
- Attribute opinions to the speaker ("According to the host...", "The guest argued..."). Never present a speaker's opinion as a fact the quiz endorses.
- Finance, health and legal topics: ask what was said and why, never what the learner should buy, sell, take or do. No price predictions, no advice.
- Make the wrong choices as long and as specific as the right one. If the correct choice is the longest in three of the four questions, a listener can guess without having listened, and the verifier will reject the quiz.
- One idea per question. Do not reuse the same quote or idea twice.
- Write in the transcript's language unless asked otherwise.

### Output

Return only JSON (see `references/schema.md` for the exact fields and a full example):

```json
{"questions": [
  {"kind": "mc", "question": "...", "choices": ["...", "...", "...", "..."], "answer_index": 2,
   "reference_answer": "...", "quote": "verbatim words from the transcript"},
  {"kind": "field_link", "question": "...", "reference_answer": "...",
   "quote": "...", "concept_terms": ["...", "...", "..."]}
]}
```

Put the four `mc` questions first and the `field_link` question last. `reference_answer` is one sentence that is supported by the quote.

## Verifying

```bash
python scripts/verify_quiz.py quiz.json transcript.txt
```

It exits non-zero when there are errors. It checks the question count and kinds, choice counts, that every quote appears in the transcript (a tolerance for speech-recognition slips is reported as a warning), the length limits, duplicate quotes, that the quotes come from different parts of the episode, and a few bias signals such as the correct answer always being the longest. Errors must be fixed. Warnings are worth a look but do not block.

If you cannot run scripts, apply the same checks by hand and say that the quiz was not machine-verified.

## Mode 2: grade

Input: the question, its `reference_answer` and `quote`, the learner's answer as transcribed speech (it may contain recognition mistakes and filler), and for `field_link` the `concept_terms`.

Return only JSON: `{"score": 0|1|2, "feedback": "one short sentence", "evidence": "what in the answer you relied on"}`.

- **mc** answers are graded by code (chosen index equals `answer_index`), so do not grade them here.
- **Open recall:** 2 = the key idea is there in the learner's own words, 1 = partly right or vague, 0 = wrong or missing. Judge meaning, not wording. Be forgiving of transcription errors and hesitation.
- **field_link:** 2 = names the episode idea (any of the `concept_terms` or a clear paraphrase) and ties it to a concrete observation from the walk; 1 = names the idea but stays abstract, or gives an observation without the link; 0 = neither. Do not reward invented scenery you cannot tell apart from a real one. The point is noticing, so a modest true observation beats an impressive vague one.
- Feedback is spoken back to the learner: one friendly sentence that says what was right and, if needed, what was missed. Do not lecture and do not repeat the whole answer.
- Never give a score above 0 for an empty or off-topic answer.
