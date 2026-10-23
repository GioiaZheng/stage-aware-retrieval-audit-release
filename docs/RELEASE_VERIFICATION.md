# Release Verification

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
323-query NFCorpus or 300-query SciFact outputs. This recheck describes local,
unreleased changes until a new commit and release identifier are assigned.
