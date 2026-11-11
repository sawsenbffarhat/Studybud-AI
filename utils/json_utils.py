import json
import re


def parse_llm_json(content):
    """
    Parse JSON returned by an LLM.

    Handles Markdown code fences and extra text before/after the JSON.
    Raises json.JSONDecodeError if no valid JSON can be found.
    """

    content = (content or "").strip()

    content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\s*```$", "", content).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    starts = [i for i in (content.find("["), content.find("{")) if i != -1]

    if not starts:
        raise json.JSONDecodeError("No JSON found", content, 0)

    start = min(starts)
    end = max(content.rfind("]"), content.rfind("}"))

    return json.loads(content[start:end + 1])
