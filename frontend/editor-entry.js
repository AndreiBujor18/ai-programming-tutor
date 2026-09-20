import {closeBrackets, closeBracketsKeymap} from "@codemirror/autocomplete";
import {defaultKeymap, history, historyKeymap, indentWithTab} from "@codemirror/commands";
import {cpp} from "@codemirror/lang-cpp";
import {
  HighlightStyle,
  bracketMatching,
  defaultHighlightStyle,
  indentOnInput,
  indentUnit,
  syntaxHighlighting
} from "@codemirror/language";
import {highlightSelectionMatches, searchKeymap} from "@codemirror/search";
import {Compartment, EditorState} from "@codemirror/state";
import {
  EditorView,
  drawSelection,
  dropCursor,
  highlightActiveLine,
  highlightActiveLineGutter,
  highlightSpecialChars,
  keymap,
  lineNumbers
} from "@codemirror/view";
import {tags} from "@lezer/highlight";

const palettes = {
  light: {
    background: "#ffffff",
    foreground: "#1f2933",
    gutter: "#f3f5f7",
    gutterText: "#667784",
    activeLine: "#eef5f8",
    selection: "#add6ff",
    cursor: "#175a7e",
    keyword: "#0000ff",
    type: "#267f99",
    function: "#795e26",
    string: "#a31515",
    number: "#098658",
    comment: "#008000",
    variable: "#001080",
    operator: "#303b45",
    invalid: "#b42318"
  },
  dark: {
    background: "#1e1e1e",
    foreground: "#d4d4d4",
    gutter: "#252526",
    gutterText: "#858585",
    activeLine: "#2a2d2e",
    selection: "#264f78",
    cursor: "#aeafad",
    keyword: "#c586c0",
    type: "#4ec9b0",
    function: "#dcdcaa",
    string: "#ce9178",
    number: "#b5cea8",
    comment: "#6a9955",
    variable: "#9cdcfe",
    operator: "#d4d4d4",
    invalid: "#f48771"
  }
};

function editorTheme(name) {
  const dark = name === "dark";
  const color = palettes[dark ? "dark" : "light"];
  const chrome = EditorView.theme({
    "&": {
      height: "100%",
      color: color.foreground,
      backgroundColor: color.background,
      fontSize: "13px"
    },
    ".cm-scroller": {
      overflow: "auto",
      fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace",
      lineHeight: "1.65"
    },
    ".cm-content": {
      padding: "14px 0",
      caretColor: color.cursor
    },
    ".cm-line": {padding: "0 16px"},
    ".cm-gutters": {
      border: "none",
      borderRight: `1px solid ${dark ? "#333333" : "#e1e7eb"}`,
      backgroundColor: color.gutter,
      color: color.gutterText
    },
    ".cm-lineNumbers .cm-gutterElement": {padding: "0 10px 0 8px"},
    ".cm-activeLine": {backgroundColor: color.activeLine},
    ".cm-activeLineGutter": {
      backgroundColor: color.activeLine,
      color: color.foreground
    },
    ".cm-cursor, .cm-dropCursor": {borderLeftColor: color.cursor},
    "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection": {
      backgroundColor: color.selection
    },
    ".cm-matchingBracket": {
      backgroundColor: dark ? "#3b514d" : "#d9edf2",
      outline: `1px solid ${dark ? "#678a80" : "#70a7b6"}`
    },
    ".cm-searchMatch": {backgroundColor: dark ? "#515c6a" : "#cce8ff"},
    ".cm-searchMatch.cm-searchMatch-selected": {
      backgroundColor: dark ? "#6a5540" : "#f5d98b"
    },
    ".cm-panels": {
      backgroundColor: color.gutter,
      color: color.foreground
    },
    ".cm-panels.cm-panels-top": {borderBottom: "1px solid #60717d"},
    ".cm-textfield": {
      border: `1px solid ${dark ? "#596b77" : "#9eacb6"}`,
      backgroundColor: color.background,
      color: color.foreground
    },
    ".cm-button": {
      border: `1px solid ${dark ? "#596b77" : "#9eacb6"}`,
      backgroundImage: "none",
      backgroundColor: color.gutter,
      color: color.foreground
    }
  }, {dark});

  const highlighting = HighlightStyle.define([
    {tag: [tags.keyword, tags.controlKeyword, tags.operatorKeyword], color: color.keyword},
    {tag: [tags.typeName, tags.className, tags.namespace], color: color.type},
    {tag: [tags.function(tags.variableName), tags.definition(tags.function(tags.variableName))], color: color.function},
    {tag: [tags.string, tags.character, tags.special(tags.string)], color: color.string},
    {tag: [tags.number, tags.bool, tags.null], color: color.number},
    {tag: [tags.comment, tags.lineComment, tags.blockComment], color: color.comment, fontStyle: "italic"},
    {tag: [tags.macroName, tags.meta, tags.processingInstruction], color: color.keyword},
    {tag: [tags.variableName, tags.propertyName], color: color.variable},
    {tag: [tags.operator, tags.punctuation], color: color.operator},
    {tag: tags.invalid, color: color.invalid, textDecoration: "underline"}
  ]);
  return [chrome, syntaxHighlighting(highlighting)];
}

