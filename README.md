# Stage-Aware Retrieval Audit

This repository provides the versioned
[`v0.2.2` release](https://github.com/GioiaZheng/stage-aware-retrieval-audit-release/releases/tag/v0.2.2)
of a small, reproducible audit of a two-stage retrieval pipeline. It checks where the first
judged-relevant document appears in a frozen BM25 run and whether that document
is available to a reranker restricted to the top 100 candidates.

[![Quality checks](https://github.com/GioiaZheng/stage-aware-retrieval-audit-release/actions/workflows/quality.yml/badge.svg)](https://github.com/GioiaZheng/stage-aware-retrieval-audit-release/actions/workflows/quality.yml)

The current evidence covers the public BEIR NFCorpus and SciFact test sets and
the judged topics from TREC Deep Learning 2019 and 2020. BEIR uses positive
judgments at relevance level 1 or above; the graded TREC-DL audit uses level 2
or above. The four reported locations are operational pipeline outcomes, not
semantic explanations of why a query is difficult:

- rank 1--10;
- rank 11--100;
- rank 101--1000; and
- no judged-relevant hit by rank 1000.

## What is included

- separate, author-produced, code-path-independent metric and category
  recomputation scripts;
- a one-command quick start that downloads a pinned ranked-run bundle;
- SHA-256 verification before computation;
- machine-readable aggregate outputs plus JSON and CSV records for all 623
  audited BEIR queries and a separate set of records for all 97 audited
  TREC-DL topics; and
- an optional Streamlit interface for the retained BEIR workflow and people
  who do not use a terminal.

The repository does not contain benchmark corpora, query text, qrels copies,
model weights, or participant-derived records and outcomes.

Artifact origin, experiment commits, integrity checks, and the external
licensing boundary are documented in [`docs/PROVENANCE.md`](docs/PROVENANCE.md)
and [`THIRD_PARTY.md`](THIRD_PARTY.md).

## Quick start

Python 3.10 or newer and internet access are required for the first run.

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r verification/requirements-usability.txt
./.venv/bin/python verification/run_usability_quickstart.py \
  --work-dir audit-work \
  --query scifact:13
```

This one-command path intentionally preserves the `v0.2.1` BEIR workflow.
Windows PowerShell commands, expected output fields, and the separate TREC-DL
regeneration workflow are documented in
[`verification/QUICKSTART.md`](verification/QUICKSTART.md).

## Browser interface

The response-free browser interface is available at
<https://stage-aware-retrieval-audit.streamlit.app/>. Its source is
`verification/web_app.py`. The page reruns extraction, qrels loading, category
computation, and the fixed-query assignment. It contains no response fields
and its optional download contains only the machine-readable verification
result. The author-run deployment checks and their evidence boundary are
documented in
[`docs/TECHNICAL_ACCESS_VERIFICATION.md`](docs/TECHNICAL_ACCESS_VERIFICATION.md).
The deployed interface retains the `v0.2.1` BEIR scope; it does not expose the
separate TREC-DL outputs added in `v0.2.2`. Those outputs are available through
the three retained files and the documented command-line workflow.

## Verification scope

The retained reports establish archive integrity, ranked-run structure, metric
recomputation, and the stated category partitions for the pinned artifacts.
The category entry point checks the complete qrels-topic population, run
structure and depth, positive-judgment precondition, and top-100 candidate-set
equality before producing a valid partition; contract violations terminate the
audit with a non-zero status.
They do not establish statistical significance, generation quality, semantic
root causes, or completeness of relevance judgments.

The clean release verification run is recorded in
[`docs/RELEASE_VERIFICATION.md`](docs/RELEASE_VERIFICATION.md), with its
machine-readable output retained as
[`verification/quickstart-reference.json`](verification/quickstart-reference.json).
The per-query schema, input fingerprints, file hashes, and regeneration
commands are documented in
[`verification/QUERY-AUDIT.md`](verification/QUERY-AUDIT.md). The canonical
TREC-DL files are
[`verification/trec-category-recomputation.json`](verification/trec-category-recomputation.json),
[`verification/trec-query-audit-records.json`](verification/trec-query-audit-records.json),
and
[`verification/trec-query-audit-records.csv`](verification/trec-query-audit-records.csv).
The `v0.2.1` BEIR files and their retained identifiers remain unchanged.

## Data and licensing boundary

The original software is licensed under Apache-2.0. Original documentation,
aggregate verification results, and the separately versioned BEIR and TREC-DL
JSON/CSV audit tables are licensed under CC BY 4.0, subject to the third-party
boundary below; see
[`LICENSE-DOCUMENTATION.md`](LICENSE-DOCUMENTATION.md). The scripts load public
benchmark judgments through `ir_datasets` and use pinned run archives from
external releases. Those external resources remain subject to their own terms
and are not relicensed here.

The pinned external BEIR and TREC-DL run archives remain at their original
release URLs and are not redistributed by this repository. Benchmark corpora
and qrels are likewise obtained from their upstream sources rather than copied
here.
