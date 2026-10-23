from __future__ import annotations

import ast
import csv
import io
import json
import sys
import tempfile
import threading
import time
import unittest
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION = ROOT / "verification"
sys.path.insert(0, str(VERIFICATION))

from run_usability_quickstart import BUNDLE_SHA256, BUNDLE_URL  # noqa: E402
from export_query_audit import records_for_category  # noqa: E402
import recompute_stage_categories as stage_categories  # noqa: E402
import run_usability_quickstart as quickstart  # noqa: E402


class ReleaseCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = json.loads(
            (VERIFICATION / "quickstart-reference.json").read_text(encoding="utf-8")
        )
        cls.recomputation = json.loads(
            (VERIFICATION / "category-recomputation.json").read_text(
                encoding="utf-8"
            )
        )

    def test_all_json_files_parse(self) -> None:
        json_files = sorted(VERIFICATION.glob("*.json"))
        self.assertGreaterEqual(len(json_files), 3)
        for path in json_files:
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"))

    def test_reference_uses_pinned_bundle(self) -> None:
        bundle = self.reference["bundle"]
        self.assertEqual(bundle["url"], BUNDLE_URL)
        self.assertEqual(bundle["sha256"], BUNDLE_SHA256)
        self.assertTrue(bundle["sha256_matches"])
        self.assertEqual(len(BUNDLE_SHA256), 64)

    def test_reference_matches_independent_recomputation(self) -> None:
        expected = {
            item["dataset"]: item for item in self.recomputation["results"]
        }
        observed = {item["dataset"]: item for item in self.reference["analysis"]}
        self.assertEqual(set(observed), {"nfcorpus", "scifact"})
        self.assertEqual(set(observed), set(expected))

        for dataset, result in observed.items():
            with self.subTest(dataset=dataset):
                self.assertEqual(result["categories"], expected[dataset]["categories"])
                self.assertEqual(
                    result["reranked_candidate_set_mismatches"],
                    expected[dataset]["reranked_candidate_set_mismatches"],
                )

    def test_category_partitions_cover_every_query(self) -> None:
        for result in self.reference["analysis"]:
            with self.subTest(dataset=result["dataset"]):
                self.assertEqual(sum(result["categories"].values()), result["query_count"])
                self.assertEqual(result["partition_sum"], result["query_count"])
                self.assertTrue(result["partition_covers_all_queries"])
                self.assertTrue(result["candidate_partition_reconciles"])

    def test_fixed_query_evidence(self) -> None:
        scifact = next(
            item for item in self.reference["analysis"] if item["dataset"] == "scifact"
        )
        query = scifact["requested_queries"][0]
        self.assertEqual(query["query_id"], "13")
        self.assertEqual(query["first_relevant_rank"], 170)
        self.assertEqual(query["category"], "depth_recoverable_101_1000")
        self.assertFalse(query["relevant_candidate_present_top100"])
        self.assertTrue(query["reranked_candidate_set_matches_bm25_top100"])

    def test_query_audit_exports_reconcile(self) -> None:
        json_path = VERIFICATION / "query-audit-records.json"
        csv_path = VERIFICATION / "query-audit-records.csv"
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        with csv_path.open(encoding="utf-8", newline="") as handle:
            csv_rows = list(csv.DictReader(handle))

        self.assertEqual(payload["schema"], "ecir-query-audit-records.v1")
        self.assertEqual(payload["verifier_version"], "0.2.1")
        self.assertEqual(payload["record_count"], 623)
        self.assertEqual(len(csv_rows), 623)

        json_rows = [
            row
            for dataset in payload["datasets"]
            for row in dataset["records"]
        ]
        keys = {(row["dataset"], row["query_id"]) for row in json_rows}
        self.assertEqual(len(keys), 623)

        expected_categories = {
            "nfcorpus": {
                "reachable_top10": 218,
                "reranker_reachable_11_100": 33,
                "depth_recoverable_101_1000": 24,
                "residual_miss_top1000": 48,
            },
            "scifact": {
                "reachable_top10": 239,
                "reranker_reachable_11_100": 26,
                "depth_recoverable_101_1000": 24,
                "residual_miss_top1000": 11,
            },
        }
        for dataset in payload["datasets"]:
            name = dataset["dataset"]
            records = dataset["records"]
            observed = Counter(row["category"] for row in records)
            self.assertEqual(dict(observed), expected_categories[name])
            self.assertEqual(len(records), dataset["aggregate"]["query_count"])
            self.assertTrue(all(row["candidate_set_matches"] for row in records))
            for binding in ("bm25_run", "reranked_run"):
                self.assertEqual(len(dataset["input_binding"][binding]["sha256"]), 64)
            qrels_binding = dataset["input_binding"]["qrels"]
            self.assertEqual(len(qrels_binding["sha256"]), 64)
            self.assertIn("No header or BOM", qrels_binding["canonicalization"])
            self.assertIn("including the last", qrels_binding["canonicalization"])

        for json_row, csv_row in zip(json_rows, csv_rows, strict=True):
            self.assertEqual(csv_row["dataset"], json_row["dataset"])
            self.assertEqual(csv_row["query_id"], json_row["query_id"])
            self.assertEqual(csv_row["category"], json_row["category"])
            self.assertEqual(
                csv_row["first_relevant_rank"],
                ""
                if json_row["first_relevant_rank"] is None
                else str(json_row["first_relevant_rank"]),
            )
            self.assertEqual(
                csv_row["first_relevant_doc_id"],
                ""
                if json_row["first_relevant_doc_id"] is None
                else json_row["first_relevant_doc_id"],
            )
            self.assertEqual(
                csv_row["positive_qrel_count"],
                str(json_row["positive_qrel_count"]),
            )
            self.assertEqual(
                csv_row["relevant_candidate_present_top100"],
                str(json_row["relevant_candidate_present_top100"]).lower(),
            )
            self.assertEqual(
                csv_row["candidate_set_matches"],
                str(json_row["candidate_set_matches"]).lower(),
            )
            self.assertEqual(
                json_row["first_relevant_rank"] is None,
                json_row["first_relevant_doc_id"] is None,
            )

        depth_records = records_for_category(
            payload, "depth_recoverable_101_1000"
        )
        self.assertEqual(len(depth_records), 48)
        self.assertEqual(
            Counter(row["dataset"] for row in depth_records),
            {"nfcorpus": 24, "scifact": 24},
        )
        self.assertTrue(
            all(
                row["first_relevant_doc_id"]
                and 101 <= int(row["first_relevant_rank"]) <= 1000
                for row in depth_records
            )
        )

    def test_release_metadata_is_present(self) -> None:
        repository_url = (
            "https://github.com/GioiaZheng/stage-aware-retrieval-audit-release"
        )
        browser_url = "https://stage-aware-retrieval-audit.streamlit.app/"
        required = [
            "LICENSE",
            "LICENSE-DOCUMENTATION.md",
            "CITATION.cff",
            "THIRD_PARTY.md",
            "docs/PROVENANCE.md",
        ]
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file())

        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn("cff-version: 1.2.0", citation)
        self.assertIn("family-names: \"Zheng\"", citation)
        self.assertIn("license: Apache-2.0", citation)
        self.assertIn(f'repository-code: "{repository_url}"', citation)
        self.assertIn(f'url: "{browser_url}"', citation)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        quality_url = f"{repository_url}/actions/workflows/quality.yml"
        self.assertIn(f"{quality_url}/badge.svg", readme)
        self.assertIn(f"]({quality_url})", readme)
        self.assertIn(browser_url, readme)
        self.assertNotIn("This is a private staging copy", readme)

        result_license = (ROOT / "LICENSE-DOCUMENTATION.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("query-audit-records.json", result_license)
        self.assertIn("query-audit-records.csv", result_license)
        self.assertIn("does not relicense identifiers", result_license)

    def test_scifact_attribution_is_visible(self) -> None:
        for relative in ["THIRD_PARTY.md", "verification/web_app.py"]:
            with self.subTest(path=relative):
                content = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("CC BY 4.0", content)
                self.assertIn("ODC-By 1.0", content)
                if relative == "THIRD_PARTY.md":
                    self.assertIn(
                        "allenai/scifact/blob/"
                        "a5254a1bf108726a1704d8e191b8a7f2225a029f/LICENSE.md",
                        content,
                    )
                else:
                    self.assertIn(
                        '"https://github.com/allenai/scifact/blob/"', content
                    )
                    self.assertIn(
                        '"a5254a1bf108726a1704d8e191b8a7f2225a029f/LICENSE.md"',
                        content,
                    )

    def test_participant_derived_evidence_is_absent(self) -> None:
        raw_records = [
            path
            for path in ROOT.rglob("*.json")
            if path.name.startswith("ecir-web-usability-record")
            or '"schema": "ecir-web-usability-record.'
            in path.read_text(encoding="utf-8", errors="replace")
        ]
        self.assertEqual(raw_records, [])

        self.assertFalse((ROOT / "docs" / "FORMATIVE_USABILITY.md").exists())

        note = (ROOT / "docs" / "TECHNICAL_ACCESS_VERIFICATION.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("only author-run deployment checks", note)
        self.assertIn("no participant", note)
        self.assertIn("not counted, quoted, classified, aggregated", note)

    def test_browser_interface_is_result_only(self) -> None:
        source = (VERIFICATION / "web_app.py").read_text(encoding="utf-8")
        for expected in [
            'APP_VERSION = "web-audit-v2"',
            '"schema": "ecir-web-audit-result.v2"',
            '"schema": "ecir-web-audit-export.v2"',
            'build_payload(run_dir)',
            '"Download all 623 query records (CSV)"',
            '"Download depth-recoverable follow-up list (CSV)"',
            '"Download complete verification result (JSON)"',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, source)

        for forbidden in [
            "participant_response",
            "st.text_area",
            "st.selectbox",
            "started_at_utc",
            "completed_at_utc",
            "Download test record",
            "send that file back",
            "web-usability-v4",
            "ecir-web-usability-record",
        ]:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

        tree = ast.parse(source)
        export_nodes = [
            node
            for node in tree.body
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id in {"APP_VERSION", "SCIFACT_LICENSE_URL"}
                    for target in node.targets
                )
            )
            or (isinstance(node, ast.FunctionDef) and node.name == "build_export")
        ]
        namespace: dict[str, object] = {"json": json}
        exec(
            compile(
                ast.Module(body=export_nodes, type_ignores=[]),
                "verification/web_app.py",
                "exec",
            ),
            namespace,
        )
        export_bytes = namespace["build_export"]({"schema": "test-result"})
        exported = json.loads(export_bytes)
        self.assertEqual(exported["schema"], "ecir-web-audit-export.v2")
        self.assertEqual(exported["result"], {"schema": "test-result"})
        scifact = exported["third_party"]["scifact"]
        self.assertEqual(scifact["claims_and_evidence_license"], "CC BY 4.0")
        self.assertEqual(scifact["corpus_abstracts_license"], "ODC-By 1.0")
        self.assertEqual(
            scifact["license_url"],
            "https://github.com/allenai/scifact/blob/"
            "a5254a1bf108726a1704d8e191b8a7f2225a029f/LICENSE.md",
        )

    def test_independent_web_contexts_share_audit_lock(self) -> None:
        source = (VERIFICATION / "web_app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        context_nodes = [
            node
            for node in tree.body
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "web_runtime"
            )
            or (
                isinstance(node, ast.FunctionDef)
                and node.name == "run_public_audit"
            )
        ]
        self.assertEqual(len(context_nodes), 2)
        self.assertNotIn("_AUDIT_LOCK =", source)

        state = {"active": 0, "maximum": 0}
        state_lock = threading.Lock()

        def fake_audit(cache_root: str) -> dict[str, object]:
            with state_lock:
                state["active"] += 1
                state["maximum"] = max(state["maximum"], state["active"])
            time.sleep(0.05)
            with state_lock:
                state["active"] -= 1
            return {"cache_root": cache_root}

        first_context: dict[str, object] = {
            "_run_public_audit_locked": fake_audit,
        }
        second_context: dict[str, object] = {
            "_run_public_audit_locked": fake_audit,
        }
        compiled = compile(
            ast.Module(body=context_nodes, type_ignores=[]),
            "verification/web_app.py",
            "exec",
        )
        exec(compiled, first_context)
        exec(compiled, second_context)

        self.assertIs(first_context["AUDIT_LOCK"], second_context["AUDIT_LOCK"])
        first_audit = first_context["run_public_audit"]
        second_audit = second_context["run_public_audit"]

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(first_audit, "shared")
            time.sleep(0.01)
            second = executor.submit(second_audit, "shared")
            observed = [first.result(), second.result()]

        self.assertEqual(state["maximum"], 1)
        self.assertEqual(observed, [{"cache_root": "shared"}] * 2)

    def test_concurrent_downloads_use_private_part_files(self) -> None:
        payload = b"complete immutable bundle"

        class SlowResponse(io.BytesIO):
            def read(self, size: int = -1) -> bytes:
                time.sleep(0.01)
                return super().read(size)

        # Keep this inside the checkout so restricted Windows sandboxes permit
        # the same-directory atomic publish used by the downloader.
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            destination = Path(directory) / "bundle.zip"
            with patch.object(
                quickstart.urllib.request,
                "urlopen",
                side_effect=lambda _url: SlowResponse(payload),
            ):
                with ThreadPoolExecutor(max_workers=2) as executor:
                    list(
                        executor.map(
                            lambda _index: quickstart.download(
                                "https://example.invalid/bundle.zip",
                                destination,
                            ),
                            range(2),
                        )
                    )

            self.assertEqual(destination.read_bytes(), payload)
            self.assertEqual(list(Path(directory).glob("*.part")), [])

    def test_private_authoring_material_is_absent(self) -> None:
        forbidden = [
            "daily-log.md",
            "claim-evidence.md",
            "artifact-inventory.md",
            "paper",
            "literature",
            "verification/usability-results",
        ]
        for relative in forbidden:
            with self.subTest(path=relative):
                self.assertFalse((ROOT / relative).exists())


