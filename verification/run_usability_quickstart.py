"""Prepare public inputs and run the fixed ECIR audit task."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path


BUNDLE_URL = (
    "https://github.com/GioiaZheng/msmarco-genqa/releases/download/"
    "v2.2-beir-cross-domain-baselines/beir-cross-domain-baselines-v1.zip"
)
BUNDLE_SHA256 = "15e8e4ded1fe8d889e24a31f7794988ce0bbb6750c5f9b10e1d7dd4b38a5f633"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(url) as response, temporary.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    temporary.replace(destination)


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if os.path.commonpath((root, target)) != str(root):
                raise ValueError(f"unsafe archive member: {member.filename}")
        bundle.extractall(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument(
        "--query", default="scifact:13", help="Fixed query in DATASET:QID form."
    )
    args = parser.parse_args()

    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 or newer is required")

    work_dir = args.work_dir.resolve()
    archive = work_dir / "downloads" / "beir-cross-domain-baselines-v1.zip"
    extracted = work_dir / "extracted"
    cache = work_dir / "ir_datasets_cache"
    output = work_dir / "quickstart-result.json"

    if not archive.exists():
        print(f"Downloading {BUNDLE_URL}", file=sys.stderr)
        download(BUNDLE_URL, archive)
    observed_hash = sha256(archive)
    if observed_hash != BUNDLE_SHA256:
        raise SystemExit(
            f"bundle SHA-256 mismatch: expected {BUNDLE_SHA256}, got {observed_hash}"
        )

    safe_extract(archive, extracted)
    os.environ["IR_DATASETS_HOME"] = str(cache)

    try:
        from recompute_stage_categories import DATASETS, evaluate
    except ModuleNotFoundError as error:
        if error.name == "ir_datasets":
            raise SystemExit(
                "Missing dependency: install verification/requirements-usability.txt"
            ) from error
        raise

    if ":" not in args.query:
        parser.error("--query must use DATASET:QID")
    dataset_name, qid = args.query.split(":", 1)
    if dataset_name not in DATASETS or not qid:
        parser.error("--query must name a supported dataset and non-empty query ID")

    run_dir = extracted / "runs"
    analysis = [
        evaluate(
            name,
            run_dir,
            {qid} if name == dataset_name else None,
        )
        for name in DATASETS
    ]
    result = {
        "schema": "ecir-usability-quickstart.v1",
        "bundle": {
            "url": BUNDLE_URL,
            "sha256": observed_hash,
            "sha256_matches": True,
        },
        "analysis": analysis,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    print(f"Saved result to {output}", file=sys.stderr)


if __name__ == "__main__":
    main()
