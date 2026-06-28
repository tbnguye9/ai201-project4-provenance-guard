import json
import os
import re
import statistics
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def analyze_with_groq(text):
    """
    Signal 1: LLM-based AI probability.
    Returns a float from 0.0 to 1.0.
    Higher means more likely AI-generated.
    """
    prompt = f"""
You are an AI content provenance classifier.

Analyze the text below and estimate how likely it is AI-generated.

Return ONLY valid JSON in this exact format:
{{"ai_probability": 0.0}}

Rules:
- ai_probability must be between 0.0 and 1.0
- 0.0 means very likely human-written
- 1.0 means very likely AI-generated
- Do not include explanations

Text:
{text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You classify text provenance and return only JSON.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )

        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        score = float(result.get("ai_probability", 0.5))

        return max(0.0, min(1.0, score))

    except Exception as error:
        print(f"Groq detection error: {error}")
        return 0.5


def analyze_stylometric(text):
    """
    Signal 2: Stylometric heuristic.
    Returns a float from 0.0 to 1.0.
    Higher means more AI-like structure.
    """
    sentences = re.split(r"[.!?]+", text)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    words = re.findall(r"\b\w+\b", text.lower())

    if len(words) < 10 or len(sentences) < 2:
        return 0.5

    sentence_lengths = [
        len(re.findall(r"\b\w+\b", sentence))
        for sentence in sentences
    ]

    # AI writing often has more uniform sentence lengths.
    if len(sentence_lengths) > 1:
        variance = statistics.pvariance(sentence_lengths)
    else:
        variance = 0

    variance_score = 1.0 - min(variance / 80, 1.0)

    unique_words = len(set(words))
    total_words = len(words)
    type_token_ratio = unique_words / total_words

    # Moderate vocabulary diversity can look AI-like.
    vocabulary_score = 1.0 - min(abs(type_token_ratio - 0.55) / 0.55, 1.0)

    punctuation_count = len(re.findall(r"[,.!?;:]", text))
    punctuation_density = punctuation_count / max(total_words, 1)

    # Polished AI-like writing often has moderate punctuation density.
    punctuation_score = 1.0 - min(abs(punctuation_density - 0.12) / 0.12, 1.0)

    stylometric_score = (
        0.45 * variance_score
        + 0.35 * vocabulary_score
        + 0.20 * punctuation_score
    )

    return round(max(0.0, min(1.0, stylometric_score)), 3)

def analyze_repetition(text):
    """
    Signal 3: Repetition and formulaic transition heuristic.
    Returns a float from 0.0 to 1.0.
    Higher means more repetitive or formulaic.
    """
    lowered = text.lower()

    formulaic_phrases = [
        "it is important to note",
        "furthermore",
        "moreover",
        "in conclusion",
        "in addition",
        "as a result",
        "therefore",
        "stakeholders",
        "ethical implications",
        "transformative",
    ]

    phrase_hits = sum(1 for phrase in formulaic_phrases if phrase in lowered)

    words = re.findall(r"\b\w+\b", lowered)

    if len(words) < 10:
        return 0.5

    word_counts = {}
    for word in words:
        if len(word) > 4:
            word_counts[word] = word_counts.get(word, 0) + 1

    repeated_words = sum(1 for count in word_counts.values() if count >= 3)

    phrase_score = min(phrase_hits / 3, 1.0)
    repeated_word_score = min(repeated_words / 4, 1.0)

    repetition_score = (0.80 * phrase_score) + (0.20 * repeated_word_score)

    return round(max(0.0, min(1.0, repetition_score)), 3)