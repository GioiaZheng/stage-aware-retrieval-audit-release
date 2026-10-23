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
        "bm25_depth": 1000,
        "reranked_depth": 100,
    },
    "scifact": {
        "dataset_id": "beir/scifact/test",
        "bm25": "beir_scifact_bm25.tsv",
        "reranked": "beir_scifact_bm25_ce.tsv",
        "bm25_depth": 1000,
        "reranked_depth": 100,
    },
}


def read_run(
    path: Path, *, expected_depth: int | None = None
) -> dict[str, list[tuple[int, str]]]:
    rows: dict[str, list[tuple[int, str]]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 6:
                raise ValueError(f"{path}:{line_number}: expected six fields")
            qid, _, doc_id, rank, _, _ = fields
            parsed_rank = int(rank)
            if parsed_rank < 1:
                raise ValueError(f"{path}:{line_number}: rank must be positive")
            if doc_id in seen[qid]:
                raise ValueError(
                    f"{path}:{line_number}: duplicate document {doc_id!r} "
                    f"for query {qid!r}"
                )
            seen[qid].add(doc_id)
            rows[qid].append((parsed_rank, doc_id))
    for qid, ranked_rows in rows.items():
        ranked_rows.sort()
        ranks = [rank for rank, _ in ranked_rows]
        if ranks != list(range(1, len(ranks) + 1)):
            raise ValueError(f"{path}: non-contiguous ranks for query {qid!r}")
        if expected_depth is not None and len(ranked_rows) != expected_depth:
            raise ValueError(
                f"{path}: query {qid!r} has depth {len(ranked_rows)}, "
                f"expected {expected_depth}"
            )
    return dict(rows)


def positive_qrels(dataset_id: str) -> dict[str, set[str]]:
    qrels: dict[str, set[str]] = defaultdict(set)
    for qrel in ir_datasets.load(dataset_id).qrels_iter():
        qid = str(qrel.query_id)
        # Touch every qrels topic so that a topic with no positive judgment is
        # not silently removed from the audit population.
        qrels[qid]
        if qrel.relevance >= 1:
            qrels[qid].add(str(qrel.doc_id))
    return dict(qrels)


def category(first_relevant_rank: int | None) -> str:
    if first_relevant_rank is None:
        return "residual_miss_top1000"
    if first_relevant_rank < 1 or first_relevant_rank > 1000:
        raise ValueError(
            f"first relevant rank {first_relevant_rank} is outside 1--1000"
        )
    if first_relevant_rank <= 10:
        return "reachable_top10"
    if first_relevant_rank <= 100:
        return "reranker_reachable_11_100"
    return "depth_recoverable_101_1000"


def evaluate(
    name: str,
    run_dir: Path,
    requested_qids: set[str] | None = None,
    *,
    include_query_records: bool = False,
) -> dict[str, object]:
    spec = DATASETS[name]
    bm25 = read_run(
        run_dir / str(spec["bm25"]), expected_depth=int(spec["bm25_depth"])
    )
    reranked = read_run(
        run_dir / str(spec["reranked"]),
        expected_depth=int(spec["reranked_depth"]),
    )
    qrels = positive_qrels(str(spec["dataset_id"]))

    qrels_topics = set(qrels)
    bm25_topics = set(bm25)
    reranked_topics = set(reranked)
    missing_bm25 = sorted(qrels_topics - bm25_topics)
    extra_bm25 = sorted(bm25_topics - qrels_topics)
    missing_reranked = sorted(qrels_topics - reranked_topics)
    extra_reranked = sorted(reranked_topics - qrels_topics)
    if missing_bm25 or extra_bm25 or missing_reranked or extra_reranked:
        raise ValueError(
            f"{name}: query population mismatch "
            f"(BM25 missing={len(missing_bm25)}, BM25 extra={len(extra_bm25)}, "
            f"reranked missing={len(missing_reranked)}, "
            f"reranked extra={len(extra_reranked)})"
        )

    no_positive_qrels = sorted(qid for qid, docs in qrels.items() if not docs)
    if no_positive_qrels:
        raise ValueError(
            f"{name}: {len(no_positive_qrels)} qrels topics have no positive "
            "judgment at relevance >= 1"
        )

    candidate_set_mismatch_qids = []
    for qid in sorted(qrels_topics):
        bm25_top100 = {doc_id for rank, doc_id in bm25[qid] if rank <= 100}
        reranked_docs = {doc_id for _, doc_id in reranked[qid]}
        if bm25_top100 != reranked_docs:
            candidate_set_mismatch_qids.append(qid)
    if candidate_set_mismatch_qids:
        preview = ", ".join(candidate_set_mismatch_qids[:5])
        raise ValueError(
            f"{name}: reranked candidate set differs from BM25 top 100 for "
            f"{len(candidate_set_mismatch_qids)} queries"
            + (f" (first: {preview})" if preview else "")
        )

    counts: Counter[str] = Counter()
    assignment_count = 0
    requested: list[dict[str, object]] = []
    query_records: list[dict[str, object]] = []
    for qid in sorted(qrels_topics):
        ranked_rows = bm25[qid]
        relevant = qrels[qid]
        first_match = next(
            (
                (rank, doc_id)
                for rank, doc_id in ranked_rows
                if doc_id in relevant
            ),
            None,
        )
        first_rank = first_match[0] if first_match else None
        first_doc_id = first_match[1] if first_match else None
        assigned_category = category(first_rank)
        candidate_present = first_rank is not None and first_rank <= 100
        counts[assigned_category] += 1
        assignment_count += 1

        query_record: dict[str, object] = {
            "dataset": name,
            "query_id": qid,
            "first_relevant_rank": first_rank,
            "first_relevant_doc_id": first_doc_id,
            "category": assigned_category,
            "positive_qrel_count": len(relevant),
            "relevant_candidate_present_top100": candidate_present,
            # The audit has already failed if any query violates this contract.
            "candidate_set_matches": True,
        }
        if include_query_records:
            query_records.append(query_record)

        if requested_qids and qid in requested_qids:
            requested.append(
                {
                    "query_id": qid,
                    "positive_qrel_count": len(relevant),
                    "first_relevant_rank": first_rank,
                    "category": assigned_category,
                    "relevant_candidate_present_top100": candidate_present,
                    "reranked_candidate_set_matches_bm25_top100": True,
                }
            )

    query_count = len(qrels_topics)
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
        "positive_qrel_count": sum(len(qrels[qid]) for qid in qrels_topics),
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
        "reranked_candidate_set_mismatches": 0,
    }
    if requested_qids:
        found = {item["query_id"] for item in requested}
        missing = sorted(requested_qids - found)
        if missing:
            raise ValueError(f"{name}: requested query IDs not found: {missing}")
        result["requested_queries"] = sorted(
            requested, key=lambda item: str(item["query_id"])
        )
    if include_query_records:
        result["query_records"] = query_records
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

    try:
        results = {
            "schema": "ecir-stage-category-recomputation.v1",
            "results": [
                evaluate(name, args.run_dir, requested_by_dataset.get(name))
                for name in DATASETS
            ],
        }
    except (OSError, ValueError) as error:
        parser.exit(status=1, message=f"audit invalid: {error}\n")
    rendered = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")


if __name__ == "__main__":
    main()
