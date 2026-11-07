# snes — só SNES / Super Famicom

![Render 3D da placa snes (KiCad, vista de cima)](render.png)

Versão mínima de uma função: um slot **SNES/SFC** (62p, 2,5 mm) em shield para Arduino Mega 2560 R3, 100% THT, só USB, **5 V** fixo. Um cartucho por vez. Pinagem idêntica ao OSCR HW5 (`docs/pinmap.md`, recorte da `16_bits`).

**CIC:** PIC12F629 em soquete (D89/D91). O RP2040-Zero (`docs/placa-v1.3-rp2040.md`) só entra depois de validado.

**Estado:** v1.0, 107,1 × 65,1 mm. ERC 0 violações; DRC sem erros nem ligações abertas (só avisos de biblioteca e paridade, os mesmos da `16_bits`); netlist confere com `docs/pinmap.md`; gerbers em `fab/`. Roteada pelo Freerouting (MCP), com GND roteado junto e costurado com vias: **revisar o layout no KiCad antes de encomendar**. Nada encomendado nem montado. Montagem: `docs/montagem.md`. Trilhas de alimentação (`+5V`) alargadas até onde cabe, 0,8 mm na maior parte (`tools/revisao/widen_power.py`, D96).

## Diferenças em relação à `16_bits`

| Item | 16_bits | snes |
|---|---|---|
| Slots | SNES, Mega Drive | só SNES |
| Mantido | Si5351 (U1), PIC (U2), R2 (pull-up do IRQ), C2, C4 (agora C3, D109), C1, LED | idem |
| Removido | | MD1, C3, C5, C6, TP3 (`/CE` do Mega Drive), `/CART` (D50 sem ligação). Referências renumeradas em D109 (C4 virou C3; TP4 a TP6 viraram TP3 a TP5) |
| Pontos de teste | `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE` | `/IRQ` (D7), `5V`, `GND`, `/RD` (D9), `/WR` (D8) |
| Placa | 108,1 × 86,1 mm | 107,1 × 65,1 mm |

O slot SNES fica no mesmo lugar (dentro da área do Mega); a placa encolheu porque o slot Mega Drive saiu.

## Como foi feita

Mesma receita da `megadrive/` (`boards/megadrive/README.md`), com `tools/snes/place.py` no lugar de `tools/megadrive/place.py`. Roteamento: `autoroute` do KiCad MCP **com o GND como trilha** (sem zonas), depois `add_zones.py`, `fix_nets.py` (D5, D16, D50), `stitch.py`. Roteando o GND como plano, dois pinos GND do Mega ficaram num grupo de cobre sem saída; roteando o GND junto, o Freerouting resolveu.

```
python3 tools/check_netlist.py --board snes
kicad-cli sch erc boards/snes/hardware/dumper.kicad_sch
kicad-cli pcb drc boards/snes/hardware/dumper.kicad_pcb
tools/export_fab.sh snes v1.0
```

**Peças opcionais:** o que se perde ao retirar cada componente, e que jogos são afetados, está em [`docs/componentes-opcionais.md`](docs/componentes-opcionais.md).
