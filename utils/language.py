"""Response-language handling for the sidebar language selector."""

LANGUAGES = ["English", "French"]


def language_instruction(language):
    """Return a prompt sentence that tells the LLM which language to use."""
    if language == "French":
        return (
            "Write the whole response in clear, simple French (français). "
            "Keep technical terms, formulas and code unchanged where that is clearer."
        )

    return "Write the response in simple English."