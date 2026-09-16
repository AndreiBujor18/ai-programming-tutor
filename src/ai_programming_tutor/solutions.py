"""Author-written, tested reference solutions; no model-generated code or student files."""

from __future__ import annotations

from ai_programming_tutor.models import Exercise
from ai_programming_tutor.style_profile import (
    apply_c_style,
    detect_cpp_features,
    normalise_style_profile,
    replace_c_identifiers,
)


# These outlines are original explanations of the bundled, author-owned solutions.
SOLUTION_STEPS: dict[str, tuple[str, ...]] = {
    "delete_occurrences": (
        "Read the vector and the value to remove; track the current logical length separately from capacity.",
        "When a match is found, shift the remaining elements left and reduce the length. "
        "Recheck the same index for consecutive matches.",
        "Print how many elements were removed, the new length, and only the surviving elements.",
    ),
    "diagonal_average": (
        "Read the square matrix row by row.",
        "For each valid position i, add the element whose row and column are both i.",
        "Convert before division so a fractional average is not truncated, then print two decimal places.",
    ),
    "frequency_count": (
        "Read the vector and the value whose occurrences you want to count.",
        "Start the frequency at zero and visit each valid vector position once.",
        "Increase the counter only when the current element equals the target; print the counter.",
    ),
    "interval_parity": (
        "Read the two boundaries of the valid closed interval.",
        "Subtract the lower boundary from the upper one and add one because both ends belong to the interval.",
        "Test the resulting count modulo two and print the required parity word.",
    ),
    "line_after_number": (
        "Read the leading integer with scanf.",
        "Consume the rest of that input line so the following fgets starts at the actual "
        "text, not the leftover newline.",
        "Read the complete text line, remove its trailing newline if present, and print the requested pair.",
    ),
    "matrix_menu": (
        "Keep the matrix dimensions and a flag recording whether a matrix has been read.",
        "Dispatch each command: R fills the matrix; X checks the state before computing a maximum for each row.",
        "Use the first element of each row as its initial maximum, then compare the other columns.",
    ),
    "min_max": (
        "Read the size and elements of the nonempty vector.",
        "Initialize both minimum and maximum from the first element, including when every number is negative.",
        "Compare each remaining element with both extrema and print their final values.",
    ),
    "odd_digit_count": (
        "Read the nonnegative integer and start the odd-digit counter at zero.",
        "Repeatedly obtain the last decimal digit with modulo ten, test its parity, and remove it with division by ten.",
        "Use a do-while loop so zero is handled consistently, then print the counter.",
    ),
    "palindrome": (
        "Read the word and find its length.",
        "Compare symmetric characters from the ends, stopping halfway or at the first mismatch.",
        "Print YES only if every compared pair matched; otherwise print NO.",
    ),
    "perfect_squares": (
        "Read the upper limit and remember whether any square has been printed.",
        "Increase a positive root while its square remains within the limit, using a wide type for the multiplication.",
        "Print the squares in order and print NONE only when the loop produced no value.",
    ),
    "sentinel_average": (
        "Read values until zero and treat zero only as the marker that ends the sequence.",
        "For every preceding value, update both a wide running total and the number of values.",
        "Report EMPTY for an empty sequence; otherwise divide in floating point and print two decimals.",
    ),
    "vector_average": (
        "Read how many values follow and keep a sufficiently large running total.",
        "Read each vector element and add it to the total exactly once.",
        "Convert before dividing by the number of elements, then print the average to two decimal places.",
    ),
    "vector_insert": (
        "Read the original vector, the new value, and the zero-based insertion position.",
        "Shift existing elements one place to the right, starting at the old end to avoid overwriting values.",
        "Store the new value at the requested position, increase the logical length, and print the vector.",
    ),
    "vector_menu": (
        "Keep the vector, its length, and a flag showing whether the R command has populated it.",
        "Dispatch R to read, S to sum, and M to find the maximum; reject operations before the first read.",
        "When finding the maximum, start from the first valid element and compare every remaining value.",
    ),
}


