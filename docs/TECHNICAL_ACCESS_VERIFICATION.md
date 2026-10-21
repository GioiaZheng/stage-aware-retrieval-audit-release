# Hosted Access: Author-Run Technical Verification

This note records only author-run deployment checks. It contains no participant
data, returned response text, participant-derived count, outcome classification,
or sender mapping.

The Streamlit interface invokes the same frozen verification workflow as the
command-line entry point. It downloads the pinned public inputs, verifies the
archive digest, recomputes the NFCorpus and SciFact partitions, checks reranked
candidate-set equality, displays the fixed SciFact query trace, and exports a
versioned result record.

## Production checks

On 21 October 2026, an author-run browser session opened
<https://stage-aware-retrieval-audit.streamlit.app/> without authentication and
executed the response-free application deployed from release commit
`fbc5e7f54512a448089c72391c89b84b15726e8d`. The deployment used Python
3.12.15, `streamlit==1.65.0`, and `ir_datasets==0.6.1`. The fresh session
confirmed:

- unauthenticated access to the deployed page;
- a matching bundle SHA-256 digest;
- NFCorpus counts of 218/33/24/48;
- SciFact counts of 239/26/24/11;
- zero reranked candidate-set mismatches;
- the fixed SciFact query-13 trace with first relevant rank 170; and
- internally consistent application and result-version metadata; and
- availability of the machine-readable verification-result download.

The verified bundle digest was
`15e8e4ded1fe8d889e24a31f7794988ce0bbb6750c5f9b10e1d7dd4b38a5f633`.
These checks establish point-in-time reachability and output consistency only.
They do not guarantee future service availability, replace the clean
command-line repeatability check, or establish usability or accessibility
compliance.

## Evidence boundary

Development-stage external records and feedback are outside the ECIR manuscript
and public artifact. They are not counted, quoted, classified, aggregated, or
used to support any claim here. Any retained private material remains subject to
institutional guidance on ethics, storage, retention, and withdrawal.

The production check above establishes that the response-free `web-audit-v1`
source was online and produced the stated result at the recorded time. It does
not turn the browser session into participant evidence or establish continuous
availability.
