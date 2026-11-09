# famicom_nes v1.0

![famicom_nes v1.0, vista de cima (render 3D do KiCad)](render-cima.png)

![famicom_nes v1.0, vista de baixo (render 3D do KiCad)](render-baixo.png)

Versão **v1.0** da placa [`famicom_nes`](../README.md): shield 100% THT para Arduino Mega 2560 R3, só USB. Versão anterior, mantida ao lado da mais nova.

| | |
|---|---|
| Slots | Famicom (60p) e NES (72p) em paralelo, 5 V; **um cartucho por vez, em um slot só** |
| Circuitos | Si5351, sem PIC. |
| Tamanho | 117,1 × 89,1 mm |
| Desligar o 5V por software | **não** |
| Projeto KiCad | [`hardware-v1.0/`](.) (`dumper.kicad_pro`, `.kicad_sch`, `.kicad_pcb`) |
| Fábrica (JLCPCB) | `../fab/gerbers-v1.0/`, `../fab/dumper-v1.0-jlcpcb.zip` |
| Renders | `render-cima.png`, `render-baixo.png` |
| Estado | Nada montado nem testado com cartucho; revisar o layout no KiCad antes de encomendar |

## Troca de cartucho

**Sem desligamento por software.** O 5V vai direto do Mega aos slots. Para trocar o cartucho, **desligue a placa tirando o cabo USB** do Mega; nunca com a USB ligada.

## Proteção de corrente e tensão (D138)

**F1: fusível de vidro 5×20 mm de 500 mA (ação rápida) em suporte de clipes, opcional.** O suporte é de furo passante (Littelfuse série 100 ou equivalente) e o fusível queimado se troca **sem solda**; fica em série com o 5 V que a placa recebe do Mega (nas versões com bloco de troca, antes do Q1). Um curto no cartucho queima o fusível e protege a placa, o Mega e a porta USB. A queda é de 0,1 a 0,2 V a 200 mA (o SA-1 do SNES continua abaixo de ~5,2 V). **Sem o fusível no suporte a placa fica sem 5 V** (um fio no lugar dele também serve). Ele limita corrente e não protege contra tensão errada.

## Lista de peças

| Referências | Valor | Footprint | Qtd |
|---|---|---|---|
| A1 | Mega2560_R3_Shield | `dumper:Mega2560_R3_Shield` | 1 |
| C1 | 470u/16V | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` | 1 |
| C2,C3 | 100n | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | 2 |
| D1 | LED 3mm | `LED_THT:LED_D3.0mm` | 1 |
| F1 | Fusivel 5x20 500mA | `Fuse:Fuseholder_Littelfuse_100_series_5x20mm` | 1 |
| FC1 | FC_Slot | `dumper:FC_Slot` | 1 |
| FLG1,FLG2 | PWR_FLAG | `` | 2 |
| NES1 | NES_Slot | `dumper:NES_Slot` | 1 |
| R1 | 220R | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | 1 |
| U1 | Si5351_Module | `Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical` | 1 |

Gerada do esquemático desta versão (`kicad-cli sch export bom`). Peças marcadas DNP ou opcionais: `docs/componentes-opcionais.md` da placa.

## Verificação e fábrica (da raiz do repositório)

```
python3 tools/check_netlist.py --board famicom_nes --sem-troca boards/famicom_nes/hardware-v1.0/dumper.kicad_sch
kicad-cli sch erc boards/famicom_nes/hardware-v1.0/dumper.kicad_sch
kicad-cli pcb drc boards/famicom_nes/hardware-v1.0/dumper.kicad_pcb
tools/export_fab.sh famicom_nes v1.0
tools/render_board.sh famicom_nes v1.0 v1.1
```

Mais: [README da placa](../README.md), [`docs/`](../docs/).
