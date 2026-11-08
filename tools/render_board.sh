#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Renders 3D comuns do KiCad (PNG de 1768 x 1064, qualidade básica), de cima e de baixo, de cada versão de uma placa.
# Saída: boards/<placa>/renders/<placa>-<versão>-cima.png e -baixo.png; boards/<placa>/render.png = a última versão, de cima.
# Pastas: hardware-<versão>/ para as congeladas; hardware/ para a última da lista.
# Uso: tools/render_board.sh <placa> <v1.0> [<v1.1> ...]     ex.: tools/render_board.sh 16_bits v1.0 v1.2 v1.3
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
B=${1:?placa (pasta em boards/)}; shift
[ $# -ge 1 ] || { echo "faltam as versões" >&2; exit 1; }
OUT="$ROOT/boards/$B/renders"; mkdir -p "$OUT"
N=$#; I=0
for V in "$@"; do
  I=$((I+1)); HW=hardware-$V; [ "$I" -eq "$N" ] && HW=hardware
  for L in "top:cima" "bottom:baixo"; do
    kicad-cli pcb render --side "${L%%:*}" --quality basic --background default --width 1768 --height 1064 \
      -o "$OUT/$B-$V-${L##*:}.png" "$ROOT/boards/$B/$HW/dumper.kicad_pcb" >/dev/null
    echo "render: boards/$B/renders/$B-$V-${L##*:}.png"
  done
  [ "$I" -eq "$N" ] && cp "$OUT/$B-$V-cima.png" "$ROOT/boards/$B/render.png"
done
