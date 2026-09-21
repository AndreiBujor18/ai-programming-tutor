# Curriculum alignment — current tree

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
| Basic file processing | `file_number_summary`, `file_longest_word` | Open fixed text files safely, read counted numeric and string sequences, aggregate values or retain the first longest word, write result files, and close both streams; public contracts and file results are shown bilingually |

The four v0.6.0 additions intentionally strengthened foundations before file-aware
tests. The two later file exercises use that infrastructure and now provide distinct
numeric and string families. Generator 0.4.0 includes both through 11 reviewed
mutation pairs and a versioned held-out evaluation. The review retained the existing
13 categories because the candidate file-cursor cases overlap loop-boundary and
wrong-argument mistakes; catalog breadth alone is still not a real-student
classifier claim. Greedy,
backtracking, dynamic allocation, records, and recursion remain future curriculum
layers rather than being squeezed into the first diagnostic benchmark.

## Compatibility layer

Older teaching environments may accept patterns that portable C17 rejects or
discourages. The tutor currently recognizes five families: unbounded `gets`,
undefined `fflush(stdin)`, selected console-only helpers, non-standard case
conversion helpers, and checking `feof` before a read. It explains the portability
issue, preserves the learner's source, and keeps compiler diagnostics visible.

This is deliberately separate from bug classification: a platform-specific call
may be acceptable in a particular laboratory while still deserving a portability
warning.
