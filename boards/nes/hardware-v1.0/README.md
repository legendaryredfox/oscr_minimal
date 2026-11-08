# nes v1.0

![nes v1.0, vista de cima (render 3D do KiCad)](../renders/nes-v1.0-cima.png)

![nes v1.0, vista de baixo (render 3D do KiCad)](../renders/nes-v1.0-baixo.png)

Versão **v1.0** da placa [`nes`](../README.md): shield 100% THT para Arduino Mega 2560 R3, só USB. Versão congelada, mantida ao lado da mais nova.

| | |
|---|---|
| Slots | NES (72p, 2,5 mm), 5 V |
| Circuitos | Si5351 (clock do slot), sem PIC. |
| Tamanho | 110,1 × 65,1 mm |
| Desligar o 5V por software | **não** |
| Projeto KiCad | [`hardware-v1.0/`](.) (`dumper.kicad_pro`, `.kicad_sch`, `.kicad_pcb`) |
| Fábrica (JLCPCB) | `../fab/gerbers-v1.0/`, `../fab/dumper-v1.0-jlcpcb.zip` |
| Renders | `../renders/nes-v1.0-cima.png`, `../renders/nes-v1.0-baixo.png` |
| Estado | Nada montado nem testado com cartucho; revisar o layout no KiCad antes de encomendar |

## Troca de cartucho

**Sem desligamento por software.** O 5V vai direto do Mega aos slots. Para trocar o cartucho, **desligue a placa tirando o cabo USB** do Mega; nunca com a USB ligada.

## Lista de peças

| Referências | Valor | Footprint | Qtd |
|---|---|---|---|
| A1 | Mega2560_R3_Shield | `dumper:Mega2560_R3_Shield` | 1 |
| C1 | 470u/16V | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` | 1 |
| C2 | 100n | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | 1 |
| D1 | LED 3mm | `LED_THT:LED_D3.0mm` | 1 |
| FLG1,FLG2 | PWR_FLAG | `` | 2 |
| NES1 | NES_Slot | `dumper:NES_Slot` | 1 |
| R1 | 220R | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | 1 |
| U1 | Si5351_Module | `Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical` | 1 |

Gerada do esquemático desta versão (`kicad-cli sch export bom`). Peças marcadas DNP ou opcionais: `docs/componentes-opcionais.md` da placa.

## Verificação e fábrica (da raiz do repositório)

```
python3 tools/check_netlist.py --board nes --sem-troca boards/nes/hardware-v1.0/dumper.kicad_sch
kicad-cli sch erc boards/nes/hardware-v1.0/dumper.kicad_sch
kicad-cli pcb drc boards/nes/hardware-v1.0/dumper.kicad_pcb
HWDIR=hardware-v1.0 GDIR=gerbers-v1.0 tools/export_fab.sh nes v1.0
tools/render_board.sh nes v1.0 v1.1
```

Mais: [README da placa](../README.md), [`docs/`](../docs/).
