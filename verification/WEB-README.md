# Browser Interface

The Streamlit interface runs the same public-input category audit as the
command-line quick start. It is intended for people who do not use Python or a
terminal. It is a technical access path, not a participant test.

## Local preview

From the repository root:

```powershell
python -m venv .venv-web
.\.venv-web\Scripts\python.exe -m pip install -r verification\requirements.txt
.\.venv-web\Scripts\python.exe -m streamlit run verification\web_app.py
```

On Linux or macOS, use `.venv-web/bin/python` in place of the Windows Python
path.

The first audit downloads the pinned run bundle and public qrels into a
temporary cache. Later sessions may reuse those immutable inputs, but each
session reruns extraction, qrels loading, fail-closed category evaluation,
input fingerprinting, and all 623 query assignments. The displayed partition,
follow-up table, and JSON/CSV downloads are produced from that in-memory
calculation; the retained `query-audit-records.*` files are not read by the
application. Set `ECIR_WEB_CACHE` to a new directory to force an empty-cache
run.

The deployment serializes complete audit runs within the application process.
The lock lives in the ordinary imported module `web_runtime.py`, so independent
Streamlit script contexts share it even though the entry script is re-executed
for each session. This protects the shared download, extraction directory, and
`ir_datasets` cache from concurrent writes; a later request waits rather than
reading a partially replaced run file. A production check must still exercise
concurrent requests against the deployed commit.

## Data boundary

- The page has no free-text response, device, assistance, name, email,
  credential, or account-identifier fields.
- The downloads contain public bundle metadata, freshly computed query-level
  output, source-license metadata, and, in the complete JSON, the runtime-loaded
  SciFact query and document excerpt shown on the page. They contain no user
  response or session timestamp.
- The hosting provider may retain ordinary service logs under its own policy;
  the application itself does not create a participant record.
- No participant-derived record or outcome is distributed in this repository.

## Deployment

The deployment entry point is `verification/web_app.py`, with dependencies in
`verification/requirements.txt`.

The response-free interface is deployed at
<https://stage-aware-retrieval-audit.streamlit.app/>. An author-run production
check against release commit `fbc5e7f54512a448089c72391c89b84b15726e8d`
completed successfully on 21 October 2026. The check and its evidence limits
are recorded in `docs/TECHNICAL_ACCESS_VERIFICATION.md`.

That check covers the earlier deployed interface only. The fail-closed
preconditions, 623-row display/export path, and depth-recoverable download in
the current working candidate require a new public commit, deployment, and
production check before they can support manuscript claims.

The earlier pilot URL serves a legacy interface and is intentionally not
advertised by this release candidate.
