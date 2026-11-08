#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# D138: confere uma versão depois do roteamento. Uso: tools/troca/verifica.sh <placa> <versão>
# Mostra as classes de DRC (peça faltando, ligação aberta, curto, folga...) e o resultado do ERC. Erros de verdade: unconnected_items, shorting_items,
# clearance, tracks_crossing, via_dangling, copper_edge_clearance, hole_clearance, courtyards_overlap.
B=${1:?placa}; V=${2:?versão}; ROOT=$(cd "$(dirname "$0")/../.." && pwd)
HW="$ROOT/boards/$B/hardware-$V"
kicad-cli pcb drc --severity-all --schematic-parity -o /tmp/claude-1000/drc-$B-$V.txt "$HW/dumper.kicad_pcb" >/dev/null 2>&1
kicad-cli sch erc --severity-all -o /tmp/claude-1000/erc-$B-$V.txt "$HW/dumper.kicad_sch" >/dev/null 2>&1
echo "== $B $V: DRC"; grep -E "^\[" /tmp/claude-1000/drc-$B-$V.txt | cut -d']' -f1 | sort | uniq -c | tr '\n' ' '; echo
echo "   ERC:"; grep -E "^\[" /tmp/claude-1000/erc-$B-$V.txt | cut -d']' -f1 | sort | uniq -c | tr '\n' ' '; echo
grep -E "^\[(unconnected_items|shorting_items|clearance|tracks_crossing|via_dangling|copper_edge_clearance|hole_clearance|courtyards_overlap|missing_footprint)\]" -A3 /tmp/claude-1000/drc-$B-$V.txt | grep -v "FLG[0-9]" | head -${3:-30}
