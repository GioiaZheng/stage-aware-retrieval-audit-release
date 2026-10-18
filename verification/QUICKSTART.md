# Stage-Aware Query Audit: Quick Start

This workflow downloads and verifies the public BEIR run bundle, obtains the
public NFCorpus and SciFact qrels through `ir_datasets`, recomputes the complete
stage partition, and reports the assignment for SciFact query `13`.

It does not require a clone of `msmarco-genqa`, corpus text, model weights, or
GPU access. On the retained clean run, the first download used about 11 MiB in
total for the 6,006,875-byte run archive and the public qrels cache.

The retained filenames `run_usability_quickstart.py` and
`requirements-usability.txt` are legacy technical names. This workflow requests
no user response and produces only a machine verification result.

## Requirements

- Python 3.10 or newer
- internet access during the first run
- a snapshot or clone of this resource package

Run all commands from the resource-package root.

## Windows PowerShell

```powershell
python -m venv .venv-audit
.\.venv-audit\Scripts\python.exe -m pip install -r verification\requirements-usability.txt
.\.venv-audit\Scripts\python.exe verification\run_usability_quickstart.py `
  --work-dir audit-work `
  --query scifact:13
```

## Linux or macOS

```bash
python3 -m venv .venv-audit
./.venv-audit/bin/python -m pip install -r verification/requirements-usability.txt
./.venv-audit/bin/python verification/run_usability_quickstart.py \
  --work-dir audit-work \
  --query scifact:13
```

## What to inspect

The command prints JSON and saves the same content to
`audit-work/quickstart-result.json`. Inspect:

1. `bundle.sha256` and `bundle.sha256_matches`;
2. the four values under `categories` for each dataset, in the displayed
   order;
3. `reranked_candidate_set_mismatches` for each dataset;
4. the requested query's `category` and `first_relevant_rank`.

## Clean-run rule

For a clean rerun, `audit-work` must not already exist. The directory is created
by the command and contains the downloaded archive, extracted ranked runs,
public qrels cache, and final JSON result. Keep it while inspecting or comparing
the output.

## Optional all-bundle structural validation

`validate_bundles.ps1` is the retained validator for all 14 ranked-run files.
Download the three pinned assets listed in `THIRD_PARTY.md`, then extract each
archive into a separate child directory whose root contains its
`bundle_manifest.json`, for example:

```text
verification/extracted/
  trec-dl-baselines-v1/bundle_manifest.json
  trec-dl-baselines-v1/runs/...
  beir-cross-domain-baselines-v1/bundle_manifest.json
  beir-cross-domain-baselines-v1/runs/...
  nfcorpus-video-query-ablation-v1/bundle_manifest.json
  nfcorpus-video-query-ablation-v1/runs/...
```

From Windows PowerShell, run:

```powershell
.\verification\validate_bundles.ps1 -Root verification\extracted
```

The command checks every member digest and the TREC field, row-count,
query-count, rank-contiguity, depth, and duplicate-document contracts. It
should finish with `Validated 14 ranked-run files.`
