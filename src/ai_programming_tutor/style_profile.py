"""Privacy-preserving C style preferences learned from explicit examples."""

from __future__ import annotations

import math
import re
from typing import Any, Callable, Iterable


PROFILE_SCHEMA_VERSION = "0.3"
MAX_SAMPLES = 100

_COUNT_KEYS = (
    "function_brace_same_line",
    "function_brace_next_line",
    "control_brace_same_line",
    "control_brace_next_line",
    "increment_prefix",
    "increment_postfix",
    "increment_assignment",
    "increment_compound",
    "indent_2",
    "indent_4",
    "comments_minimal",
    "comments_explanatory",
    "comment_line",
    "comment_block",
    "comment_inline",
    "comment_outline",
    "main_empty",
    "main_void",
    "identifiers_short",
    "identifiers_descriptive",
    "identifier_language_ro",
    "identifier_language_en",
    "identifier_case_snake",
    "identifier_case_camel",
    "declarations_grouped",
    "declarations_separate",
    "loop_variable_predeclared",
    "loop_variable_inline",
    "control_spacing_compact",
    "control_spacing_spaced",
)

_DIMENSIONS: dict[str, tuple[tuple[tuple[str, str | int], ...], str | int]] = {
    "function_brace_style": (
        (("function_brace_same_line", "same_line"), ("function_brace_next_line", "next_line")),
        "same_line",
    ),
    "control_brace_style": (
        (("control_brace_same_line", "same_line"), ("control_brace_next_line", "next_line")),
        "same_line",
    ),
    "increment_style": (
        (
            ("increment_prefix", "prefix"),
            ("increment_postfix", "postfix"),
            ("increment_assignment", "assignment"),
            ("increment_compound", "compound"),
        ),
        "postfix",
    ),
    "indent_width": ((("indent_2", 2), ("indent_4", 4)), 4),
    "comment_style": (
        (("comments_minimal", "minimal"), ("comments_explanatory", "explanatory")),
        "minimal",
    ),
    "comment_syntax": ((("comment_line", "line"), ("comment_block", "block")), "block"),
    "comment_placement": (
        (("comment_inline", "inline"), ("comment_outline", "outline")),
        "outline",
    ),
    "main_signature": ((("main_empty", "empty"), ("main_void", "void")), "void"),
    "identifier_style": (
        (("identifiers_short", "short"), ("identifiers_descriptive", "descriptive")),
        "descriptive",
    ),
    "identifier_language": (
        (("identifier_language_ro", "romanian"), ("identifier_language_en", "english")),
        "english",
    ),
    "identifier_case": (
        (("identifier_case_snake", "snake"), ("identifier_case_camel", "camel")),
        "snake",
    ),
    "declaration_style": (
        (("declarations_grouped", "grouped"), ("declarations_separate", "separate")),
        "separate",
    ),
    "loop_variable_style": (
        (("loop_variable_predeclared", "predeclared"), ("loop_variable_inline", "inline")),
        "inline",
    ),
    "control_spacing": (
        (("control_spacing_compact", "compact"), ("control_spacing_spaced", "spaced")),
        "compact",
    ),
}

