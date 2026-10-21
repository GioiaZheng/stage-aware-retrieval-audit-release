from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION = ROOT / "verification"
sys.path.insert(0, str(VERIFICATION))

from run_usability_quickstart import BUNDLE_SHA256, BUNDLE_URL  # noqa: E402


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
            'APP_VERSION = "web-audit-v1"',
            '"schema": "ecir-web-audit-result.v1"',
            '"schema": "ecir-web-audit-export.v1"',
            '"Download verification result"',
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
        self.assertEqual(exported["schema"], "ecir-web-audit-export.v1")
        self.assertEqual(exported["result"], {"schema": "test-result"})
        scifact = exported["third_party"]["scifact"]
        self.assertEqual(scifact["claims_and_evidence_license"], "CC BY 4.0")
        self.assertEqual(scifact["corpus_abstracts_license"], "ODC-By 1.0")
        self.assertEqual(
            scifact["license_url"],
            "https://github.com/allenai/scifact/blob/"
            "a5254a1bf108726a1704d8e191b8a7f2225a029f/LICENSE.md",
        )

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


if __name__ == "__main__":
    unittest.main()
