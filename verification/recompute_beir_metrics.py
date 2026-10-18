"""Separately recompute the headline BEIR metrics from frozen public runs.

This script intentionally does not import project code from ``msmarco-genqa``.
It reads the public run bundle, obtains the public BEIR qrels via
``ir_datasets``, implements the documented metric contract directly, and
checks every result against the bundle manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import ir_datasets


REL_THRESHOLD = 1
TOLERANCE = 1e-12


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_run(path: Path) -> dict[str, list[str]]:
    rows: dict[str, list[tuple[int, str]]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 6:
                raise ValueError(f"{path}:{line_number}: expected six fields")
            qid, _, doc_id, rank_text, _, _ = fields
            rank = int(rank_text)
            if rank < 1:
                raise ValueError(f"{path}:{line_number}: rank must be positive")
            if doc_id in seen[qid]:
                raise ValueError(f"{path}:{line_number}: duplicate document {doc_id!r}")
            seen[qid].add(doc_id)
            rows[qid].append((rank, doc_id))

    result: dict[str, list[str]] = {}
    for qid, ranked in rows.items():
        ranked.sort()
        ranks = [rank for rank, _ in ranked]
        if ranks != list(range(1, len(ranks) + 1)):
            raise ValueError(f"{path}: non-contiguous ranks for query {qid!r}")
        result[qid] = [doc_id for _, doc_id in ranked]
    return result


def load_qrels(dataset_id: str) -> dict[str, dict[str, int]]:
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    for qrel in ir_datasets.load(dataset_id).qrels_iter():
        qid = str(qrel.query_id)
        doc_id = str(qrel.doc_id)
        relevance = int(qrel.relevance)
        if doc_id in qrels[qid]:
            raise ValueError(f"{dataset_id}: duplicate qrel for {qid}/{doc_id}")
        qrels[qid][doc_id] = relevance
    return dict(qrels)


def reciprocal_rank(retrieved: list[str], relevant: set[str], k: int) -> float:
    for rank, doc_id in enumerate(retrieved[:k], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def graded_ndcg_at_k(
    retrieved: list[str], judgments: dict[str, int], k: int
) -> float:
    # The resource contract uses raw non-negative relevance labels as gains.
    gains = [max(0, judgments.get(doc_id, 0)) for doc_id in retrieved[:k]]
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal = sorted((max(0, rel) for rel in judgments.values()), reverse=True)[:k]
    idcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(ideal, 1))
    return dcg / idcg if idcg else 0.0


def evaluate(
    run: dict[str, list[str]], qrels: dict[str, dict[str, int]]
) -> dict[str, Any]:
    qids = sorted(qrels)
    relevant = {
        qid: {doc_id for doc_id, rel in judgments.items() if rel >= REL_THRESHOLD}
        for qid, judgments in qrels.items()
    }
    n = len(qids)
    if not n:
        raise ValueError("qrels contain no topics")
    missing_run_topics = sorted(set(qids) - set(run))
    extra_run_topics = sorted(set(run) - set(qids))
    metrics = {
        "mrr@10": sum(
            reciprocal_rank(run.get(qid, []), relevant[qid], 10) for qid in qids
        )
        / n,
        "ndcg@10": sum(
            graded_ndcg_at_k(run.get(qid, []), qrels[qid], 10) for qid in qids
        )
        / n,
        "recall@100": sum(
            recall_at_k(run.get(qid, []), relevant[qid], 100) for qid in qids
        )
        / n,
        "recall@1000": sum(
            recall_at_k(run.get(qid, []), relevant[qid], 1000) for qid in qids
        )
        / n,
    }
    return {
        "query_count": n,
        "run_query_count": len(run),
        "positive_qrel_count": sum(len(items) for items in relevant.values()),
        "missing_run_topic_count": len(missing_run_topics),
        "extra_run_topic_count": len(extra_run_topics),
        "max_depth": max((len(items) for items in run.values()), default=0),
        "metrics": metrics,
        "no_hit_queries": {
            "at_100": sum(
                recall_at_k(run.get(qid, []), relevant[qid], 100) == 0.0
                for qid in qids
            ),
            "at_1000": sum(
                recall_at_k(run.get(qid, []), relevant[qid], 1000) == 0.0
                for qid in qids
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest_path = args.bundle_dir / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_members = [
        member for member in manifest["members"] if member.get("kind") == "beir_run"
    ]
    qrels_cache: dict[str, dict[str, dict[str, int]]] = {}
    results: list[dict[str, Any]] = []
    all_within_tolerance = True

    for member in run_members:
        run_path = args.bundle_dir / member["path"]
        actual_hash = sha256_file(run_path)
        if actual_hash != member["sha256"]:
            raise ValueError(f"{run_path}: SHA-256 mismatch")
        dataset_id = str(member["dataset_id"])
        if dataset_id not in qrels_cache:
            qrels_cache[dataset_id] = load_qrels(dataset_id)
        evaluated = evaluate(read_run(run_path), qrels_cache[dataset_id])

        expected = dict(member["expected_metrics"])
        comparable = {
            name: value for name, value in evaluated["metrics"].items() if name in expected
        }
        deltas = {name: abs(comparable[name] - float(expected[name])) for name in expected}
        within_tolerance = all(delta <= TOLERANCE for delta in deltas.values())
        all_within_tolerance = all_within_tolerance and within_tolerance
        results.append(
            {
                "dataset": member["dataset_key"],
                "dataset_id": dataset_id,
                "system": member["system"],
                "run_path": member["path"],
                "run_sha256": actual_hash,
                **evaluated,
                "expected_metrics": expected,
                "absolute_deltas": deltas,
                "max_absolute_delta": max(deltas.values(), default=0.0),
                "within_tolerance": within_tolerance,
            }
        )

    by_key = {(row["dataset"], row["system"]): row for row in results}
    comparisons = []
    for dataset in ("nfcorpus", "scifact"):
        bm25 = by_key[(dataset, "bm25")]
        reranked = by_key[(dataset, "bm25_ce")]
        deltas = {
            metric: reranked["metrics"][metric] - bm25["metrics"][metric]
            for metric in ("mrr@10", "ndcg@10", "recall@100")
        }
        comparisons.append(
            {
                "dataset": dataset,
                "query_count": bm25["query_count"],
                "bm25_ce_minus_bm25": deltas,
                "early_ranking_improves": deltas["mrr@10"] > 0
                and deltas["ndcg@10"] > 0,
                "candidate_recall_unchanged": abs(deltas["recall@100"]) <= TOLERANCE,
            }
        )

    payload = {
        "schema": "ecir-beir-metric-recomputation.v1",
        "metric_contract": {
            "topic_scope": "all_qrels_topics",
            "binary_relevance_threshold": REL_THRESHOLD,
            "mrr": "reciprocal rank of first relevant document at rank <= 10",
            "ndcg": "raw non-negative graded labels with log2 rank discount",
            "recall": "macro mean of per-query relevant-document recall",
            "tolerance": TOLERANCE,
        },
        "manifest_sha256": sha256_file(manifest_path),
        "all_expected_metrics_within_tolerance": all_within_tolerance,
        "results": results,
        "comparisons": comparisons,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    if not all_within_tolerance:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
