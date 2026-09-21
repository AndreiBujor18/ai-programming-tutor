# Experiment 004 — fixed-file family benchmark review

## Question

Can the two independent fixed-file exercises enter the controlled benchmark using
the existing semantic taxonomy, and does the proposed `file_cursor_state` concept
justify a separate fourteenth label?

## Category decision

The proposed label was not admitted. The review applied the same causal-label rule
used by the earlier taxonomy:

- reading too few or too many counted records after the initial read is a
  `loop_boundary` error;
- passing the output stream to a read call is a
  `wrong_identifier_or_argument` error;
- numeric initialization, accumulation, comparison, and update mistakes retain
  their existing categories;
- longest-word initialization, strict tie comparison, and coordinated state updates
  also retain their existing categories.

Both exercises can instantiate the candidate surface pattern, but it has no
non-overlapping misconception or unique hint goal. Splitting it by FILE* context
would inflate the taxonomy without adding explanatory value. `C-SEED-007` now
records this rejected-category decision.

## Dataset and audit

- generator 0.4.0 with unchanged dataset schema 0.3;
- 16 project-authored exercises and 13 semantic labels;
- 82 reviewed exercise/mutation pairs: the previous 71 plus five string-file and
  six numeric-file pairs;
- 16 identifier/layout variants per pair, for 1,312 controlled programs;
- GCC execution and test signals recorded for every row;
- 1,312/1,312 unique IDs, 1,312/1,312 successful compilations, and 1,312/1,312
  mutations failing at least one authored test;
- the intended category appears in the rule layer's top three for all 1,312 rows;
- leave-one-exercise-out evaluation, including separate held-out folds for each file
  family.

All rows remain controlled mutations of project-authored C17 references. No learner
submission, private source text, or copied course exercise is included.

## Overall results

| Track | Accuracy | Macro-F1 | Top-3 recall |
| --- | ---: | ---: | ---: |
| ML only | 0.7675 | 0.6473 | 0.8704 |
| Rules only | 1.0000 | 1.0000 | 1.0000 |
| Hybrid | 0.9665 | 0.9524 | 1.0000 |

The expanded benchmark is not directly interchangeable with Experiment 003 because
it adds two held-out groups and 176 programs. Relative to that earlier run, ML-only
macro-F1 changes from 0.6375 to 0.6473 while top-3 recall changes from 0.8750 to
0.8704. Hybrid macro-F1 changes from 0.9610 to 0.9524 and retains 1.0000 top-3
recall. These small movements should be read as behavior on a broader controlled
set, not as a longitudinal student-performance claim.

## Held-out file-family results

| Held-out exercise | Programs | ML accuracy | ML macro-F1 | ML top-3 | Hybrid macro-F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `file_longest_word` | 80 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `file_number_summary` | 96 | 0.8333 | 0.7667 | 0.8333 | 1.0000 |

The model sees no variant of the held-out exercise during its fold. The two file
folds therefore show controlled cross-exercise transfer for existing labels, with a
clearer result on string selection than numeric aggregation. They do not validate
performance on naturally written file-processing submissions.

## Interpretation

The review supports including both file families without changing the taxonomy.
The rule layer recognizes every authored mutation, and the hybrid preserves perfect
top-three recall, but rule-only perfection is partly a construction property because
the mutations and rules were reviewed together. The honest ML-only macro-F1 remains
0.6473, below the 0.75 product target, and `sentinel_handling` remains at 0.0 ML-only
F1.

The next evaluation priority is a small consented, de-identified, frozen natural-code
set with independent labeling. A new file-specific category should be reconsidered
only if that evidence contains a recurring causal misconception that cannot be
explained by the existing 13 labels.
