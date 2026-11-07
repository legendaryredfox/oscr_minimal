# gb_gba — GBA; GB e GBC por adaptador

Versão mínima de uma função: um slot **GBA** (32 pads SMD, 1,5 mm, **3,3 V**) em shield para Arduino Mega 2560 R3, só USB. GB e GBC entram **só pelo slot GBA, com adaptador** (D56). Um cartucho por vez. Pinagem idêntica ao OSCR HW5 (`docs/pinmap.md`, recorte da `16_and_8_bits`). Sem SD, sem LCD, sem Si5351 e sem PIC.

**Estado:** v1.0, 138,1 × 67,1 mm. ERC com 1 aviso de biblioteca (U1, antes U3; o mesmo da `16_and_8_bits`); DRC sem erros nem ligações abertas (só avisos de biblioteca e paridade); netlist confere com `docs/pinmap.md`; gerbers em `fab/`. Roteada pelo Freerouting (MCP) com o GND junto; o `/D9` o autoroteador não achou caminho em nenhuma tentativa e foi roteado pelo A* de `tools/pcb_v12` (`tools/gb_gba/route_net.py`). **Revisar o layout no KiCad antes de encomendar.** Nada encomendado nem montado. Montagem: `docs/montagem.md`. Trilhas de alimentação (`+5V`, `+3V3`) alargadas até onde cabe, 0,8 mm na maior parte (`tools/revisao/widen_power.py`, D96).

## Diferenças em relação à `16_and_8_bits`

| Item | 16_and_8_bits | gb_gba |
|---|---|---|
| Slots | SNES, NES, Famicom, Mega Drive, GBA | só GBA |
| Regulador 3,3 V (U3, C7, C8, C9; na gb_gba: U1, C2, C3, C4, D109) | sim | sim |
| Si5351, PIC, R2, C2 a C6 | sim | não |
| Placa | 144 × 108 mm | 138,1 × 67,1 mm |
| Furos | 4 M3 de canto, 6 do Mega, 2 M2 do Si5351 | 4 M3 junto ao Mega (nenhum do lado do slot GBA); sem os 6 do Mega |

O slot GBA ficou **na mesma orientação** (boca para a direita, etiqueta para cima), mas encostado no Mega, com as peças soltas dentro da área do Mega. O pino 31 (AUD_IRQ) continua sem ligação (D22).

## Como foi feita

Mesma receita da `megadrive/` e da `snes/` (`boards/megadrive/README.md`, D92 e D93), com `tools/gb_gba/place.py`. `fix_nets.py` leva **um pad por chamada** (num laço de shell).

```
python3 tools/check_netlist.py --board gb_gba
kicad-cli sch erc boards/gb_gba/hardware/dumper.kicad_sch
kicad-cli pcb drc boards/gb_gba/hardware/dumper.kicad_pcb
tools/export_fab.sh gb_gba v1.0
```
