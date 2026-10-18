# Public Run Bundle Verification Report

Date: 2026-10-04

## Scope

This check verifies the public accessibility, archive integrity, member
integrity, and structural validity of the ranked-run bundles proposed as core
ECIR paper artifacts. This structural check does not recompute IR metrics from
qrels; the separate metric recomputation is documented below.

All downloads and extracted files were kept outside the read-only
`msmarco-genqa` checkout and are excluded from this repository by `.gitignore`.

## Archive verification

| Archive | Bytes | SHA-256 result | Run files |
|---|---:|---|---:|
| `trec-dl-baselines-v1.zip` | 1,041,738 | Match | 4 |
| `beir-cross-domain-baselines-v1.zip` | 6,006,875 | Match | 4 |
| `nfcorpus-video-query-ablation-v1.zip` | 2,975,679 | Match | 6 |

All three archives were downloaded without credentials from their pinned
GitHub release URLs. Their byte sizes and SHA-256 digests matched the checked
artifact pointers.

## Structural checks

For every ranked-run member, `verification/validate_bundles.ps1` checked:

- member byte size and SHA-256 against `bundle_manifest.json`;
- exactly six tab-separated TREC fields per row;
- integer rank values;
- manifest row count and query count;
- ranks beginning at 1 and continuing without gaps to the declared depth for
  every query; and
- no duplicate document identifier within a query.

## Results

| Bundle | Run | Rows | Queries | Depth | Result |
|---|---|---:|---:|---:|---|
| TREC-DL | `trec_dl_2019_bm25.tsv` | 43,000 | 43 | 1,000 | PASS |
| TREC-DL | `trec_dl_2019_bm25_ce.tsv` | 4,300 | 43 | 100 | PASS |
| TREC-DL | `trec_dl_2020_bm25.tsv` | 54,000 | 54 | 1,000 | PASS |
| TREC-DL | `trec_dl_2020_bm25_ce.tsv` | 5,400 | 54 | 100 | PASS |
| BEIR | `beir_nfcorpus_bm25.tsv` | 323,000 | 323 | 1,000 | PASS |
| BEIR | `beir_nfcorpus_bm25_ce.tsv` | 32,300 | 323 | 100 | PASS |
| BEIR | `beir_scifact_bm25.tsv` | 300,000 | 300 | 1,000 | PASS |
| BEIR | `beir_scifact_bm25_ce.tsv` | 30,000 | 300 | 100 | PASS |
| NFCorpus video | `nfcorpus_video_title_bm25.tsv` | 102,000 | 102 | 1,000 | PASS |
| NFCorpus video | `nfcorpus_video_title_bm25_ce.tsv` | 10,200 | 102 | 100 | PASS |
| NFCorpus video | `nfcorpus_video_description_bm25.tsv` | 102,000 | 102 | 1,000 | PASS |
| NFCorpus video | `nfcorpus_video_description_bm25_ce.tsv` | 10,200 | 102 | 100 | PASS |
| NFCorpus video | `nfcorpus_video_title_plus_description_bm25.tsv` | 102,000 | 102 | 1,000 | PASS |
| NFCorpus video | `nfcorpus_video_title_plus_description_bm25_ce.tsv` | 10,200 | 102 | 100 | PASS |

Total: 14 of 14 ranked-run files passed.

## Redistribution boundary observed

The bundles contain ranked query/document identifiers, ranks, scores,
documentation, and checksums. They do not redistribute query text, document
text, qrels mirrors, model weights, caches, or machine-local manifests.

## What this establishes

- The three pinned public release archives were accessible on 2026-10-04.
- The archives and all ranked-run members matched their declared hashes.
- The stated 14-run inventory can be reconstructed from public artifacts.
- The run files satisfy the declared structural contracts.

## What this report does not establish

- This structural report does not recompute metrics. A separate,
  author-produced recomputation of MRR, nDCG, and recall is documented in
  `verification/beir-metric-recomputation.md`; paired-bootstrap values remain
  outside the current verification.
- This report does not establish novelty, broad usability, or scientific
  validity of the diagnostic categories.
- Public accessibility is a point-in-time observation; the paper should use
  permanent release URLs and preserve the pinned hashes.
