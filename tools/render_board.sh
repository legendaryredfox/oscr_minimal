#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Refaz boards/<placa>/render.png (3D do KiCad, vista de cima). Uso: tools/render_board.sh <placa> [<placa> ...]
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
for B in "$@"; do
  kicad-cli pcb render --side top --quality basic --background default --width 1768 --height 1064 \
    -o "$ROOT/boards/$B/render.png" "$ROOT/boards/$B/hardware/dumper.kicad_pcb" >/dev/null
  echo "render: boards/$B/render.png"
done
