# 16_bits v1.3

![16_bits v1.3, vista de cima (render 3D do KiCad)](render-cima.png)

![16_bits v1.3, vista de baixo (render 3D do KiCad)](render-baixo.png)

Versão **v1.3** da placa [`16_bits`](../README.md): shield 100% THT para Arduino Mega 2560 R3, só USB. Esta é a versão mais nova.

| | |
|---|---|
| Slots | SNES (62p) e Mega Drive (64p), 5 V |
| Circuitos | Si5351 em header fêmea e PIC12F629 (CIC do SNES) em soquete. Sem botão de reset em nenhuma versão (D128). |
| Tamanho | 108,1 × 126,1 mm |
| Projeto KiCad | [`hardware-v1.3/`](.) (`dumper.kicad_pro`, `.kicad_sch`, `.kicad_pcb`) |
| Fábrica (JLCPCB) | `../fab/gerbers-v1.3/`, `../fab/dumper-v1.3-jlcpcb.zip` |
| Renders | `render-cima.png`, `render-baixo.png` |
| Estado | Nada montado nem testado com cartucho; revisar o layout no KiCad antes de encomendar |

## Troca de cartucho

O 5V dos slots vai direto do Mega e **não é cortado por software** (o desligamento por software foi retirado, D139). Para trocar o cartucho, **desligue a placa tirando o cabo USB** do Mega; nunca com a USB ligada.

## Proteção de corrente e tensão (D138)

**F1: fusível de vidro 5×20 mm de 500 mA (ação rápida) em suporte de clipes, opcional.** O suporte é de furo passante (Littelfuse série 100 ou equivalente) e o fusível queimado se troca **sem solda**; fica em série com o 5 V que a placa recebe do Mega Um curto no cartucho queima o fusível e protege a placa, o Mega e a porta USB. A queda é de 0,1 a 0,2 V a 200 mA (o SA-1 do SNES continua abaixo de ~5,2 V). **Sem o fusível no suporte a placa fica sem 5 V** (um fio no lugar dele também serve). Ele limita corrente e não protege contra tensão errada.

**Seletor de tensão 3,3 V/5 V dos slots Mega Drive** (LDO LD1117V33 em TO-220, Q4 de bypass, Q5 de carga, redes de resistores de 470 Ω em série com as linhas entre o Mega e esses slots, comando no D18). **Padrão: 5 V**; 3,3 V só quando o usuário pede (`--voltage 3v3`, ou o botão da GUI). Passar de 3,3 V para 5 V mostra um alerta e pede confirmação. Os outros slots e o Si5351/PIC ficam direto no 5 V. Cartuchos de 3,3 V ligados em 5 V podem queimar.

**J1: jumper "TRAVA 3,3 V", opcional.** Fechado, prende o gate do Q4 no 5 V e o slot nunca passa de 3,3 V, mesmo com erro de software ou de GUI: é a única defesa independente do firmware. Aberto, o seletor funciona normalmente.

## Particularidades desta versão

A v1.2 mais os 12 TVS 5 V (D3 a D14, DNP), o seletor de tensão 3,3 V/5 V do slot Mega Drive (D138) e os resistores em série das linhas desse slot. Roteada pelo Freerouting: **revisar no KiCad antes de encomendar**.

## O que muda em relação à v1.2

| Peça | Referências | Antes | Agora |
|---|---|---|---|
| 10u/16V | C8 | 0 | 1 |
| TVS ou zener 5V (DNP) | D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13,D14 | 0 | 12 |
| TRAVA 3,3 V | J1 | 0 | 1 |
| IRF9540N | Q4 | 0 | 1 |
| 2N7000 | Q5 | 0 | 1 |
| 100k | R23 | 0 | 1 |
| 1k | R24 | 0 | 1 |
| 220R | R25 | 0 | 1 |
| 470R | RN1,RN2,RN3,RN4,RN5 | 0 | 5 |
| LD1117V33 | U3 | 0 | 1 |
| 100n | C2,C3,C4,C5,C6,C7 | 5 | 6 |

## Lista de peças

| Referências | Valor | Footprint | Qtd |
|---|---|---|---|
| A1 | Mega2560_R3_Shield | `dumper:Mega2560_R3_Shield` | 1 |
| C1 | 470u/16V | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` | 1 |
| C2,C3,C4,C5,C6,C7 | 100n | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | 6 |
| C8 | 10u/16V | `Capacitor_THT:CP_Radial_D5.0mm_P2.00mm` | 1 |
| D1 | LED 3mm | `LED_THT:LED_D3.0mm` | 1 |
| D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13,D14 | TVS ou zener 5V (DNP) | `Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_CathodeUp` | 12 |
| F1 | Fusivel 5x20 500mA | `Fuse:Fuseholder_Littelfuse_100_series_5x20mm` | 1 |
| FLG1,FLG2 | PWR_FLAG | `` | 2 |
| J1 | TRAVA 3,3 V | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | 1 |
| MD1 | MD_Slot | `dumper:MD_Slot` | 1 |
| Q4 | IRF9540N | `Package_TO_SOT_THT:TO-220-3_Vertical` | 1 |
| Q5 | 2N7000 | `Package_TO_SOT_THT:TO-92_Inline` | 1 |
| R1 | 220R | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | 1 |
| R2 | 1k | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | 1 |
| R3,R4,R5,R6,R7,R8,R9,R10,R11,R12,R13,R14 | 0R | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 12 |
| R15 | 10k (DNP) | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 1 |
| R23 | 100k | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 1 |
| R24 | 1k | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 1 |
| R25 | 220R | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | 1 |
| RN1,RN2,RN3,RN4,RN5 | 470R | `Package_DIP:DIP-16_W7.62mm` | 5 |
| SNES1 | SNES_Slot | `dumper:SNES_Slot` | 1 |
| U1 | Si5351_Module | `Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical` | 1 |
| U2 | PIC12F629 (em soquete; snescic-lock-resync) | `Package_DIP:DIP-8_W7.62mm` | 1 |
| U3 | LD1117V33 | `Package_TO_SOT_THT:TO-220-3_Vertical` | 1 |

Gerada do esquemático desta versão (`kicad-cli sch export bom`). Peças marcadas DNP ou opcionais: `docs/componentes-opcionais.md` da placa.

## Verificação e fábrica (da raiz do repositório)

```
python3 tools/check_netlist.py --board 16_bits boards/16_bits/hardware-v1.3/dumper.kicad_sch
kicad-cli sch erc boards/16_bits/hardware-v1.3/dumper.kicad_sch
kicad-cli pcb drc boards/16_bits/hardware-v1.3/dumper.kicad_pcb
tools/export_fab.sh 16_bits v1.3
tools/render_board.sh 16_bits v1.0 v1.2 v1.3
```

Mais: [README da placa](../README.md), [`docs/`](../docs/). Comparação entre as versões: [`docs/versoes.md`](../docs/versoes.md).
