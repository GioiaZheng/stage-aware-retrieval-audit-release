"""Recompute mutually exclusive stage-aware query categories from public runs."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import ir_datasets


DATASETS = {
    "nfcorpus": {
        "dataset_id": "beir/nfcorpus/test",
        "bm25": "beir_nfcorpus_bm25.tsv",
        "reranked": "beir_nfcorpus_bm25_ce.tsv",
    },
    "scifact": {
        "dataset_id": "beir/scifact/test",
        "bm25": "beir_scifact_bm25.tsv",
        "reranked": "beir_scifact_bm25_ce.tsv",
    },
}


def read_run(path: Path) -> dict[str, list[tuple[int, str]]]:
    rows: dict[str, list[tuple[int, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 6:
                raise ValueError(f"{path}:{line_number}: expected six fields")
            qid, _, doc_id, rank, _, _ = fields
            rows[qid].append((int(rank), doc_id))
    for qid in rows:
        rows[qid].sort()
    return dict(rows)


def positive_qrels(dataset_id: str) -> dict[str, set[str]]:
    qrels: dict[str, set[str]] = defaultdict(set)
    for qrel in ir_datasets.load(dataset_id).qrels_iter():
        if qrel.relevance >= 1:
            qrels[str(qrel.query_id)].add(str(qrel.doc_id))
    return dict(qrels)


def category(first_relevant_rank: int | None) -> str:
    if first_relevant_rank is None:
        return "residual_miss_top1000"
    if first_relevant_rank <= 10:
        return "reachable_top10"
    if first_relevant_rank <= 100:
        return "reranker_reachable_11_100"
    return "depth_recoverable_101_1000"


def evaluate(
    name: str, run_dir: Path, requested_qids: set[str] | None = None
) -> dict[str, object]:
    spec = DATASETS[name]
    bm25 = read_run(run_dir / str(spec["bm25"]))
    reranked = read_run(run_dir / str(spec["reranked"]))
    qrels = positive_qrels(str(spec["dataset_id"]))

    if set(bm25) != set(reranked):
        raise ValueError(f"{name}: BM25 and reranked query sets differ")
    missing_qrels = sorted(set(bm25) - set(qrels))
    if missing_qrels:
        raise ValueError(f"{name}: {len(missing_qrels)} run queries lack positive qrels")

    counts: Counter[str] = Counter()
    assignment_count = 0
    candidate_set_mismatches = 0
    requested: list[dict[str, object]] = []
    for qid, ranked_rows in bm25.items():
        relevant = qrels[qid]
        first_rank = next(
            (rank for rank, doc_id in ranked_rows if doc_id in relevant), None
        )
        counts[category(first_rank)] += 1
        assignment_count += 1

        bm25_top100 = {doc_id for rank, doc_id in ranked_rows if rank <= 100}
        reranked_docs = {doc_id for _, doc_id in reranked[qid]}
        if bm25_top100 != reranked_docs:
            candidate_set_mismatches += 1

        if requested_qids and qid in requested_qids:
            requested.append(
                {
                    "query_id": qid,
                    "positive_qrel_count": len(relevant),
                    "first_relevant_rank": first_rank,
                    "category": category(first_rank),
                    "relevant_candidate_present_top100": first_rank is not None
                    and first_rank <= 100,
                    "reranked_candidate_set_matches_bm25_top100": (
                        bm25_top100 == reranked_docs
                    ),
                }
            )

    query_count = len(bm25)
    candidate_present = (
        counts["reachable_top10"] + counts["reranker_reachable_11_100"]
    )
    candidate_absent = (
        counts["depth_recoverable_101_1000"]
        + counts["residual_miss_top1000"]
    )
    result: dict[str, object] = {
        "dataset": name,
        "dataset_id": spec["dataset_id"],
        "relevance_threshold": 1,
        "query_count": query_count,
        "positive_qrel_count": sum(len(qrels[qid]) for qid in bm25),
        "categories": {
            key: counts[key]
            for key in (
                "reachable_top10",
                "reranker_reachable_11_100",
                "depth_recoverable_101_1000",
                "residual_miss_top1000",
            )
        },
        "candidate_present_top100": candidate_present,
        "candidate_absent_top100": candidate_absent,
        "partition_sum": assignment_count,
        "partition_covers_all_queries": assignment_count == query_count,
        "candidate_partition_reconciles": (
            candidate_present + candidate_absent == query_count
        ),
        "reranked_candidate_set_mismatches": candidate_set_mismatches,
    }
    if requested_qids:
        found = {item["query_id"] for item in requested}
        missing = sorted(requested_qids - found)
        if missing:
            raise ValueError(f"{name}: requested query IDs not found: {missing}")
        result["requested_queries"] = sorted(
            requested, key=lambda item: str(item["query_id"])
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        metavar="DATASET:QID",
        help="Include the stage assignment for one query (repeatable).",
    )
    args = parser.parse_args()

    requested_by_dataset: dict[str, set[str]] = defaultdict(set)
    for value in args.query:
        if ":" not in value:
            parser.error(f"invalid --query value {value!r}; expected DATASET:QID")
        dataset_name, qid = value.split(":", 1)
        if dataset_name not in DATASETS or not qid:
            parser.error(f"invalid --query value {value!r}")
        requested_by_dataset[dataset_name].add(qid)

    results = {
        "schema": "ecir-stage-category-recomputation.v1",
        "results": [
            evaluate(name, args.run_dir, requested_by_dataset.get(name))
            for name in DATASETS
        ],
    }
    rendered = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")


if __name__ == "__main__":
    main()
