# Generated data

Run `aptutor generate-data` to create `synthetic_bugs.jsonl`. Generated datasets
are reproducible and intentionally excluded from version control.

Generator 0.4.0 creates 1,312 rows by default: 82 reviewed single-mutation pairs
across all 16 exercises, each rendered in 16 identifier/layout variants. The
generated dataset contains project-authored code only.

The review adds five pairs for `file_longest_word` and six for
`file_number_summary`, all using the existing semantic taxonomy. The proposed
`file_cursor_state` label was not admitted: counted over/under-reading overlaps
`loop_boundary`, and selecting the wrong stream overlaps
`wrong_identifier_or_argument`. This decision avoids splitting the same causal
mistake by API context.

`case_seeds.json` contains public-safe, abstract provenance metadata. It does not
contain source conversations, course files, personal identifiers, or copied student
code. See `docs/DATA_PROVENANCE.md`.
