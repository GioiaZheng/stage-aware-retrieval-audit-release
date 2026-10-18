# Release-Candidate Verification

Date: 2026-10-14

The Quick Start was executed from this clean staging repository with a new
`audit-work` directory and Python 3.12. Without source-repository checkout or
credentials, the workflow downloaded the pinned ranked-run archive and the
public NFCorpus and SciFact resources.

The following checks passed:

- the ranked-run archive matched its pinned SHA-256 digest;
- all 323 NFCorpus queries and 300 SciFact queries received exactly one
  category assignment;
- both category partitions reconciled to their full query counts;
- the BM25 top-100 candidate sets matched the reranked candidate sets for every
  query; and
- SciFact query 13 was assigned to `depth_recoverable_101_1000`, with its first
  judged-relevant document at BM25 rank 170.

The retained output is `verification/quickstart-reference.json`, with SHA-256:

```text
412fe2a2878c927064459dfd3a9c677e05a0b116f56ec05f4294230daaacd2b9
```

Its category counts and candidate-set mismatch counts match
`verification/category-recomputation.json`.

This verifies the staged access path and computation. It does not verify every
future host environment or guarantee continued availability of external URLs.
