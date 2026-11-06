# Pedido da placa 16_bits v. 1.2 (JLCPCB)

Placa **SNES + Mega Drive**, 2 camadas, 108,1 × 86,1 mm. Feita em 2026-11-04 a partir de `../hardware/dumper.kicad_pcb`.

## Arquivo

Envie `dumper-v1.2-jlcpcb.zip` (cópia idêntica: `dumper-v1.2-gerbers-jlcpcb.zip`). SHA-256: `84b2866a73c273dd547fffbe28db6aff1bcabff8df97335fd009bf3406414e27`. Revisada em 2026-11-06 (D97): trilhas de alimentação alargadas até 0,8 mm onde cabe e alívio térmico dos 3 pads de GND que davam `starved_thermal` trocado por conexão sólida; mesmo silk, mesmos furos e mesma netlist. Os `dumper-v1.0-*.zip` que ainda estão nesta pasta são da revisão anterior e **não** devem ser usados.

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`. A pasta `gerbers/` tem os mesmos arquivos mais o `.gbrjob` e os mapas de furos (não vão no zip).

## O que a JLCPCB deve ler do arquivo

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 108,1 × 86,1 mm |
| Furos metalizados / não metalizados | 344 / 4 (os 4 são M3 de canto, 3,2 mm) |
| Furo mínimo | 0,3 mm (as 94 vias) |

Se a pré-visualização mostrar outra coisa, **não pague**: avise.

## O que mudou da v1.0 para a v. 1.2

- Silk com `v. 1.2   2026-11-04`.
- `/CART` (B32 do slot Mega Drive) ligado ao pino D50 do Mega: detecção de cartucho (o cartucho liga B32 ao GND; no Mega, `INPUT_PULLUP`).
- Dois capacitores de 100 nF a mais: **C5** junto ao pino A31 (5V) e **C6** junto ao A2 (5V) do slot Mega Drive.
- Seis pontos de teste (pad de 2 mm, furo de 1 mm) numa fileira acima do cabeçalho do Mega, a 2,54 mm um do outro (revisão D99: antes eram 5,5 mm), rotulados na vertical: `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE`. Recebem uma tira de pinos macho 1x6 padrão para a ponta de prova.
- **Não** entraram: resistores série e TVS nas linhas do cartucho (não há espaço sem refazer o roteamento) e o pull-up de `/VRES`.

## Configurações do formulário

| Campo | Valor |
|---|---|
| Base material | FR-4 |
| Layers | 2 |
| Dimensions | 108 × 86 mm (lido do arquivo) |
| PCB Qty | 5 |
| Thickness | 1,6 mm |
| Outer copper weight | 1 oz |
| Surface finish | HASL (com ou sem chumbo, a gosto) |
| Min track / spacing | 0,2 mm / 0,2 mm (projeto usa 0,2 mm; o padrão 5/5 mil serve) |
| Min hole size | 0,3 mm (padrão) |
| Via covering | padrão da fábrica (o projeto não define máscara sobre as vias) |
| Solder mask / silkscreen | **cor à sua escolha** (o projeto não define; verde com silk branco é o padrão) |
| Impedance, gold fingers, castellated, V-cut | não |
| Remove Order Number | opcional (cobra à parte; sem isso a fábrica imprime um código no silk de baixo) |
| Assembly (PCBA), stencil | **não**: montagem manual, tudo THT |

## Antes de pagar

1. Veja a prévia de cima e de baixo na página da JLCPCB e compare com `previa-cima.png` e `previa-baixo.png` desta pasta (a de baixo está espelhada, como se vira a placa).
2. A largura de 108 mm passa de 100 mm, então cai na faixa de preço maior.
3. O silk de baixo tem 3 linhas de crédito (OSCR, sanni, github): conferir que não ficou cortado.

## Compras (para 1 placa; multiplique)

Lista completa e observações: `../docs/bom.md`. Resumo:

| Peça | Qtd |
|---|---|
| Slot de cartucho SNES, 62 pinos, 2,5 mm | 1 |
| Slot de cartucho Mega Drive, 64 pinos, 2,54 mm | 1 |
| Módulo Si5351 (CJMCU-5351) + header fêmea 1x7 | 1 + 1 |
| PIC12F629-I/P + soquete DIP-8 | 1 + 1 |
| LED 3 mm | 1 |
| Resistor 220 Ω e 1 kΩ, 1/4 W | 1 + 1 |
| Capacitor 470 µF/16 V radial Ø8, passo 3,5 mm | 1 |
| Capacitor cerâmico 100 nF, passo 5 mm | 5 |
| Pinos macho 2,54 mm de **cauda longa** | **85 posições** |
| Espaçador M3 + pé de borracha | 4 |
| Cabo USB-C | 1 |

## Pendências que o pedido não resolve (só o hardware responde)

- Corpo e altura reais dos slots (estimados, D17): conferir com o slot comprado.
- Lado da etiqueta do cartucho em cada slot (D27).
- Altura dos espaçadores dos cantos: o USB-C e o jack do Mega têm que passar por baixo do shield.
- O slot SNES foi deslocado para não encostar no header 2x18 do Mega (D71); se o corpo real for maior que a estimativa, confira antes de pedir.

## v1.0 revisada (`dumper-v1.0-rev2`) — para quem já encomendou ou vai encomendar a v1.0

O `dumper-v1.0-jlcpcb.zip` original (o que foi encomendado) tem todas as trilhas de alimentação com 0,3 mm. A `dumper-v1.0-rev2-jlcpcb.zip` (cópia: `-gerbers-`) é a **mesma v1.0, sem `/CART`, sem C5 e C6 e sem pontos de teste**, com duas correções (D97): trilhas do `+5V` alargadas até 0,8 mm onde cabe (22 segmentos em 0,8 mm, 9 em 0,6, 1 em 0,5, 2 em 0,4; 14 ficam em 0,3 mm entre pads) e conexão sólida nos 3 pads de GND que davam `starved_thermal`. Silk, furos (325 metalizados, 4 não metalizados), contorno e netlist iguais à v1.0. SHA-256: `7751339eaaf2d1c663c42653bd9cc5245a8797c110befc729391cefc0172da62`. Fontes em `../hardware-v1.0/`, gerbers em `gerbers-v1.0-rev2/`.

DRC: 0 erros, 0 ligações abertas, 5 avisos de biblioteca. `check_netlist --board 16_bits` só reclama dos itens da v. 1.2 (`/CART`, C5, C6, TP1 a TP6), que a v1.0 não tem. Exportar de novo: `HWDIR=hardware-v1.0 GDIR=gerbers-v1.0-rev2 tools/export_fab.sh 16_bits v1.0-rev2`.
