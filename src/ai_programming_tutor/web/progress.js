"use strict";

// Pure helpers for device-local learning progress. Stored attempts deliberately
// exclude source code, compiler output, diagnoses, hints, and profile traits.
window.APT_PROGRESS = (() => {
  const SCHEMA_VERSION = "0.1";
  const TRANSFER_FORMAT = "ai-programming-tutor-progress";
  const TRANSFER_SCHEMA_VERSION = "0.1";
  const MAX_ATTEMPTS_PER_EXERCISE = 20;
  const MAX_TESTS_PER_EXERCISE = 100;
  const MAX_FUTURE_SKEW_MS = 24 * 60 * 60 * 1000;

  function blank() {
    return {schema_version: SCHEMA_VERSION, favorites: [], attempts: {}};
  }

  function exerciseSet(exerciseIds) {
    return new Set(Array.isArray(exerciseIds)
      ? exerciseIds.filter((id) => typeof id === "string" && id.length > 0)
      : []);
  }

  function sanitiseAttempt(value, now) {
    if (!value || typeof value !== "object") return null;
    const at = value.at;
    const passed = value.passed;
    const total = value.total;
    if (!Number.isInteger(at) || at <= 0 || at > now + MAX_FUTURE_SKEW_MS ||
        !Number.isInteger(passed) || !Number.isInteger(total) ||
        total < 0 || total > MAX_TESTS_PER_EXERCISE || passed < 0 || passed > total ||
        typeof value.compiled !== "boolean") return null;
    return {at, passed, total, compiled: value.compiled};
  }

  function sanitise(value, exerciseIds, now = Date.now()) {
    const known = exerciseSet(exerciseIds);
    if (!value || typeof value !== "object" || value.schema_version !== SCHEMA_VERSION) {
      return blank();
    }
    const favorites = [];
    const seen = new Set();
    if (Array.isArray(value.favorites)) {
      for (const id of value.favorites) {
        if (known.has(id) && !seen.has(id)) {
          favorites.push(id);
          seen.add(id);
        }
      }
    }
    const attempts = {};
    if (value.attempts && typeof value.attempts === "object" && !Array.isArray(value.attempts)) {
      for (const id of known) {
        if (!Array.isArray(value.attempts[id])) continue;
        const valid = value.attempts[id]
          .map((attempt) => sanitiseAttempt(attempt, now))
          .filter(Boolean)
          .sort((left, right) => left.at - right.at)
          .slice(-MAX_ATTEMPTS_PER_EXERCISE);
        if (valid.length) attempts[id] = valid;
      }
    }
    return {schema_version: SCHEMA_VERSION, favorites, attempts};
  }

  function toggleFavorite(value, exerciseId, exerciseIds) {
    const progress = sanitise(value, exerciseIds);
    if (!exerciseSet(exerciseIds).has(exerciseId)) return progress;
    const current = new Set(progress.favorites);
    if (current.has(exerciseId)) current.delete(exerciseId);
    else current.add(exerciseId);
    progress.favorites = [...current];
    return progress;
  }

  function recordAttempt(value, exerciseId, evaluation, exerciseIds, at = Date.now()) {
    const progress = sanitise(value, exerciseIds, at);
    if (!exerciseSet(exerciseIds).has(exerciseId) || !evaluation || typeof evaluation !== "object") {
      return progress;
    }
    const attempt = sanitiseAttempt({
      at,
      passed: evaluation.passed_count,
      total: evaluation.total_count,
      compiled: Boolean(evaluation.compilation?.succeeded)
    }, at);
    if (!attempt) return progress;
    const history = [...(progress.attempts[exerciseId] || []), attempt]
      .slice(-MAX_ATTEMPTS_PER_EXERCISE);
    progress.attempts[exerciseId] = history;
    return progress;
  }

  function clearAttempts(value, exerciseIds) {
    const progress = sanitise(value, exerciseIds);
    progress.attempts = {};
    return progress;
  }

  function betterAttempt(left, right) {
    const leftRatio = left.total > 0 ? left.passed / left.total : -1;
    const rightRatio = right.total > 0 ? right.passed / right.total : -1;
    if (leftRatio !== rightRatio) return leftRatio > rightRatio ? left : right;
    if (left.passed !== right.passed) return left.passed > right.passed ? left : right;
    if (left.compiled !== right.compiled) return left.compiled ? left : right;
    return left.at >= right.at ? left : right;
  }

  function bestScoredAttempt(history) {
    const scored = history.filter((attempt) => attempt.compiled && attempt.total > 0);
    return scored.length ? scored.reduce(betterAttempt) : null;
  }

  function summary(value, exerciseId, exerciseIds) {
    const progress = sanitise(value, exerciseIds);
    const history = progress.attempts[exerciseId] || [];
    if (!history.length) return {count: 0, last: null, best: null};
    return {
      count: history.length,
      last: history[history.length - 1],
      best: bestScoredAttempt(history)
    };
  }

  function totals(value, exerciseIds) {
    const progress = sanitise(value, exerciseIds);
    let attemptCount = 0;
    let solvedCount = 0;
    for (const id of exerciseSet(exerciseIds)) {
      const history = progress.attempts[id] || [];
      attemptCount += history.length;
      if (history.length) {
        const best = bestScoredAttempt(history);
        if (best && best.passed === best.total) solvedCount += 1;
      }
    }
    return {favoriteCount: progress.favorites.length, attemptCount, solvedCount};
  }

  function exactKeys(value, expected) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    const actual = Object.keys(value).sort();
    const wanted = [...expected].sort();
    return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
  }

  function exportPayload(value, historyEnabled, exerciseIds) {
    const progress = sanitise(value, exerciseIds);
    if (!historyEnabled) progress.attempts = {};
    return {
      format: TRANSFER_FORMAT,
      schema_version: TRANSFER_SCHEMA_VERSION,
      history_enabled: Boolean(historyEnabled),
      favorites: progress.favorites,
      attempts: progress.attempts
    };
  }

  function rejected(reason) {
    return {ok: false, reason};
  }

  function importPayload(value, exerciseIds, now = Date.now()) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      return rejected("invalid_structure");
    }
    if (value.format !== TRANSFER_FORMAT || value.schema_version !== TRANSFER_SCHEMA_VERSION) {
      return rejected("unsupported_format");
    }
    if (!exactKeys(value, [
      "format", "schema_version", "history_enabled", "favorites", "attempts"
    ]) || typeof value.history_enabled !== "boolean") {
      return rejected("invalid_structure");
    }

    const known = exerciseSet(exerciseIds);
    if (!Array.isArray(value.favorites) || value.favorites.length > known.size) {
      return rejected("invalid_favorites");
    }
    const seen = new Set();
    for (const id of value.favorites) {
      if (typeof id !== "string" || !known.has(id) || seen.has(id)) {
        return rejected("invalid_favorites");
      }
      seen.add(id);
    }

    if (!value.attempts || typeof value.attempts !== "object" || Array.isArray(value.attempts)) {
      return rejected("invalid_attempts");
    }
    for (const [id, history] of Object.entries(value.attempts)) {
      if (!known.has(id) || !Array.isArray(history) ||
          history.length > MAX_ATTEMPTS_PER_EXERCISE) {
        return rejected("invalid_attempts");
      }
      for (const attempt of history) {
        if (!exactKeys(attempt, ["at", "passed", "total", "compiled"]) ||
            !sanitiseAttempt(attempt, now)) {
          return rejected("invalid_attempt");
        }
      }
    }
    const hasAttempts = Object.values(value.attempts).some((history) => history.length > 0);
    if (!value.history_enabled && hasAttempts) return rejected("history_conflict");

    return {
      ok: true,
      historyEnabled: value.history_enabled,
      progress: sanitise({
        schema_version: SCHEMA_VERSION,
        favorites: value.favorites,
        attempts: value.attempts
      }, exerciseIds, now)
    };
  }

  return {
    SCHEMA_VERSION,
    TRANSFER_FORMAT,
    TRANSFER_SCHEMA_VERSION,
    MAX_ATTEMPTS_PER_EXERCISE,
    blank,
    sanitise,
    toggleFavorite,
    recordAttempt,
    clearAttempts,
    summary,
    totals,
    exportPayload,
    importPayload
  };
})();
