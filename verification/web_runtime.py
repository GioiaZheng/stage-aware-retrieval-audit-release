"""Process-shared runtime state for independently rerun Streamlit sessions."""

from __future__ import annotations

import threading


# Streamlit re-executes the entry script for each session, but normal imported
# modules remain cached once per Python process. Keeping the lock here makes it
# shared across those independent script contexts.
AUDIT_LOCK = threading.Lock()