function normalizedIndentSize(value) {
  return value === 2 ? 2 : 4;
}

const editorSetup = [
  lineNumbers(),
  highlightActiveLineGutter(),
  highlightSpecialChars(),
  history(),
  drawSelection(),
  dropCursor(),
  indentOnInput(),
  syntaxHighlighting(defaultHighlightStyle, {fallback: true}),
  bracketMatching(),
  closeBrackets(),
  highlightActiveLine(),
  highlightSelectionMatches(),
  keymap.of([
    indentWithTab,
    ...closeBracketsKeymap,
    ...defaultKeymap,
    ...searchKeymap,
    ...historyKeymap
  ])
];

function create(options) {
  const parent = options?.parent;
  const textarea = options?.textarea;
  if (!parent || !textarea) throw new Error("Code editor host and fallback textarea are required.");

  let themeName = options.theme === "dark" ? "dark" : "light";
  let indentSize = normalizedIndentSize(options.indentSize);
  let programmaticChange = false;
  const themeCompartment = new Compartment();
  const indentCompartment = new Compartment();
  const nonce = document.querySelector('meta[name="aptutor-csp-nonce"]')?.content || "";
  const onChange = typeof options.onChange === "function" ? options.onChange : () => {};
  const languageSupport = cpp();
  const contentAttributes = EditorView.contentAttributes.of({
    "aria-labelledby": options.labelledBy || "editor-heading",
    "aria-describedby": options.describedBy || "editor-help",
    "aria-multiline": "true",
    "aria-roledescription": "code editor",
    spellcheck: "false",
    autocapitalize: "off",
    autocomplete: "off",
    autocorrect: "off"
  });
  const changeListener = EditorView.updateListener.of((update) => {
    if (!update.docChanged) return;
    const source = update.state.doc.toString();
    textarea.value = source;
    if (!programmaticChange) onChange(source);
  });

  function extensions() {
    const configured = [
      editorSetup,
      languageSupport,
      themeCompartment.of(editorTheme(themeName)),
      indentCompartment.of([
        EditorState.tabSize.of(indentSize),
        indentUnit.of(" ".repeat(indentSize))
      ]),
      contentAttributes,
      changeListener
    ];
    if (nonce) configured.push(EditorView.cspNonce.of(nonce));
    return configured;
  }

  const originallyHidden = parent.hidden;
  parent.hidden = false;
  let view;
  try {
    view = new EditorView({
      parent,
      state: EditorState.create({doc: textarea.value, extensions: extensions()})
    });
  } catch (error) {
    parent.replaceChildren();
    parent.hidden = originallyHidden;
    throw error;
  }
  textarea.hidden = true;
  parent.dataset.enhanced = "true";

  return {
    getValue() {
      return view.state.doc.toString();
    },
    setValue(value) {
      const source = typeof value === "string" ? value : String(value ?? "");
      if (source === view.state.doc.toString()) {
        textarea.value = source;
        return;
      }
      programmaticChange = true;
      try {
        view.setState(EditorState.create({doc: source, extensions: extensions()}));
        textarea.value = source;
      } finally {
        programmaticChange = false;
      }
    },
    setTheme(value) {
      const next = value === "dark" ? "dark" : "light";
      if (next === themeName) return;
      themeName = next;
      view.dispatch({effects: themeCompartment.reconfigure(editorTheme(themeName))});
    },
    setIndentSize(value) {
      const next = normalizedIndentSize(value);
      if (next === indentSize) return;
      indentSize = next;
      view.dispatch({effects: indentCompartment.reconfigure([
        EditorState.tabSize.of(indentSize),
        indentUnit.of(" ".repeat(indentSize))
      ])});
    },
    focus() {
      view.focus();
    },
    destroy() {
      view.destroy();
      parent.replaceChildren();
      delete parent.dataset.enhanced;
      parent.hidden = originallyHidden;
      textarea.hidden = false;
    }
  };
}

window.APT_CODE_EDITOR = Object.freeze({create});