# Authored aliases used only on the project's tested references. They make the
# controlled experiment more realistic without retaining or copying learner names.
SHORT_IDENTIFIER_MAPS: dict[str, dict[str, str]] = {
    "delete_occurrences": {
        "item_count": "n", "values": "v", "target": "x", "removed_count": "nr",
        "position": "i", "index": "j",
    },
    "diagonal_average": {
        "item_count": "n", "matrix": "a", "row": "i", "column": "j",
        "total": "s", "position": "i",
    },
    "frequency_count": {
        "item_count": "n", "values": "v", "position": "i", "target": "x",
        "frequency": "f",
    },
    "interval_parity": {
        "lower_bound": "a", "upper_bound": "b", "item_count": "n",
    },
    "line_after_number": {"identifier": "id", "character": "c", "text": "s"},
    "matrix_menu": {
        "read_matrix": "citire", "print_row_maxima": "afisare", "matrix": "a",
        "row_count": "n", "column_count": "m", "row": "i", "column": "j",
        "maximum": "max", "command_count": "q", "command_index": "k",
        "command": "op", "has_matrix": "ok",
    },
    "min_max": {
        "item_count": "n", "values": "v", "position": "i",
        "minimum": "min", "maximum": "max",
    },
    "odd_digit_count": {"number": "n", "digit": "c", "frequency": "nr"},
    "palindrome": {"word": "s", "length": "n", "is_palindrome": "ok", "position": "i"},
    "perfect_squares": {"limit": "n", "root": "i", "square": "p", "printed": "ok"},
    "sentinel_average": {"value": "x", "total": "s", "item_count": "n"},
    "vector_average": {"item_count": "n", "values": "v", "total": "s", "position": "i"},
    "vector_insert": {
        "item_count": "n", "values": "v", "position": "i", "inserted_value": "x",
        "insertion_position": "p", "index": "j",
    },
    "vector_menu": {
        "read_vector": "citire", "vector_sum": "suma", "vector_maximum": "maxim",
        "values": "v", "item_count": "n", "total": "s", "position": "i",
        "maximum": "max", "has_values": "ok", "command_count": "q",
        "command_index": "k", "command": "op",
    },
}

ROMANIAN_IDENTIFIER_MAPS: dict[str, dict[str, str]] = {
    "delete_occurrences": {
        "item_count": "numar_elemente", "values": "valori", "target": "valoare_cautata",
        "removed_count": "numar_sterse", "position": "pozitie", "index": "indice",
    },
    "diagonal_average": {
        "item_count": "dimensiune", "matrix": "matrice", "row": "linie",
        "column": "coloana", "total": "suma", "position": "pozitie",
    },
    "frequency_count": {
        "item_count": "numar_elemente", "values": "valori", "position": "pozitie",
        "target": "valoare_cautata", "frequency": "frecventa",
    },
    "interval_parity": {
        "lower_bound": "limita_stanga", "upper_bound": "limita_dreapta",
        "item_count": "numar_valori",
    },
    "line_after_number": {
        "identifier": "identificator", "character": "caracter", "text": "text",
    },
    "matrix_menu": {
        "read_matrix": "citeste_matrice", "print_row_maxima": "afiseaza_maxime_linii",
        "matrix": "matrice", "row_count": "numar_linii", "column_count": "numar_coloane",
        "row": "linie", "column": "coloana", "maximum": "maxim",
        "command_count": "numar_comenzi", "command_index": "indice_comanda",
        "command": "comanda", "has_matrix": "matrice_citita",
    },
    "min_max": {
        "item_count": "numar_elemente", "values": "valori", "position": "pozitie",
        "minimum": "minim", "maximum": "maxim",
    },
    "odd_digit_count": {
        "number": "numar", "digit": "cifra", "frequency": "numar_cifre_impare",
    },
    "palindrome": {
        "word": "cuvant", "length": "lungime", "is_palindrome": "este_palindrom",
        "position": "pozitie",
    },
    "perfect_squares": {
        "limit": "limita", "root": "radacina", "square": "patrat",
        "printed": "a_afisat",
    },
    "sentinel_average": {
        "value": "valoare", "total": "suma", "item_count": "numar_valori",
    },
    "vector_average": {
        "item_count": "numar_elemente", "values": "valori", "total": "suma",
        "position": "pozitie",
    },
    "vector_insert": {
        "item_count": "numar_elemente", "values": "valori", "position": "pozitie",
        "inserted_value": "valoare_inserata", "insertion_position": "pozitie_inserare",
        "index": "indice",
    },
    "vector_menu": {
        "read_vector": "citeste_vector", "vector_sum": "suma_vector",
        "vector_maximum": "maxim_vector", "values": "valori",
        "item_count": "numar_elemente", "total": "suma", "position": "pozitie",
        "maximum": "maxim", "has_values": "vector_citit",
        "command_count": "numar_comenzi", "command_index": "indice_comanda",
        "command": "comanda",
    },
}

