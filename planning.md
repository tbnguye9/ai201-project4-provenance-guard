# Provenance Guard Planning

## Project Overview

Provenance Guard is a backend attribution system for creative writing platforms. It accepts text-based content, analyzes the likelihood that the content was AI-generated or human-written, returns a confidence score, displays a plain-language transparency label, and supports appeals when creators believe the system made a wrong decision.

The system is designed to avoid treating AI detection as a perfect binary answer. Instead, it combines multiple signals, communicates uncertainty clearly, and gives creators a path to contest classifications.

---

## Architecture

### Submission Flow

```text
Client
  |
  | POST /submit
  | Body: text, creator_id
  v
Flask API
  |
  | raw text
  v
Signal 1: LLM Classification using Groq
  |
  | llm_score between 0.0 and 1.0
  v
Signal 2: Stylometric Heuristics
  |
  | stylometric_score between 0.0 and 1.0
  v
Signal 3: Repetition / Uniformity Heuristic
  |
  | repetition_score between 0.0 and 1.0
  v
Confidence Scoring
  |
  | combined_score + attribution result
  v
Transparency Label Generator
  |
  | plain-language label text
  v
Audit Logger
  |
  | structured JSON entry
  v
JSON Response to Client
```

### Appeal Flow

```text
Client
  |
  | POST /appeal
  | Body: content_id, creator_reasoning
  v
Flask API
  |
  | lookup original decision
  v
Status Update
  |
  | status changes from "classified" to "under_review"
  v
Audit Logger
  |
  | appeal entry linked to original content_id
  v
JSON Response to Client
```

### Architecture Narrative

When a creator submits text, the Flask API sends the raw content through multiple detection signals. The Groq-based signal provides a semantic judgment, while the stylometric and repetition signals measure structural properties of the writing. These scores are combined into a single confidence score, mapped to an attribution result, converted into a plain-language transparency label, written to the audit log, and returned as structured JSON.

When a creator appeals a decision, the system records the creator's reasoning, updates the content status to `under_review`, and writes a structured appeal entry to the audit log. The system does not automatically re-classify the content during appeal; a human reviewer would examine the original decision, individual signal scores, and appeal reasoning.

---

## API Surface

### POST /submit

Accepts a text submission for attribution analysis.

Request body:

```json
{
  "text": "Creative writing text goes here.",
  "creator_id": "creator-123"
}
```

Response body:

```json
{
  "content_id": "uuid-value",
  "creator_id": "creator-123",
  "attribution": "likely_ai | uncertain | likely_human",
  "confidence": 0.84,
  "label": "Plain-language label text",
  "signals": {
    "llm_score": 0.88,
    "stylometric_score": 0.74,
    "repetition_score": 0.81
  },
  "status": "classified"
}
```

### POST /appeal

Accepts an appeal from a creator who contests the classification.

Request body:

```json
{
  "content_id": "uuid-value",
  "creator_reasoning": "I wrote this myself from personal experience."
}
```

Response body:

```json
{
  "content_id": "uuid-value",
  "status": "under_review",
  "message": "Appeal received and content status updated to under review."
}
```

### GET /log

Returns recent structured audit log entries.

Response body:

```json
{
  "entries": [
    {
      "event_type": "classification",
      "timestamp": "2026-06-26T10:00:00Z",
      "content_id": "uuid-value",
      "creator_id": "creator-123",
      "attribution": "likely_ai",
      "confidence": 0.84,
      "signals": {
        "llm_score": 0.88,
        "stylometric_score": 0.74,
        "repetition_score": 0.81
      },
      "status": "classified"
    }
  ]
}
```

## Detection Signals

The system uses three detection signals. The first two satisfy the required multi-signal detection pipeline. The third signal is implemented as the Ensemble Detection stretch feature.

### Signal 1: LLM Classification (Groq)

This signal uses the Groq LLM to analyze the submitted text and estimate whether it appears more likely to be AI-generated or human-written.

**What it measures**

- Overall writing style
- Semantic coherence
- Generic or formulaic language
- Personal specificity
- Tone consistency

**Output**

```
llm_score (0.0 - 1.0)
```

A higher score means the LLM believes the content is more likely AI-generated.

**Why this signal was chosen**

Large language models can evaluate writing holistically instead of relying on simple statistical rules.

**Limitations**

- Cannot truly determine authorship.
- May classify polished academic writing as AI-generated.
- May underestimate heavily edited AI content.

---

### Signal 2: Stylometric Heuristics

This signal measures statistical properties of the text using pure Python.

The following features are measured:

- Sentence length variance
- Vocabulary diversity (Type-Token Ratio)
- Punctuation density

**Output**

```
stylometric_score (0.0 - 1.0)
```

