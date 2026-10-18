# Artifact Provenance

## Public release chain

The fixed run bundle is published as a GitHub release asset in
`GioiaZheng/msmarco-genqa`. The release identifies the code commit used to
publish the bundle and the experiment commits associated with each run:

| Run | Experiment commit |
|---|---|
| NFCorpus BM25 | `e276d80fb4da` |
| NFCorpus BM25 + cross-encoder | `e276d80fb4da` |
| SciFact BM25 | `e276d80fb4da` |
| SciFact BM25 + cross-encoder | `f82caf651041` |

Release tag `v2.2-beir-cross-domain-baselines` resolves to code commit
`e0f240ef9e5e3ea3f74a3df5fe835f77b487573c`. That commit was authored by
Gioia Zheng and merged through pull request 169.

## Integrity chain

The verification workflow checks the downloaded archive against the SHA-256
recorded in `verification/run_usability_quickstart.py`. The archive manifest
then supplies a separate SHA-256 digest for every member. Metric recomputation
checks the run files against that manifest before evaluating them.

The release-candidate Quick Start was run from a clean work directory on
2026-10-14. Its retained output is
`verification/quickstart-reference.json`; the verification record and output
digest are in `docs/RELEASE_VERIFICATION.md`.

## Scope boundary

This chain establishes which ranked outputs were evaluated and whether the
downloaded bytes match the published release. It does not reconstruct the
BM25 indexes or rerun cross-encoder inference, and it does not establish the
completeness of benchmark relevance judgments.
