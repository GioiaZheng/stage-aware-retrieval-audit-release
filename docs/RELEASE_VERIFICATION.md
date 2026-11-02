# Release Verification

## v0.2.1 BEIR verification record

Date: 2026-10-21

The complete documented workflow was executed from a clean release-candidate
checkout with a new work directory, an isolated Python 3.12 environment, and
`ir_datasets==0.6.1`. Without a source-repository checkout or credentials, the
workflow downloaded the pinned ranked-run archive and the public NFCorpus and
SciFact resources.

The following checks passed:

- the ranked-run archive matched its pinned SHA-256 digest;
- all 323 NFCorpus queries and 300 SciFact queries received exactly one
  category assignment;
- both category partitions reconciled to their full query counts;
- the BM25 top-100 candidate sets matched the reranked candidate sets for every
  query; and
- SciFact query 13 was assigned to `depth_recoverable_101_1000`, with its first
  judged-relevant document at BM25 rank 170;
- the newly generated 1,860-byte JSON output matched
  `verification/quickstart-reference.json` byte for byte; and
- all ten release invariants in `tests/test_release_candidate.py` passed.

The retained output is `verification/quickstart-reference.json`, with SHA-256:

```text
412fe2a2878c927064459dfd3a9c677e05a0b116f56ec05f4294230daaacd2b9
```

Its category counts and candidate-set mismatch counts match
`verification/category-recomputation.json`.

This verifies the documented access path and computation. It does not verify
every future host environment or guarantee continued availability of external
URLs.

## Local contract-hardening recheck

On 2026-10-21, before assigning a new release identifier, the category entry
point was changed to fail closed on incomplete or extra query populations,
zero-positive qrels topics, invalid ranks or depth, duplicate documents, and
candidate-set inequality. Eight synthetic regression cases cover those
boundaries, and a separate export test reconciles all JSON and CSV records.
Two concurrency regressions also verify that independently executed web-script
contexts import the same process-level lock and that concurrent downloads use
private temporary files. The complete local suite passed 21 tests.

The web candidate now calls the same export module on the freshly extracted
runs and runtime-loaded qrels. Its partition table, complete 623-row CSV,
48-row depth-recoverable follow-up list, and JSON download are all derived from
that in-memory result. The retained JSON/CSV files remain reference outputs for
testing and are not application inputs. This web change is not covered by the
older production check and remains unreleased.

After an overlapping-call failure was reproduced against the shared
extraction directory, the candidate was changed to serialize each complete
audit within the application process. The lock is defined in the separately
imported `web_runtime.py` module, rather than the Streamlit entry script, so
independently re-executed session contexts receive the same lock. It covers
bundle download, extraction, qrels-cache access, computation, and fixed-query
lookup. Downloads also use a request-private `.part` path and publish the
complete archive under a separate lock. A fresh empty-cache test started two
real independently loaded entry-script modules 50 ms apart. They imported the
same lock object, both returned 623 records and SciFact query 13 at rank 170,
the bundle digest matched, and no `.part` file remained. This is local evidence
only; the deployed commit still requires its own concurrency check.

A new end-to-end Quick Start used an empty work directory, downloaded the
pinned archive and public qrels, and produced a result byte-identical to
`verification/quickstart-reference.json`, including its retained SHA-256 above.
Thus the stricter contract rejects invalid inputs without changing the fixed
323-query NFCorpus or 300-query SciFact outputs. This paragraph records the
pre-release status at the time of the recheck. The BEIR files and their
retained identifiers are preserved unchanged in later versions.

## v0.2.2 TREC-DL pre-publication verification (2026-11-02)

On 2026-11-02, the category evaluator and query exporter were run explicitly
for `trec_dl_2019` and `trec_dl_2020` against the externally hosted
`trec-dl-baselines-v1.zip`. The downloaded archive matched its pinned SHA-256:

```text
e7001a943beb1b1a220ef4a58fae445569725682dc0dbbcb0d9300473a360aa3
```

Using Python 3.12.2 and `ir_datasets==0.6.1`, the audit loaded the judged
TREC-DL 2019 and 2020 topics, used relevance threshold 2, and produced 43 and
54 records, respectively. The category counts in display order
`reachable_top10`, `reranker_reachable_11_100`,
`depth_recoverable_101_1000`, and `residual_miss_top1000` were:

- TREC-DL 2019: 40, 2, 0, and 1;
- TREC-DL 2020: 47, 3, 3, and 1.

Both partitions reconciled to their full judged-topic populations, all 97
records received exactly one category, and the reranked candidate-set mismatch
count was zero for both datasets. The complete local suite passed 29 tests,
including the associated category and export regressions.

The three separate canonical outputs are:

| File | Rows | Bytes | SHA-256 |
|---|---:|---:|---|
| `verification/trec-category-recomputation.json` | 2 datasets | 1,296 | `92f84492022e03623a30fa85230a1a978ab85cabdd21871a8ab1669ec5dc64de` |
| `verification/trec-query-audit-records.json` | 97 | 37,390 | `73c799bb2d00ac78f53ffc1d482ea03d7cf3dd75e09649a9a727dae031106675` |
| `verification/trec-query-audit-records.csv` | 97 | 5,971 | `ae8c6626f4faabc6724c6038a6969fcba0ffa42f5a4dd1ec215098adcdcd0516` |

This dated check is the pre-publication evidence for the retained `v0.2.2`
outputs. Public identity and access are established separately by the Git tag,
GitHub Release, and permanent archive metadata. These checks do not redistribute
or regenerate the corpus, qrels, or ranked-run ZIP, and they do not establish
semantic relevance beyond the benchmark judgments.
