# Pedido da placa 16_bits v. 1.2 (JLCPCB)

> **Versões (D128):** o texto abaixo é do pedido da v1.2 de 2026-11-06. A v1.2 foi refeita em 2026-11-07 **sem** Q1, R16 a R18, D2 e SW1 (zip novo `dumper-v1.2-jlcpcb.zip`, gerbers em `gerbers-v1.2/`; confira o SHA-256 com `sha256sum`). A **v1.3** (`dumper-v1.3-jlcpcb.zip`, gerbers em `gerbers-v1.3/`) leva o bloco de troca e continua sem o botão. Contagem de furos: v1.2 e v1.3 têm os mesmos 7 furos não metalizados; o número de furos metalizados e de vias mudou, **leia a pré-visualização da fábrica, não a tabela abaixo**. Ver `docs/versoes.md`.

> **D130 (2026-11-08):** a v1.2 foi refeita **sem os 12 TVS (D3 a D14)**; o zip e o SHA-256 abaixo são os novos, e as linhas sobre TVS no texto são da v1.3. A v1.3 não mudou.

Placa **SNES + Mega Drive**, 2 camadas, 108,1 × 86,1 mm. Feita em 2026-11-04 a partir de `../hardware-v1.3/dumper.kicad_pcb`.

## Arquivo

Envie `dumper-v1.2-jlcpcb.zip`. SHA-256: `aee22f2c885a84f732ba62a4675615c2752872510255a19cf38f8e8f922ca59b`. Revisada em 2026-11-06 (D97): trilhas de alimentação alargadas até 0,8 mm onde cabe e alívio térmico dos 3 pads de GND que davam `starved_thermal` trocado por conexão sólida; mesmo silk, mesmos furos e mesma netlist. Os `dumper-v1.0-*.zip` que ainda estão nesta pasta são da revisão anterior e **não** devem ser usados.

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`. A pasta `gerbers-v1.3/` tem os mesmos arquivos mais o `.gbrjob` e os mapas de furos (não vão no zip).

## O que a JLCPCB deve ler do arquivo

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 108,1 × 86,1 mm |
| Furos metalizados / não metalizados | 404 / 7 (os 7 são M3 de 3,2 mm: 4 de canto e 3 alinhados com o Mega) |
| Furo mínimo | 0,3 mm (as 87 vias de 0,6/0,3 mm; mais 2 de 0,8/0,4 mm) |

Se a pré-visualização mostrar outra coisa, **não pague**: avise.

## Revisão final da v. 1.2 (2026-11-06, D108): o que antes era da v1.3

O usuário levou para a v. 1.2 tudo o que estava planejado para a v. 1.3, menos o RP2040. Detalhes e testes de bancada: `docs/v12-final.md`. **A placa foi roteada de novo** (Freerouting, 0 não roteadas; DRC 0 erros, `check_netlist` OK): as trilhas não são as da versão anterior desta pasta.

- 12 resistores série (R3 a R14, 0 Ω) e 12 TVS (D3 a D14, **DNP**) nas linhas de controle; pull-up de `/VRES` (R15, DNP).
- Chave de 5V dos slots (Q1 P-MOSFET, R16 a R18, LED verde D2), comando no D19 (nível baixo liga; o firmware liga no `setup()`).
- Botão de reset (SW1) e três furos M3 alinhados com o Mega (MH5 a MH7). PIC, C4, C6 e pontos de teste mudaram de lugar.
- Compras a mais: 12 resistores 0 Ω (ou 47 a 100 Ω), 3 resistores, 1 P-MOSFET TO-220, 1 LED verde, 1 botão tátil 6 mm, 3 espaçadores M3 com parafusos. Os TVS e o R15 só se for usar.

## O que mudou da v1.0 para a v. 1.2

- Silk com `v. 1.2   2026-11-06` e, a partir da revisão final de 2026-11-06 (D107), o aviso "NÃO COLOQUE NEM RETIRE O CARTUCHO COM USB LIGADO" junto a "UM CARTUCHO POR VEZ".
- **C4 (100 nF do PIC) movido para junto do PIC** (D107): estava a 21,7 mm do VDD e 20 mm do GND; agora a 2,5 mm e 3,6 mm, acima do soquete (rente à borda de cima, a 0,7 mm). O pad antigo era também a passagem do 5V e do GND entre camadas; no lugar entraram duas vias.
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

1. Veja a prévia de cima e de baixo na página da JLCPCB e compare com `../renders/16_bits-v1.2-cima.png` e `../renders/16_bits-v1.2-baixo.png` (a de baixo está espelhada, como se vira a placa).
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

## v1.0 (`dumper-v1.0`, a antiga `rev2`)

O `dumper-v1.0-jlcpcb.zip` é a v1.0 revisada em D97 e **substitui a v1.0 original** (a que foi encomendada, com todas as trilhas de alimentação em 0,3 mm; D110 tirou os gerbers dela do repositório, o histórico do git os guarda). É a **mesma v1.0, sem `/CART`, sem C5 e C6 e sem pontos de teste**, com duas correções (D97): trilhas do `+5V` alargadas até 0,8 mm onde cabe (22 segmentos em 0,8 mm, 9 em 0,6, 1 em 0,5, 2 em 0,4; 14 ficam em 0,3 mm entre pads) e conexão sólida nos 3 pads de GND que davam `starved_thermal`. Silk, furos (325 metalizados, 4 não metalizados), contorno e netlist iguais à v1.0. SHA-256: `7751339eaaf2d1c663c42653bd9cc5245a8797c110befc729391cefc0172da62`. Fontes em `../hardware-v1.0/`, gerbers em `gerbers-v1.0/`.

DRC: 0 erros, 0 ligações abertas, 5 avisos de biblioteca. `check_netlist --board 16_bits` só reclama dos itens da v. 1.2 (`/CART`, C5, C6, TP1 a TP6), que a v1.0 não tem. Exportar de novo: `HWDIR=hardware-v1.0 GDIR=gerbers-v1.0 tools/export_fab.sh 16_bits v1.0`.
