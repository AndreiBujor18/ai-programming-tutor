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
