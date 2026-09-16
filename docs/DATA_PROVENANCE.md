# Data provenance and privacy v0.6.0

## Purpose

The project uses private tutoring material only to discover problem shapes and
candidate misconceptions. It does not copy conversation text, course documents,
student submissions, screenshots, names, groups, local paths, or personal metadata
into the repository or generated dataset.

`data/case_seeds.json` is the public-safe bridge between the private review and the
implementation. It stores aggregate source types, abstract observations, status,
and the newly authored exercises that cover each observation. It contains no raw
training examples.

## Transformation boundary

1. Review a private source locally.
2. Record an abstract misconception without copying its wording or code.
3. Assign a neutral seed ID such as `C-SEED-002`.
4. Author a new exercise, reference solution, mutation, tests, and hints from
   scratch.
5. Store only the seed ID in generated sample metadata.
6. Verify that no private identifier or original material entered the repository.

This creates provenance for design decisions without implying that the generated
program is a real student's submission.

## Source reliability

| Source group | Permitted use | Not permitted |
|---|---|---|
| Tutoring conversations | Teaching constraints and recurring confusion patterns | Quoting or training on raw messages |
| Laboratory PDFs | Curriculum mapping | Republishing pages or exercises verbatim |
| Reference templates | Confirming beginner-level scope | Presenting generated templates as human submissions |
| Mixed code notes | Candidate bug discovery | Assuming authorship, consent, or ground-truth labels |
| Algorithm scaffolds | Future exercise ideas | Treating incomplete menus as correct algorithmic solutions |
| Private C curriculum packet | Abstract topic coverage and portability requirements | Copying text, code, filenames, authorship, document metadata, or page images |

## Current dataset claims

- Every classifier row is a controlled mutation of an author-owned reference
  solution.
- `origin=controlled_mutation` must not be described as real-world student data.
- `evidence_basis` identifies either the original synthetic design or one abstract
  case seed.
- Style variants are near-duplicates and always remain grouped by exercise during
  evaluation.
- No consent claim is needed for the synthetic rows because they contain no copied
  student submission.
- v0.6.0 answer styles, aliases, anchors, and explanations were written for this
  project and do not derive student authorship or personal profiles from the
  tutoring conversations.
- A style profile is updated only after the learner explicitly selects
  “Learn from current code”. It stores bounded votes and resolved preferences for
  contextual braces, updates, indentation, comments, signatures, declaration
  layout, spacing, and aggregate identifier categories/conventions—not raw code,
  identifiers, or text.
- Optional browser draft persistence is separate from the profile and classifier
  data. It is disabled by default, stores raw code only on the learner's current
  device, separates it by profile and exercise, and deletes it when the option is
  disabled or that draft is restored to its starter.
- The two-profile experiment is controlled testing by the project owner. Its
  output is product-validation evidence, not a real-student dataset or a model
  accuracy result.
- The v0.5.2 regression suite encodes only abstract style traits observed during
  that controlled test. The uploaded test reports and their source text are not
  included in the repository or release archive.
- The private Calculatoare curriculum packet was reviewed locally only. Its raw
  archive, PDFs, extracted text, filenames, author fields, and other metadata are
  excluded from the repository, dataset, model artifact, and release archive.
- `CURR-C-002` records only an abstract coverage decision. The four v0.6 exercises,
  their statements, tests, solutions, mutations, hints, translations, and exam
  rubric were newly authored for this project.
- The PCLP1 preset represents a bounded list of general formatting conventions; it
  does not reproduce a private template. Compatibility warnings contain fixed
  project-authored messages and never echo the matching source fragment.

## Future human-data gate

A real submission may be collected only with informed consent, de-identification,
restricted raw storage, a documented deletion path, and separation from the public
repository. A frozen human test set must report participant count and labeling
procedure without publishing reconstructable code. Ambiguous or multi-bug examples
require independent review before benchmark use.
