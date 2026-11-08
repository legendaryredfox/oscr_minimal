#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Bloco de troca (D126), fechamento de uma placa: confere netlist, exporta a fábrica, refaz as prévias e o render, atualiza os docs.
# Uso (da raiz): tools/troca/fechar.sh <placa>
set -euo pipefail
B=${1:?placa}; ROOT=$(cd "$(dirname "$0")/../.." && pwd); cd "$ROOT"
VER=$(python3 -c "import json; print(json.load(open('tools/troca/boards.json'))['$B']['version'])")
OUT=$(python3 tools/check_netlist.py --board "$B"); echo "$OUT"
NETS=$(echo "$OUT" | sed -n 's/^OK: \([0-9]*\) nets e \([0-9]*\) ligações.*/\1/p'); LINKS=$(echo "$OUT" | sed -n 's/^OK: \([0-9]*\) nets e \([0-9]*\) ligações.*/\2/p')
# o PCB precisa ter as peças do esquemático (a paridade pega peça faltando: o prep pode ter falhado em "sem lugar")
kicad-cli pcb drc --severity-all --schematic-parity -o /tmp/fechar_drc.txt "boards/$B/hardware-$VER/dumper.kicad_pcb" >/dev/null 2>&1
if grep -E "^\[missing_footprint\]" /tmp/fechar_drc.txt | grep -vE "FLG[0-9]+ " | grep -q .; then echo "ERRO: faltam peças no PCB:"; grep -E "^\[missing_footprint\]" /tmp/fechar_drc.txt | grep -vE "FLG[0-9]+ "; exit 1; fi
if grep -E "^\[(clearance|shorting_items|unconnected_items|via_dangling|tracks_crossing|courtyards_overlap|hole_clearance|copper_edge_clearance)\]" /tmp/fechar_drc.txt | grep -q .; then echo "ERRO: DRC com problemas:"; grep -E "^\[(clearance|shorting_items|unconnected_items|via_dangling|tracks_crossing|courtyards_overlap)\]" /tmp/fechar_drc.txt | sort | uniq -c; exit 1; fi
# a versão anterior (v1.0) sai da pasta fab/ (nada foi encomendado)
git rm -q --ignore-unmatch -f "boards/$B/fab/dumper-v1.0-jlcpcb.zip" "boards/$B/fab/dumper-v1.0-gerbers-jlcpcb.zip" 2>/dev/null || true
tools/export_fab.sh "$B" "$VER" >/dev/null
tools/render_board.sh "$B" v1.0 "$VER" >/dev/null
python3 tools/troca/docs.py "$B" --nets "$NETS" --links "$LINKS"