# Each step is placed immediately before a stable statement from the authored
# reference. The text itself stays authored in SOLUTION_STEPS and is translated
# by the browser, so learner comments are never copied into an answer.
INLINE_COMMENT_ANCHORS: dict[str, tuple[tuple[str, int], ...]] = {
    "delete_occurrences": (
        ('scanf("%d", &item_count);', 0), ('while (position < item_count) {', 1),
        ('printf("%d %d", removed_count, item_count);', 2),
    ),
    "diagonal_average": (
        ('scanf("%d", &item_count);', 0), ('long long total = 0;', 1),
        ('printf("%.2f\\n", (double) total / item_count);', 2),
    ),
    "frequency_count": (
        ('scanf("%d", &item_count);', 0), ('int frequency = 0;', 1),
        ('printf("%d\\n", frequency);', 2),
    ),
    "interval_parity": (
        ('scanf("%lld %lld", &lower_bound, &upper_bound);', 0),
        ('long long item_count = upper_bound - lower_bound + 1;', 1),
        ('if (item_count % 2 == 0) {', 2),
    ),
    "line_after_number": (
        ('scanf("%d", &identifier);', 0), ('int character;', 1),
        ('printf("%d:%s\\n", identifier, text);', 2),
    ),
    "matrix_menu": (
        ('int matrix[20][20] = {{0}};', 0), ('switch (toupper((unsigned char) command)) {', 1),
        ('int maximum = matrix[row][0];', 2),
    ),
    "min_max": (
        ('scanf("%d", &item_count);', 0), ('int minimum = values[0];', 1),
        ('printf("%d %d\\n", minimum, maximum);', 2),
    ),
    "odd_digit_count": (
        ('scanf("%llu", &number);', 0), ('int digit = (int) (number % 10);', 1),
        ('printf("%d\\n", frequency);', 2),
    ),
    "palindrome": (
        ('scanf("%1000s", word);', 0), ('int length = (int) strlen(word);', 1),
        ('printf("%s\\n", is_palindrome ? "YES" : "NO");', 2),
    ),
    "perfect_squares": (
        ('scanf("%d", &limit);', 0),
        ('for (int root = 1; (long long) root * root <= limit; root++) {', 1),
        ('if (!printed) {', 2),
    ),
    "sentinel_average": (
        ('int value;', 0), ('if (value != 0) {', 1), ('if (item_count == 0) {', 2),
    ),
    "vector_average": (
        ('scanf("%d", &item_count);', 0), ('long long total = 0;', 1),
        ('printf("%.2f\\n", (double) total / item_count);', 2),
    ),
    "vector_insert": (
        ('scanf("%d", &item_count);', 0),
        ('for (int index = item_count; index > insertion_position; index--) {', 1),
        ('values[insertion_position] = inserted_value;', 2),
    ),
    "vector_menu": (
        ('int values[100] = {0};', 0), ('switch (toupper((unsigned char) command)) {', 1),
        ('int maximum = values[0];', 2),
    ),
}


def cpp_features(source: str) -> tuple[str, ...]:
    """Backward-compatible alias for the C-only scope warning."""
    return detect_cpp_features(source)


def available_styles(exercise: Exercise) -> tuple[str, ...]:
    del exercise
    return ("personalized_c", "pclp1_classic", "classic_c", "commented_c")


def _pclp1_classic_profile() -> dict[str, object]:
    """A safe C17 rendering of recurring course conventions, not a learner profile."""
    return normalise_style_profile(
        {
            "schema_version": "0.3",
            "samples": 1,
            "counts": {
                "function_brace_next_line": 1,
                "control_brace_next_line": 1,
                "increment_postfix": 1,
                "indent_4": 1,
                "comments_explanatory": 1,
                "comment_line": 1,
                "comment_inline": 1,
                "main_empty": 1,
                "identifiers_short": 1,
                "declarations_grouped": 1,
                "loop_variable_predeclared": 1,
                "control_spacing_compact": 1,
            },
        }
    )


