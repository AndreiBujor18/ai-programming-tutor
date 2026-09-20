# v0.9.0 editor and workspace manual acceptance

Date: 2026-09-21

This record covers the focused local Windows acceptance pass for the v0.9.0
browser-interface refresh. It contains only public-safe outcomes. No learner source,
screenshot, browser-storage dump, private material, identity, or local path is
included.

## Scope

The accepted release replaces the plain learner editing surface with a locally
bundled, C-aware CodeMirror 6 surface and reorganizes the browser into Exercises, Practice
exam, and Progress modes. The exercise requirement and editor share the primary
desktop workspace, while style settings and the complete solution use progressive
disclosure. Existing local profiles, drafts, progress, exam state, language, theme,
and execution boundaries remain unchanged.

## Automated prerequisite

The release tree passed 69/69 automated tests before final manual acceptance. The
suite covers editor fallback and state synchronization, the three workspace modes,
profile switching inside the progress view, active-exam navigation and timer status,
Romanian/English transitions, all reference and generated solution styles, and the
existing runner, privacy, file-contract, and progress regressions. The committed
editor bundle also rebuilt byte-for-byte from its source configuration.

## Manual protocol and outcome

The local Windows browser workflow passed all of the following checks:

1. The C editor displayed line numbers and syntax highlighting without obscuring or
   changing the learner source.
2. In Exercises mode, the selected requirement appeared beside the editor on a full
   desktop window. Draft controls and the Run tests action remained directly below
   the editor.
3. The style profile and complete solution were collapsed by default and could be
   recognized without occupying the primary coding workspace.
4. Practice exam mode displayed its timer, estimated score, task list, and rubric
   above the same requirement/editor workspace. A completed session retained its
   frozen time and review state.
5. Progress mode displayed its own centered summary and retained access to the
   active Profile A/Profile B selector.
6. The complete interface remained readable and correctly aligned in the dark
   theme and Romanian locale.
7. The light theme and English locale rendered correctly without losing the active
   exercise or workspace state.
8. At approximately half a desktop window, the problem and editor stacked into a
   readable single-column layout without horizontal overlap.

## Accepted privacy and delivery boundary

- CodeMirror and its themes are bundled locally; the browser loads no editor code or
  styles from a remote CDN.
- The strict content-security policy remains in force. Generated editor styles use
  the page nonce rather than an `unsafe-inline` exception.
- Style profiles retain bounded aggregate preferences only. Existing optional raw
  drafts remain device-local and profile/exercise-specific.
- Numeric progress, exam persistence, and JSON transfer retain their accepted
  source-free schemas.
- Local execution remains opt-in and restricted to trusted localhost use. The
  interface refresh does not create a public sandbox or upload surface.

## Result

The complete v0.9.0 editor and workspace refresh is manually accepted: both themes,
both locales, full and half-width desktop layouts, the three top-level modes, and the
primary coding workflow all behave as intended.
