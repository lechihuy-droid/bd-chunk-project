#!/usr/bin/env sh
set -eu

suite="${1:-workspace-smoke}"
if [ "$#" -gt 0 ]; then
  shift
fi

mkdir -p /work/repo
cp -a /src/. /work/repo/
cd /work/repo

python harness/run_harness.py --suite "$suite" "$@"
