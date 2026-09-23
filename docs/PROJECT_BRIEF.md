# Project brief — v0.11.0

## Product hypothesis

Beginning PCLP1 students have different study preferences. Some need a next
reasoning step after a failed test; others want to study a complete solution.
The tutor offers both paths and can adapt safe formatting details without implying
that memorization represents all students or that formatting equals understanding.

## Primary user

A first-year Computer Engineering student learning classic C through short PCLP1
console exercises. Other degree programs and mixed C/C++ teaching styles are
outside the current product experiment.

## V1 experience

1. The student chooses one of 16 curated exercises or starts the four-task practice exam.
2. They choose local Profile A or Profile B and write classic C in the browser.
3. They run public and hidden tests; hidden expected and actual output stay private.
4. The system suggests likely C bug categories.
5. They reveal up to three hints, or independently request the complete verified
   reference answer with an authored explanation.
6. They may explicitly teach the active profile bounded style preferences from their
   current code and request a personalized, classic, or explained C reference.
7. They may explicitly keep drafts on the current device, independently for each
   profile and exercise, and can remove them by restoring the starter or disabling
   local saving.
8. During a practice exam, the browser keeps the timer, active task, and numeric
   best-attempt score locally without adding source code to the exam record.

The stable v0.11.0 release implements this flow in a dependency-free localhost
website, CLI, and optional FastAPI service for 16 exercises, including two
independent fixed-file families. No account or server-side attempt history is
persisted; optional drafts, bounded numeric progress, and exam state never leave
browser storage. The file workflow uses strict project-authored runner contracts
and two original exercises with bilingual contract and result rendering. The
browser uses a locally bundled, C-aware editor and separates Exercises, Practice
exam, and Progress into focused top-level modes.

## In scope for V1

- C17/GCC for the classic-C PCLP1 workflow;
- fixed, versioned exercises and tests;
- bounded project-authored text fixtures and expected output files, each test in a
  fresh disposable working directory;
- 13 semantic bug labels plus compilation errors;
- rule baseline, TF-IDF/logistic-regression baseline, and later a pretrained code
  encoder comparison;
- public/hidden test distinction;
- progressive hints plus a distinct optional full-solution action;
- a locally bundled CodeMirror 6 C editor with a plain-text fallback and no runtime
  dependency on a remote CDN;
- separate Exercises, Practice exam, and Progress modes, with a side-by-side desktop
  workbench and a single-column narrow-window layout;
- curated, tested C answer variants for all exercises;
- an author-owned practice exam and a separate, author-defined PCLP1 classic preset;
- source-free compatibility warnings for a small reviewed set of legacy constructs;
- two local profiles and explicit extraction of contextual braces, update forms,
  indentation, comments, main signature, loop declarations, spacing, and aggregate
  identifier preferences, identifier convention, and declaration layout;
- deterministic application of those preferences to tested references;
- experiment metrics and a future learner-feedback mechanism;
- localhost-only execution for development; disposable workers required for public use.

## Explicit non-goals

- arbitrary user-authored problems;
- Python support before the C workflow is validated;
- C++ and degree-program-specific mixed-language modes in the current experiment;
- authentication, server-side history, social features, mobile apps, or plagiarism
  detection;
- arbitrary learner file uploads in the local browser;
- generated arbitrary full solutions or semantic imitation of learner code;
- public execution of untrusted code inside the API process.

## Data strategy

The classifier dataset uses correct, author-owned reference solutions and one
controlled mutation per example. Identifier and formatting variants reduce trivial
lexical memorisation. No student submission is collected without informed consent.
Human submissions, if added later, must be de-identified, access-controlled, and
tracked separately from synthetic data.

The local style experiment is separate from the classifier dataset. An explicit
button sends the current source only to the local analyser; the returned and stored
profile contains bounded aggregate votes, resolved preferences, and their evidence
origin, never raw source, identifiers, or comment text. Short and Romanian answer
identifiers are selected from authored per-exercise alias maps, not copied from code.
Optional local draft saving is a distinct consented setting, not part of the style
profile or classifier dataset.