class StageCategoryContractTests(unittest.TestCase):
    def evaluate_with(
        self,
        bm25: dict[str, list[tuple[int, str]]],
        reranked: dict[str, list[tuple[int, str]]],
        qrels: dict[str, set[str]],
    ) -> dict[str, object]:
        with (
            patch.object(stage_categories, "read_run", side_effect=[bm25, reranked]),
            patch.object(stage_categories, "positive_qrels", return_value=qrels),
        ):
            return stage_categories.evaluate("nfcorpus", Path("unused"))

    def test_missing_qrels_topic_invalidates_audit(self) -> None:
        with self.assertRaisesRegex(ValueError, "query population mismatch"):
            self.evaluate_with(
                {"1": [(1, "d1")]},
                {"1": [(1, "d1")]},
                {"1": {"d1"}, "2": {"d2"}},
            )

    def test_zero_positive_qrels_topic_invalidates_audit(self) -> None:
        with self.assertRaisesRegex(ValueError, "no positive judgment"):
            self.evaluate_with(
                {"1": [(1, "d1")]},
                {"1": [(1, "d1")]},
                {"1": set()},
            )

    def test_candidate_set_mismatch_invalidates_audit(self) -> None:
        with self.assertRaisesRegex(ValueError, "candidate set differs"):
            self.evaluate_with(
                {"1": [(1, "d1"), (2, "d2")]},
                {"1": [(1, "d1"), (2, "dx")]},
                {"1": {"d1"}},
            )

    def test_valid_partition_uses_qrels_population(self) -> None:
        result = self.evaluate_with(
            {"1": [(1, "d1")], "2": [(1, "d2")]},
            {"1": [(1, "d1")], "2": [(1, "d2")]},
            {"1": {"d1"}, "2": {"dx"}},
        )
        self.assertEqual(result["query_count"], 2)
        self.assertEqual(result["partition_sum"], 2)
        self.assertTrue(result["partition_covers_all_queries"])

    def test_run_parser_rejects_duplicate_documents(self) -> None:
        content = "1\tQ0\td1\t1\t1.0\ttest\n1\tQ0\td1\t2\t0.9\ttest\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.tsv"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate document"):
                stage_categories.read_run(path)

    def test_run_parser_rejects_non_contiguous_ranks(self) -> None:
        content = "1\tQ0\td1\t1\t1.0\ttest\n1\tQ0\td2\t3\t0.9\ttest\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.tsv"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-contiguous ranks"):
                stage_categories.read_run(path)

    def test_run_parser_rejects_wrong_depth(self) -> None:
        content = "1\tQ0\td1\t1\t1.0\ttest\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.tsv"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "has depth 1, expected 2"):
                stage_categories.read_run(path, expected_depth=2)

    def test_category_rejects_rank_beyond_declared_depth(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside 1--1000"):
            stage_categories.category(1001)


if __name__ == "__main__":
    unittest.main()
