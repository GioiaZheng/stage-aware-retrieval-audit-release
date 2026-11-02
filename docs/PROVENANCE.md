# Artifact Provenance

## Public release chains

The fixed run bundles are published as GitHub release assets in
`GioiaZheng/msmarco-genqa`. Their manifests identify the experiment commits
associated with each run.

### BEIR audit retained from v0.2.1

| Run | Experiment commit |
|---|---|
| NFCorpus BM25 | `e276d80fb4da` |
| NFCorpus BM25 + cross-encoder | `e276d80fb4da` |
| SciFact BM25 | `e276d80fb4da` |
| SciFact BM25 + cross-encoder | `f82caf651041` |

Release tag `v2.2-beir-cross-domain-baselines` resolves to code commit
`e0f240ef9e5e3ea3f74a3df5fe835f77b487573c`. That commit was authored by
Gioia Zheng and merged through pull request 169.

### TREC-DL audit added in v0.2.2

| Run | Experiment commit | Run SHA-256 |
|---|---|---|
| TREC-DL 2019 BM25 | `0362a48bb4d000a93f5af5c26a4de934db37e74f` | `19f1befb601bafebe363fc97ab770ff8debd34288a41c0b526a584735a1b093c` |
| TREC-DL 2019 BM25 + cross-encoder | `0362a48bb4d000a93f5af5c26a4de934db37e74f` | `abaa3cb5f5bf13fab6ddd5425cbe0788568f7e62931d3e79381413bae184ac68` |
| TREC-DL 2020 BM25 | `0362a48bb4d000a93f5af5c26a4de934db37e74f` | `67ad11dd8672c011dd8c1f8d68d95fbad6c08d67c4deeb5008cf176d66032a8f` |
| TREC-DL 2020 BM25 + cross-encoder | `0362a48bb4d000a93f5af5c26a4de934db37e74f` | `68ea162d07cff4fd35144f83ce868823cef66d77bd84db437108e6b62b4b7680` |

Release tag `v2.1-trec-dl-baselines` resolves to code commit
`af10885ea8b0b712cb49146c6db06a430af36105`. Its pinned asset is
[`trec-dl-baselines-v1.zip`](https://github.com/GioiaZheng/msmarco-genqa/releases/download/v2.1-trec-dl-baselines/trec-dl-baselines-v1.zip),
with SHA-256
`e7001a943beb1b1a220ef4a58fae445569725682dc0dbbcb0d9300473a360aa3`.
The ZIP is downloaded from that release and is not redistributed here.

## Integrity chain

The BEIR Quick Start checks its downloaded archive against the SHA-256 recorded
in `verification/run_usability_quickstart.py`; the TREC-DL workflow checks its
archive against the digest documented below. Each archive manifest also records
a separate SHA-256 digest for every member. The pinned whole-archive digests
bind the extracted bytes used by these workflows, and the per-query JSON binds
the evaluated run files to their individual SHA-256 values.

The release Quick Start was run from a clean work directory on 2026-10-21.
Its retained output is
`verification/quickstart-reference.json`; the verification record and output
digest are in `docs/RELEASE_VERIFICATION.md`.

For TREC-DL, the same fail-closed category evaluator is invoked with explicit
dataset contracts for `msmarco-passage/trec-dl-2019/judged` and
`msmarco-passage/trec-dl-2020/judged`. Both use relevance threshold 2. The
canonicalized qrels fingerprints are
`a5847a267e8fbf7b10f6997cf2b43d0a8217ed89bda0c494fd01ccd7c6673743`
and
`4869f52b6c8adcecd5e55cc5830eb722739415a69d1f296e491aa833bdeba42e`,
respectively. The aggregate result and 97 query records are retained separately
from the `v0.2.1` BEIR outputs.

## Scope boundary

This chain establishes which ranked outputs were evaluated and whether the
downloaded bytes match the published release. It does not reconstruct the
BM25 indexes or rerun cross-encoder inference, and it does not establish the
completeness of benchmark relevance judgments.
