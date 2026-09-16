# Experiment 003 — expanded curriculum baseline

## Question

Does the existing diagnostic architecture still transfer when four independently
authored foundation exercises and a thirteenth semantic label are added?

## Dataset and split

- 14 exercises, each with two public and three hidden tests;
- 13 single-bug labels;
- 71 exercise/mutation pairs × 16 identifier/layout variants = 1,136 programs;
- GCC execution and test signals recorded for every generated row;
- independent release audit: 1,136/1,136 compile, fail at least one test, have a
  unique ID, and surface the intended label in the rule layer's top three;
- leave-one-exercise-out evaluation, so no variant of the held-out exercise appears
  in that fold's training data.

All rows are controlled mutations of project-authored C17 references. The private
curriculum packet contributed only an abstract coverage decision and is not part of
the dataset.

## Results

| Track | Accuracy | Macro-F1 | Top-3 recall |
| --- | ---: | ---: | ---: |
| ML only | 0.7509 | 0.6375 | 0.8750 |
| Rules only | 1.0000 | 1.0000 | 1.0000 |
| Hybrid | 0.9718 | 0.9610 | 1.0000 |

The primary ML-only result is below the original 0.75 macro-F1 target. Its weakest
new class is `sentinel_handling` (0.0 F1), and transfer also remains weak for menu
dispatch and mixed-input patterns. The explicit rule layer recognizes all controlled
mutations, while the hybrid misses some top-1 cases in held-out interval and
number-plus-line exercises but keeps the correct category in its top three.

## Interpretation

The result supports the hybrid product architecture, but not a 0.9610 “AI model
accuracy” claim. Rules score perfectly partly because these mutations were designed
alongside those rules. The honest model result is 0.6375 macro-F1, and neither track
has yet been tested on a consented, naturally written student benchmark.

Next evaluation work should collect a small de-identified frozen set, add naturally
different correct structures, and investigate representations that distinguish
marker semantics without memorizing exercise text. Style-personalization and exam
scores remain separate product experiments and are not classifier metrics.
