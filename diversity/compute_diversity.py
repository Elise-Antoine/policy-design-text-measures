"""
Compute lexical diversity of policy documents using Shannon entropy.

For each document the script computes:

1. The Shannon entropy (in bits) of the document's lemmatised
   content-word distribution.
2. A normalised entropy, H / log2(V), where V is the vocabulary size.
   The normalised value sits on [0, 1] and corrects for the mechanical
   tendency of longer documents to have higher raw entropy.

The pipeline lowercases the text, removes stopwords and non-alphabetic
tokens, and lemmatises with spaCy so that morphological variants
("regulate", "regulates", "regulating") count as a single type rather
than three.

Higher entropy indicates greater lexical diversity (vocabulary is more
spread out across many types); lower entropy indicates concentration
(a small set of types accounts for most of the text).
"""

import argparse
import csv
import math
from collections import Counter
from pathlib import Path

import nltk
import spacy
from nltk.corpus import stopwords
from PyPDF2 import PdfReader


# ---- Setup -------------------------------------------------------------------

def _load_stopwords():
    try:
        return set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        return set(stopwords.words("english"))


def _load_spacy():
    """Load spaCy with NER and parser disabled to keep things light."""
    try:
        nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
    except OSError:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is not installed. "
            "Install it with: python -m spacy download en_core_web_sm"
        )
    # Allow longer documents than the default.
    nlp.max_length = max(nlp.max_length, 1_200_000)
    return nlp


_STOPWORDS = None
_NLP = None


def _stopwords_set():
    global _STOPWORDS
    if _STOPWORDS is None:
        _STOPWORDS = _load_stopwords()
    return _STOPWORDS


def _nlp():
    global _NLP
    if _NLP is None:
        _NLP = _load_spacy()
    return _NLP


# ---- Text extraction and tokenisation ----------------------------------------

def extract_text_pages(pdf_path):
    """Yield the text of each page in the PDF."""
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        yield page.extract_text() or ""


def content_lemmas(pdf_path):
    """
    Return the document's content-word lemmas:
      - lowercased
      - alphabetic only
      - stopwords removed
      - lemmatised

    Pages are processed individually via nlp.pipe so that very long
    documents do not exceed spaCy's per-document length limit.
    """
    lemmas = []
    pages = (p.lower() for p in extract_text_pages(pdf_path))
    stops = _stopwords_set()

    for doc in _nlp().pipe(pages, batch_size=1):
        for tok in doc:
            if tok.is_alpha:
                lemma = tok.lemma_.lower()
                if lemma and lemma not in stops:
                    lemmas.append(lemma)
    return lemmas


# ---- Entropy computation -----------------------------------------------------

def entropy_from_tokens(tokens):
    """
    Compute Shannon entropy (in bits) and vocabulary size for a list
    of tokens.

    Returns (entropy_bits, vocab_size).
    """
    if not tokens:
        return 0.0, 0
    counts = Counter(tokens)
    total = sum(counts.values())
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    return entropy, len(counts)


def diversity_score(pdf_path):
    """
    Compute raw and normalised Shannon entropy for a single PDF.

    Returns
    -------
    dict
        {'entropy_bits': raw entropy in bits,
         'entropy_normalised': entropy / log2(vocab_size),
         'vocab_size': number of distinct lemmas}
    """
    lemmas = content_lemmas(pdf_path)
    entropy, vocab_size = entropy_from_tokens(lemmas)
    normalised = entropy / math.log2(vocab_size) if vocab_size > 1 else 0.0
    return {
        "entropy_bits": entropy,
        "entropy_normalised": normalised,
        "vocab_size": vocab_size,
    }


def diversity_score_batch(folder):
    """
    Compute diversity scores for every PDF in a folder.

    Returns a dict mapping filename to the result dictionary from
    `diversity_score`.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise ValueError(f"{folder} is not a directory.")

    results = {}
    for pdf_path in sorted(folder.glob("*.pdf")):
        try:
            results[pdf_path.name] = diversity_score(pdf_path)
        except Exception as e:
            print(f"Skipping {pdf_path.name}: {e}")
    return results


def write_results_csv(results, output_path):
    """Write batch results to a CSV file."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "entropy_bits", "entropy_normalised",
                         "vocab_size"])
        for filename in sorted(results):
            r = results[filename]
            writer.writerow([
                filename,
                f"{r['entropy_bits']:.6f}",
                f"{r['entropy_normalised']:.6f}",
                r["vocab_size"],
            ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Compute Shannon entropy of policy documents as a measure "
            "of lexical diversity. Higher values indicate greater "
            "diversity of vocabulary."
        )
    )
    parser.add_argument(
        "path",
        help="Path to a PDF file or a folder of PDF files.",
    )
    parser.add_argument(
        "--output",
        default="diversity.csv",
        help=(
            "Output CSV path for batch results (default: diversity.csv). "
            "Ignored when processing a single file."
        ),
    )
    args = parser.parse_args()

    target = Path(args.path)

    if target.is_dir():
        results = diversity_score_batch(target)
        write_results_csv(results, args.output)
        for filename in sorted(results):
            r = results[filename]
            print(f"{filename}: entropy={r['entropy_bits']:.3f} bits, "
                  f"normalised={r['entropy_normalised']:.3f}, "
                  f"vocab={r['vocab_size']}")
        print(f"\nWrote {len(results)} rows to {args.output}.")
    else:
        result = diversity_score(target)
        print(f"{target.name}:")
        print(f"  entropy:    {result['entropy_bits']:.3f} bits")
        print(f"  normalised: {result['entropy_normalised']:.3f}")
        print(f"  vocab size: {result['vocab_size']}")
