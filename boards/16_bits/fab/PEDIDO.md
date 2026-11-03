# Pedido da placa 16_bits v1.0 (JLCPCB)

Placa **SNES + Mega Drive**, 2 camadas, 108,1 × 86,1 mm. Feita em 2026-11-03 a partir de `../hardware/dumper.kicad_pcb`.

## Arquivo

Envie `dumper-v1.0-jlcpcb.zip` (cópia idêntica: `dumper-v1.0-gerbers-jlcpcb.zip`). SHA-256: `64a4a3fe620ce581fa328a8e2a98fa7e26d390af752000d4fa276ac81d5cc686`.

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`. A pasta `gerbers/` tem os mesmos arquivos mais o `.gbrjob` e os mapas de furos (não vão no zip).

## O que a JLCPCB deve ler do arquivo

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 108,1 × 86,1 mm |
| Furos metalizados / não metalizados | 325 / 4 (os 4 são M3 de canto, 3,2 mm) |
| Furo mínimo | 0,3 mm (as 85 vias) |

Se a pré-visualização mostrar outra coisa, **não pague**: avise.

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
| Capacitor cerâmico 100 nF, passo 5 mm | 3 |
| Pinos macho 2,54 mm de **cauda longa** | **85 posições** |
| Espaçador M3 + pé de borracha | 4 |
| Cabo USB-C | 1 |

## Pendências que o pedido não resolve (só o hardware responde)

- Corpo e altura reais dos slots (estimados, D17): conferir com o slot comprado.
- Lado da etiqueta do cartucho em cada slot (D27).
- Altura dos espaçadores dos cantos: o USB-C e o jack do Mega têm que passar por baixo do shield.
- O slot SNES foi deslocado para não encostar no header 2x18 do Mega (D71); se o corpo real for maior que a estimativa, confira antes de pedir.
