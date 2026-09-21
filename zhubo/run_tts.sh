#!/usr/bin/env bash
set -e
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$project_dir/.local/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd "$project_dir"
exec /home/ln/AI/index-tts/.venv/bin/python -u -m tts_broadcast "$@"
