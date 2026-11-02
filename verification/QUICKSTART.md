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

The audit is fail-closed. It exits with a non-zero status and does not emit a
valid result if a qrels topic is missing from either run, a run contains an
extra topic, a qrels topic has no positive judgment at the declared threshold,
rank structure or depth is invalid, a query repeats a document, or a reranked
candidate set differs from the corresponding BM25 top 100.

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

## Export all query records

To generate the separate JSON and CSV audit tables from the validated BEIR run
directory, run:

```powershell
.\.venv-audit\Scripts\python.exe verification\export_query_audit.py `
  --run-dir audit-work\extracted\runs `
  --json-output verification\query-audit-records.json `
  --csv-output verification\query-audit-records.csv
```

The retained BEIR file identifiers and schema are documented in
[`QUERY-AUDIT.md`](QUERY-AUDIT.md). The original aggregate JSON schema and
retained hashes remain unchanged.

## TREC-DL v0.2.2 retained-output regeneration

The TREC-DL audit is a separate, explicit workflow. It does not change the
default BEIR datasets used by the one-command Quick Start. The recommended
release check downloads the pinned archive, verifies its SHA-256, regenerates
all three TREC-DL outputs in an isolated directory, and requires them to match
the retained files byte for byte:

```powershell
.\.venv-audit\Scripts\python.exe verification\reproduce_trec_release.py `
  --work-dir trec-release-work `
  --output-dir trec-release-work\generated
```

On Linux or macOS, use `.venv-audit/bin/python` with the same arguments.

For manual inspection, the helper uses this pinned external asset without
adding it to the repository:

```text
https://github.com/GioiaZheng/msmarco-genqa/releases/download/v2.1-trec-dl-baselines/trec-dl-baselines-v1.zip
```

Its required SHA-256 is:

```text
e7001a943beb1b1a220ef4a58fae445569725682dc0dbbcb0d9300473a360aa3
```

On Windows PowerShell, download, verify, and extract it into a clean work
directory:

```powershell
New-Item -ItemType Directory -Path trec-work | Out-Null
Invoke-WebRequest `
  -Uri "https://github.com/GioiaZheng/msmarco-genqa/releases/download/v2.1-trec-dl-baselines/trec-dl-baselines-v1.zip" `
  -OutFile trec-work\trec-dl-baselines-v1.zip
$trecDigest = (Get-FileHash -Algorithm SHA256 `
  trec-work\trec-dl-baselines-v1.zip).Hash.ToLower()
if ($trecDigest -ne "e7001a943beb1b1a220ef4a58fae445569725682dc0dbbcb0d9300473a360aa3") {
  throw "TREC-DL bundle SHA-256 mismatch"
}
Expand-Archive trec-work\trec-dl-baselines-v1.zip `
  -DestinationPath trec-work\extracted
```

Then run the category and per-query exporters with both judged-topic
contracts selected explicitly:

```powershell
.\.venv-audit\Scripts\python.exe verification\recompute_stage_categories.py `
  --run-dir trec-work\extracted\runs `
  --dataset trec_dl_2019 `
  --dataset trec_dl_2020 `
  --output trec-work\trec-category-recomputation.json

.\.venv-audit\Scripts\python.exe verification\export_query_audit.py `
  --run-dir trec-work\extracted\runs `
  --dataset trec_dl_2019 `
  --dataset trec_dl_2020 `
  --json-output trec-work\trec-query-audit-records.json `
  --csv-output trec-work\trec-query-audit-records.csv
```

On Linux or macOS, use the equivalent `.venv-audit/bin/python` commands shown
in `QUERY-AUDIT.md` after verifying the ZIP with `sha256sum` and extracting it
under `trec-work/extracted`.

The aggregate output must report 43 TREC-DL 2019 topics with counts
`40 / 2 / 0 / 1` and 54 TREC-DL 2020 topics with counts `47 / 3 / 3 / 1`, in
the documented category order. Both candidate-set mismatch counts must be zero,
and the JSON and CSV exports must each contain 97 records. The expected output
sizes and SHA-256 values are recorded in `QUERY-AUDIT.md`.

Neither this workflow nor the repository redistributes the MS MARCO corpus,
TREC-DL qrels, or the ranked-run ZIP. Their source and licensing boundary are
documented in `THIRD_PARTY.md`.
