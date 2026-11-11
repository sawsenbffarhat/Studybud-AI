"""Split an LLM's Markdown answer into sections (used for tabs)."""

import re

_HEADING = re.compile(r"^(#{1,3})\s+(.*\S)\s*$")

def split_sections(markdown):
    """
    Return [(title, body), ...].

    A single top title (for example "# Learning Reflection") is dropped and
    its sub-headings become the sections. Text without headings returns one
    "Overview" section.
    """

    lines = markdown.splitlines()

    headings = []

    for number, line in enumerate(lines):
        match = _HEADING.match(line)
        if match:
            headings.append((number, len(match.group(1)), match.group(2)))

    if not headings:
        return [("Overview", markdown.strip())]

    levels = sorted({level for _, level, _ in headings})
    top_level = levels[0]

    use_level = top_level

    top_count = sum(1 for _, level, _ in headings if level == top_level)

    if top_count == 1 and len(levels) > 1:
        use_level = levels[1]

    sections = []
    current_title = None
    current_body = []
    intro = []

    for line in lines:

        match = _HEADING.match(line)

        if match and len(match.group(1)) == use_level:

            if current_title is not None:
                sections.append((current_title, "\n".join(current_body).strip()))

            current_title = match.group(2)
            current_body = []

        elif match and len(match.group(1)) < use_level:
            continue  # dropped top title

        elif current_title is None:
            intro.append(line)

        else:
            current_body.append(line)

    if current_title is not None:
        sections.append((current_title, "\n".join(current_body).strip()))

    intro_text = "\n".join(intro).strip()

    if intro_text:
        sections.insert(0, ("Overview", intro_text))

    return [(title, body) for title, body in sections if body]
