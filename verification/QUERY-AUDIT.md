# Per-Query Audit Export

The fixed audit is exported as two semantically equivalent files:

- `query-audit-records.json` retains dataset-level input bindings, aggregates,
  and all query records;
- `query-audit-records.csv` provides the same 623 query records as a flat table.

The composite key is `(dataset, query_id)`, with `query_id` represented as a
string. Each record contains the first judged-relevant BM25 rank and document
identifier, the exclusive stage category, the number of positive qrels,
top-100 candidate availability, and the already-validated candidate-set result.
Rank and document identifier are both null or blank for a residual miss.

The JSON binds each dataset to the raw BM25 and reranked run SHA-256 values,
byte sizes, declared depths, the relevance threshold and candidate cutoff, and
an order-independent qrels fingerprint. For every qrel, `query_id` and
`document_id` are first converted to strings and relevance to a base-10
integer. The resulting tuples are sorted lexicographically by those three
fields. The canonical byte stream has no header or BOM, uses UTF-8,
tab-separated fields, and an LF after every row including the last. It also
records the `ir_datasets` version and qrels row count.

## Retained identifiers

| File | Rows | Bytes | SHA-256 |
|---|---:|---:|---|
| `query-audit-records.json` | 623 | 216,812 | `4da1cf5968d10853ed2376fb42aa98eb4307f1f798c91db39de49a7c5c4d4219` |
| `query-audit-records.csv` | 623 | 35,768 | `f8536f083801765f9b6e85e9ee5bcc7d00dc833e9cb5bfa857dceb511afb0986` |

The JSON contains 323 NFCorpus records with category counts 218, 33, 24, and
48, plus 300 SciFact records with counts 239, 26, 24, and 11. JSON and CSV were
regenerated twice and were byte-identical on 2026-10-21.

The software and original audit outputs in these two files are covered by the
repository's Apache-2.0 and CC BY 4.0 files, respectively. Dataset and document
identifiers and qrels-derived values remain subject to the source-resource
terms described in `THIRD_PARTY.md` and are not relicensed here.

## Regeneration

After preparing the verified BEIR run directory described in `QUICKSTART.md`:

```bash
python verification/export_query_audit.py \
  --run-dir audit-work/extracted/runs \
  --json-output verification/query-audit-records.json \
  --csv-output verification/query-audit-records.csv
```

The exporter calls the same fail-closed category evaluator used by the Quick
Start. It does not write an export if query populations, positive-qrel
preconditions, rank structure, declared depths, or candidate-set equality fail.
