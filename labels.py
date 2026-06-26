def generate_label(attribution):
    if attribution == "likely_ai":
        return (
            "Likely AI-generated. Our system found strong evidence that this "
            "content may have been generated with AI. This result is an estimate, "
            "not proof, and the creator may submit an appeal."
        )

    if attribution == "likely_human":
        return (
            "Likely human-written. Our system found stronger evidence that this "
            "content was primarily written by a person. This result is an estimate "
            "and should not be considered a guarantee."
        )

    return (
        "Attribution uncertain. Our system could not confidently determine whether "
        "this content was written by a person or generated with AI. Readers should "
        "treat this as contextual information rather than a final judgment."
    )