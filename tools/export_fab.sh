#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Gera gerbers, furos e zips para a JLCPCB de uma placa de boards/.
# Uso: tools/export_fab.sh <placa> <versão>      ex.: tools/export_fab.sh 16_bits v1.0
set -euo pipefail
BOARD=${1:?placa (pasta em boards/)}; VER=${2:?versão, ex. v1.0}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
# HWDIR e GDIR permitem exportar uma revisão antiga guardada ao lado (ex.: HWDIR=hardware-v1.0 GDIR=gerbers-v1.0-rev2 tools/export_fab.sh 16_bits v1.0-rev2)
HWDIR=${HWDIR:-hardware}; GDIR=${GDIR:-gerbers}
PCB="$ROOT/boards/$BOARD/$HWDIR/dumper.kicad_pcb"
SCH="$ROOT/boards/$BOARD/$HWDIR/dumper.kicad_sch"
FAB="$ROOT/boards/$BOARD/fab"
G="$FAB/$GDIR"
mkdir -p "$G"; rm -f "$G"/*
kicad-cli pcb export gerbers --no-x2 --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts" -o "$G/" "$PCB"
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th \
  --generate-map --map-format gerberx2 -o "$G/" "$PCB"
[ "$HWDIR" = hardware ] && kicad-cli sch export bom --fields 'Reference,Value,Footprint,${QUANTITY}' --labels 'Ref,Valor,Footprint,Qtd' \
  --group-by Value,Footprint --ref-range-delimiter '' -o "$FAB/bom.csv" "$SCH" || true
rm -f "$FAB/dumper-$VER-jlcpcb.zip" "$FAB/dumper-$VER-gerbers-jlcpcb.zip"
( cd "$G" && zip -q -X "$FAB/dumper-$VER-jlcpcb.zip" ./*.gtl ./*.gbl ./*.gts ./*.gbs ./*.gto ./*.gbo ./*.gm1 ./*.drl )
cp "$FAB/dumper-$VER-jlcpcb.zip" "$FAB/dumper-$VER-gerbers-jlcpcb.zip"
ls -l "$G" "$FAB"
