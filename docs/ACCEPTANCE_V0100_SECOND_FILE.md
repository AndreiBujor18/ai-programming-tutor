# v0.10.0 second file-family manual acceptance

Date: 2026-09-21

This record covers the focused local Windows acceptance pass for the second
independent fixed-file exercise in v0.10.0. It contains only public-safe outcomes.
No learner source, screenshot, browser-storage dump, private material, identity, or
local path is included.

## Scope

The accepted release adds `file_longest_word`, an original bounded-string exercise
that reads `words.txt` and creates `longest.txt`. The required result is the first
word of maximum length followed by that length. Two public and three hidden cases
cover mixed lengths, one word, an equal-length tie, a final maximum, and the
100-character input boundary.

The exercise uses the existing project-authored file contract, trusted-local runner,
relational-operator diagnosis, progressive-hint system, complete-solution styles,
and source-free progress schema. It adds no upload surface or public execution
claim, and it does not change the frozen 14-exercise diagnostic benchmark.

## Automated prerequisite

The release tree passed 71/71 automated tests before final manual acceptance. The
sixteenth authored reference and all four generated solution styles pass all five
file cases. Regressions also cover the bilingual contract, hidden redaction,
first-on-tie diagnosis, catalog and progress metadata, wheel contents, and the
existing runner, editor, privacy, and browser behavior.

## Manual protocol and outcome

The local Windows browser workflow passed all of the following checks:

1. The Romanian exercise card displayed the correct `words.txt` input and
   `longest.txt` result contract, both public examples, and a 16-exercise catalog.
2. The intentionally incomplete starter compiled and failed all five cases. Public
   results named only `longest.txt`, while hidden cases used generic file labels and
   disclosed no fixture name, result name, or content.
3. The complete verified solution passed both public and all three hidden cases,
   producing a 5/5 result.
4. Replacing the strict longest-word comparison with an equal-inclusive comparison
   produced 4/5: only the hidden first-on-tie case failed. The tutor selected the
   existing relational-operator category and revealed three increasingly specific
   hints without exposing the hidden data or complete answer.
5. Switching to English without refreshing or rerunning preserved the edited source
   and 4/5 result, translated the exercise, diagnosis, and hints, and kept hidden
   file details redacted.
6. Restoring the strict comparison produced 5/5. With numeric history explicitly
   enabled, Progress showed one fully solved exercise and one bounded attempt, a
   best result of 5/5, Files coverage of 1/2, and Strings and input coverage of 1/3.

## Accepted privacy and evaluation boundary

- Public authored fixtures and expected files are visible; hidden names and contents
  remain redacted in both locales.
- Numeric attempt history stores the timestamp, compilation state, and test count,
  never learner source, diagnostics, hints, fixture contents, or profile traits.
- The exercise accepts only repository-authored fixtures. There is no arbitrary file
  upload, network execution, or production-sandbox claim.
- Both file exercises remain outside generator 0.3.0. A new label or metric claim
  requires a separate reviewed mutation set and versioned held-out evaluation.

## Result

The complete v0.10.0 second-file-family workflow is manually accepted in Romanian
and English: contracts, redaction, success and failure feedback, diagnosis, all
three hints, state continuity, and source-free progress behave as intended.