_PROTECTED_TEXT = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
)
_CPP_MARKERS = (
    ("iostream", re.compile(r"#\s*include\s*<\s*(?:iostream|fstream)\s*>")),
    ("cin", re.compile(r"\b(?:std\s*::\s*)?cin\s*>>")),
    ("cout", re.compile(r"\b(?:std\s*::\s*)?cout\s*<<")),
    ("ifstream", re.compile(r"\b(?:std\s*::\s*)?ifstream\b")),
    ("ofstream", re.compile(r"\b(?:std\s*::\s*)?ofstream\b")),
    ("std::", re.compile(r"\bstd\s*::")),
    ("namespace", re.compile(r"\busing\s+namespace\s+std\b")),
)
_CONTROL_HEADER = re.compile(r"^(?:}\s*)?(?:if|else|for|while|switch|do)\b")
_CONTROL_OPEN = re.compile(r"\b(?:if|for|while|switch)\s*\(")
_FOR_INLINE = re.compile(
    r"\bfor\s*\(\s*(?:(?:const|signed|unsigned)\s+)*int\s+[A-Za-z_]\w*\s*="
)
_FOR_PREDECLARED = re.compile(r"\bfor\s*\(\s*[A-Za-z_]\w*\s*=")
_TYPE = (
    r"(?:(?:const|signed|unsigned)\s+)*(?:long\s+long|long|short|int|char|float|double|size_t)"
)
_DECLARATION = re.compile(rf"\b{_TYPE}\s+([^;()]+);")
_DECLARATION_LINE = re.compile(
    rf"^(?P<indent>[ \t]*)(?P<type>{_TYPE})[ \t]+"
    r"(?P<declarators>[^;()]+);[ \t]*$"
)
_FUNCTION_OPEN = re.compile(
    r"(?m)^(?![ \t]*(?:if|else|for|while|switch|do)\b)"
    r"[ \t]*[^\n;{}]*\([^;\n{}]*\)[ \t]*\{"
)
_FUNCTION_DEFINITION = re.compile(
    rf"(?m)^[ \t]*(?:void|{_TYPE})[ \t*]+(?P<name>[A-Za-z_]\w*)"
    r"\s*\((?P<parameters>[^;{}]*)\)\s*(?:\n[ \t]*)?\{"
)
_UPDATE = re.compile(
    r"(?:(?P<prefix_op>\+\+|--)\s*(?P<prefix_name>\b[A-Za-z_]\w*)"
    r"|(?P<postfix_name>\b[A-Za-z_]\w*)\s*(?P<postfix_op>\+\+|--)"
    r"|(?P<compound_name>\b[A-Za-z_]\w*)\s*(?P<compound_op>\+=|-=)\s*1\b"
    r"|(?P<assignment_name>\b[A-Za-z_]\w*)\s*=\s*(?P=assignment_name)\s*"
    r"(?P<assignment_op>[+-])\s*1\b)(?=\s*(?:;|\)))"
)
_ROMANIAN_TOKENS = {
    "afisare",
    "afiseaza",
    "citeste",
    "citire",
    "coloana",
    "coloane",
    "comanda",
    "cuvant",
    "element",
    "elemente",
    "frecventa",
    "indice",
    "linie",
    "linii",
    "lungime",
    "maxim",
    "minim",
    "numar",
    "palindrom",
    "pozitie",
    "sterse",
    "suma",
    "valoare",
    "valori",
}
_ENGLISH_TOKENS = {
    "character",
    "column",
    "command",
    "count",
    "frequency",
    "identifier",
    "index",
    "item",
    "length",
    "maximum",
    "minimum",
    "palindrome",
    "position",
    "read",
    "removed",
    "row",
    "target",
    "total",
    "value",
    "values",
    "word",
}


def _safe_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return max(0, min(value, 10_000))


def _resolve(
    counts: dict[str, int], choices: tuple[tuple[str, str | int], ...], default: str | int
) -> tuple[str | int, str]:
    maximum = max((counts[key] for key, _ in choices), default=0)
    if maximum == 0:
        return default, "default"
    winners = [value for key, value in choices if counts[key] == maximum]
    if len(winners) == 1:
        return winners[0], "learned"
    return (default if default in winners else winners[0]), "mixed"


def normalise_style_profile(value: object = None) -> dict[str, Any]:
    """Return a bounded profile and derive every preference from aggregate counts."""
    raw = value if isinstance(value, dict) else {}
    if raw.get("schema_version") not in {None, "0.2", PROFILE_SCHEMA_VERSION}:
        raw = {}
    raw_counts = raw.get("counts")
    raw_counts = raw_counts if isinstance(raw_counts, dict) else {}
    counts = {key: _safe_count(raw_counts.get(key)) for key in _COUNT_KEYS}
    preferences: dict[str, str | int] = {}
    origins: dict[str, str] = {}
    for dimension, (choices, default) in _DIMENSIONS.items():
        preference, origin = _resolve(counts, choices, default)
        preferences[dimension] = preference
        origins[dimension] = origin
    function_brace = preferences["function_brace_style"]
    control_brace = preferences["control_brace_style"]
    preferences["brace_style"] = function_brace if function_brace == control_brace else "mixed"
    samples = min(_safe_count(raw.get("samples")), MAX_SAMPLES) if any(counts.values()) else 0
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "samples": samples,
        "counts": counts,
        "preferences": preferences,
        "origins": origins,
    }


def empty_style_profile() -> dict[str, Any]:
    return normalise_style_profile()


