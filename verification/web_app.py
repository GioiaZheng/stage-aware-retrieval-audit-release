"""Streamlit interface for the stage-aware retrieval audit."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import streamlit as st

from run_usability_quickstart import (
    BUNDLE_SHA256,
    BUNDLE_URL,
    download,
    safe_extract,
    sha256,
)
from web_runtime import AUDIT_LOCK


APP_VERSION = "web-audit-v2"
FIXED_QUERY = "scifact:13"
DOCUMENT_EXCERPT_LENGTH = 600
SCIFACT_LICENSE_URL = (
    "https://github.com/allenai/scifact/blob/"
    "a5254a1bf108726a1704d8e191b8a7f2225a029f/LICENSE.md"
)


def fixed_query_context(dataset_id: str, qid: str) -> dict[str, object]:
    """Load the public query and judged-relevant document shown in the UI."""
    import ir_datasets

    dataset = ir_datasets.load(dataset_id)
    query = next(
        (item for item in dataset.queries_iter() if str(item.query_id) == qid),
        None,
    )
    if query is None:
        raise ValueError(f"{dataset_id}: query {qid} is missing")

    relevant_doc_ids = [
        str(qrel.doc_id)
        for qrel in dataset.qrels_iter()
        if str(qrel.query_id) == qid and qrel.relevance >= 1
    ]
    if not relevant_doc_ids:
        raise ValueError(f"{dataset_id}: query {qid} has no positive qrel")

    doc_id = relevant_doc_ids[0]
    document = dataset.docs_store().get(doc_id)
    if document is None:
        raise ValueError(f"{dataset_id}: relevant document {doc_id} is missing")
    text = " ".join(str(getattr(document, "text", "")).split())
    excerpt = text[:DOCUMENT_EXCERPT_LENGTH]
    if len(text) > DOCUMENT_EXCERPT_LENGTH:
        excerpt += "…"

    return {
        "query_id": qid,
        "query_text": str(getattr(query, "text", "")),
        "relevant_document": {
            "doc_id": doc_id,
            "title": str(getattr(document, "title", "")),
            "text_excerpt": excerpt,
            "judgment": "relevant",
        },
    }


def run_public_audit(cache_root: str) -> dict[str, object]:
    """Serialize access to the shared download, extraction, and dataset cache."""
    with AUDIT_LOCK:
        return _run_public_audit_locked(cache_root)


def _run_public_audit_locked(cache_root: str) -> dict[str, object]:
    """Download public inputs as needed and recompute one complete audit."""
    root = Path(cache_root)
    archive = root / "downloads" / "beir-cross-domain-baselines-v1.zip"
    extracted = root / "extracted"
    dataset_cache = root / "ir_datasets_cache"

    if not archive.exists():
        download(BUNDLE_URL, archive)
    observed_hash = sha256(archive)
    if observed_hash != BUNDLE_SHA256:
        raise ValueError(
            f"Bundle SHA-256 mismatch: expected {BUNDLE_SHA256}, "
            f"observed {observed_hash}"
        )

    safe_extract(archive, extracted)
    os.environ["IR_DATASETS_HOME"] = str(dataset_cache)

    from export_query_audit import build_payload
    from recompute_stage_categories import DATASETS

    dataset_name, qid = FIXED_QUERY.split(":", 1)
    run_dir = extracted / "runs"
    query_audit = build_payload(run_dir)
    analysis = [dataset["aggregate"] for dataset in query_audit["datasets"]]
    context = fixed_query_context(str(DATASETS[dataset_name]["dataset_id"]), qid)
    return {
        "schema": "ecir-web-audit-result.v2",
        "app_version": APP_VERSION,
        "bundle": {
            "url": BUNDLE_URL,
            "sha256": observed_hash,
            "sha256_matches": True,
        },
        "analysis": analysis,
        "query_audit": query_audit,
        "fixed_query_context": context,
    }


def category_rows(result: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for dataset in result["analysis"]:  # type: ignore[index]
        categories = dataset["categories"]
        rows.append(
            {
                "Dataset": dataset["dataset"],
                "Rank 1–10": categories["reachable_top10"],
                "Rank 11–100": categories["reranker_reachable_11_100"],
                "Rank 101–1000": categories["depth_recoverable_101_1000"],
                "No hit ≤1000": categories["residual_miss_top1000"],
                "Candidate mismatches": dataset[
                    "reranked_candidate_set_mismatches"
                ],
            }
        )
    return rows


def requested_query(result: dict[str, object]) -> dict[str, object]:
    dataset_name, qid = FIXED_QUERY.split(":", 1)
    query_audit = result["query_audit"]  # type: ignore[index]
    for dataset in query_audit["datasets"]:
        if dataset["dataset"] != dataset_name:
            continue
        for record in dataset["records"]:
            if record["query_id"] == qid:
                return record
    raise ValueError("Fixed query result is missing")


def build_export(result: dict[str, object]) -> bytes:
    """Serialize public verification output without collecting user data."""
    export = {
        "schema": "ecir-web-audit-export.v2",
        "app_version": APP_VERSION,
        "third_party": {
            "scifact": {
                "access_path": "loaded at runtime through ir_datasets",
                "claims_and_evidence_license": "CC BY 4.0",
                "corpus_abstracts_license": "ODC-By 1.0",
                "license_url": SCIFACT_LICENSE_URL,
            }
        },
        "result": result,
    }
    return (json.dumps(export, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


st.set_page_config(
    page_title="Stage-Aware Retrieval Audit",
    page_icon="🔎",
    layout="centered",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 860px; padding-top: 3rem; padding-bottom: 4rem;}
    h1 {letter-spacing: -0.035em;}
    [data-testid="stMetricValue"] {font-size: 1.6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Stage-Aware Retrieval Audit")
st.caption("Hosted technical verification of a fixed two-stage retrieval case")

st.info(
    "**Purpose:** reproduce the released audit from pinned public inputs and "
    "show one candidate-set limitation: a second-stage reranker cannot use a "
    "document that the first stage placed outside its top-100 candidate set. "
    "This is a technical demonstration, not a participant study."
)

st.markdown(
    """
    **What you can do**

    1. Click **Run public audit**. The page will download public result files,
       check that they are unchanged, and calculate the result.
    2. Read the displayed query, judged-relevant document, and rank information.
    3. Inspect or download records produced by that same computation.

    The page does not ask for responses, a name, contact details, device details,
    or an account identifier, and it does not ask you to send anything back.
    """
)

st.write(
    "The computation uses a frozen public ranked-run bundle and public "
    "relevance judgments. No command line or local installation is required."
)

with st.expander("What the four categories mean", expanded=False):
    st.markdown(
        """
        - **Rank 1–10:** judged-relevant evidence is already near the top.
        - **Rank 11–100:** judged-relevant evidence is inside the reranker's candidate set.
        - **Rank 101–1000:** deeper retrieval finds evidence that top-100 reranking cannot reach.
        - **No hit ≤1000:** the released lexical run finds no judged-relevant document by depth 1000.

        These are operational locations in a fixed pipeline, not semantic root causes.
        """
    )

with st.expander("Plain-language guide and cutoff example", expanded=True):
    st.markdown(
        """
        - A **relevance judgment** is a benchmark label saying that a document
          is relevant to a query.
        - The **candidate set** is the first 100 documents passed to the
          reranker.
        - A **reranker** can reorder those 100 candidates, but it cannot add a
          document that was left outside the set.
        - The **top-100 cutoff** is therefore a boundary: documents at ranks
          101–1000 exist in deeper retrieval, but the reranker never sees them.

        **Small example:** retrieval returns five documents, but a reranker is
        allowed to see only the first three. If the relevant document is fourth,
        the reranker cannot move it upward because it is outside its candidate
        set. Searching more deeply can still reveal that document.
        """
    )

if st.button("Run public audit", type="primary"):
    cache_root = os.environ.get(
        "ECIR_WEB_CACHE",
        str(Path(tempfile.gettempdir()) / "ecir-stage-audit-web"),
    )
    try:
        st.session_state.pop("audit_error", None)
        with st.status("Running the public audit…", expanded=True) as status:
            st.write("Downloading and verifying the frozen run bundle")
            st.write("Loading public NFCorpus and SciFact relevance judgments")
            st.write("Recomputing all 623 query assignments and input fingerprints")
            st.session_state.audit_result = run_public_audit(cache_root)
            status.update(label="Audit complete", state="complete", expanded=False)
    except Exception as error:  # Surface a useful technical error in the UI.
        st.session_state.pop("audit_result", None)
        st.session_state.audit_error = f"{type(error).__name__}: {error}"

if "audit_error" in st.session_state:
    st.error(st.session_state.audit_error)
    st.info(
        "No result was exported. You can retry later or use the documented "
        "command-line quick start."
    )

if "audit_result" in st.session_state:
    result = st.session_state.audit_result
    st.divider()
    st.subheader("Verification result")

    bundle = result["bundle"]
    left, right = st.columns(2)
    left.metric("Bundle checksum", "PASS" if bundle["sha256_matches"] else "FAIL")
    right.metric("Datasets audited", len(result["analysis"]))
    st.code(bundle["sha256"], language=None)

    st.markdown("#### Query partition")
    st.table(category_rows(result))

    from export_query_audit import (
        records_for_category,
        render_csv,
        render_record_selection_csv,
    )

    query_audit = result["query_audit"]
    depth_records = records_for_category(
        query_audit, "depth_recoverable_101_1000"
    )
    st.markdown("#### Depth-recoverable follow-up list")
    st.write(
        f"The current computation found {len(depth_records)} queries whose "
        "first judged-relevant document occurs at ranks 101–1000. The table "
        "identifies the query, document, and rank for candidate-depth review."
    )
    st.dataframe(
        [
            {
                "Dataset": row["dataset"],
                "Query ID": row["query_id"],
                "First relevant document": row["first_relevant_doc_id"],
                "BM25 rank": row["first_relevant_rank"],
            }
            for row in depth_records
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.download_button(
        "Download all 623 query records (CSV)",
        data=render_csv(query_audit).encode("utf-8"),
        file_name="query-audit-records.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download depth-recoverable follow-up list (CSV)",
        data=render_record_selection_csv(depth_records).encode("utf-8"),
        file_name="depth-recoverable-queries.csv",
        mime="text/csv",
    )

    query = requested_query(result)
    context = result["fixed_query_context"]
    document = context["relevant_document"]
    st.markdown("#### Worked query case")
    st.markdown("**Query text**")
    st.success(context["query_text"])
    st.markdown("**Benchmark-judged relevant document**")
    st.write(f"Document ID: `{document['doc_id']}`")
    st.write(f"Title: {document['title']}")
    st.caption(f"Document excerpt: {document['text_excerpt']}")
    st.caption(
        "Source: SciFact via ir_datasets. Claims and evidence annotations are "
        "licensed under CC BY 4.0; corpus abstracts are licensed under "
        f"ODC-By 1.0. [SciFact license]({SCIFACT_LICENSE_URL})"
    )

    q1, q2, q3 = st.columns(3)
    q1.metric("BM25 rank", query["first_relevant_rank"])
    q2.metric("Reranker cutoff", "100")
    q3.metric("Inside candidate set", "NO")
    st.code(query["category"], language=None)

    st.info(
        "The benchmark already labels this document as relevant; you are not "
        "being asked to judge that label. The first-stage run places it at rank "
        "170. Because the reranker receives only ranks 1–100, this document is "
        "not available to the reranker. Deeper retrieval up to rank 1000 does "
        "recover it."
    )

    export = build_export(result)
    st.download_button(
        "Download complete verification result (JSON)",
        data=export,
        file_name="ecir-web-audit-result.json",
        mime="application/json",
    )
    st.caption(
        "The file contains public bundle metadata, computed output, and the "
        "runtime-loaded SciFact query and document excerpt shown above. It "
        "contains no user-supplied response, device or account details, or "
        "session timestamp."
    )
