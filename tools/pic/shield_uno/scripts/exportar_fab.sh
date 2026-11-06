#!/usr/bin/env bash
# SPDX-License-Identifier: CC-BY-SA-2.5
# Gera gerbers, furos, BOM e o zip para a JLCPCB em fab/ (mesmos parametros de tools/export_fab.sh).
# Uso: tools/pic/shield_uno/scripts/exportar_fab.sh [versao]      ex.: v1.0
set -euo pipefail
VER=${1:-v1.0}
D=$(cd "$(dirname "$0")/.." && pwd)
PCB="$D/hardware/shield_uno.kicad_pcb"; SCH="$D/hardware/shield_uno.kicad_sch"
G="$D/fab/gerbers"; mkdir -p "$G"; rm -f "$G"/*
kicad-cli pcb export gerbers --no-x2 --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts" -o "$G/" "$PCB"
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 -o "$G/" "$PCB"
kicad-cli sch export bom --fields 'Reference,Value,Footprint,${QUANTITY}' --labels 'Ref,Valor,Footprint,Qtd' \
  --exclude-dnp --group-by Value,Footprint --ref-range-delimiter '' -o "$D/fab/bom.csv" "$SCH"
rm -f "$D/fab/shield_uno-$VER-jlcpcb.zip"
( cd "$G" && zip -q -X "$D/fab/shield_uno-$VER-jlcpcb.zip" ./*.gtl ./*.gbl ./*.gts ./*.gbs ./*.gto ./*.gbo ./*.gm1 ./*.drl )
ls -l "$G" "$D/fab"