def _mask_protected(source: str) -> str:
    def mask(match: re.Match[str]) -> str:
        return "".join("\n" if character == "\n" else " " for character in match.group())

    return _PROTECTED_TEXT.sub(mask, source)


def detect_cpp_features(source: str) -> tuple[str, ...]:
    """Detect representative C++ syntax while ignoring comments and literals."""
    code = _mask_protected(source)
    return tuple(label for label, expression in _CPP_MARKERS if expression.search(code))


def _brace_context(header: str) -> str | None:
    stripped = header.strip()
    if _CONTROL_HEADER.match(stripped):
        return "control"
    if ")" in stripped and not stripped.endswith(";"):
        return "function"
    return None


def _matching_delimiter(code: str, opening: int, left: str, right: str) -> int | None:
    depth = 0
    for position in range(opening, len(code)):
        if code[position] == left:
            depth += 1
        elif code[position] == right:
            depth -= 1
            if depth == 0:
                return position
    return None


def _control_parentheses(source: str, code: str) -> Iterable[tuple[int, int]]:
    for match in _CONTROL_OPEN.finditer(code):
        opening = code.find("(", match.start(), match.end())
        closing = _matching_delimiter(code, opening, "(", ")")
        if closing is not None and "\n" not in source[opening : closing + 1]:
            yield opening, closing


def _split_declarators(value: str) -> list[str]:
    result: list[str] = []
    start = 0
    depth = 0
    for position, character in enumerate(value):
        if character in "([{":
            depth += 1
        elif character in ")]}" and depth:
            depth -= 1
        elif character == "," and depth == 0:
            result.append(value[start:position])
            start = position + 1
    result.append(value[start:])
    return result


def _declared_identifiers(code: str) -> list[str]:
    identifiers: list[str] = []
    for match in _DECLARATION.finditer(code):
        for declarator in _split_declarators(match.group(1)):
            left = declarator.split("=", 1)[0].strip()
            name = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\]\s*)*$", left)
            if name and name.group(1) != "main":
                identifiers.append(name.group(1))
    return identifiers


def _identifier_tokens(identifier: str) -> list[str]:
    expanded = re.sub(r"([a-z])([A-Z])", r"\1_\2", identifier)
    return [token.lower() for token in expanded.split("_") if token]


def _identifier_case(identifier: str) -> str | None:
    name = identifier.strip("_")
    if "_" in name and len([part for part in name.split("_") if part]) >= 2:
        return "snake"
    if re.search(r"[a-z0-9][A-Z]", name):
        return "camel"
    return None


def _function_identifiers(code: str) -> list[str]:
    identifiers: list[str] = []
    type_words = {
        "char", "const", "double", "float", "int", "long", "short",
        "signed", "size_t", "unsigned", "void",
    }
    for match in _FUNCTION_DEFINITION.finditer(code):
        if match.group("name") != "main":
            identifiers.append(match.group("name"))
        parameters = match.group("parameters").strip()
        if not parameters or parameters == "void":
            continue
        for parameter in _split_declarators(parameters):
            name = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\]\s*)*$", parameter)
            if name and name.group(1) not in type_words:
                identifiers.append(name.group(1))
    return identifiers


def _style_identifiers(code: str) -> list[str]:
    return list(dict.fromkeys((*_declared_identifiers(code), *_function_identifiers(code))))


def _update_style(match: re.Match[str]) -> tuple[str, str, str]:
    if match.group("prefix_name"):
        return "prefix", match.group("prefix_name"), match.group("prefix_op")
    if match.group("postfix_name"):
        return "postfix", match.group("postfix_name"), match.group("postfix_op")
    if match.group("compound_name"):
        return "compound", match.group("compound_name"), match.group("compound_op")
    return "assignment", match.group("assignment_name"), match.group("assignment_op")


