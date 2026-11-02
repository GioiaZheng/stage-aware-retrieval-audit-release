"""Reproduce the retained TREC-DL audit outputs from the pinned bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from run_usability_quickstart import download, safe_extract, sha256


TREC_DATASETS = ("trec_dl_2019", "trec_dl_2020")
TREC_BUNDLE_URL = (
    "https://github.com/GioiaZheng/msmarco-genqa/releases/download/"
    "v2.1-trec-dl-baselines/trec-dl-baselines-v1.zip"
)
TREC_BUNDLE_SHA256 = (
    "e7001a943beb1b1a220ef4a58fae445569725682dc0dbbcb0d9300473a360aa3"
)
OUTPUT_NAMES = (
    "trec-category-recomputation.json",
    "trec-query-audit-records.json",
    "trec-query-audit-records.csv",
)
REFERENCE_DIR = Path(__file__).resolve().parent


def write_and_compare(
    output_dir: Path, name: str, rendered: str
) -> str:
    """Write one generated result and require an exact retained-file match."""
    generated = output_dir / name
    reference = REFERENCE_DIR / name
    generated.write_text(rendered, encoding="utf-8", newline="\n")
    if generated.read_bytes() != reference.read_bytes():
        raise SystemExit(
            f"generated output differs from retained reference: {name}"
        )
    return hashlib.sha256(generated.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required")

    work_dir = args.work_dir.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir == REFERENCE_DIR:
        parser.error("--output-dir must not overwrite retained references")
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    archive = work_dir / "downloads" / "trec-dl-baselines-v1.zip"
    if not archive.exists():
        print(f"Downloading {TREC_BUNDLE_URL}", file=sys.stderr)
        download(TREC_BUNDLE_URL, archive)
    observed_hash = sha256(archive)
    if observed_hash != TREC_BUNDLE_SHA256:
        raise SystemExit(
            "bundle SHA-256 mismatch: "
            f"expected {TREC_BUNDLE_SHA256}, got {observed_hash}"
        )

    cache = work_dir / "ir_datasets_cache"
    os.environ["IR_DATASETS_HOME"] = str(cache)

    try:
        from export_query_audit import (
            build_payload,
            render_csv,
            render_json,
        )
        from recompute_stage_categories import evaluate
    except ModuleNotFoundError as error:
        if error.name == "ir_datasets":
            raise SystemExit(
                "Missing dependency: install "
                "verification/requirements-usability.txt"
            ) from error
        raise

    with tempfile.TemporaryDirectory(
        dir=work_dir, prefix="trec-extracted-"
    ) as extracted_directory:
        extracted = Path(extracted_directory)
        safe_extract(archive, extracted)
        run_dir = extracted / "runs"

        aggregate = {
            "schema": "ecir-stage-category-recomputation.v1",
            "results": [evaluate(name, run_dir) for name in TREC_DATASETS],
        }
        payload = build_payload(run_dir, TREC_DATASETS)

    rendered = {
        OUTPUT_NAMES[0]: json.dumps(aggregate, indent=2, sort_keys=True) + "\n",
        OUTPUT_NAMES[1]: render_json(payload),
        OUTPUT_NAMES[2]: render_csv(payload),
    }
    for name in OUTPUT_NAMES:
        digest = write_and_compare(output_dir, name, rendered[name])
        print(f"matched {name}: sha256={digest}")


if __name__ == "__main__":
    main()
