[README.md](https://github.com/user-attachments/files/28397052/README.md)
# Measuring Dimensions of Policy Design: US State AI Legislation

A computational text-analysis toolkit for measuring substantive
dimensions of policy design in policy documents, applied here to a
corpus of US state-level AI legislation.

## About this project

Policy documents are not just records of decisions — they are sites
where ideas, frames, and competing preferences get translated into
language. The way a policy is written carries information about how
contested its formation was, how strongly it constrains behaviour, and
how innovative its provisions are relative to existing templates.

This project develops measures for three dimensions of policy design:

- **Diversity** — how varied a document's content and vocabulary are,
  often a signal of negotiation and compromise among actors with
  diverging preferences.
- **Stringency** — how strongly the document constrains behaviour
  through obligations, prohibitions, or restrictions.
- **Novelty** *(in development)* — how innovative the language is
  relative to existing policy templates.

The toolkit applies these measures to US state-level AI legislation, a
substantively interesting corpus because states have been actively
legislating on AI while federal policy has moved more slowly, producing
genuine cross-state variation in both the content and the regulatory
strength of these bills.

## Dimensions

### 1. Diversity

**Conceptual meaning.** Diversity captures how far a policy document
integrates multiple ideas, frames, or considerations. A document that
covers a single topic in a single register has low diversity; a
document that incorporates many distinct concerns — perhaps as a
result of negotiation and compromise — has higher diversity.

**Operationalisation.** Diversity is measured using Shannon entropy
on the document's lemmatised content vocabulary, normalised by the
log of vocabulary size to correct for document length. Lemmatisation
ensures that morphological variants (*regulate*, *regulates*,
*regulating*) count as one type rather than three, so the measure
captures genuine lexical diversity rather than morphological surface
variation. Higher entropy indicates more varied vocabulary use.

See `diversity/` for the implementation and methodological details.

### 2. Stringency

**Conceptual meaning.** Stringency captures how strongly a policy
document constrains behaviour. Constraint comes through obligations
(*shall*, *must*, *require*), prohibitions (*forbid*, *prohibit*,
*may not*), and restrictions (*limit*, *restrict*, *only*). A document
heavy on permissive language is less stringent than one heavy on
binding language, even when the topics are similar.

**Operationalisation.** Stringency is measured as the share of tokens
that match the constraining-words list from the Loughran-McDonald
Master Dictionary (1993–2023), supplemented by regular-expression
detection of context-sensitive *may* constructions. Unqualified *may*
is permissive and not counted, but *may not*, *may only*, and *may
[...] subject to / if / unless / provided that* are constraining and
are counted as additional occurrences.

See `stringency/` for the implementation and methodological details.

### 3. Novelty (in development)

**Conceptual meaning.** Novelty captures how innovative a policy's
language is relative to existing policy templates and prior
legislation. Highly novel documents introduce new concepts, structures,
or framings; less novel documents reproduce existing templates,
boilerplate, or language from earlier policies.

**Operationalisation.** Methodology under development. Candidate
approaches include comparison against reference corpora of earlier
legislation, distance measures in embedding space, and n-gram overlap
with established policy templates.

## Repository structure

```
.
├── README.md
├── ncsl_extractor/
│   ├── extract_ncsl_metadata.R       # Build bill index from NCSL tracker
│  
├── diversity/
│   ├── compute_diversity.py          # Shannon entropy measure
│   ├── requirements.txt
│   
├── stringency/
│   ├── compute_stringency.py         # Constraining-language measure
│   ├── constraining_words.txt        # Loughran-McDonald constraining dictionary
│   ├── requirements.txt
│  
├── examples/
│   ├── example_bill.pdf              # Sample US state AI bill
│   └── example_outputs/              # Example results from running the scripts
└── LICENSE
```

## Workflow

The toolkit is modular: each component can be used on its own, or all
three can be chained for an end-to-end analysis.

1. **Build a bill index.** Run `ncsl_extractor/extract_ncsl_metadata.R`
   on a saved copy of the NCSL AI Legislation Tracker to produce a CSV
   of bill IDs, years, statuses, and topics.
2. **Obtain bill texts.** The NCSL tracker links to external services
   whose terms of use do not permit automated access. Bill texts can
   be obtained instead from individual state legislature websites or
   via [LegiScan's API](https://legiscan.com/) (free for non-commercial
   use), which provides programmatic access to legislation across all
   50 states.
3. **Run the measures.** Apply `diversity/compute_diversity.py` and
   `stringency/compute_stringency.py` to the bill texts (singly or in
   batch).

See the subfolder READMEs for component-specific installation and
usage details.

## Example output

Running both measures on the example bill in `examples/`:

```
example_bill.pdf:
  diversity (normalised entropy):  [X]
  stringency (constraining share): [X]
```

Diversity scores for typical state AI bills sit in the range
[X] to [X]; stringency scores typically range from [X] to [X].
Bills that delegate authority broadly to regulators tend to score
lower on stringency; bills that impose specific obligations on private
actors tend to score higher.

## Citing this work

If you use this toolkit in your own research, please cite:

> Antoine, E. (2026). Measuring Dimensions of Policy Design: US State
> AI Legislation [Computer software]. https://github.com/[username]/[repo]

The constraining-words dictionary used in the stringency measure is
from:

> Loughran, T., & McDonald, B. (2011, and updates through 2023).
> When is a Liability not a Liability? Textual Analysis, Dictionaries,
> and 10-Ks. *Journal of Finance*, 66(1), 35–65.
> https://sraf.nd.edu/loughranmcdonald-master-dictionary/

## License

This code is released under the MIT License. See `LICENSE` for details.
