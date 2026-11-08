#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Roteia de novo a placa famicom_nes (depois de mexer nas posições): Freerouting fora do MCP, zonas, costura de GND e preenchimento.
# Uso (da raiz): tools/boards/famicom_nes/reroute.sh   (precisa do venv do KiCad MCP, Java e ~/.kicad-mcp/freerouting.jar)
set -e
PY=${PY:-$HOME/development/llms/KiCAD-MCP-Server/.venv/bin/python}
PCB=boards/famicom_nes/hardware-v1.1/dumper.kicad_pcb
T=$(mktemp -d)
$PY -c "import pcbnew; b=pcbnew.LoadBoard('$PCB'); pcbnew.ExportSpecctraDSN(b,'$T/b.dsn')"
java -jar $HOME/.kicad-mcp/freerouting.jar -de $T/b.dsn -do $T/b.ses -mp 60 > $T/fr.log 2>&1 || true
tail -2 $T/fr.log | cut -c1-200
$PY -c "import pcbnew; b=pcbnew.LoadBoard('$PCB'); print(pcbnew.ImportSpecctraSES(b,'$T/b.ses')); b.Save('$PCB')"
$PY tools/historico/revisao/widen_power.py $PCB
$PY tools/boards/megadrive/add_zones.py $PCB
$PY tools/boards/megadrive/stitch.py $PCB 5
$PY tools/fill_zones.py $PCB
rm -rf $T