def analyse_c_style(source: str) -> dict[str, Any]:
    """Extract aggregate style observations only; no identifiers or source are returned."""
    code = _mask_protected(source)
    source_lines = source.splitlines()
    code_lines = code.splitlines()
    brace_counts = {
        "function_same_line": 0,
        "function_next_line": 0,
        "control_same_line": 0,
        "control_next_line": 0,
    }
    indent_lengths: list[int] = []
    nonempty_lines = 0
    previous_header = ""
    for source_line, code_line in zip(source_lines, code_lines):
        stripped = code_line.strip()
        if not stripped:
            continue
        nonempty_lines += 1
        leading = len(source_line) - len(source_line.lstrip(" "))
        if leading and not source_line.startswith("\t"):
            indent_lengths.append(leading)
        if stripped == "{":
            context = _brace_context(previous_header)
            if context:
                brace_counts[f"{context}_next_line"] += 1
        elif "{" in stripped and not re.search(r"=\s*\{", stripped):
            header = stripped[: stripped.find("{")]
            context = _brace_context(header)
            if context:
                brace_counts[f"{context}_same_line"] += 1
        previous_header = stripped

    update_counts = {style: 0 for style in ("prefix", "postfix", "assignment", "compound")}
    for match in _UPDATE.finditer(code):
        update_counts[_update_style(match)[0]] += 1

    protected = list(_PROTECTED_TEXT.finditer(source))
    comments = [match for match in protected if match.group().startswith(("//", "/*"))]
    line_comments = sum(match.group().startswith("//") for match in comments)
    block_comments = sum(match.group().startswith("/*") for match in comments)
    inline_comments = 0
    outline_comments = 0
    for match in comments:
        before = code[: match.start()]
        if before.count("{") > before.count("}"):
            inline_comments += 1
        else:
            outline_comments += 1

    inline_loops = len(_FOR_INLINE.findall(code))
    predeclared_loops = len(_FOR_PREDECLARED.findall(code))
    compact_controls = 0
    spaced_controls = 0
    for opening, closing in _control_parentheses(source, code):
        left_space = source[opening + 1 : opening + 2] in {" ", "\t"}
        right_space = source[closing - 1 : closing] in {" ", "\t"}
        if left_space and right_space:
            spaced_controls += 1
        else:
            compact_controls += 1

    identifiers = _declared_identifiers(code)
    short_identifiers = sum(len(identifier) <= 3 for identifier in identifiers)
    descriptive_identifiers = len(identifiers) - short_identifiers
    romanian_tokens = 0
    english_tokens = 0
    for identifier in identifiers:
        if len(identifier) <= 3:
            continue
        tokens = _identifier_tokens(identifier)
        romanian_tokens += sum(token in _ROMANIAN_TOKENS for token in tokens)
        english_tokens += sum(token in _ENGLISH_TOKENS for token in tokens)

    snake_identifiers = sum(_identifier_case(identifier) == "snake" for identifier in identifiers)
    camel_identifiers = sum(_identifier_case(identifier) == "camel" for identifier in identifiers)
    grouped_declarators = 0
    separate_declarations = 0
    for line in code_lines:
        declaration = _DECLARATION_LINE.match(line)
        if not declaration:
            continue
        declarators = _split_declarators(declaration.group("declarators"))
        if len(declarators) > 1:
            grouped_declarators += len(declarators)
        else:
            separate_declarations += 1

    evidence = {
        **brace_counts,
        "prefix_updates": update_counts["prefix"],
        "postfix_updates": update_counts["postfix"],
        "assignment_updates": update_counts["assignment"],
        "compound_updates": update_counts["compound"],
        "line_comments": line_comments,
        "block_comments": block_comments,
        "inline_comments": inline_comments,
        "outline_comments": outline_comments,
        "inline_loop_variables": inline_loops,
        "predeclared_loop_variables": predeclared_loops,
        "compact_controls": compact_controls,
        "spaced_controls": spaced_controls,
        "short_identifiers": short_identifiers,
        "descriptive_identifiers": descriptive_identifiers,
        "romanian_identifier_tokens": romanian_tokens,
        "english_identifier_tokens": english_tokens,
        "snake_identifiers": snake_identifiers,
        "camel_identifiers": camel_identifiers,
        "grouped_declarators": grouped_declarators,
        "separate_declarations": separate_declarations,
        "code_lines": nonempty_lines,
    }
    observation: dict[str, Any] = {"evidence": evidence}

    for context in ("function", "control"):
        same = brace_counts[f"{context}_same_line"]
        next_line = brace_counts[f"{context}_next_line"]
        if same != next_line:
            observation[f"{context}_brace_style"] = (
                "same_line" if same > next_line else "next_line"
            )
        elif same:
            observation[f"{context}_brace_style"] = "mixed"
    maximum_update = max(update_counts.values(), default=0)
    update_winners = [style for style, count in update_counts.items() if count == maximum_update]
    if maximum_update and len(update_winners) == 1:
        observation["increment_style"] = update_winners[0]
    elif maximum_update:
        observation["increment_style"] = "mixed"
    if indent_lengths:
        common_indent = math.gcd(*indent_lengths)
        observation["indent_width"] = 2 if common_indent == 2 else 4
    if nonempty_lines:
        observation["comment_style"] = "explanatory" if len(comments) >= 2 else "minimal"
    if comments:
        observation["comment_syntax"] = "line" if line_comments > block_comments else "block"
        observation["comment_placement"] = (
            "inline" if inline_comments >= outline_comments else "outline"
        )
    if re.search(r"\bint\s+main\s*\(\s*void\s*\)", code):
        observation["main_signature"] = "void"
    elif re.search(r"\bint\s+main\s*\(\s*\)", code):
        observation["main_signature"] = "empty"
    if short_identifiers != descriptive_identifiers:
        observation["identifier_style"] = (
            "short" if short_identifiers > descriptive_identifiers else "descriptive"
        )
    if romanian_tokens != english_tokens and (romanian_tokens or english_tokens):
        observation["identifier_language"] = (
            "romanian" if romanian_tokens > english_tokens else "english"
        )
    if snake_identifiers != camel_identifiers and (snake_identifiers or camel_identifiers):
        observation["identifier_case"] = (
            "snake" if snake_identifiers > camel_identifiers else "camel"
        )
    elif snake_identifiers:
        observation["identifier_case"] = "mixed"
    if grouped_declarators or separate_declarations >= 2:
        if grouped_declarators != separate_declarations:
            observation["declaration_style"] = (
                "grouped" if grouped_declarators > separate_declarations else "separate"
            )
        elif grouped_declarators:
            observation["declaration_style"] = "mixed"
    if inline_loops != predeclared_loops:
        observation["loop_variable_style"] = (
            "inline" if inline_loops > predeclared_loops else "predeclared"
        )
    if compact_controls != spaced_controls:
        observation["control_spacing"] = (
            "compact" if compact_controls > spaced_controls else "spaced"
        )
    return observation


