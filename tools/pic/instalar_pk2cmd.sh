#!/usr/bin/env bash
# Baixa e compila o pk2cmd (programador PICkit 2) FORA do git.
#
# Licença: o pk2cmd é da Microchip, "software não livre" (licença restritiva): não pode ser
# copiado para este repositório nem redistribuído sem os avisos dela. Por isso este script baixa do
# upstream na SUA máquina; os fontes vão para vendor/pk2cmd/ e o binário para tools/pic/bin/, ambos
# ignorados pelo git. Leia vendor/pk2cmd/README.md (a licença) antes de usar.
#
# Uso: tools/pic/instalar_pk2cmd.sh
set -euo pipefail

REPO="https://github.com/psmay/pk2cmd.git"          # Microchip pk2cmd v1.20 + patches do v1.21 RC1 (Linux/Mac)
COMMIT="3007bdce7dd360437e36deea1e172dcae53817e3"   # fixo, para a build ser reproduzível
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
FONTE="$RAIZ/vendor/pk2cmd"
BIN="$RAIZ/tools/pic/bin"

for f in git make g++; do
  command -v "$f" >/dev/null || { echo "Falta o '$f'. Instale: sudo apt install git build-essential" >&2; exit 1; }
done
if [ ! -f /usr/include/usb.h ]; then
  echo "Falta o cabeçalho do libusb 0.1. Instale: sudo apt install libusb-dev" >&2
  exit 1
fi

if [ ! -d "$FONTE/.git" ]; then
  git clone --quiet "$REPO" "$FONTE"
fi
git -C "$FONTE" fetch --quiet origin
git -C "$FONTE" checkout --quiet "$COMMIT"

# Compila numa cópia, para não sujar o clone (vendor/ é só leitura).
rm -rf "$BIN/build" && mkdir -p "$BIN/build"
cp -r "$FONTE/pk2cmd/." "$BIN/build/"
cd "$BIN/build"
if ! make linux LIBUSB=/usr >"$BIN/build.log" 2>&1; then
  echo "A build padrão falhou (código antigo, compilador novo). Tentando com -fpermissive..." >&2
  make clean >/dev/null 2>&1 || true
  make linux LIBUSB=/usr \
    CFLAGS="-O2 -D_GNU_SOURCE -I/usr/include -DLINUX -DUSE_DETACH -DCLAIM_USB -fpermissive -w" \
    >>"$BIN/build.log" 2>&1 || { echo "Falhou de novo. Veja $BIN/build.log" >&2; exit 1; }
fi
cp pk2cmd PK2DeviceFile.dat "$BIN/"

if ! grep -aq "PIC12F629" "$BIN/PK2DeviceFile.dat"; then
  echo "ATENÇÃO: o PK2DeviceFile.dat não lista o PIC12F629." >&2
  exit 1
fi
echo "OK: $BIN/pk2cmd e $BIN/PK2DeviceFile.dat (lista o PIC12F629)."
echo "Falta a regra de USB (uma vez, com sudo):"
echo "  sudo cp $RAIZ/tools/pic/60-pickit.rules /etc/udev/rules.d/ && sudo udevadm control --reload && sudo udevadm trigger"
echo "Depois reconecte o PICkit 2. Guia: tools/pic/README.md"
