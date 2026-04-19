function renderStatusBadge(status) {
  if (status === "ok") {
    return "OK";
  }
  return "UNKNOWN";
}

module.exports = { renderStatusBadge };
