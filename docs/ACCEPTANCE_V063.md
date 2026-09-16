# v0.6.3 manual acceptance record

Status: **passed**

This document records the final local Windows acceptance pass for v0.6.3. It
contains no screenshots, local paths, learner identities, private source material,
or raw learner code.

## Scope

- release commit: `9a96b642c6d983c4659a275e346c3e6b5266f092`;
- local loopback web server with execution explicitly enabled;
- Romanian interface and dark theme;
- GCC-backed C17 execution;
- permanent draft saving disabled for the final privacy check.

## Result summary

| Test | Area | Result |
| --- | --- | --- |
| 1 | Catalog, exam start, task navigation, timer, score, and refresh | Passed |
| 2 | Correct/incorrect Windows execution, diagnosis, hints, solution, and best-attempt score | Passed |
| 3 | Romanian/English transitions, exact source, hint depth, feedback, and theme | Passed after the v0.6.2 fixes |
| 4 | Distinct Profile A, Profile B, and PCLP1 formatting on two exercises | Passed; every generated solution passed 5/5 tests |
| 5 | Source-free `fflush(stdin)` compatibility warning without source rewriting | Passed; the valid solution still passed 5/5 tests |
| 6 | Finished-exam time and source lifecycle across refresh and tab closure | Passed after the v0.6.3 fixes |

## Final regression verification

A fresh practice exam was finished with `59:50` remaining and an estimated score
of `3.00 / 10`. The second task retained its best result of 5/5 tests and 2.00
task points.

After a refresh in the same browser tab:

- the timer remained frozen at `59:50`;
- the score and best task result remained unchanged;
- the second task remained selected;
- the exact edited task source was restored for review.

After closing the tab and opening the application again:

- the frozen time, score, selected task, and numeric best result remained;
- the temporary exam source was gone and the authored starter was shown;
- no opt-in permanent draft had been created implicitly.

The retained style-profile summary is expected: it contains bounded aggregate
preferences rather than raw source, identifiers, or comment text.

## Conclusion

v0.6.3 satisfies the planned manual acceptance checks. It is the stable baseline
for the v0.7.0 local-learning-progress sprint.

## Hosted CI follow-up

The first public GitHub Actions matrix run did not contradict the local acceptance
result, but it did not complete. The baseline test passed; subsequent GCC-backed
runner checks repeatedly reached the four-second compilation timeout on the hosted
Ubuntu runner, and both matrix jobs were cancelled at their 15-minute job limit.

Local source and extracted-release runs remain at 49/49 tests. Hosted-runner
portability and CI duration therefore require a focused follow-up before v0.7.0
feature work.
