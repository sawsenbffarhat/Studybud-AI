"""
Works out WHICH subject and chapters a sentence is about.

    "I need a summary of chapter 1 of math"  ->  Math / Chapter 1
    "summarize chapters 2 to 4 in science"   ->  Science / Chapter 2, 3, 4
    "summary of the whole math subject"      ->  every document in Math

It is plain rule-based matching (no AI call), so it is instant, free and
predictable.
"""

import difflib
import re
import unicodedata

from rag.library import Library

_KEYWORDS = (
    "chapters|chapter|chap|ch|units|unit|modules|module|lessons|lesson|"
    "lectures|lecture|parts|part|weeks|week|sections|section|topics|topic|"
    "chapitres|chapitre|unites|unite|parties|partie|lecons|lecon|cours|"
    "seances|seance|semaines|semaine"
)

_ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
}

# Words that carry no information about the subject name
_GENERIC = {
    "summary", "summarize", "summarise", "summarization", "resume", "give",
    "need", "want", "please", "for", "the", "of", "in", "subject", "course",
    "chapter", "chapters", "module", "modules", "unit", "units", "lesson",
    "lessons", "lecture", "lectures", "part", "parts", "week", "section",
    "topic", "topics", "from", "about", "and", "with", "all", "whole",
    "entire", "full", "make", "create", "write", "show", "can", "you",
    "key", "points", "notes", "ch", "chap", "this", "that", "its",
    "du", "de", "des", "le", "la", "les", "un", "une", "pour", "moi",
    "besoin", "donne", "matiere", "sujet", "chapitre", "chapitres",
    "cours", "partie", "unite", "lecon", "seance", "semaine",
}

_ALL_WORDS = re.compile(
    r"\b(all|whole|entire|every|full|complete|everything)\b"
)


def _strip_accents(text):

    text = unicodedata.normalize("NFKD", text or "")

    return "".join(c for c in text if not unicodedata.combining(c))


def normalize(text):
    """lower case, no accents, only letters/digits separated by single spaces."""

    return re.sub(r"[^a-z0-9]+", " ", _strip_accents(text).lower()).strip()


def _title_in_prompt(title, prompt_norm):
    """True when the whole title appears as separate words in the prompt
    ('chapter 1' must NOT match 'chapter 10')."""

    title_norm = normalize(title)

    return (
        len(title_norm) >= 4
        and re.search(rf"\b{re.escape(title_norm)}\b", prompt_norm) is not None
    )


def _parse_group(group):
    """'1, 2 and 3' -> [1,2,3];  '2 to 4' / '2-4' -> [2,3,4]"""

    numbers = [int(n) for n in re.findall(r"\d+", group)]

    if len(numbers) == 2 and re.search(r"\bto\b|[-\u2013\u2014]", group):
        low, high = sorted(numbers)
        if high - low <= 30:
            return list(range(low, high + 1))

    return numbers


def extract_numbers(prompt):
    """Chapter numbers mentioned in the prompt."""

    text = _strip_accents(prompt or "").lower()
    found = []

    pattern = (
        rf"(?:{_KEYWORDS})[\s_.:#-]*"
        r"((?:\d+\s*(?:,|&|and|et|to|-|\u2013|\u2014)?\s*)+)"
    )

    for group in re.findall(pattern, text):
        found.extend(_parse_group(group))

    # "1st chapter", "first chapter"
    for number in re.findall(rf"\b(\d+)(?:st|nd|rd|th)\s+(?:{_KEYWORDS})\b", text):
        found.append(int(number))

    for word, number in _ORDINALS.items():
        if re.search(rf"\b{word}\s+(?:{_KEYWORDS})\b", text):
            found.append(number)

    seen = []

    for number in found:
        if number not in seen:
            seen.append(number)

    return seen


def title_number(title):
    """The chapter number of a document title ('ITN Module 2' -> 2)."""

    text = _strip_accents(title or "").lower()

    match = re.search(rf"(?:{_KEYWORDS})[\s_.:#-]*0*(\d+)", text)

    if match:
        return int(match.group(1))

    match = re.search(r"\d+", text)

    return int(match.group(0)) if match else None


