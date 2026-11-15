#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# H-0b: abre a GUI num display virtual (Xvfb), confere que a janela aparece e não está em branco, em largura normal e estreita
# (layout de uma coluna), e guarda as capturas. Não precisa de placa nem de tela. Uso: tools/gui_smoke.sh [pasta-das-capturas]
# Precisa de: Xvfb, xdotool, ImageMagick (import, convert) e Java. Sai com 1 se alguma conferência falhar.
# Não usa pkill -f nem pgrep -f (casam com a própria linha de comando e matam o shell): só kill por PID.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-${TMPDIR:-/tmp}/oscr-gui-smoke}; mkdir -p "$OUT"
D=:97; FAIL=0
for c in Xvfb xdotool import convert java; do command -v "$c" >/dev/null || { echo "falta o programa: $c"; exit 2; }; done
Xvfb $D -screen 0 1920x1100x24 -ac >/dev/null 2>&1 & XPID=$!
sleep 1
cd "$ROOT/gui"
DISPLAY=$D SKIKO_RENDER_API=SOFTWARE ./gradlew --offline -q :desktopApp:run >"$OUT/gui.log" 2>&1 & GPID=$!
cleanup() { kill "$GPID" 2>/dev/null; pkill -P "$GPID" 2>/dev/null; kill "$XPID" 2>/dev/null; }
trap cleanup EXIT
WIN=""
for _ in $(seq 1 180); do
  WIN=$(DISPLAY=$D xdotool search --name oscr_minimal 2>/dev/null | head -1)
  [ -n "$WIN" ] && break
  kill -0 "$GPID" 2>/dev/null || { echo "ERRO: a GUI terminou antes de abrir a janela (veja $OUT/gui.log)"; exit 1; }
  sleep 1
done
[ -z "$WIN" ] && { echo "ERRO: a janela não apareceu em 180 s (veja $OUT/gui.log)"; exit 1; }
sleep 8   # primeira composição e carga da base de dados

confere() {  # confere <nome> <largura> <altura>
  DISPLAY=$D xdotool windowsize "$WIN" "$2" "$3"; sleep 3
  DISPLAY=$D import -window root "$OUT/$1.png"
  local sd; sd=$(convert "$OUT/$1.png" -format "%[fx:standard_deviation]" info:)
  if awk "BEGIN{exit !($sd > 0.02)}"; then echo "ok    $1 ($2x$3, desvio $sd)"; else echo "ERRO  $1: captura quase uniforme (desvio $sd): janela em branco?"; FAIL=1; fi
}
confere larga 1280 900
confere estreita 560 900
kill -0 "$GPID" 2>/dev/null || { echo "ERRO: a GUI morreu durante o teste"; FAIL=1; }
grep -iE "exception|error" "$OUT/gui.log" | grep -v "^$" | head -5 | sed 's/^/log: /' && true
echo "capturas em $OUT"
exit $FAIL
