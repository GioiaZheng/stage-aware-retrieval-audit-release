# BEIR Metric Recomputation

Date: 2026-10-11

## Scope

This separate, author-produced check recomputes C3 and C4 from the frozen
public BEIR run bundle. It is code-path independent of the source evaluator and
does not import evaluation code or generated results from
`msmarco-genqa`, and it does not modify that repository. Public qrels are
loaded through `ir_datasets` 0.6.1 for `beir/nfcorpus/test` and
`beir/scifact/test`.

The evaluator checks each run file's SHA-256 against the bundle manifest before
computing metrics. All 323 NFCorpus and 300 SciFact qrels topics are included;
missing run topics would contribute zero.

## Metric contract

- MRR@10: reciprocal rank of the first document with relevance at least 1 in
  the top 10.
- nDCG@10: raw non-negative graded relevance labels with log2 rank discount.
- Recall@100 and Recall@1000: macro mean of per-query relevant-document recall,
  with relevance at least 1.
- Manifest comparison tolerance: `1e-12`.

## Command

First complete the Quick Start in `verification/QUICKSTART.md`; it creates the
verified bundle extraction and qrels cache under `audit-work`. Then run:

### Windows PowerShell

```powershell
$env:IR_DATASETS_HOME=(Resolve-Path 'audit-work\ir_datasets_cache').Path
.\.venv-audit\Scripts\python.exe verification\recompute_beir_metrics.py `
  --bundle-dir audit-work\extracted `
  --output audit-work\beir-metric-recomputation.json
```

### Linux or macOS

```bash
IR_DATASETS_HOME=audit-work/ir_datasets_cache \
  ./.venv-audit/bin/python verification/recompute_beir_metrics.py \
  --bundle-dir audit-work/extracted \
  --output audit-work/beir-metric-recomputation.json
```

## Aggregate results

| Dataset | System | Queries | MRR@10 | nDCG@10 | Recall@100 | Recall@1000 | Maximum manifest delta |
|---|---|---:|---:|---:|---:|---:|---:|
| NFCorpus | BM25 | 323 | 0.518604 | 0.306407 | 0.237756 | 0.457233 | 0.0 |
| NFCorpus | BM25 + CE | 323 | 0.566213 | 0.341129 | 0.237756 | n/a | 0.0 |
| SciFact | BM25 | 300 | 0.631230 | 0.661691 | 0.875889 | 0.960556 | 0.0 |
| SciFact | BM25 + CE | 300 | 0.651721 | 0.678651 | 0.875889 | n/a | 0.0 |

The CE outputs have depth 100, so Recall@1000 is not reported for them. Their
computed depth-100 value cannot be interpreted as an independent depth-1000
measurement.

## Paired first-stage/reranker comparison

| Dataset | Delta MRR@10 | Delta nDCG@10 | Delta Recall@100 |
|---|---:|---:|---:|
| NFCorpus | +0.047609 | +0.034722 | 0.000000 |
| SciFact | +0.020491 | +0.016960 | 0.000000 |

This verifies C3 within the stated scope: the unchanged reranker improves both
early-ranking metrics on both collections while only reordering the fixed
BM25 top-100 candidate set.

## First-stage coverage

| Dataset | BM25 Recall@100 | BM25 Recall@1000 | No hit at 100 | No hit at 1000 |
|---|---:|---:|---:|---:|
| NFCorpus | 0.237756 | 0.457233 | 72 | 48 |
| SciFact | 0.875889 | 0.960556 | 35 | 11 |

This verifies the numerical basis of C4. NFCorpus has much lower macro
candidate recall even though it has 12,334 positive qrels versus 339 for
SciFact, so macro recall and no-hit query counts are retained as distinct
descriptions of coverage rather than conflated into one statistic.

## Retained evidence

- Separate, author-produced implementation:
  `verification/recompute_beir_metrics.py`
- Machine-readable result: `verification/beir-metric-recomputation.json`
- Frozen bundle manifest SHA-256:
  `4f9a403e5c14b5afa0ff8175edce63287b89a77df320803829c8f55011a02dbc`

## Interpretation boundary

The check verifies effectiveness and coverage values for the released runs. It
does not establish statistical significance, explain semantic causes of
individual misses, treat unjudged documents as irrelevant, or extend the
retrieval-only evidence to generation quality.
