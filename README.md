# Stage-Aware Retrieval Audit

This repository is a release candidate for a small, reproducible audit of a
two-stage retrieval pipeline. It checks where the first judged-relevant
document appears in a frozen BM25 run and whether that document is available
to a reranker restricted to the top 100 candidates.

[![Quality checks](https://github.com/GioiaZheng/stage-aware-retrieval-audit-release/actions/workflows/quality.yml/badge.svg)](https://github.com/GioiaZheng/stage-aware-retrieval-audit-release/actions/workflows/quality.yml)

The current evidence covers the public BEIR NFCorpus and SciFact test sets. The
four reported locations are operational pipeline outcomes, not semantic
explanations of why a query is difficult:

- rank 1--10;
- rank 11--100;
- rank 101--1000; and
- no judged-relevant hit by rank 1000.

## What is included

- separate, author-produced, code-path-independent metric and category
  recomputation scripts;
- a one-command quick start that downloads a pinned ranked-run bundle;
- SHA-256 verification before computation;
- machine-readable recomputation outputs; and
- an optional Streamlit interface for people who do not use a terminal.

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

Windows PowerShell commands and the expected output fields are documented in
[`verification/QUICKSTART.md`](verification/QUICKSTART.md).

## Browser interface

Its source is `verification/web_app.py`. The page reruns extraction, qrels
loading, category computation, and the fixed-query assignment. It contains no
response fields and its optional download contains only the machine-readable
verification result. The author-run deployment checks and their evidence
boundary are documented in
[`docs/TECHNICAL_ACCESS_VERIFICATION.md`](docs/TECHNICAL_ACCESS_VERIFICATION.md).

This exact response-free source revision has not yet been deployed. A hosted
URL will be added only after an approved deployment and a fresh check against
the exact release candidate.

## Verification scope

The retained reports establish archive integrity, ranked-run structure, metric
recomputation, and the stated category partition for the pinned artifacts.
They do not establish statistical significance, generation quality, semantic
root causes, or completeness of relevance judgments.

The clean staging run is recorded in
[`docs/RELEASE_VERIFICATION.md`](docs/RELEASE_VERIFICATION.md), with its
machine-readable output retained as
[`verification/quickstart-reference.json`](verification/quickstart-reference.json).

## Data and licensing boundary

The original software is licensed under Apache-2.0. Original documentation and
aggregate results are licensed under CC BY 4.0; see
[`LICENSE-DOCUMENTATION.md`](LICENSE-DOCUMENTATION.md). The scripts load public
benchmark judgments through `ir_datasets` and download a pinned run archive
from an external release. Those external resources remain subject to their own
terms and are not relicensed here.

The pinned external run archive remains at its original release URL and is not
redistributed by this repository.