Higher scores indicate writing patterns commonly associated with AI-generated text.

**Why this signal was chosen**

Stylometric analysis is independent from the LLM's reasoning and provides structural evidence.

**Limitations**

- Very short text is difficult to evaluate.
- Poetry and lyrics often break statistical assumptions.
- Professional writing can appear AI-like.

---

### Signal 3: Repetition and Uniformity (Stretch)

This signal detects repetitive phrases and overly uniform transitions.

Examples include:

- "Furthermore"
- "Moreover"
- "It is important to note"
- repeated sentence openings
- repeated wording

**Output**

```
repetition_score (0.0 - 1.0)
```

Higher scores indicate more repetitive or formulaic writing.

**Why this signal was chosen**

AI-generated writing frequently reuses similar transitions and sentence structures.

**Limitations**

Creative writing, speeches, and poetry may intentionally repeat phrases.

---

## Signal Combination

The three signals are combined using a weighted average.

```
combined_ai_score =
(0.50 × llm_score)
+
(0.30 × stylometric_score)
+
(0.20 × repetition_score)
```

### Why these weights?

The LLM receives the highest weight because it captures semantic and stylistic information.

Stylometric heuristics provide independent structural evidence.

The repetition signal has the smallest weight because repetition alone is not enough to determine authorship.

### Conflict Resolution

If all three signals agree, the confidence score becomes high.

If the signals disagree, the score moves toward the uncertain range instead of forcing a binary decision.

---

## Uncertainty Representation

The confidence score represents how confident the system is in its attribution decision.

It is **not proof** that the content was written by AI or by a human.

The score is interpreted as follows:

| Combined Score | Attribution          |
| -------------- | -------------------- |
| 0.80 - 1.00    | Likely AI-generated  |
| 0.40 - 0.79    | Uncertain            |
| 0.00 - 0.39    | Likely Human-written |

### False Positive Strategy

False positives are considered more harmful than false negatives.

Therefore, the threshold for classifying content as AI-generated is intentionally conservative.

Borderline cases are classified as **Uncertain** rather than **Likely AI-generated**.

---

## Transparency Label Design

The system generates one of three labels.

### High Confidence AI

> "Likely AI-generated. Our system found strong evidence that this content may have been generated with AI. This result is an estimate, not proof, and the creator may submit an appeal."

---

### Uncertain

> "Attribution uncertain. Our system could not confidently determine whether this content was written by a person or generated with AI. Readers should treat this as contextual information rather than a final judgment."

---

### High Confidence Human

> "Likely human-written. Our system found stronger evidence that this content was primarily written by a person. This result is an estimate and should not be considered a guarantee."

---

## Appeals Workflow

Creators may appeal a classification if they believe it is incorrect.

Required information:

- content_id
- creator_reasoning

When an appeal is submitted the system will:

1. Find the original submission.
2. Change the status from

```
classified
```

to

```
under_review
```

3. Store the creator's reasoning.
4. Record the appeal in the audit log.
5. Return a confirmation message.

A reviewer would see:

- Original classification
- Confidence score
- Individual signal scores
- Creator reasoning
- Current status

---

## Anticipated Edge Cases

### Edge Case 1

Academic papers.

Professional writing often contains formal structure and balanced sentences, making it resemble AI-generated text.

---

### Edge Case 2

Poetry.

Poems intentionally repeat phrases and use unusual punctuation, which may confuse stylometric heuristics.

---

### Edge Case 3

Very short submissions.

Short text provides too little statistical information for reliable stylometric analysis.

---

### Edge Case 4

Human-edited AI content.

When AI-generated text has been significantly edited by a human, the detection signals may disagree.

---

## AI Tool Plan

### Milestone 3

AI will generate:

- Flask application skeleton
- POST /submit endpoint
- Groq classification helper

Verification:

- Test endpoint using curl.
- Verify JSON response.
- Verify audit log entry.

---

### Milestone 4

AI will generate:

- Stylometric detector
- Repetition detector
- Confidence scoring function

Verification:

Test four different writing samples.

Confirm that:

- confidence changes
- individual signal scores appear
- uncertainty behaves correctly

---

### Milestone 5

AI will generate:

- Transparency label generator
- POST /appeal endpoint
- Audit logging
- Rate limiting

Verification:

Confirm:

- all three label variants appear
- appeal updates status
- audit log records appeal
- rate limit returns HTTP 429

---

## Stretch Feature Plan

### Ensemble Detection

The stretch feature introduces a third detection signal.

Final ensemble:

- 50% LLM Classification
- 30% Stylometric Heuristics
- 20% Repetition Heuristic

All three individual scores will be included in the API response.

Signal disagreement produces an **Uncertain** result instead of forcing a binary classification.

This design improves transparency while reducing false positives.