def learn_c_style(source: str, previous: object = None) -> dict[str, Any]:
    """Merge one explicitly submitted C example into an aggregate profile."""
    profile = normalise_style_profile(previous)
    cpp = detect_cpp_features(source)
    if cpp:
        return {
            "accepted": False,
            "reason": "cpp_ignored",
            "cpp_features": list(cpp),
            "profile": profile,
        }

    observation = analyse_c_style(source)
    vote_keys = {
        (dimension, value): count_key
        for dimension, (choices, _) in _DIMENSIONS.items()
        for count_key, value in choices
    }
    counts = dict(profile["counts"])
    learned = False
    for (dimension, value), count_key in vote_keys.items():
        if observation.get(dimension) == value:
            counts[count_key] = min(counts[count_key] + 1, 10_000)
            learned = True
    if not learned:
        return {
            "accepted": False,
            "reason": "not_enough_style_evidence",
            "cpp_features": [],
            "observation": observation,
            "profile": profile,
        }
    updated = normalise_style_profile(
        {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "samples": min(profile["samples"] + 1, MAX_SAMPLES),
            "counts": counts,
        }
    )
    return {
        "accepted": True,
        "reason": "learned",
        "cpp_features": [],
        "observation": observation,
        "profile": updated,
    }


def _map_unprotected(source: str, transform: Callable[[str], str]) -> str:
    parts: list[str] = []
    position = 0
    for match in _PROTECTED_TEXT.finditer(source):
        parts.append(transform(source[position : match.start()]))
        parts.append(match.group())
        position = match.end()
    parts.append(transform(source[position:]))
    return "".join(parts)


def replace_c_identifiers(source: str, replacements: dict[str, str]) -> str:
    """Replace an authored set of C identifiers without touching strings or comments."""
    if not replacements:
        return source
    names = sorted(replacements, key=len, reverse=True)
    expression = re.compile(r"\b(?:" + "|".join(map(re.escape, names)) + r")\b")
    return _map_unprotected(
        source, lambda code: expression.sub(lambda match: replacements[match.group()], code)
    )


