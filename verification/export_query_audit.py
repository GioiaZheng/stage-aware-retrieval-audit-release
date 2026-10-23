"""Export deterministic per-query audit records from the validated inputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from typing import Any

import ir_datasets

from recompute_stage_categories import DATASETS, evaluate


SCHEMA = "ecir-query-audit-records.v1"
VERIFIER_VERSION = "0.2.1"
CSV_FIELDS = [
    "dataset",
    "query_id",
    "first_relevant_rank",
    "first_relevant_doc_id",
    "category",
    "positive_qrel_count",
    "relevant_candidate_present_top100",
    "candidate_set_matches",
]
DEPTH_RECOVERABLE_FIELDS = [
    "dataset",
    "query_id",
    "first_relevant_doc_id",
    "first_relevant_rank",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def qrels_binding(dataset_id: str) -> dict[str, Any]:
    """Fingerprint an order-independent canonical representation of qrels."""
    rows = sorted(
        (
            str(qrel.query_id),
            str(qrel.doc_id),
            int(qrel.relevance),
        )
        for qrel in ir_datasets.load(dataset_id).qrels_iter()
    )
    canonical = "".join(
        f"{qid}\t{doc_id}\t{relevance}\n"
        for qid, doc_id, relevance in rows
    ).encode("utf-8")
    return {
        "dataset_id": dataset_id,
        "ir_datasets_version": version("ir_datasets"),
        "canonicalization": (
            "No header or BOM; query_id and document_id converted to strings; "
            "relevance converted to a base-10 integer; tuples sorted "
            "lexicographically by query_id, document_id, relevance; UTF-8 "
            "tab-separated fields; every row, including the last, ends with LF"
        ),
        "row_count": len(rows),
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


def run_binding(path: Path, expected_depth: int) -> dict[str, Any]:
    return {
        "path": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "expected_depth": expected_depth,
    }


def validate_records(
    records: list[dict[str, object]], aggregate: dict[str, object]
) -> None:
    keys = {(str(row["dataset"]), str(row["query_id"])) for row in records}
    if len(keys) != len(records):
        raise ValueError("query records contain duplicate dataset/query_id keys")
    if len(records) != int(aggregate["query_count"]):
        raise ValueError("query record count does not match aggregate query_count")
    observed = Counter(str(row["category"]) for row in records)
    expected = {
        str(key): int(value)
        for key, value in dict(aggregate["categories"]).items()
    }
    if dict(observed) != {key: value for key, value in expected.items() if value}:
        raise ValueError("query records do not reproduce aggregate categories")
    for row in records:
        rank = row["first_relevant_rank"]
        doc_id = row["first_relevant_doc_id"]
        if (rank is None) != (doc_id is None):
            raise ValueError("first relevant rank and document must be jointly null")
        if not bool(row["candidate_set_matches"]):
            raise ValueError("valid query record contains a candidate-set mismatch")


def build_payload(run_dir: Path) -> dict[str, Any]:
    datasets = []
    total_records = 0
    for name, spec in DATASETS.items():
        evaluated = evaluate(name, run_dir, include_query_records=True)
        records = list(evaluated.pop("query_records"))
        validate_records(records, evaluated)
        total_records += len(records)

        bm25_path = run_dir / str(spec["bm25"])
        reranked_path = run_dir / str(spec["reranked"])
        dataset_id = str(spec["dataset_id"])
        datasets.append(
            {
                "dataset": name,
                "dataset_id": dataset_id,
                "input_binding": {
                    "bm25_run": run_binding(
                        bm25_path, int(spec["bm25_depth"])
                    ),
                    "reranked_run": run_binding(
                        reranked_path, int(spec["reranked_depth"])
                    ),
                    "qrels": qrels_binding(dataset_id),
                    "relevance_threshold": 1,
                    "candidate_cutoff": 100,
                    "first_stage_depth": 1000,
                },
                "aggregate": evaluated,
                "records": records,
            }
        )
    return {
        "schema": SCHEMA,
        "verifier_version": VERIFIER_VERSION,
        "record_count": total_records,
        "record_key": ["dataset", "query_id"],
        "datasets": datasets,
    }


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_csv(payload: dict[str, Any]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for dataset in payload["datasets"]:
        for record in dataset["records"]:
            row = dict(record)
            row["first_relevant_rank"] = (
                "" if row["first_relevant_rank"] is None else row["first_relevant_rank"]
            )
            row["first_relevant_doc_id"] = (
                "" if row["first_relevant_doc_id"] is None else row["first_relevant_doc_id"]
            )
            row["relevant_candidate_present_top100"] = str(
                row["relevant_candidate_present_top100"]
            ).lower()
            row["candidate_set_matches"] = str(
                row["candidate_set_matches"]
            ).lower()
            writer.writerow({field: row[field] for field in CSV_FIELDS})
    return output.getvalue()


def records_for_category(
    payload: dict[str, Any], category_name: str
) -> list[dict[str, object]]:
    """Select records from the current computation, never a retained file."""
    return [
        dict(record)
        for dataset in payload["datasets"]
        for record in dataset["records"]
        if record["category"] == category_name
    ]


def render_record_selection_csv(records: list[dict[str, object]]) -> str:
    """Render the compact follow-up list used by the web demonstration."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=DEPTH_RECOVERABLE_FIELDS,
        lineterminator="\n",
    )
    writer.writeheader()
    for record in records:
        writer.writerow(
            {field: record[field] for field in DEPTH_RECOVERABLE_FIELDS}
        )
    return output.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--csv-output", required=True, type=Path)
    args = parser.parse_args()

    try:
        payload = build_payload(args.run_dir)
        rendered_json = render_json(payload)
        rendered_csv = render_csv(payload)
    except (OSError, ValueError) as error:
        parser.exit(status=1, message=f"audit export invalid: {error}\n")

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(rendered_json, encoding="utf-8", newline="\n")
    args.csv_output.write_text(rendered_csv, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