The synthetic generator creates 1,312 examples by default: 82 exercise/mutation
pairs times 16 source variants. It stores compiler and test signals, origin, and an
abstract evidence basis alongside each sample. Synthetic coverage is a seed dataset,
not evidence of real-world quality. Private source material is excluded according
to docs/DATA_PROVENANCE.md. Generator 0.4.0 includes all 16 exercises. Its reviewed
file mutations reuse existing labels; the proposed `file_cursor_state` category was
not admitted because its cases overlap loop-boundary and wrong-argument concepts.

## Evaluation design

Random row splits would leak nearly identical variants across train and test. The
baseline therefore uses leave-one-exercise-out cross-validation: every prediction
is made for an exercise absent from that fold's training data. The strengthened
baseline combines character n-grams with compiler/test signals and a token-normalised
structural diff against the exercise's known reference solution. Reference solutions
are available at inference time for this fixed-exercise product, so this is a product
feature rather than train/test leakage; it must still be validated on naturally
written student programs rather than controlled mutations alone.

The natural-code harness is a separate, frozen-test evaluation path. It accepts
only consented, de-identified C17 submissions with two-labeler agreement or
adjudication and precomputed statuses from an external disposable worker. It never
executes imported code, trains on the frozen set, or writes source/per-sample
predictions to its aggregate report. No qualifying human dataset has been collected
yet, so this infrastructure is not itself an accuracy result.

The worker path defines an exact source-bound job/result protocol and a
one-container-per-submission reference invocation. Profile 0.2 uses no network or
host volumes, separates its namespace-root controller from the untrusted
compiler/program by UID, protects controller package files, bounds host output while
reading it, and returns only source-free compilation/test signals. The repository
also provides an authored hostile-probe command. Profile 0.2 passed its complete
Windows/Docker Desktop integration audit, but still requires a dedicated secret-free
host, immutable image recording, and complete host acceptance before a real pilot;
it is not a production-sandbox claim.

The host path also provides `aptutor inspect-host`: a read-only source-free report
over 17 rootless Docker and Linux boundary checks. `automated_ready` never attests
that the machine is dedicated or secret-free; manual retention, network, build,
reboot, and incident evidence remains blocking in the external operations record.

Target product metrics:

- bug classification macro-F1 >= 0.75;
- top-3 category recall >= 0.90;
- full-solution leakage in hints < 5% under human review;
- evaluation response time < 3 seconds at p95;
- at least 70% of students rate the hint as useful;
- next-attempt improvement measured separately from simple test pass rate.

## Technical shape

- present browser prototype: static HTML, CSS, and JavaScript with a committed
  editor bundle; Node.js is needed only to rebuild that maintainer-owned asset;
- optional future client: React, TypeScript, Vite, Monaco Editor if the UX needs it;
- application API: FastAPI and Pydantic;
- execution: isolated disposable C runner workers;
- ML: scikit-learn baseline, then PyTorch/Hugging Face experiments;
- persistence: PostgreSQL for exercises, attempts, hints, and feedback;
- experiment tracking: dataset versions plus MLflow or an equivalent tool;
- delivery: Docker Compose and GitHub Actions.

## Established acceptance criteria

- all 16 C references and every complete-solution style pass all exercise tests;
- personalized references for both controlled and natural contrasting profiles pass
  every test;
- Profile A and Profile B keep separate aggregate preferences and drafts;
- schema-0.2 profiles migrate without losing votes, while the new dimensions remain
  visibly unobserved until learned;
- descriptive identifier convention is learned as `snake_case` or `camelCase`, and
  declaration layout is transformed without moving declarations across statements;
- device-local draft saving is off by default, distinguishes an empty saved draft
  from no draft, and deletes stored drafts when disabled;
