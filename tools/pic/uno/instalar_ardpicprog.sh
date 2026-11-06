#!/usr/bin/env bash
# Prepara o ardpicprog (programador de PIC com Arduino Uno, GPL v3): baixa do upstream no commit fixo,
# compila o programa do PC e copia o sketch para uma pasta com o nome que o Arduino exige.
# Fontes ficam em vendor/ardpicprog/ (ignorado pelo git); resultados em tools/pic/bin/.
#
# Uso: tools/pic/uno/instalar_ardpicprog.sh
set -euo pipefail

REPO="https://github.com/rweather/ardpicprog.git"
COMMIT="2f8b5405440b30b0390f6d9d459da70e70e894cd"
RAIZ="$(cd "$(dirname "$0")/../../.." && pwd)"
FONTE="$RAIZ/vendor/ardpicprog"
BIN="$RAIZ/tools/pic/bin"

for f in git make g++; do
  command -v "$f" >/dev/null || { echo "Falta o '$f'. Instale: sudo apt install git build-essential" >&2; exit 1; }
done

if [ ! -d "$FONTE/.git" ]; then
  git clone --quiet "$REPO" "$FONTE"
fi
git -C "$FONTE" fetch --quiet origin
git -C "$FONTE" checkout --quiet "$COMMIT"

mkdir -p "$BIN"
# Programa do PC: compila numa cópia (vendor/ é só leitura).
rm -rf "$BIN/ardpicprog-build" && cp -r "$FONTE/host" "$BIN/ardpicprog-build"
make -C "$BIN/ardpicprog-build" >"$BIN/ardpicprog-build.log" 2>&1 \
  || { echo "A build falhou. Veja $BIN/ardpicprog-build.log" >&2; exit 1; }
cp "$BIN/ardpicprog-build/ardpicprog" "$BIN/ardpicprog"

# Sketch: o Arduino só abre pasta/arquivo com o mesmo nome e extensão .ino (o original é .pde).
rm -rf "$BIN/ProgramPIC" && mkdir -p "$BIN/ProgramPIC"
cp "$FONTE/ProgramPIC/ProgramPIC.pde" "$BIN/ProgramPIC/ProgramPIC.ino"

echo "OK: $BIN/ardpicprog e o sketch em $BIN/ProgramPIC/"
echo "Grave o sketch no Uno (ver tools/pic/uno/README.md):"
echo "  arduino-cli compile -b arduino:avr:uno $BIN/ProgramPIC"
echo "  arduino-cli upload  -b arduino:avr:uno -p <porta> $BIN/ProgramPIC   (arduino-cli board list mostra a porta: ttyUSB0 em clones CH340, ttyACM0 em Uno original)"
