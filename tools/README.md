# tools/

Scripts de apoio ao hardware. Todos rodam a partir da raiz do repositório. Hoje apontam para a placa `boards/16_and_8_bits/` (única com projeto KiCad).

| Script | Para quê | Precisa de |
|---|---|---|
| `check_netlist.py` | Confere a netlist do esquemático com `boards/16_and_8_bits/docs/pinmap.md` (nets, VCC no 5V, GND). **Rode ao fim das fases 3 e 5.** Sai com código 1 se algo diverge. | `kicad-cli` 10 no PATH, Python 3.11 |
| `gen_pinmap.py` | Gera `boards/16_and_8_bits/docs/pinmap.md` a partir do clone do OSCR em `vendor/oscr/` (não versionado; ver o README da raiz para recriar). | `vendor/oscr/`, Python 3.11 |
| `build_lib.py` | Gera os símbolos e footprints de `boards/_lib/` (slots do OSCR, Mega R3, Si5351). | Python 3.11 |
| `gen_connections.py`, `sync_net_names.py` | Geram e sincronizam as ligações e nomes de net do esquemático. | Python 3.11 |
| `plan_layout.py` | Calcula as posições dos slots e peças (D23). | Python 3.11 |
| `fill_zones.py` | Preenche as zonas de cobre pelo `pcbnew`. | Python do venv do KiCad MCP (`~/development/llms/KiCAD-MCP-Server`), KiCad 10 |

Atenção: o MCP do KiCad grava os arquivos sem atomicidade (um timeout já zerou um `.kicad_sch`). Copie `boards/16_and_8_bits/hardware/*.kicad_*` antes de rodar em lote.

Gerbers: `kicad-cli pcb export gerbers --no-x2 --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts"` (o `--no-x2` reproduz os arquivos de `boards/16_and_8_bits/fab/gerbers`) e `kicad-cli pcb export drill`; depois atualize o zip.
