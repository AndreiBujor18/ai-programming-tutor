# Curriculum alignment — v0.8.0 development

## Scope and privacy boundary

This map records only general first-semester C topics observed during a private,
local curriculum review. It contains no copied statement, solution, filename,
author, document property, or extracted passage. Every public exercise, test, hint,
translation, solution, and rubric item listed below was newly written for this
project.

## Topic-to-product map

| Abstract topic | Current coverage | Product treatment |
| --- | --- | --- |
| Console input, arithmetic, and conditions | `interval_parity` | Closed-interval reasoning and parity branching |
| Repetition and decimal-digit processing | `odd_digit_count` | Digit extraction, counter state, and zero as an edge case |
| Sentinel-controlled repetition | `sentinel_average`, `line_after_number` | Marker exclusion, stopping point, empty sequence, and input over-consumption |
| Loop bounds and generated sequences | `perfect_squares` | Inclusive upper bound and explicit no-result output |
| One-dimensional arrays | average, min/max, frequency, insertion, deletion | Bounds, indices, shifts, size updates, and accumulators |
| Character arrays and strings | palindrome, number-plus-line input | Symmetric indices, length, token versus line input |
| Matrices | diagonal average, matrix menu | Rectangular dimensions, diagonal positions, row operations |
| Functions, parameters, and menus | vector menu, matrix menu | Contracts, pointer output, dispatch, and valid program state |
| Basic file processing | runner foundation ready; exercise deferred | Strict project-authored text fixtures and expected files now run in a fresh directory per test; the first browser exercise and its presentation remain the next slice |

The four v0.6.0 additions intentionally strengthened foundations before file-aware
tests. The v0.8.0 development runner now supplies that infrastructure without yet
claiming browser-level file-exercise acceptance. Greedy, backtracking, dynamic
allocation, records, and recursion remain future curriculum layers rather than
being squeezed into the first diagnostic benchmark.

## Compatibility layer

Older teaching environments may accept patterns that portable C17 rejects or
discourages. The tutor currently recognizes five families: unbounded `gets`,
undefined `fflush(stdin)`, selected console-only helpers, non-standard case
conversion helpers, and checking `feof` before a read. It explains the portability
issue, preserves the learner's source, and keeps compiler diagnostics visible.

This is deliberately separate from bug classification: a platform-specific call
may be acceptable in a particular laboratory while still deserving a portability
warning.
