from __future__ import annotations


HINTS: dict[str, tuple[str, str, str]] = {
    "loop_boundary": (
        "Which elements should the loop visit, including the first and last valid one?",
        "Write down the valid index interval, then compare it with the loop condition.",
        "Check whether the stopping condition skips the final required iteration or performs one too many.",
    ),
    "relational_operator": (
        "What must be true at the exact moment this branch should execute?",
        "Trace one value that should enter the branch and one that should not, then inspect the comparison.",
        "Revisit the direction or equality part of the comparison used to update the result.",
    ),
    "wrong_initialization": (
        "What invariant should the result variable satisfy before the first iteration?",
        "Compare the initial value with the neutral value—or first input value—required by the operation.",
        "Inspect the assignment made before the main loop; it biases every later result.",
    ),
    "missing_update": (
        "Which variable must change each time useful work is found?",
        "Trace two iterations and write the value of the result variable after each one.",
        "The relevant loop or branch observes a value but does not preserve its contribution to the result.",
    ),
    "invalid_index": (
        "For an array of size n, what are the smallest and largest legal indices?",
        "Evaluate every array subscript during the first and last loop iterations.",
        "One subscript is shifted from the current element and can read the wrong position or leave the array.",
    ),
    "logical_condition": (
        "Should both parts of this condition be true, or is either one sufficient?",
        "Build a tiny truth table for the compound condition used by the loop or branch.",
        "Inspect the boolean connector or negation in the condition controlling the key operation.",
    ),
    "integer_division": (
        "Check the types involved when the total is divided by the number of values.",
        "Try a case whose mathematical result has a fractional part and inspect when conversion occurs.",
        "Make the division operate in floating-point rather than converting only after an integer result exists.",
    ),
    "accumulator_misuse": (
        "Should each iteration replace the previous result or combine with it?",
        "Trace the accumulator across at least three values and watch whether earlier contributions survive.",
        "Inspect the assignment inside the loop: the accumulated value is being overwritten.",
    ),
    "menu_dispatch": (
        "Which menu key should reach the operation requested by this test?",
        "Match every documented command with exactly one switch branch, then trace the failing key.",
        "Inspect the case label attached to the operation; the command and branch no longer correspond.",
    ),
    "input_buffer_misuse": (
        "What character is still waiting in the input stream before the next read?",
        "Trace the input one character at a time where token-based and line-based reads meet.",
        "Make the next character read skip or consume the pending newline before using the value.",
    ),
    "invalid_program_state": (
        "What must the user do before this operation has valid data to process?",
        "Trace the state flag before and after the read command, including a query made first.",
        "Restore the guard that prevents the operation from running before its required input exists.",
    ),
    "wrong_identifier_or_argument": (
        "Does each expression represent the value or parameter required at that exact position?",
        "Write the meaning of every argument or right-hand-side identifier before tracing its value.",
        "One call or assignment uses a valid identifier with the wrong role; compare it with the function contract.",
    ),
    "sentinel_handling": (
        "Which value or character ends the input, and should that marker be processed as data?",
        "Trace the final real value, the stop marker, and the first operation after each is read.",
        "Keep the termination marker out of the result and stop exactly at that boundary, without consuming later data.",
    ),
    "compilation_error": (
        "Start with the first compiler diagnostic; later messages may be consequences of it.",
        "Use the reported line and inspect punctuation, declarations, and matching delimiters nearby.",
        "Fix the first reported error, compile again, and only then move to the next remaining diagnostic.",
    ),
    "unknown": (
        "Choose the smallest failing test and trace the program state by hand.",
        "Compare the expected output with the first point where your traced state diverges.",
        "Add a temporary print around that point to verify the values controlling the result.",
    ),
}


def get_hint(category: str, level: int = 1) -> str:
    if level not in {1, 2, 3}:
        raise ValueError("Hint level must be 1, 2, or 3.")
    return HINTS.get(category, HINTS["unknown"])[level - 1]
