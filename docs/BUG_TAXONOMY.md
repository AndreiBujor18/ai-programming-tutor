# Bug taxonomy v0.3

Each classifier sample contains exactly one intended semantic mutation. Labels
describe the misconception rather than one token spelling. The four v0.2 labels
and the v0.3 sentinel label were admitted only after each could be instantiated in
at least two exercises.

| Label | Student misconception | Typical signal | Hint goal |
|---|---|---|---|
| `loop_boundary` | A loop visits too few or too many elements. | Edge or last-element tests fail. | Reconstruct the valid iteration interval. |
| `relational_operator` | A comparison has the wrong direction or equality. | Contrasting values take the opposite branch. | Trace one positive and one negative case. |
| `wrong_initialization` | A result, flag, or state begins with a biased value. | All-negative input or a pre-read command fails. | Recover the invariant before iteration one. |
| `missing_update` | The program observes an event but does not update related state. | A count, size, or readiness flag remains unchanged. | Identify which state must change and when. |
| `invalid_index` | An array or matrix position does not denote the intended element. | Boundary cases corrupt or skip values. | Evaluate every subscript at both boundaries. |
| `logical_condition` | Boolean terms are connected or negated incorrectly. | A branch is always or never active. | Build a small truth table. |
| `integer_division` | Integer division occurs before conversion. | Whole results pass while fractions fail. | Inspect operand types at the division itself. |
| `accumulator_misuse` | A running result is overwritten rather than combined. | Output resembles only the last visited value. | Trace whether earlier contributions survive. |
| `menu_dispatch` | A command is missing or routed to the wrong operation. | One documented key produces INVALID or another action. | Map each command to one branch. |
| `input_buffer_misuse` | A token, character, or line read consumes leftover input. | The first command or line is empty or shifted. | Trace the pending characters between reads. |
| `invalid_program_state` | An action runs before required data exists. | A query before the first read returns a fabricated value. | State the operation's precondition and guard it. |
| `wrong_identifier_or_argument` | A valid variable with the wrong role is assigned or passed. | Dimensions, lengths, positions, or values are swapped. | Compare each expression with the function contract. |
| `sentinel_handling` | A stop marker is processed as ordinary data or input is consumed past it. | Empty-series, first-marker, or following-field tests fail. | Separate marker detection from value processing and stop at the first marker. |

## Operational and deferred categories

`compilation_error` and `unknown` remain tutor outputs but are not semantic
classifier labels. Declaration typos are explained through compiler diagnostics.
Toolchain mismatches and non-portable APIs require environment-aware checks rather
than controlled semantic mutations. v0.6.0 therefore reports source-free operational
warnings for removed, undefined, or commonly non-portable constructs; they are not
classifier labels and do not alter the submitted source.

`file_cursor_state` remains deferred. Two independent fixed-file families now exist:
`file_number_summary` covers counted numeric aggregation and `file_longest_word`
covers bounded string selection with first-on-tie semantics. Generator 0.3.0 has no
reviewed file-specific mutations for either family, however, and catalog breadth
alone is not evidence that a new label is reliable. Both exercises therefore reuse
existing categories and remain excluded until a versioned mutation review can test
the proposed category across both held-out families.

## Labeling rules

- Prefer the earliest causal mistake rather than a later symptom.
- Do not infer intent solely from formatting or variable names.
- Use `wrong_identifier_or_argument` only when the identifier is valid; unknown
  identifiers remain compilation errors.
- Use `invalid_program_state` for a missing precondition, not merely a badly
  initialized numeric accumulator.
- If two independent mistakes exist, mark the example as multi-bug and exclude it
  from the first single-label benchmark.
- Store the exercise version, test-suite version, compiler version, origin, and
  evidence basis.
- Review ambiguous real submissions with two annotators before benchmark use.
