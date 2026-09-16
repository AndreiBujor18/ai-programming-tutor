# Style personalization experiment v0.6.0

## Goal

Test whether two deliberately different C formatting profiles lead to visibly
different complete solutions without changing program behavior. One person can
operate both profiles, so this sprint does not require accounts or real student
data.

This is a deterministic product experiment, not an AI-style-model accuracy claim.

v0.6.0 also offers a separate **PCLP1 classic · FIESC** preset. Unlike the two
learner profiles, this preset is not learned and never changes with user code. It
applies a reviewed set of general, portable-C conventions to the same authored and
tested reference solutions. It is useful as a familiar starting point, but it is
not presented as an official faculty template.

## What the profile learns

The learner must explicitly choose **Learn from current code**. The analyser records
one bounded vote per observable dimension:

| Dimension | Values currently supported |
| --- | --- |
| Function braces | same line / next line |
| Control braces | same line / next line, independently from functions |
| Scalar updates | prefix (`++i`), postfix (`i++`), compound (`i += 1`), explicit (`i = i + 1`) |
| Indentation | two spaces / four spaces |
| Comments | minimal / explanatory |
| Comment syntax | line (//) / block (slash-star) |
| Comment placement | grouped outline / beside the relevant code block |
| Main signature | `main()` / `main(void)` |
| Loop counter declaration | before the loop / inside `for` |
| Control spacing | `for (...)` / `for ( ... )` |
| Identifiers | short / descriptive; Romanian / English when language evidence exists |
| Identifier convention | `snake_case` / `camelCase` when a multiword identifier provides evidence |
| Declaration layout | compatible declarations grouped / declarations on separate lines |

The browser stores the number of accepted examples, bounded counters, and the
resolved preferences. It does not store the source, identifiers, comment text,
exercise answers, or compiler output in the profile. Optional draft persistence is
a separate, explicit browser setting and is not style-learning data. Each resolved dimension is
also labeled as learned, mixed, or default, so missing evidence is never presented
as if it were learned.

C++ markers such as iostream, cin, cout, ifstream, and ofstream cause the example
to be ignored. Text inside comments and string literals does not trigger that
check.

## What personalization changes

A complete personalized answer always begins from the project's tested reference
solution. The formatter may:

- move function and control braces independently;
- switch safe standalone or loop updates among the four supported forms;
- convert four-space indentation to two spaces;
- choose `main()` or `main(void)`, loop-counter placement, and control spacing;
- add authored explanations either as an outline or beside stable logic anchors;
- choose line or block comment syntax;
- select authored short or Romanian identifier aliases without copying learner names.
- convert reviewed authored identifiers between `snake_case` and `camelCase`;
- split grouped declarations, or merge only adjacent declarations with the same C type.

It does not copy names or comment text, change algorithms, infer arbitrary naming
schemes, move declarations across statements, or rewrite arbitrary learner source.
Identifier transformations come from reviewed per-exercise maps and are
compilation-tested. Those boundaries keep this test measurable and make regression
testing practical.

Profile schema 0.3 preserves and migrates schema-0.2 profiles. The two new dimensions
begin as unobserved defaults until another example supplies evidence. Schema-0.1
profiles still reset because their single brace vote cannot be separated into
function and control evidence.

## Manual two-profile protocol

1. Select **Profile A** and write a representative C program containing at least
   one loop or function body. Use one deliberate style, for example same-line
   function/control braces, four spaces, postfix updates, and at least two line
   comments placed near the blocks they explain.
2. Select **Learn from current code** and verify that the summary matches the code.
3. Switch to **Profile B**. Confirm that Profile A's draft is no longer visible,
   then write a contrasting example, for example a same-line function brace, a
   next-line loop brace, `i = i + 1`, spaces inside `for ( ... )`, and no comments.
4. Learn Profile B and switch back to Profile A. Confirm that each in-tab draft
   and each aggregate style summary is independent.
5. On a different exercise, select **Match my profile** and reveal the complete
   solution under each profile.
6. Compare the two answers. Their logic and output should match while the supported
   style dimensions differ.
7. Run the generated answers through every exercise test before recording a
   result.
8. Optionally enable **Save drafts on this device**, reload, and verify that an
   intentionally empty draft stays empty. Disable the option and verify that stored
   drafts are deleted while the current in-tab text remains available.

Suggested observation sheet:

| Check | Profile A | Profile B |
| --- | --- | --- |
| Summary matches intended style | pass/fail | pass/fail |
| Function braces match | pass/fail | pass/fail |
| Control braces match | pass/fail | pass/fail |
| Generated updates match | pass/fail | pass/fail |
| Generated indentation matches | pass/fail | pass/fail |
| Generated comments match | pass/fail | pass/fail |
| Main, loop declaration, and spacing match | pass/fail | pass/fail |
| Identifier family matches | pass/fail | pass/fail |
| Identifier convention and declaration layout match | pass/fail | pass/fail |
| Defaults are visibly marked | pass/fail | pass/fail |
| Draft stayed isolated and opt-in persistence behaved correctly | pass/fail | pass/fail |
| All exercise tests pass | pass/fail | pass/fail |

## Interpretation

Passing this protocol shows that the profile mechanism and user experience work
for controlled differences. It does not show that the system understands a person,
improves learning outcomes, or generalises to natural student code. Those claims
would need consented participants, a frozen protocol, and separate evaluation.