def _convert_updates(source: str, style: str) -> str:
    def replacement(match: re.Match[str]) -> str:
        _, name, operator = _update_style(match)
        decrement = "-" in operator
        sign = "-" if decrement else "+"
        if style == "prefix":
            return ("--" if decrement else "++") + name
        if style == "assignment":
            return f"{name} = {name} {sign} 1"
        if style == "compound":
            return f"{name} {sign}= 1"
        return name + ("--" if decrement else "++")

    return _map_unprotected(source, lambda code: _UPDATE.sub(replacement, code))


def _snake_case(identifier: str) -> str:
    first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", identifier)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first).lower()


def _camel_case(identifier: str) -> str:
    parts = [part for part in identifier.split("_") if part]
    if len(parts) < 2:
        return identifier
    return parts[0].lower() + "".join(part[:1].upper() + part[1:].lower() for part in parts[1:])


def _convert_identifier_case(source: str, style: str) -> str:
    identifiers = _style_identifiers(_mask_protected(source))
    replacements: dict[str, str] = {}
    for identifier in identifiers:
        if identifier.startswith("_") or identifier.isupper():
            continue
        replacement = _camel_case(identifier) if style == "camel" else _snake_case(identifier)
        if replacement != identifier and re.fullmatch(r"[A-Za-z_]\w*", replacement):
            replacements[identifier] = replacement
    return replace_c_identifiers(source, replacements)


def _declaration_parts(line: str) -> tuple[str, str, list[str], str] | None:
    ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
    content = line[: -len(ending)] if ending else line
    match = _DECLARATION_LINE.match(content)
    if not match:
        return None
    return (
        match.group("indent"),
        match.group("type"),
        [part.strip() for part in _split_declarators(match.group("declarators"))],
        ending,
    )


def _convert_declaration_layout(source: str, style: str) -> str:
    lines = source.splitlines(keepends=True)
    if style == "separate":
        output: list[str] = []
        for line in lines:
            parsed = _declaration_parts(line)
            if not parsed or len(parsed[2]) < 2:
                output.append(line)
                continue
            indent, type_name, declarators, ending = parsed
            separator = ending or "\n"
            for index, declarator in enumerate(declarators):
                suffix = ending if index == len(declarators) - 1 else separator
                output.append(f"{indent}{type_name} {declarator};{suffix}")
        return "".join(output)

    output = []
    position = 0
    while position < len(lines):
        parsed = _declaration_parts(lines[position])
        if not parsed or len(parsed[2]) != 1:
            output.append(lines[position])
            position += 1
            continue
        indent, type_name, declarators, ending = parsed
        grouped = list(declarators)
        cursor = position + 1
        last_ending = ending
        while cursor < len(lines):
            following = _declaration_parts(lines[cursor])
            if (
                not following
                or following[0] != indent
                or following[1] != type_name
                or len(following[2]) != 1
            ):
                break
            grouped.extend(following[2])
            last_ending = following[3]
            cursor += 1
        if len(grouped) > 1:
            output.append(f"{indent}{type_name} {', '.join(grouped)};{last_ending}")
            position = cursor
        else:
            output.append(lines[position])
            position += 1
    return "".join(output)


def _convert_main_signature(source: str, style: str) -> str:
    if style == "empty":
        expression = re.compile(r"\bint\s+main\s*\(\s*void\s*\)")
        return _map_unprotected(source, lambda code: expression.sub("int main()", code))
    expression = re.compile(r"\bint\s+main\s*\(\s*\)")
    return _map_unprotected(source, lambda code: expression.sub("int main(void)", code))


