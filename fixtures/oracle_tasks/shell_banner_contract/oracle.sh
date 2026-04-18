#!/bin/sh
set -eu

output="$(sh "$CANDIDATE_DIR/bin/report.sh")"

if [ "$output" != "verified:PASS" ]; then
  printf 'Expected verified:PASS but saw %s\n' "$output" >&2
  exit 1
fi

printf 'Shell banner matches expected output.\n'