class ScopeResolver:

    def __init__(self, library=None):
        self.library = library or Library()

    # ------------------------------------------------------

    @staticmethod
    def _words(prompt_norm):
        return [
            w for w in prompt_norm.split()
            if w not in _GENERIC and not w.isdigit()
        ]

    @staticmethod
    def _subject_score(prompt_norm, words, name):

        name_norm = normalize(name)

        if not name_norm:
            return 0

        if re.search(rf"\b{re.escape(name_norm)}\b", prompt_norm):
            return 100 + len(name_norm)

        score = 0

        for name_word in name_norm.split():

            if name_word in _GENERIC:
                continue

            for word in words:

                if word == name_word:
                    score = max(score, 50 + len(name_word))
                elif (
                    min(len(word), len(name_word)) >= 4
                    and (word.startswith(name_word) or name_word.startswith(word))
                ):
                    score = max(score, 30 + min(len(word), len(name_word)))
                elif (
                    min(len(word), len(name_word)) >= 4
                    and difflib.SequenceMatcher(None, word, name_word).ratio() >= 0.85
                ):
                    score = max(score, 25)

        return score

    def _match_subject(self, prompt_norm, subjects):

        words = self._words(prompt_norm)

        best, best_score = None, 0

        for subject in subjects:
            score = self._subject_score(prompt_norm, words, subject["name"])
            if score > best_score:
                best, best_score = subject, score

        return best

    # ------------------------------------------------------

    def describe_library(self):
        """'Math (Chapter 1, Chapter 2); Science (Biology)'"""

        parts = []

        for subject in self.library.list_subjects():
            titles = [
                d["title"] for d in self.library.list_documents(subject["id"])
            ]
            parts.append(
                f'{subject["name"]} ({", ".join(titles) if titles else "no documents"})'
            )

        return "; ".join(parts)

    def resolve(self, prompt):
        """
        Returns {"ok": True, "subject": str, "documents": [...], "label": str}
        or      {"ok": False, "message": str}
        """

        subjects = self.library.list_subjects()

        if not subjects:
            return {
                "ok": False,
                "message": "Your library is empty. Create a subject and add PDFs in the Library page first."
            }

        prompt_norm = normalize(prompt)

        subject = self._match_subject(prompt_norm, subjects)

        if subject is None and len(subjects) == 1:
            subject = subjects[0]

        all_documents = self.library.list_documents()

        # No subject named: maybe a document title is named directly
        if subject is None:

            by_title = [
                d for d in all_documents
                if _title_in_prompt(d["title"], prompt_norm)
            ]

            names = sorted({d["subject"] for d in by_title})

            if len(names) > 1:
                return {
                    "ok": False,
                    "message": (
                        "More than one subject has a matching document "
                        f"({', '.join(names)}). Please mention the subject name."
                    )
                }

            if by_title:
                return {
                    "ok": True,
                    "subject": ", ".join(names),
                    "documents": by_title,
                    "label": ", ".join(f'{d["subject"]}: {d["title"]}' for d in by_title)
                }

            return {
                "ok": False,
                "message": (
                    "I could not tell which subject you mean. "
                    "Mention the subject name, for example \"summary of chapter 1 of "
                    f"{subjects[0]['name']}\". Your library: {self.describe_library()}."
                )
            }

        documents = [d for d in all_documents if d["subject_id"] == subject["id"]]

        if not documents:
            return {
                "ok": False,
                "message": f'The subject "{subject["name"]}" has no documents yet. Add PDFs in the Library page.'
            }

        numbers = extract_numbers(prompt)

        by_title = [
            d for d in documents
            if _title_in_prompt(d["title"], prompt_norm)
        ]

        if by_title:
            selected = by_title

        elif numbers:

            selected = [
                d for d in documents if title_number(d["title"]) in numbers
            ]

            if not selected:
                available = ", ".join(d["title"] for d in documents)
                wanted = ", ".join(str(n) for n in numbers)
                return {
                    "ok": False,
                    "message": (
                        f'I found the subject "{subject["name"]}" but no chapter {wanted} in it. '
                        f"Available: {available}."
                    )
                }

        else:
            selected = documents

        if len(selected) == len(documents) and len(documents) > 1:
            label = f'{subject["name"]} (all {len(documents)} documents)'
        else:
            label = f'{subject["name"]}: ' + ", ".join(d["title"] for d in selected)

        return {
            "ok": True,
            "subject": subject["name"],
            "documents": selected,
            "label": label
        }
