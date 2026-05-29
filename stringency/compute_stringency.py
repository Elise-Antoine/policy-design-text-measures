"""
Compute stringency of policy documents.

Stringency is operationalised as the share of constraining language in
a document. Constraining language is identified in two ways:

1. Tokens that match a dictionary of constraining words (e.g. SHALL,
   MUST, REQUIRE, PROHIBIT, MANDATE, OBLIGATION). The wordlist used
   here is the constraining-words list from the Loughran-McDonald
   Master Dictionary (1993-2023), a widely-used resource originally
   developed for financial text analysis.

2. Context-sensitive occurrences of "may". Unqualified "may" is
   permissive ("the agency may issue guidance") and is not counted,
   but qualified forms such as "may not", "may only", or "may [...]
   subject to / if / unless / provided that" are constraining and
   are counted.

The stringency score for a document is:

    (constraining dictionary hits + constraining may occurrences)
    -----------------------------------------------------------
                       total content tokens

Higher values indicate more stringent language.

Reference for the dictionary:
    Loughran, T., & McDonald, B. (2011, and updates through 2023).
    Master Dictionary. https://sraf.nd.edu/loughranmcdonald-master-dictionary/
"""

import argparse
import re
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from PyPDF2 import PdfReader


# Standard English stopwords, but keep modal verbs that carry deontic
# force ("may", "shall", "must", "should") because they matter for
# stringency measurement.
def _load_stopwords():
    try:
        sw = set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        sw = set(stopwords.words("english"))
    return sw - {"may", "shall", "must", "should"}


_STOPWORDS = None


def _stopwords():
    """Lazy-load stopwords on first use."""
    global _STOPWORDS
    if _STOPWORDS is None:
        _STOPWORDS = _load_stopwords()
    return _STOPWORDS


# Regex patterns for context-sensitive "may" occurrences that are
# constraining rather than permissive.
MAY_CONSTRAINING_PATTERNS = [
    re.compile(r"\bmay\s+not\b", re.IGNORECASE),
    re.compile(r"\bmay\s+only\b", re.IGNORECASE),
    re.compile(
        r"\bmay\b[^.]*?\b(subject to|if|unless|provided that)\b",
        re.IGNORECASE,
    ),
]

TOKEN_RE = re.compile(r"[A-Za-z']+")


def load_constraining_words(wordlist_path):
    """
    Load the constraining words dictionary from a text file.

    Expects one word per line. Comments (lines starting with #) and
    blank lines are ignored. Words are lowercased.
    """
    words = set()
    with open(wordlist_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                words.add(line.lower())
    return words


def extract_text_from_pdf(pdf_path):
    """Concatenate text from every page of a PDF."""
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)
    return "\n".join(pages)


def tokenize_content(text):
    """Lowercase, extract alphabetic tokens, remove stopwords."""
    tokens = TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t.isalpha() and t not in _stopwords()]


def count_may_occurrences(text):
    """Count occurrences of constraining 'may' patterns in raw text."""
    total = 0
    for pattern in MAY_CONSTRAINING_PATTERNS:
        total += len(pattern.findall(text))
    return total


def stringency_score(pdf_path, constraining_words):
    """
    Compute the stringency score for a single PDF.

    Parameters
    ----------
    pdf_path : str or Path
        Path to a PDF document.
    constraining_words : set of str
        Set of lowercased constraining words from the dictionary.

    Returns
    -------
    float
        The stringency score, or 0.0 if the document contains no
        content tokens.
    """
    text = extract_text_from_pdf(pdf_path)
    tokens = tokenize_content(text)
    total = len(tokens)

    if total == 0:
        return 0.0

    dictionary_hits = sum(1 for t in tokens if t in constraining_words)
    may_hits = count_may_occurrences(text)

    return (dictionary_hits + may_hits) / total


def stringency_score_batch(folder, constraining_words):
    """
    Compute stringency scores for every PDF in a folder.

    Returns a dict mapping filename to stringency score.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise ValueError(f"{folder} is not a directory.")

    results = {}
    for pdf_path in sorted(folder.glob("*.pdf")):
        try:
            results[pdf_path.name] = stringency_score(pdf_path, constraining_words)
        except Exception as e:
            print(f"Skipping {pdf_path.name}: {e}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Compute the stringency score of a policy document, or of "
            "every PDF in a folder. Higher values indicate more "
            "constraining language."
        )
    )
    parser.add_argument(
        "path",
        help="Path to a PDF file or a folder of PDF files.",
    )
    parser.add_argument(
        "--wordlist",
        default="constraining_words.txt",
        help=(
            "Path to the constraining words dictionary file "
            "(default: constraining_words.txt)."
        ),
    )
    args = parser.parse_args()

    constraining_words = load_constraining_words(args.wordlist)
    target = Path(args.path)

    if target.is_dir():
        results = stringency_score_batch(target, constraining_words)
        for filename, score in results.items():
            print(f"{filename}: {score:.4f}")
    else:
        score = stringency_score(target, constraining_words)
        print(f"{target.name}: {score:.4f}")
