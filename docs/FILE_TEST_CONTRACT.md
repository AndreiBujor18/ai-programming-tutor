# File test contract — v0.8.0

This contract is for project-authored exercise data. It does not accept browser
uploads and does not turn the trusted-local runner into a security sandbox.

## Test schema

Existing stdin/stdout tests remain valid without either new field. A file-aware
case may add `fixtures` and `expected_files`:

```json
{
  "name": "public-small-file",
  "input": "",
  "expected": "",
  "hidden": false,
  "fixtures": [
    {"name": "input.txt", "content": "2 3 5\n"}
  ],
  "expected_files": [
    {"name": "output.txt", "content": "10\n"}
  ]
}
```

Each entry has exactly `name` and `content`. Names are portable ASCII filenames,
not paths: no separators, leading dot, trailing dot, Windows device name, or
runner-reserved `program.stdout`/`program.stderr` name is accepted. Names are
checked case-insensitively for duplicates. A fixture may also be an expected output
when both entries use exactly the same spelling, which supports exercises that
modify an existing file.

One case may declare at most eight fixture and expected-file entries combined.
Each content value is UTF-8 text of at most 32,000 bytes; all declared fixture and
expected content together may use at most 64,000 bytes.

## Execution lifecycle

The source is compiled once in the evaluation root. Every test then receives a new
disposable child directory:

1. only that case's declared fixtures are written;
2. the executable runs with the child directory as its current and temporary
   directory;
3. stdout and stderr are captured under reserved names;
4. each declared result is inspected through a bounded regular-file read;
5. the child directory is deleted before the next case starts.

On POSIX, the process group is terminated after the test leader exits so surviving
descendants cannot continue writing. Windows does not yet have an equivalent job
object in this prototype; file tests there remain trusted-local only.

## Comparison and result statuses

Stdout and every expected file must pass for the case to pass. Text comparison uses
the runner's existing whitespace-normalized behavior. Each file result contains its
name, expected text, bounded actual text, and one of these statuses:

| Status | Meaning |
| --- | --- |
| `passed` | A bounded UTF-8 regular file matched the authored expectation |
| `wrong_answer` | The file was safe to read but its normalized text differed |
| `missing` | The declared result was not created |
| `unreadable` | The result could not be opened or read |
| `invalid_type` | The path was not a regular file or changed during inspection |
| `invalid_encoding` | The result was not valid UTF-8 text |
| `output_limit` | The result exceeded the runner's output cap |

Symbolic links are non-regular and are never followed as expected outputs. Hidden
tests keep only public-safe status information: their case name, file names,
expected contents, actual contents, and stderr are redacted from normal responses.

## Acceptance boundary

The automated contract covers strict parsing, name/count/byte limits, public versus
hidden serialization, test-suite fingerprints, fresh workspaces, matching and
missing files, oversized and invalid-UTF-8 output, and POSIX symbolic-link rejection.
The `file_number_summary` catalog exercise exercises the contract with two public
and three hidden cases. Browser regressions cover bilingual public fixture and
expected-file rendering, nested result-file statuses, and generic hidden-file
labels. The focused Windows browser protocol also passed in both locales with
profile-specific draft/progress continuity; see `docs/ACCEPTANCE_V080_FILES.md`.
Arbitrary uploads and public execution remain outside this boundary.
