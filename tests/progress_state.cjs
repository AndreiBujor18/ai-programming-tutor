"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..", "src", "ai_programming_tutor", "web");
const context = vm.createContext({window: {}});
vm.runInContext(fs.readFileSync(path.join(root, "progress.js"), "utf8"), context);
const progress = context.window.APT_PROGRESS;
const ids = ["alpha", "beta"];
const now = Date.now();

const sanitised = JSON.parse(JSON.stringify(progress.sanitise({
  schema_version: "0.1",
  favorites: ["alpha", "missing", "alpha", 42],
  attempts: {
    alpha: [
      {at: now - 1000, passed: 2, total: 5, compiled: true,
        source: "private source", compiler_output: "private output"},
      {at: now - 500, passed: 9, total: 5, compiled: true},
      {at: "yesterday", passed: 0, total: 5, compiled: false}
    ],
    missing: [{at: now, passed: 1, total: 1, compiled: true}]
  },
  raw_source: "must disappear"
}, ids, now)));

assert.deepStrictEqual(sanitised, {
  schema_version: "0.1",
  favorites: ["alpha"],
  attempts: {alpha: [{at: now - 1000, passed: 2, total: 5, compiled: true}]}
});
assert.equal(JSON.stringify(sanitised).includes("private"), false);

let value = progress.blank();
value = progress.toggleFavorite(value, "beta", ids);
for (let index = 0; index < 25; index += 1) {
  value = progress.recordAttempt(value, "beta", {
    compilation: {succeeded: true},
    passed_count: index === 10 ? 5 : index % 5,
    total_count: 5
  }, ids, now + index);
}
const bounded = JSON.parse(JSON.stringify(value));
assert.equal(bounded.attempts.beta.length, progress.MAX_ATTEMPTS_PER_EXERCISE);
assert.equal(bounded.attempts.beta[0].at, now + 5);
const summary = progress.summary(value, "beta", ids);
assert.equal(summary.count, 20);
assert.equal(summary.last.at, now + 24);
assert.equal(summary.best.passed, 5);
assert.deepStrictEqual(JSON.parse(JSON.stringify(progress.totals(value, ids))), {
  favoriteCount: 1, attemptCount: 20, solvedCount: 1
});

const compileFailure = progress.recordAttempt(progress.blank(), "alpha", {
  compilation: {succeeded: false}, passed_count: 0, total_count: 0
}, ids, now);
const failedSummary = progress.summary(compileFailure, "alpha", ids);
assert.equal(failedSummary.count, 1);
assert.equal(failedSummary.last.compiled, false);
assert.equal(failedSummary.best, null);
assert.deepStrictEqual(JSON.parse(JSON.stringify(progress.totals(compileFailure, ids))), {
  favoriteCount: 0, attemptCount: 1, solvedCount: 0
});

const cleared = JSON.parse(JSON.stringify(progress.clearAttempts(value, ids)));
assert.deepStrictEqual(cleared.favorites, ["beta"]);
assert.deepStrictEqual(cleared.attempts, {});
assert.deepStrictEqual(JSON.parse(JSON.stringify(progress.sanitise({schema_version: "old"}, ids))),
  {schema_version: "0.1", favorites: [], attempts: {}});

const exported = JSON.parse(JSON.stringify(progress.exportPayload(value, true, ids)));
assert.deepStrictEqual(Object.keys(exported).sort(),
  ["attempts", "favorites", "format", "history_enabled", "schema_version"]);
assert.equal(exported.format, "ai-programming-tutor-progress");
assert.equal(exported.schema_version, "0.1");
assert.equal(exported.history_enabled, true);
assert.equal(exported.favorites[0], "beta");
assert.equal(exported.attempts.beta.length, progress.MAX_ATTEMPTS_PER_EXERCISE);
assert.equal(JSON.stringify(exported).includes("source"), false);

const imported = progress.importPayload(exported, ids, now + 1000);
assert.equal(imported.ok, true);
assert.equal(imported.historyEnabled, true);
assert.deepStrictEqual(JSON.parse(JSON.stringify(imported.progress)), {
  schema_version: "0.1", favorites: ["beta"], attempts: {beta: exported.attempts.beta}
});

const favoritesOnly = progress.exportPayload(cleared, false, ids);
assert.equal(favoritesOnly.history_enabled, false);
assert.deepStrictEqual(JSON.parse(JSON.stringify(favoritesOnly.attempts)), {});
assert.equal(progress.importPayload(favoritesOnly, ids, now + 1000).ok, true);

function rejectedTransfer(change, reason) {
  const candidate = JSON.parse(JSON.stringify(exported));
  change(candidate);
  const result = progress.importPayload(candidate, ids, now + 1000);
  assert.equal(result.ok, false);
  assert.equal(result.reason, reason);
}

rejectedTransfer((candidate) => { candidate.source = "private source"; }, "invalid_structure");
rejectedTransfer((candidate) => { candidate.format = "another-product"; }, "unsupported_format");
rejectedTransfer((candidate) => { candidate.favorites.push("beta"); }, "invalid_favorites");
rejectedTransfer((candidate) => { candidate.favorites = ["missing"]; }, "invalid_favorites");
rejectedTransfer((candidate) => {
  candidate.attempts.beta[0].compiler_output = "private output";
}, "invalid_attempt");
rejectedTransfer((candidate) => {
  candidate.attempts.missing = [{at: now, passed: 1, total: 1, compiled: true}];
}, "invalid_attempts");
rejectedTransfer((candidate) => {
  candidate.attempts.beta.push({at: now, passed: 1, total: 1, compiled: true});
}, "invalid_attempts");
rejectedTransfer((candidate) => { candidate.history_enabled = false; }, "history_conflict");
