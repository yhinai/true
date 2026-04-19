const assert = require("node:assert/strict");
const { renderStatusBadge } = require("./status");

assert.equal(renderStatusBadge("ok"), "PASS");
assert.equal(renderStatusBadge("fail"), "FAIL");
assert.equal(renderStatusBadge("maybe"), "UNKNOWN");

console.log("ok");
