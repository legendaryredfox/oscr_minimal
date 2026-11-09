# BOM — placa 16_bits (SNES e Mega Drive) v. 1.2

> **Versões (D128, D139):** nenhuma versão tem a chave de 5V (Q1, R16 a R18, D2), o botão de reset (SW1) nem o bloco de troca de cartucho. A lista de peças de cada versão está em `../fab/bom-v1.2.csv` e `../fab/bom-v1.3.csv`; a v1.3 acrescenta o seletor de tensão (ver `versoes.md`). Nenhuma versão tem TVS nem resistores em série de 470 Ω (D140).

> **Atualização D130 e D140:** a v1.2 ficou sem os 12 TVS (D3 a D14, D130) e a v1.3 também os perdeu em 2026-11-09 (D140), junto com o R15 (pull-up de `/VRES`, DNP) e as redes RN1 a RN5; a v1.2 congelada mantém o R15. Os resistores série R3 a R14 continuam. Menções a D3 a D14 e RN que restarem neste texto são históricas.

Montagem **manual** (sem montagem pela JLCPCB). Esta lista vem de `boards/16_bits/fab/bom-v1.3.csv` (gerado do esquemático) mais as peças que não têm símbolo (pinos, espaçadores, cabo).

> **Pendências antes de comprar (conferir quando as peças chegarem):**
> - Medidas reais dos slots e do módulo Si5351 (estimadas: `docs/decisoes.md` D17, D23).
> - Direção da etiqueta de cada slot (D27).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/16_bits/fab/dumper-v1.2-jlcpcb.zip` |
| Camadas | 2 |
| Dimensões | 108,1 × 86,1 mm (largura acima de 100 mm: faixa de preço maior) |
| Espessura | 1,6 mm |
| Acabamento | HASL (com chumbo ou sem; sem chumbo é mais comum) |
| Quantidade | 5 |
| Cor / máscara | tanto faz (padrão verde) |
| Cobre | 1 oz |
| Furos | 404 metalizados (mín. 0,3 mm; 89 deles são vias), 7 não metalizados (3,2 mm: 4 de canto e 3 alinhados com o Mega) |
| Demais | trilha/espaço mín. 0,2 mm / 0,2 mm; sem borda castelada; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (placa do usuário, USB-C) | `Mega2560_R3_Shield` | **Não vai na compra da placa.** Os pads do shield pedem pinos macho longos (abaixo). |
| SNES1 | 1 | Slot de cartucho SNES/SFC 62 pinos, passo 2,5 mm | `SNES_Slot` | Igual ao do OSCR. |
| MD1 | 1 | Slot de cartucho Mega Drive/Genesis 64 pinos, passo 2,54 mm | `MD_Slot` | Igual ao do OSCR. |
| U1 | 1 | Módulo Si5351 (CJMCU-5351, 25 MHz) | header fêmea 1x7 2,54 mm | Pinos: VIN, GND, SDA, SCL, 2, 1, 0. |
| U1 (header) | 1 | Header fêmea 1x7, 2,54 mm | `PinSocket_1x07_P2.54mm_Vertical` | |
| U2 | 1 | PIC12F629-I/P (DIP-8), gravado com `snescic-lock-resync.hex` | | Fora do soquete até o teste de tensão. |
| U2 (soquete) | 1 | Soquete DIP-8 tradicional (7,62 mm), de preferência de pino torneado | `DIP-8_W7.62mm` | **O PIC é removível:** vai sempre no soquete (troca, regravação e manutenção sem dessoldar). O footprint é o do CI; o soquete encaixa nos mesmos 8 furos. |
| D1 | 1 | LED 3 mm, qualquer cor | `LED_D3.0mm` | Ativo em nível baixo (cátodo no D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| R2 | 1 | 1 kΩ 1/4 W | idem | Pull-up do D7 (IRQ do SNES). |
| C1 | 1 | 470 µF / 16 V eletrolítico, radial, Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2, C3, C4, C5, C6 | 5 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | Um por slot (C2 SNES, C3 Mega Drive), um no PIC (C4) e, na v. 1.2, dois extras no slot Mega Drive: C5 junto ao pino A31 e C6 junto ao A2 (5V). |
| R3 a R14 | 12 | 0 Ω (fio) de fábrica; 47 a 100 Ω depois dos testes | `R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` | Série das linhas de controle (D2 a D9, D14 a D17), em pé. `docs/v12-final.md`. |
| TP1 a TP6 | 6 | Pontos de teste: pad de 2 mm, furo de 1 mm (`TestPoint_THTPad_D2.0mm_Drill1.0mm`) | só cobre | Na placa, sem peça: `5V`, `GND`, `/CE`, `/OE`, `/WE`, `/UWR`. Opcional: tira de pinos macho 1x6 de 2,54 mm (os furos ficam a 2,54 mm um do outro). Fora da BOM de compra. |

## Pinos e mecânica (sem símbolo no esquemático)

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo do plástico, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal. Sugestão: 2 tiras 1x40 e 1 tira 2x20 (corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 | Furos de canto da placa; só apoio. Comprimento a definir (o Mega fica sob o shield). |
| Espaçador M3 fêmea-fêmea + 2 parafusos M3 | 3 | Entre o shield e o Mega, nos furos MH5, MH6 e MH7 (alinhados com furos do Mega). Altura = a do encaixe dos pinos; definir com o Mega na mão. |
| Cabo USB-C para USB-C (ou USB-A) | 1 | Interface com o PC (D30). |

## Ferramentas e consumíveis
Ver `boards/16_bits/docs/montagem.md`.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

Peças opcionais a comprar a mais por placa:

| Ref. | Peça | Qtd | Onde |
|---|---|---|---|
| F1 | suporte de clipes para fusível 5×20 mm (Littelfuse série 100, 2 clipes) e fusível de vidro 5×20 mm de 500 mA, ação rápida | 1 + 1 (compre fusíveis de reserva) | todas as versões (v1.2 e v1.3 (a v1.0 já foi encomendada e não muda)) |
| J1 | cabeçalho de 2 pinos de 2,54 mm e um jumper ("TRAVA 3,3 V") | 1 | v1.3 |
| LDO | LD1117V33 (TO-220) | 1 | v1.3 |
| Q4 | IRF9540N (P-MOSFET, TO-220) | 1 | v1.3 |
| Q5 | 2N7000 (TO-92) | 1 | v1.3 |
| C (2) | 100 nF cerâmico e 10 µF/16 V eletrolítico (entrada e saída do LDO) | 2 | v1.3 |
| R (3) | 100 kΩ, 1 kΩ e 220 Ω, axiais 1/4 W | 3 | v1.3 |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.2 e v1.3 (a v1.0 já foi encomendada e não muda) (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.

Seletor 3,3 V/5 V nos slots Mega Drive (resto da placa sempre em 5 V). Preço aproximado das peças extras: menos de US$ 3 por placa (estimativa de varejo, não cotada).