- C++ examples are ignored by profile learning and C++ modes are absent from the UI;
- explicit and compound updates are recognized; function/control brace preferences
  remain independent; unobserved dimensions are labeled as defaults;
- the local browser can show exercise, feedback, hints, or a separately requested
  complete explanation without putting that answer into a normal exercise response;
- the original practice exam totals 10 points, retains only source-free browser
  progress, and labels its score as an estimate rather than an official grade;
- legacy compatibility matches ignore comments and string literals, return fixed
  source-free messages, and never rewrite the learner's code;
- hidden expected/actual values are omitted from user-facing feedback;
- no private teaching materials, raw text, filenames, authorship, metadata, or copied
  source are included; benchmark claims remain limited to controlled mutations;
- local HTTP execution is opt-in and rejects cross-origin requests;
- the enhanced editor preserves exercise, profile, draft, locale, theme, test, and
  exam state, while the fallback textarea remains usable without enhancement;
- the three workspace modes keep the problem/editor path primary, put exam context
  above the same workbench, and give detailed progress a dedicated view.
- worker jobs contain no participant or labeling fields, are bound to exact source,
  exercise, and test-suite fingerprints, and produce exact source-free receipts;
- the reference worker invocation uses an immutable image ID/digest, no network or
  volumes, a namespace-root controller separated from the non-root submission UID,
  a read-only root, bounded transport/resources, and failure cleanup without
  claiming a formally verified sandbox;
- every authored adversarial check and the separate dedicated-host checklist are
  blocking before natural source is processed.

The first v0.8.0 engineering slice additionally requires exact file-contract keys,
portable flat names, eight combined entries at most, bounded authored content, a
fresh work directory for every test, regular-file-only result inspection, hidden
content redaction, and unchanged behavior for all existing stdin/stdout exercises.
The second slice additionally requires one original five-case file exercise,
bilingual public fixture/expected-file blocks, nested file-result statuses, generic
hidden-file labels, a Files progress concept, and no arbitrary upload surface.
The v0.10.0 follow-on slice adds a second five-case family based on bounded strings,
preserves the first word on equal maximum lengths, reuses reviewed diagnostic
categories, and originally left the benchmark unchanged pending a separate review.
The v0.11.0 generator 0.4.0 release completes that review with 11 file-family
mutation pairs, separate held-out folds, and no additional semantic label.

## Next sprint

The v0.9.0 interface refresh and its focused Windows manual acceptance are complete.
The locally bundled editor, both themes and locales, full and half-width desktop
layouts, and all three workspace modes are accepted without changing local privacy
or execution boundaries.

The v0.8.0 file workflow and its focused Windows manual acceptance protocol are
complete. Strict project-authored fixtures, bounded expected-file checks, a fresh
disposable work directory for every test, bilingual file feedback, profile/draft
continuity, and Files progress are accepted. This remains a trusted-local
improvement, not a public sandbox claim.

The second independent file-processing family and its focused Windows acceptance
are complete in both locales. Public contracts, hidden redaction, verified and
faulty tie behavior, progressive hints, and source-free Files/Strings progress are
accepted. The generator 0.4.0 review now covers both file families and rejects a
file-specific label as redundant with existing causal categories. Do not add
arbitrary uploads or broaden the execution boundary.

The private-input, aggregate-output natural-code evaluation harness is now defined
and implemented without collecting submissions or making a human-code metric claim.
The disposable-worker protocol, hardened profile 0.2 path, and source-free
adversarial command are implemented and have passed the complete local
Windows/Docker Desktop integration protocol. Next, select and prepare the dedicated
secret-free Linux host, rebuild and pin its image, and repeat the full gate using the
recorded image/compiler/runtime identity and incident path. Only then recruit a
small consented pilot, especially for sentinel handling and naturally structured
file processing. Freeze and label that set independently before inspecting tutor
predictions. Before public code execution, move the product runner behind the same
accepted class of worker boundary.
