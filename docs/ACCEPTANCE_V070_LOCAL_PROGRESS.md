# v0.7.0 local-progress manual acceptance

Date: 2026-09-17

This record covers all three v0.7.0 feature slices. It contains only public-safe
results. No learner source, screenshot, local path, private material, filename,
identity, or browser-storage dump is included.

## Scope

The accepted slice adds profile-specific favorite exercises and optional numeric
attempt history. Saved attempts contain only a timestamp, compilation status, and
passed/total test counts. History is capped at 20 attempts per exercise and is
disabled by default.

## Automated prerequisite

The development tree passed 52/52 automated tests before manual acceptance. The
tests cover schema sanitization, bounded retention, source-free storage, profile
isolation, result summaries, deletion behavior, and strict JSON transfer.

## Manual protocol and outcome

The local Windows browser workflow passed all of the following checks:

1. Attempt history began disabled and saved no result until explicitly enabled.
2. Favorites, history settings, drafts, and numeric results remained isolated
   between Profile A and Profile B.
3. A failed compilation was shown as `compilarea a eșuat`, not as the misleading
   score `0/0`, and it did not become the best scored attempt.
4. After a fully successful attempt followed by a compilation failure, the latest
   result reported the failure while the best result remained the successful score.
5. A forced browser refresh preserved the expected profile-specific favorite,
   history setting, attempt count, latest result, best result, and optional draft.
6. Disabling history deleted every saved attempt and best/latest result for the
   active profile while retaining that profile's favorites; the result survived a
   forced refresh.
7. Clearing progress removed the active profile's favorites and attempt history.
8. Returning to the other profile confirmed that its favorite, history setting,
   and attempt count were unchanged by the deletion operations.

The compact concept/exercise view then passed a separate bilingual check:

9. Profile A showed all seven authored concept groups, with attempted and fully
   solved counts derived from the existing numeric history and public exercise tags.
10. Its tracked-exercise list contained only favorited or attempted exercises,
    marked the favorite, and reported each best numeric result and attempt count.
11. Switching from Romanian to English translated every heading, concept, and
    result label without changing any numeric value.
12. Profile B, whose progress had been cleared, showed zero favorites and attempts,
    the disabled-history explanation, and the correct empty tracked-exercise state.
13. Returning to Profile A restored the same concept and exercise view, confirming
    that the derived display remained profile-specific.
14. The expanded view remained readable in the dark theme and did not disturb the
    editor or the separately persisted draft controls.

The strict JSON transfer then passed its final bilingual and cross-profile check:

15. Exporting Profile A produced the success state without changing its one favorite
    or two numeric attempts.
16. The exported object had exactly the documented format/version, history setting,
    favorites, and attempts fields. It contained no source, compiler output, draft,
    style evidence, or personal identifier.
17. Importing that object into the empty Profile B required confirmation and replaced
    only Profile B with the expected favorite, enabled history setting, and two
    attempts.
18. Returning to Profile A showed its original progress unchanged, confirming active-
    profile isolation.
19. Clearing Profile B and disabling its history restored its zero-favorite,
    zero-attempt state without changing Profile A.
20. The empty summary, transfer controls, privacy explanation, and deletion feedback
    were correct in English as well as Romanian.

## Accepted privacy and deletion boundary

- No source code, compiler output, diagnosis, hint, style evidence, or personal
  identifier is stored in learning progress.
- Attempt retention is explicit, device-local, profile-specific, and bounded.
- Disabling history immediately deletes attempts while preserving favorites.
- Clearing progress immediately deletes both attempts and favorites for only the
  active profile.
- Accounts and server-side persistence remain outside this slice.
- Concept/exercise counts are derived in browser memory and add no storage fields.
- A displayed solved count means only that all local tests passed at least once; it
  is not a learner-mastery or official-grade claim.
- JSON transfer includes only the active profile's favorites, history setting, and
  bounded numeric attempts. Import requires confirmation and rejects extra fields.
- Import cannot alter drafts, style profiles, exam state, or the other profile.

## Result

All three v0.7.0 local-progress slices are manually accepted: profile-specific
favorites and bounded history, the derived concept/exercise view, and strict JSON
export/import. The planned local-progress sprint is complete.
