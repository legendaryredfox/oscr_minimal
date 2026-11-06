# tools/

Scripts de apoio ao hardware. Todos rodam a partir da raiz do repositório. Os gerais (`gen_pinmap.py`, `build_lib.py`, `plan_layout.py`...) apontam para a placa `boards/16_and_8_bits/`; `check_netlist.py` e `export_fab.sh` aceitam a placa como argumento, e cada placa de um sistema só tem a sua pasta de scripts.

| Script | Para quê | Precisa de |
|---|---|---|
| `check_netlist.py` | Confere a netlist do esquemático com `boards/<placa>/docs/pinmap.md` (`--board <placa>`: `16_bits`, `megadrive`, `snes`, `nes`, `famicom`, `famicom_nes`, `gb_gba`; na `16_bits` v. 1.2 vêm C5, C6, TPs e D50) (nets, VCC no 5V, GND). **Rode ao fim das fases 3 e 5.** Sai com código 1 se algo diverge. | `kicad-cli` 10 no PATH, Python 3.11 |
| `gen_pinmap.py` | Gera `boards/16_and_8_bits/docs/pinmap.md` a partir do clone do OSCR em `vendor/oscr/` (não versionado; ver o README da raiz para recriar). | `vendor/oscr/`, Python 3.11 |
| `build_lib.py` | Gera os símbolos e footprints de `boards/_lib/` (slots do OSCR, Mega R3, Si5351). | Python 3.11 |
| `gen_connections.py`, `sync_net_names.py` | Geram e sincronizam as ligações e nomes de net do esquemático. | Python 3.11 |
| `plan_layout.py` | Calcula as posições dos slots e peças (D23). | Python 3.11 |
| `pcb_v12/` | Registro dos scripts que alteraram a `16_bits` para a v. 1.2 (D87): mapa de folgas em grade, roteador A*, C5, C6, `/CART` e pontos de teste. Referência, não ferramenta pronta (`pcb_v12/README.md`). | Python do venv do KiCad MCP (`pcbnew`, `numpy`, `scipy`) |
| `megadrive/`, `snes/`, `nes/`, `famicom/`, `famicom_nes/`, `gb_gba/`, `revisao/` | Scripts das placas de um sistema só (D92 a D95, D98, D100, D101) e da revisão (D96, D97, D99): `place.py` de cada placa; genéricos em `megadrive/` (`strip_sch.py`, `fix_nets.py`, `add_zones.py`, `stitch.py`, `frag_vias.py`, `tp_header.py`); `nes/sync_unconnected.py` e `retext.py`; `revisao/` (`widen_power.py`, `solid_pad.py`, `move_tps.py`); `gb_gba/route_net.py`. Ver o README de cada placa em `boards/`. | Python do venv do KiCad MCP |
| `importar_base_oscr.py` | Copia para `database/oscr/` as bases de jogos do OSCR legado (`vendor/oscr/legacy/sd`) dos sistemas que o projeto lê, com `ORIGEM.txt` e `INDEX.txt` (D88). Rode de novo ao atualizar o clone. | Python 3.11, clone `vendor/oscr/` |
| `export_fab.sh` | `tools/export_fab.sh <placa> <versão>`: gerbers, furos, `bom.csv` e os dois zips de `boards/<placa>/fab/` (`HWDIR`/`GDIR` exportam uma revisão guardada ao lado, D97). | `kicad-cli` 10, `zip` |
| `gen_decisoes_index.py` | Regera o índice de `docs/decisoes.md`. | Python 3 |
| `pic/` | Gravação do PIC12F629 (PICkit 2 e Arduino Uno com ardpicprog, D90, D91). | ver `pic/README.md` |
| `fill_zones.py` | Preenche as zonas de cobre pelo `pcbnew`. | Python do venv do KiCad MCP (`~/development/llms/KiCAD-MCP-Server`), KiCad 10 |

Atenção: o MCP do KiCad grava os arquivos sem atomicidade (um timeout já zerou um `.kicad_sch`). Copie `boards/16_and_8_bits/hardware/*.kicad_*` antes de rodar em lote.

Gerbers: `kicad-cli pcb export gerbers --no-x2 --layers "F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts"` (o `--no-x2` reproduz os arquivos de `boards/16_and_8_bits/fab/gerbers`) e `kicad-cli pcb export drill`; depois atualize o zip.
