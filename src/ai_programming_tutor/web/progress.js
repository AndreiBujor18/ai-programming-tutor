"use strict";

// Pure helpers for device-local learning progress. Stored attempts deliberately
// exclude source code, compiler output, diagnoses, hints, and profile traits.
window.APT_PROGRESS = (() => {
  const SCHEMA_VERSION = "0.1";
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

  return {
    SCHEMA_VERSION,
    MAX_ATTEMPTS_PER_EXERCISE,
    blank,
    sanitise,
    toggleFavorite,
    recordAttempt,
    clearAttempts,
    summary,
    totals
  };
})();