def _function_spans(code: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in _FUNCTION_OPEN.finditer(code):
        opening = code.find("{", match.start(), match.end())
        closing = _matching_delimiter(code, opening, "{", "}")
        if closing is not None:
            spans.append((opening, closing))
    return spans


def _convert_loop_declarations(source: str, style: str) -> str:
    if style != "predeclared":
        return source
    result = source
    for opening, closing in reversed(_function_spans(_mask_protected(result))):
        body = result[opening + 1 : closing]
        masked_body = _mask_protected(body)
        names = list(
            dict.fromkeys(
                match.group(1)
                for match in re.finditer(
                    r"\bfor\s*\(\s*int\s+([A-Za-z_]\w*)\s*=", masked_body
                )
            )
        )
        if not names:
            continue
        transformed = _map_unprotected(
            body,
            lambda code: re.sub(
                r"\bfor(\s*\(\s*)int\s+([A-Za-z_]\w*)\s*=",
                r"for\1\2 =",
                code,
            ),
        )
        for name in names:
            escaped = re.escape(name)
            transformed = _map_unprotected(
                transformed,
                lambda code, pattern=escaped: re.sub(
                    rf"(?m)^([ \t]*)int\s+{pattern}\s*=\s*",
                    rf"\1{pattern} = ",
                    code,
                ),
            )
            transformed = _map_unprotected(
                transformed,
                lambda code, pattern=escaped: re.sub(
                    rf"(?m)^[ \t]*int\s+{pattern}\s*;[ \t]*\n?",
                    "",
                    code,
                ),
            )
        line_start = result.rfind("\n", 0, opening) + 1
        function_indent = result[line_start:opening]
        function_indent = function_indent[: len(function_indent) - len(function_indent.lstrip())]
        declaration = function_indent + "    int " + ", ".join(names) + ";"
        separator = "\n" if transformed.startswith("\n") else "\n\n"
        transformed = "\n" + declaration + separator + transformed.lstrip("\n")
        result = result[: opening + 1] + transformed + result[closing:]
    return result


def _convert_braces(source: str, function_style: str, control_style: str) -> str:
    lines = source.splitlines()
    converted: list[str] = []
    for line in lines:
        stripped = line.strip()
        indent = line[: len(line) - len(line.lstrip())]
        if stripped == "{" and converted:
            previous = converted[-1].strip()
            context = _brace_context(previous)
            desired = function_style if context == "function" else control_style
            if context and desired == "same_line":
                converted[-1] = converted[-1].rstrip() + " {"
            else:
                converted.append(line)
            continue
        if "{" in stripped and not re.search(r"=\s*\{", stripped):
            brace_position = line.find("{")
            header = line[:brace_position].rstrip()
            context = _brace_context(header)
            desired = function_style if context == "function" else control_style
            if context and desired == "next_line":
                if header.strip() == "} else":
                    converted.extend((indent + "}", indent + "else", indent + "{"))
                else:
                    converted.extend((header, indent + "{"))
                continue
        converted.append(line)
    joined = "\n".join(converted)
    if control_style == "same_line":
        joined = re.sub(r"(?m)^([ \t]*)\}\n\1else\s*\{", r"\1} else {", joined)
    return joined + ("\n" if source.endswith("\n") else "")


def _convert_control_spacing(source: str, style: str) -> str:
    code = _mask_protected(source)
    edits: list[tuple[int, int, str]] = []
    for opening, closing in _control_parentheses(source, code):
        left = opening + 1
        while left < closing and source[left] in " \t":
            left += 1
        right = closing
        while right > opening + 1 and source[right - 1] in " \t":
            right -= 1
        padding = " " if style == "spaced" else ""
        edits.extend(((opening + 1, left, padding), (right, closing, padding)))
    for start, end, replacement in sorted(edits, reverse=True):
        source = source[:start] + replacement + source[end:]
    return source


def _convert_indentation(source: str, width: int) -> str:
    if width == 4:
        return source
    output = []
    for line in source.splitlines(keepends=True):
        leading = len(line) - len(line.lstrip(" "))
        if leading >= 4:
            line = " " * ((leading // 4) * 2 + leading % 4) + line[leading:]
        output.append(line)
    return "".join(output)


def apply_c_style(source: str, profile: object) -> tuple[str, dict[str, Any]]:
    """Apply semantics-preserving style choices to an authored and tested C reference."""
    normalised = normalise_style_profile(profile)
    preferences = normalised["preferences"]
    formatted = _convert_identifier_case(source, str(preferences["identifier_case"]))
    formatted = _convert_updates(formatted, str(preferences["increment_style"]))
    formatted = _convert_main_signature(formatted, str(preferences["main_signature"]))
    formatted = _convert_loop_declarations(formatted, str(preferences["loop_variable_style"]))
    formatted = _convert_declaration_layout(formatted, str(preferences["declaration_style"]))
    formatted = _convert_control_spacing(formatted, str(preferences["control_spacing"]))
    formatted = _convert_braces(
        formatted,
        str(preferences["function_brace_style"]),
        str(preferences["control_brace_style"]),
    )
    formatted = _convert_indentation(formatted, int(preferences["indent_width"]))
    return formatted, normalised
