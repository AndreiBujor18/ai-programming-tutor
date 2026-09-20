# Generated data

Run `aptutor generate-data` to create `synthetic_bugs.jsonl`. Generated datasets
are reproducible and intentionally excluded from version control.

Generator 0.3.0 creates 1,136 rows by default: 71 reviewed single-mutation pairs
across 14 exercises, each rendered in 16 identifier/layout variants. The generated
release dataset contains project-authored code only.

The 15th and 16th catalog exercises, `file_longest_word` and
`file_number_summary`, are intentionally excluded from this frozen generator
version. A second family enables a useful review, but does not retroactively validate
a file-specific label; a future benchmark version must add reviewed mutations and
held-out evaluation before including either exercise.

`case_seeds.json` contains public-safe, abstract provenance metadata. It does not
contain source conversations, course files, personal identifiers, or copied student
code. See `docs/DATA_PROVENANCE.md`.
