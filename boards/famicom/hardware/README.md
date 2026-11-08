# famicom v1.1

![famicom v1.1, vista de cima (render 3D do KiCad)](../renders/famicom-v1.1-cima.png)

![famicom v1.1, vista de baixo (render 3D do KiCad)](../renders/famicom-v1.1-baixo.png)

Versão **v1.1** da placa [`famicom`](../README.md): shield 100% THT para Arduino Mega 2560 R3, só USB. Esta é a versão mais nova.

| | |
|---|---|
| Slots | Famicom (60p, 2,54 mm), 5 V |
| Circuitos | Sem Si5351 e sem PIC. |
| Tamanho | 107,1 × 65,1 mm |
| Desligar o 5V por software | **sim** |
| Projeto KiCad | [`hardware/`](.) (`dumper.kicad_pro`, `.kicad_sch`, `.kicad_pcb`) |
| Fábrica (JLCPCB) | `../fab/gerbers/`, `../fab/dumper-v1.1-jlcpcb.zip` |
| Renders | `../renders/famicom-v1.1-cima.png`, `../renders/famicom-v1.1-baixo.png` |
| Estado | Nada montado nem testado com cartucho; revisar o layout no KiCad antes de encomendar |

## Troca de cartucho

**Com desligamento por software** (bloco de troca de cartucho, D126): o comando `POWER` liga e desliga o 5V dos slots, o rail é descarregado e o LED amarelo "SEGURO TROCAR" acende quando dá para tirar o cartucho. Circuito, peças e testes: [`docs/bloco-troca.md`](../../../docs/bloco-troca.md).

## O que muda em relação à v1.0

| Peça | Referências | Antes | Agora |
|---|---|---|---|
| LED verde 3mm | D2 | 0 | 1 |
| LED amarelo 3mm | D3 | 0 | 1 |
| IRF9540N | Q1 | 0 | 1 |
| 2N7000 | Q2,Q3 | 0 | 2 |
| 100k | R2,R6 | 0 | 2 |
| 100R | R3 | 0 | 1 |
| 1k | R4,R7,R8 | 0 | 3 |
| 330R | R5 | 0 | 1 |

## Lista de peças

| Referências | Valor | Footprint | Qtd |
|---|---|---|---|
| A1 | Mega2560_R3_Shield | `dumper:Mega2560_R3_Shield` | 1 |
| C1 | 470u/16V | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` | 1 |
| C2 | 100n | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | 1 |
| D1 | LED 3mm | `LED_THT:LED_D3.0mm` | 1 |
| D2 | LED verde 3mm | `LED_THT:LED_D3.0mm` | 1 |
| D3 | LED amarelo 3mm | `LED_THT:LED_D3.0mm` | 1 |
| FC1 | FC_Slot | `dumper:FC_Slot` | 1 |
| FLG1,FLG2 | PWR_FLAG | `` | 2 |
| Q1 | IRF9540N | `Package_TO_SOT_THT:TO-220-3_Vertical` | 1 |
| Q2,Q3 | 2N7000 | `Package_TO_SOT_THT:TO-92_Inline` | 2 |
| R1 | 220R | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | 1 |
| R2,R6 | 100k | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 2 |
| R3 | 100R | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 1 |
| R4,R7,R8 | 1k | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 3 |
| R5 | 330R | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 1 |

Gerada do esquemático desta versão (`kicad-cli sch export bom`). Peças marcadas DNP ou opcionais: `docs/componentes-opcionais.md` da placa.

## Verificação e fábrica (da raiz do repositório)

```
python3 tools/check_netlist.py --board famicom
kicad-cli sch erc boards/famicom/hardware/dumper.kicad_sch
kicad-cli pcb drc boards/famicom/hardware/dumper.kicad_pcb
tools/export_fab.sh famicom v1.1
tools/render_board.sh famicom v1.0 v1.1
```

Mais: [README da placa](../README.md), [`docs/`](../docs/).
