#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Refaz o PCB da placa n64 do zero: cópia da 16_and_8_bits, place.py, nets, Freerouting e SES.
# Uso (da raiz): tools/n64/build_pcb.sh   (precisa do venv do KiCad MCP, kicad-cli, Java e ~/.kicad-mcp/freerouting.jar)
set -e
PY=${PY:-$HOME/development/llms/KiCAD-MCP-Server/.venv/bin/python}
T=$(mktemp -d)
B=boards/n64/hardware
PCB=$B/dumper.kicad_pcb
cp boards/16_and_8_bits/hardware/dumper.kicad_pcb $B/dumper.kicad_pcb
$PY tools/n64/place.py $B/dumper.kicad_pcb
kicad-cli sch export netlist --format kicadsexpr -o $T/n64.net $B/dumper.kicad_sch
$PY tools/nes/sync_unconnected.py $B/dumper.kicad_pcb $T/n64.net
$PY tools/sch/sync_names.py $B/dumper.kicad_sch $B/dumper.kicad_pcb
$PY -c "import pcbnew,sys; b=pcbnew.LoadBoard('$B/dumper.kicad_pcb'); pcbnew.ExportSpecctraDSN(b,'$T/n64.dsn')"
java -jar $HOME/.kicad-mcp/freerouting.jar -de $T/n64.dsn -do $T/n64.ses -mp 60 > $T/fr.log 2>&1 || true
tail -2 $T/fr.log | cut -c1-200
$PY -c "import pcbnew; b=pcbnew.LoadBoard('$B/dumper.kicad_pcb'); print(pcbnew.ImportSpecctraSES(b,'$T/n64.ses')); b.Save('$B/dumper.kicad_pcb')"
$PY tools/revisao/widen_power.py $PCB
$PY tools/megadrive/add_zones.py $PCB
$PY tools/megadrive/stitch.py $PCB 5
$PY tools/fill_zones.py $PCB
rm -rf $T
