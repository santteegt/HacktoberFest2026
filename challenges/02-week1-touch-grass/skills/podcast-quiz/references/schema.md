# Quiz JSON schema

Exactly five questions: four `mc` first, then one `field_link`.

| Field | Applies to | Rules |
| --- | --- | --- |
| `kind` | all | `"mc"` or `"field_link"` |
| `question` | all | at most 25 words, answerable by ear |
| `choices` | mc | exactly 4 distinct strings, each at most 12 words |
| `answer_index` | mc | integer 0 to 3 |
| `reference_answer` | all | one sentence supported by `quote` |
| `quote` | all | 8 to 40 words copied verbatim from the transcript |
| `concept_terms` | field_link | 3 to 6 words or phrases an answer about the idea would contain |

## Example (from a made-up episode about sleep)

```json
{
  "questions": [
    {
      "kind": "mc",
      "question": "According to the guest, why does a regular wake-up time matter more than bedtime?",
      "choices": [
        "It anchors the body clock",
        "It lowers caffeine tolerance",
        "It removes the need for naps",
        "It makes dreams more vivid"
      ],
      "answer_index": 0,
      "reference_answer": "The guest says a fixed wake-up time anchors the body clock.",
      "quote": "the thing that actually anchors your body clock is when you wake up, not when you go to bed"
    },
    {
      "kind": "field_link",
      "question": "The host said morning light resets your body clock. What did you see or feel outside today that connects to that?",
      "reference_answer": "Morning light resets the body clock, so any concrete observation about light, time of day or tiredness counts.",
      "quote": "morning light is the strongest signal your body gets that the day has started",
      "concept_terms": ["light", "morning", "sun", "body clock", "tired", "awake"]
    }
  ]
}
```

The real quiz has five questions (four `mc`, one `field_link`); the example shows one of each.
