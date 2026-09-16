# Project brief v0.6.0

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

1. The student chooses one of 14 curated exercises or starts the four-task practice exam.
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

The v0.6.0 prototype implements this flow in a dependency-free localhost website,
CLI, and optional FastAPI service for 14 exercises. No account or server-side attempt
history is persisted; optional drafts and exam state never leave browser storage.

## In scope for V1

- C17/GCC for the classic-C PCLP1 workflow;
- fixed, versioned exercises and tests;
- 13 semantic bug labels plus compilation errors;
- rule baseline, TF-IDF/logistic-regression baseline, and later a pretrained code
  encoder comparison;
- public/hidden test distinction;
- progressive hints plus a distinct optional full-solution action;
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
- authentication, saved history, favorites, social features, mobile apps, or
  plagiarism detection;
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

The synthetic generator creates 1,136 examples by default: 71 exercise/mutation
pairs times 16 source variants. It stores compiler and test signals, origin, and an
abstract evidence basis alongside each sample. Synthetic coverage is a seed dataset,
not evidence of real-world quality. Private source material is excluded according
to docs/DATA_PROVENANCE.md.

## Evaluation design

Random row splits would leak nearly identical variants across train and test. The
baseline therefore uses leave-one-exercise-out cross-validation: every prediction
is made for an exercise absent from that fold's training data. The strengthened
baseline combines character n-grams with compiler/test signals and a token-normalised
structural diff against the exercise's known reference solution. Reference solutions
are available at inference time for this fixed-exercise product, so this is a product
feature rather than train/test leakage; it must still be validated on naturally
written student programs rather than controlled mutations alone.

Target product metrics:

- bug classification macro-F1 >= 0.75;
- top-3 category recall >= 0.90;
- full-solution leakage in hints < 5% under human review;
- evaluation response time < 3 seconds at p95;
- at least 70% of students rate the hint as useful;
- next-attempt improvement measured separately from simple test pass rate.

## Technical shape

- present browser prototype: static HTML, CSS, and JavaScript with no build step;
- optional future client: React, TypeScript, Vite, Monaco Editor if the UX needs it;
- application API: FastAPI and Pydantic;
- execution: isolated disposable C runner workers;
- ML: scikit-learn baseline, then PyTorch/Hugging Face experiments;
- persistence: PostgreSQL for exercises, attempts, hints, and feedback;
- experiment tracking: dataset versions plus MLflow or an equivalent tool;
- delivery: Docker Compose and GitHub Actions.

## v0.6.0 acceptance criteria

- 14 baseline C references and every complete-solution style pass all exercise tests;
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
- local HTTP execution is opt-in and rejects cross-origin requests.

## Next sprint

Run the practice simulation and expanded style protocol with the project owner's two
controlled profiles. Then design a consented, de-identified natural-code evaluation,
especially for sentinel handling. Before public release, move execution behind a
disposable worker boundary. Consider accounts, history, and favorites only after
defining retention, deletion, and consent policies.
