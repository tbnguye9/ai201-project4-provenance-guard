def combine_scores(llm_score, stylometric_score, repetition_score):
    """
    Combine three detection signals into one AI probability score.

    Weights match planning.md:
    - 50% LLM
    - 30% stylometric
    - 20% repetition
    """
    combined_score = (
        0.50 * llm_score
        + 0.30 * stylometric_score
        + 0.20 * repetition_score
    )

    return round(combined_score, 3)


def get_attribution(confidence):
    """
    Map confidence score to attribution category.
    """
    if confidence >= 0.80:
        return "likely_ai"

    if confidence <= 0.39:
        return "likely_human"

    return "uncertain"