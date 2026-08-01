#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BLENDER="${ROOT}/.tools/blender/4.5.12/blender"

[[ -x "${BLENDER}" ]] || { echo "Execute blender_env/bootstrap_linux.sh primeiro" >&2; exit 2; }
[[ $# -ge 1 ]] || { echo "Uso: run_blender.sh script.py [-- argumentos]" >&2; exit 2; }

SCRIPT="$1"
shift

exec "${BLENDER}" \
  --background \
  --factory-startup \
  --disable-autoexec \
  --python-exit-code 1 \
  --python "${SCRIPT}" \
  -- "$@"
