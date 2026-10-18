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

Fresh author-run browser sessions after material interface revisions confirmed:

- unauthenticated access to the deployed page;
- a matching bundle SHA-256 digest;
- NFCorpus counts of 218/33/24/48;
- SciFact counts of 239/26/24/11;
- zero reranked candidate-set mismatches;
- the fixed SciFact query-13 trace with first relevant rank 170; and
- internally consistent application and result-version metadata.

On 18 October 2026, a new unauthenticated session also reached the public entry
page successfully. These checks establish point-in-time reachability and output
consistency only. They do not guarantee future service availability, replace the
clean command-line repeatability check, or establish usability or accessibility
compliance.

## Evidence boundary

Development-stage external records and feedback are outside the ECIR manuscript
and public artifact. They are not counted, quoted, classified, aggregated, or
used to support any claim here. Any retained private material remains subject to
institutional guidance on ethics, storage, retention, and withdrawal.

The production checks above describe earlier deployed revisions. They do not
establish that the current response-free `web-audit-v1` source is online. That
source requires an approved deployment followed by a new author-run production
check before a hosted URL can support the release claim.