def _inline_commented_solution(exercise: Exercise, comment_syntax: str) -> str:
    anchors = INLINE_COMMENT_ANCHORS[exercise.id]
    used: set[int] = set()
    output: list[str] = []
    for line in exercise.reference_solution.splitlines(keepends=True):
        for anchor, step_index in anchors:
            if step_index in used or anchor not in line:
                continue
            indent = line[: len(line) - len(line.lstrip())]
            step = SOLUTION_STEPS[exercise.id][step_index]
            comment = f"// {step}" if comment_syntax == "line" else f"/* {step} */"
            output.append(indent + comment + "\n")
            used.add(step_index)
            break
        output.append(line)
    if len(used) != len(SOLUTION_STEPS[exercise.id]):
        raise ValueError(f"Inline comment anchors are incomplete for '{exercise.id}'.")
    return "".join(output)


def _commented_solution(
    exercise: Exercise, comment_syntax: str = "block", comment_placement: str = "outline"
) -> str:
    if comment_placement == "inline":
        return _inline_commented_solution(exercise, comment_syntax)
    steps = SOLUTION_STEPS[exercise.id]
    if comment_syntax == "line":
        outline = "// Solution outline:\n" + "".join(
            f"// {index}. {step}\n" for index, step in enumerate(steps, start=1)
        ) + "\n"
    else:
        outline = "/* Solution outline:\n" + "".join(
            f" * {index}. {step}\n" for index, step in enumerate(steps, start=1)
        ) + " */\n\n"
    lines = exercise.reference_solution.splitlines(keepends=True)
    position = 0
    while position < len(lines) and (
        not lines[position].strip() or lines[position].lstrip().startswith("#include")
    ):
        position += 1
    return "".join(lines[:position]) + outline + "".join(lines[position:])


def _personalize_identifiers(exercise: Exercise, source: str, preferences: dict) -> str:
    if preferences["identifier_style"] == "short":
        return replace_c_identifiers(source, SHORT_IDENTIFIER_MAPS[exercise.id])
    if preferences["identifier_language"] == "romanian":
        return replace_c_identifiers(source, ROMANIAN_IDENTIFIER_MAPS[exercise.id])
    return source


def reference_answer(
    exercise: Exercise,
    *,
    style: str = "auto",
    source: str = "",
    profile: object = None,
) -> dict[str, object]:
    """Only return a complete answer after an explicit solution request."""
    choices = available_styles(exercise)
    if style not in {"auto", *choices}:
        raise ValueError(f"Style '{style}' is unavailable for this exercise. Choices: {choices}.")

    normalised_profile = normalise_style_profile(profile)
    contains_comments = "//" in source or "/*" in source
    selected = style
    note = "These are curated style presets, not a model of the student's personal coding style."
    if style == "auto":
        selected = (
            "personalized_c"
            if normalised_profile["samples"] > 0
            else "commented_c" if contains_comments else "classic_c"
        )

    personalization = {
        "applied": False,
        "samples": normalised_profile["samples"],
        "preferences": normalised_profile["preferences"],
        "origins": normalised_profile["origins"],
    }
    if selected == "personalized_c":
        preferences = normalised_profile["preferences"]
        base = (
            _commented_solution(
                exercise,
                str(preferences["comment_syntax"]),
                str(preferences["comment_placement"]),
            )
            if preferences["comment_style"] == "explanatory"
            else exercise.reference_solution
        )
        base = _personalize_identifiers(exercise, base, preferences)
        code, normalised_profile = apply_c_style(base, normalised_profile)
        personalization = {
            "applied": normalised_profile["samples"] > 0,
            "samples": normalised_profile["samples"],
            "preferences": normalised_profile["preferences"],
            "origins": normalised_profile["origins"],
        }
        note = (
            "Applied the active local profile's aggregate style preferences to an "
            "authored, tested reference; no learner source or comment text was copied."
            if personalization["applied"]
            else "This profile has no learned examples yet; showing the safe classic C defaults."
        )
    elif selected == "pclp1_classic":
        preset_profile = _pclp1_classic_profile()
        base = _commented_solution(exercise, "line", "inline")
        base = replace_c_identifiers(base, SHORT_IDENTIFIER_MAPS[exercise.id])
        code, _ = apply_c_style(base, preset_profile)
        note = (
            "Applied an author-defined, portable C17 preset based on recurring PCLP1 "
            "course conventions; no private source text was copied."
        )
    elif selected == "commented_c":
        code = _commented_solution(exercise)
    else:
        code = exercise.reference_solution

    return {
        "course": "PCLP1",
        "style": selected,
        "compiler": "gcc -std=c17",
        "source": code,
        "explanation": list(SOLUTION_STEPS[exercise.id]),
        "note": note,
        "personalization": personalization,
    }
