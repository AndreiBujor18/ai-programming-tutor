# Generated data

Run `aptutor generate-data` to create `synthetic_bugs.jsonl`. Generated datasets
are reproducible and intentionally excluded from version control.

Generator 0.3.0 creates 1,136 rows by default: 71 reviewed single-mutation pairs
across 14 exercises, each rendered in 16 identifier/layout variants. The generated
release dataset contains project-authored code only.

`case_seeds.json` contains public-safe, abstract provenance metadata. It does not
contain source conversations, course files, personal identifiers, or copied student
code. See `docs/DATA_PROVENANCE.md`.
