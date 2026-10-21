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
session reruns extraction, qrels loading, category evaluation, and fixed-query
assignment. Set `ECIR_WEB_CACHE` to a new directory to force an empty-cache
run.

## Data boundary

- The page has no free-text response, device, assistance, name, email,
  credential, or account-identifier fields.
- The optional JSON download contains public bundle metadata, computed output,
  source-license metadata, and the runtime-loaded SciFact query and document
  excerpt shown on the page. It contains no user response or session timestamp.
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

The earlier pilot URL serves a legacy interface and is intentionally not
advertised by this release candidate.
