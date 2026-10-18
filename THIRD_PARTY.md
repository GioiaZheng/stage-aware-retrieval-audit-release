# Third-Party and External Resources

This repository contains original verification code and reports, but it does
not redistribute benchmark datasets, qrels, model weights, or ranked-run
archives.

## Ranked-run bundles

The broader resource inventory uses three external release assets hosted in
`GioiaZheng/msmarco-genqa`:

| Release tag | Asset | Bytes | SHA-256 |
|---|---|---:|---|
| `v2.1-trec-dl-baselines` | [`trec-dl-baselines-v1.zip`](https://github.com/GioiaZheng/msmarco-genqa/releases/download/v2.1-trec-dl-baselines/trec-dl-baselines-v1.zip) | 1,041,738 | `e7001a943beb1b1a220ef4a58fae445569725682dc0dbbcb0d9300473a360aa3` |
| `v2.2-beir-cross-domain-baselines` | [`beir-cross-domain-baselines-v1.zip`](https://github.com/GioiaZheng/msmarco-genqa/releases/download/v2.2-beir-cross-domain-baselines/beir-cross-domain-baselines-v1.zip) | 6,006,875 | `15e8e4ded1fe8d889e24a31f7794988ce0bbb6750c5f9b10e1d7dd4b38a5f633` |
| `v2.3-nfcorpus-video-query-ablation` | [`nfcorpus-video-query-ablation-v1.zip`](https://github.com/GioiaZheng/msmarco-genqa/releases/download/v2.3-nfcorpus-video-query-ablation/nfcorpus-video-query-ablation-v1.zip) | 2,975,679 | `6d588eef275989e822d12e40afa67396a6226dd6df52246877a312556c64272f` |

The one-command Quick Start downloads only the BEIR asset used by the complete
query-level audit. Its release tag resolves to code commit
`e0f240ef9e5e3ea3f74a3df5fe835f77b487573c`. The optional structural validator
accepts all three archives after extraction as documented in
`verification/QUICKSTART.md`.

The upstream repository's software is licensed under MIT, but the three ZIP
files do not contain an asset-specific license and their GitHub Release pages
do not state one. The MIT software license is therefore not treated here as an
unambiguous reuse license for the ranked-run data. The assets remain hosted in
their original releases and are not copied into this repository. Their internal
manifests record available experiment commits, member hashes, query counts, row
counts, depths, and expected metrics.

The archives contain ranked document identifiers, ranks, scores, checksums,
and documentation. They exclude query text, document text, qrels mirrors,
model weights, caches, and machine-local manifests.

## Benchmark resources

The verification scripts use `ir_datasets` to obtain public NFCorpus and
SciFact resources. No copy of those resources is committed here. Users are
responsible for observing the applicable upstream dataset terms.

The browser's worked example loads SciFact query text and a relevant-document
title and abstract excerpt at runtime. Under the
[SciFact license](https://github.com/allenai/scifact/blob/a5254a1bf108726a1704d8e191b8a7f2225a029f/LICENSE.md),
claims and evidence annotations are CC BY 4.0, while corpus abstracts from
S2ORC are ODC-By 1.0. The release-candidate application source includes this
attribution beside the example; deployment of that source revision is a
separate release step. Any downloaded verification export that retains the
example text includes the corresponding source-license metadata, remains
subject to those source terms, and is not relicensed by this repository.

## License boundary

The Apache-2.0 and CC BY 4.0 licenses in this repository cover only the
original material identified in this repository. They do not relicense the
external release asset, `ir_datasets`, NFCorpus, SciFact, benchmark judgments,
or any other downloaded dependency.
