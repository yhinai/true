#!/bin/sh
set -eu

candidate_dir="${CANDIDATE_DIR:-$(pwd)}"
output="$(sh "$candidate_dir/bin/report.sh")"

if [ "$output" != "verified:PASS" ]; then
  printf 'Expected verified:PASS but saw %s\n' "$output" >&2
  exit 1
fi

printf 'Shell banner matches expected output.\n'
