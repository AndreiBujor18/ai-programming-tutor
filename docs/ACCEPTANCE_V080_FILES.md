# v0.8.0 file-workflow manual acceptance

Date: 2026-09-20

This record covers the focused local Windows acceptance pass for the v0.8.0 file
workflow. It contains only public-safe results. No learner source, screenshot,
local path, private material, identity, or browser-storage dump is included.

## Scope

The accepted release adds bounded project-authored text fixtures and expected
output files, a fresh disposable directory for every test, and the original
`file_number_summary` exercise. The browser renders public file contracts and
per-file results in Romanian and English while keeping hidden file names and
contents private. Arbitrary learner uploads remain outside the product.

## Automated prerequisite

The release tree passed 68/68 automated tests before final manual acceptance. The
suite covers strict schema parsing, portable names and byte bounds, isolated test
directories, structured result statuses, hidden serialization, all reference and
generated solution styles, bilingual browser rendering, and Files progress.

## Manual protocol and outcome

The local Windows browser workflow passed all of the following checks:

1. The catalog contained 15 exercises and exposed the new file exercise in Romanian.
2. Both public examples displayed `numbers.txt` fixture contents and the expected
   `summary.txt` contents without empty standard-input or standard-output blocks.
3. The untouched starter compiled and failed all five tests because its result file
   was empty. Public cases identified `summary.txt`; hidden cases used only generic
   hidden-file labels and revealed no file name or content.
4. The separately requested Profile A reference compiled and passed all five public
   and hidden cases. Every nested result-file status was successful.
5. Switching to English without a refresh translated the exercise, public contracts,
   result headings, statuses, and hidden-file labels while retaining the edited
   source and the visible 5/5 result.
6. With numeric history enabled, the derived Files group reported one attempted and
   one fully solved exercise. The tracked-exercise row retained its 5/5 best result
   and numeric attempt count.
7. Switching to Profile B showed its untouched starter and empty progress rather
   than Profile A's saved reference or results. Returning to Profile A restored its
   saved source and file-related progress.
8. The complete workflow used only the fixed `numbers.txt` to `summary.txt` contract.
   No browser upload control or arbitrary filename surface was present.

## Accepted privacy and execution boundary

- Fixtures and expectations are authored, versioned project data.
- Hidden test names, file names, expected text, actual text, and stderr remain
  redacted from normal learner-facing responses.
- Optional drafts and numeric progress stay device-local and profile-specific.
- Numeric progress stores no submitted source or file contents.
- The runner remains restricted to trusted localhost development and testing.
- Arbitrary uploads and public execution remain explicit non-goals.

## Result

The complete v0.8.0 file workflow is manually accepted: public contracts, failed
and successful file results, hidden redaction, bilingual continuity, profile/draft
isolation, and Files progress all behave as intended.
