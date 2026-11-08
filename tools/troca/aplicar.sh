#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Bloco de troca de cartucho (D126) numa placa: esquemático e PCB (etapa "prep") ou roteamento e acabamento (etapa "rota").
# Uso (da raiz): tools/troca/aplicar.sh <placa> prep|rota   (parâmetros em tools/troca/boards.json; precisa do venv do KiCad MCP)
set -euo pipefail
B=${1:?placa}; ETAPA=${2:?prep|rota}
ROOT=$(cd "$(dirname "$0")/../.." && pwd); cd "$ROOT"
PY=${PY:-$HOME/development/llms/KiCAD-MCP-Server/.venv/bin/python}
P() { python3 -c "import json,sys; c=json.load(open('tools/troca/boards.json'))['$B']; print($1)"; }
VER=$(P "c['version']"); AX=$(P "c['anchor'][0]"); AY=$(P "c['anchor'][1]"); REG=$(P "' '.join(str(v) for v in c['region'])")
MOVES=$(P "' '.join('--move \"%s\"' % m for m in c.get('moves', []))")
HIDE=$(P "' '.join('--hide %s' % h for h in c.get('hide', []))")
HW=boards/$B/hardware-$VER
if [ "$ETAPA" = prep ]; then
  python3 tools/troca/sch_block.py $HW/dumper.kicad_sch "$VER"
  $PY tools/troca/pcb_block.py $HW "$VER" $AX $AY $REG || { echo "FALHA: pcb_block (veja acima); a rota não deve rodar" >&2; exit 1; }
else
  $PY tools/troca/route.py $HW ${PASSES:-40} | tail -2
  eval $PY tools/troca/finish.py $HW $MOVES $HIDE
fi
