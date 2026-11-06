# megadrive — só Mega Drive / Genesis

Versão mínima de uma função: um slot **Mega Drive** (64p, 2,54 mm) em shield para Arduino Mega 2560 R3, 100% THT, só USB, **5 V** fixo. Um cartucho por vez. Pinagem idêntica ao OSCR HW5 (`docs/pinmap.md`, recorte da `16_bits`).

**Estado:** v1.0, 107,1 × 65,1 mm. ERC 0 violações; DRC sem erros de roteamento (2 `starved_thermal` justificados, ver `fab/PEDIDO.md`); netlist confere com `docs/pinmap.md`; gerbers em `fab/`. Roteada pelo Freerouting (MCP) e costurada com vias de GND: **revisar o layout no KiCad antes de encomendar** (trilhas não foram conferidas à mão). Nada encomendado nem montado. Montagem: `docs/montagem.md`.

## Diferenças em relação à `16_bits`

| Item | 16_bits | megadrive |
|---|---|---|
| Slots | SNES, Mega Drive | só Mega Drive |
| Si5351, PIC12F629 (CIC), R2 (pull-up do IRQ do SNES) | sim | **não** (o `MegaDrive.cpp` do OSCR não usa clock nem CIC) |
| Capacitores de 100 nF | C2 a C6 | C3, C5, C6 (slot Mega Drive) |
| Slot dentro da área do Mega | não (SNES ocupava) | **sim**: o slot MD fica entre as fileiras de pinos do Mega |
| Placa | 108,1 × 86,1 mm | 107,1 × 65,1 mm |
| Mantido | `/CART` em D50, pontos de teste (`/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE`), LED de status em D38, C1 470 µF | idem |

Ficam sem ligação no Mega: `D20`, `D21`, `D40`, `D41` (I²C do Si5351 e reset do PIC).

## Como foi feita

Scripts em `tools/megadrive/` (da raiz do repositório):

1. `strip_sch.py` tira do esquemático da `16_bits` SNES1, U1, U2, R2, C2, C4 e os rótulos dos pinos deles.
2. `place.py` (Python do venv do KiCad MCP) limpa as trilhas, remove as peças, move o slot, refaz contorno e zonas.
3. Roteamento: `autoroute` (Freerouting) do KiCad MCP (3 tentativas, 215 s).
4. `fix_nets.py` (pinos sem uso do Mega), `fill_zones.py`, `stitch.py` e `frag_vias.py` (vias de GND que ligam fragmentos do preenchimento), depois DRC e `check_netlist.py`.

Verificação:

```
python3 tools/check_netlist.py --board megadrive
kicad-cli sch erc boards/megadrive/hardware/dumper.kicad_sch
kicad-cli pcb drc boards/megadrive/hardware/dumper.kicad_pcb
tools/export_fab.sh megadrive v1.0
```
