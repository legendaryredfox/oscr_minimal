# 16_bits v1.2

![16_bits v1.2, vista de cima (render 3D do KiCad)](render-cima.png)

![16_bits v1.2, vista de baixo (render 3D do KiCad)](render-baixo.png)

Versão **v1.2** da placa [`16_bits`](../README.md): shield 100% THT para Arduino Mega 2560 R3, só USB. Versão anterior, mantida ao lado da mais nova.

| | |
|---|---|
| Slots | SNES (62p) e Mega Drive (64p), 5 V |
| Circuitos | Si5351 em header fêmea e PIC12F629 (CIC do SNES) em soquete. Sem botão de reset em nenhuma versão (D128). |
| Tamanho | 108,1 × 96,1 mm |
| Projeto KiCad | [`hardware-v1.2/`](.) (`dumper.kicad_pro`, `.kicad_sch`, `.kicad_pcb`) |
| Fábrica (JLCPCB) | `../fab/gerbers-v1.2/`, `../fab/dumper-v1.2-jlcpcb.zip` |
| Renders | `render-cima.png`, `render-baixo.png` |
| Estado | Nada montado nem testado com cartucho; revisar o layout no KiCad antes de encomendar |

## Troca de cartucho

O 5V dos slots vai direto do Mega e **não é cortado por software** (o desligamento por software foi retirado, D139). Para trocar o cartucho, **desligue a placa tirando o cabo USB** do Mega; nunca com a USB ligada.

## Proteção de corrente e tensão (D138)

**F1: fusível de vidro 5×20 mm de 500 mA (ação rápida) em suporte de clipes, opcional.** O suporte é de furo passante (Littelfuse série 100 ou equivalente) e o fusível queimado se troca **sem solda**; fica em série com o 5 V que a placa recebe do Mega Um curto no cartucho queima o fusível e protege a placa, o Mega e a porta USB. A queda é de 0,1 a 0,2 V a 200 mA (o SA-1 do SNES continua abaixo de ~5,2 V). **Sem o fusível no suporte a placa fica sem 5 V** (um fio no lugar dele também serve). Ele limita corrente e não protege contra tensão errada.

## Resistores série R3 a R14: existiam e foram retirados (D145)

A v. 1.2 de 2026-11-06 (D108) tinha 12 resistores em série, um em cada linha de controle entre o pino do Mega e o slot do Mega Drive: `D2` a `D9` e `D14` a `D17` (/WRAM, Refresh, /ASEL, EDCLK, /CE, /IRQ ou /UWR, /WR ou /LWR, /RD ou /CAS0, /PAWR, /TIME, /VRES e as demais; lista em `docs/v12-final.md`).

- **Para que serviam:** limitar a corrente nessas linhas. O Mega é 5 V e um cartucho ou adaptador pode ligar a linha ao GND, ao 5 V ou a algo errado (curto, mau contato, tensão alta, ruído); o resistor protegeria o pino do ATmega2560 e o cartucho. Só nas linhas de **controle**, que o Mega aciona como saída. Endereço e dados mudam de direção a cada leitura e precisam ser rápidos, então já iam direto. Montados como 0 Ω (um fio), a leitura era igual à do OSCR; 47 a 100 Ω protegeriam mais, mas deixariam a borda do sinal mais lenta.
- **Por que saíram:** o OSCR original não tem nenhum resistor nessas linhas (o HW5 liga o Mega direto ao slot), com 0 Ω não protegiam nada, e o valor maior nunca foi testado em hardware. Cada linha agora vai direto do pino do Mega ao slot, no mesmo roteamento (as duas redes de cada resistor viraram uma só). A proteção que sobra é o F1.
- **Como foi feito:** `tools/troca/sem_res.py` (mantém o roteamento; cada resistor virou uma ponte de cobre).

## Particularidades desta versão
## Particularidades desta versão

Sem os resistores série das linhas de controle (retirados em D145) e sem os TVS (D130); pull-up de `/VRES` (DNP), `/CART` no D50, C5, C6, pontos de teste e três furos M3 alinhados com o Mega. Sem a chave de 5V (Q1) e sem o botão de reset (D128); D19 e RST ficam sem ligação.

## O que muda em relação à v1.0

| Peça | Referências | Antes | Agora |
|---|---|---|---|
| Fusivel 5x20 500mA | F1 | 0 | 1 |
| 0R | 10k (DNP) | R15 | 0 | 1 |
| 100n | C2,C3,C4,C5,C6 | 3 | 5 |

## Lista de peças

| Referências | Valor | Footprint | Qtd |
|---|---|---|---|
| A1 | Mega2560_R3_Shield | `dumper:Mega2560_R3_Shield` | 1 |
| C1 | 470u/16V | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` | 1 |
| C2,C3,C4,C5,C6 | 100n | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | 5 |
| D1 | LED 3mm | `LED_THT:LED_D3.0mm` | 1 |
| F1 | Fusivel 5x20 500mA | `Fuse:Fuseholder_Littelfuse_100_series_5x20mm` | 1 |
| FLG1,FLG2 | PWR_FLAG | `` | 2 |
| MD1 | MD_Slot | `dumper:MD_Slot` | 1 |
| R1 | 220R | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | 1 |
| R2 | 1k | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | 1 |
| R15 | 10k (DNP) | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal` | 1 |
| SNES1 | SNES_Slot | `dumper:SNES_Slot` | 1 |
| U1 | Si5351_Module | `Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical` | 1 |
| U2 | PIC12F629 (em soquete; snescic-lock-resync) | `Package_DIP:DIP-8_W7.62mm` | 1 |

Gerada do esquemático desta versão (`kicad-cli sch export bom`). Peças marcadas DNP ou opcionais: `docs/componentes-opcionais.md` da placa.

## Verificação e fábrica (da raiz do repositório)

```
python3 tools/check_netlist.py --board 16_bits --sem-tvs boards/16_bits/hardware-v1.2/dumper.kicad_sch
kicad-cli sch erc boards/16_bits/hardware-v1.2/dumper.kicad_sch
kicad-cli pcb drc boards/16_bits/hardware-v1.2/dumper.kicad_pcb
tools/export_fab.sh 16_bits v1.2
tools/render_board.sh 16_bits v1.0 v1.2 v1.3
```

Mais: [README da placa](../README.md), [`docs/`](../docs/). Comparação entre as versões: [`docs/versoes.md`](../docs/versoes.md).
