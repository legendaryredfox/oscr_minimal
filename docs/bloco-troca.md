# Bloco de troca de cartucho (hardware, D126)

Todas as placas v1.1 e a `16_bits` v1.3 (D128: o bloco é uma versão separada; as v1.0 e a `16_bits` v1.2 não o têm) ligam e desligam o 5V dos slots **por software** (`POWER`, D116), descarregam o rail e acendem um LED quando é seguro trocar o cartucho. **Não há chave física** (D123). O firmware que usa o bloco está em D116 e D119; o plano de origem é `docs/plano-chave-fisica.md`.

## Circuito

| Função | Peças | Liga |
|---|---|---|
| Chave de alta do 5V | Q1 IRF9540N (P-MOSFET, TO-220), R 100 kΩ, R 100 Ω | fonte no 5V do Mega, dreno em `+5V_CART`; gate em `PWR_G`; o 100 kΩ puxa o gate ao 5V (desligado com o Mega em reset); o 100 Ω liga o D19 (`PWR_EN`) ao gate; **D19 em nível baixo liga** |
| LED verde | R 1 kΩ, LED 3 mm | `+5V_CART` ao GND: aceso = slots energizados |
| Descarga | Q2 2N7000 (TO-92), R 330 Ω (mais um 330 Ω do `+3V3` nas placas com regulador) | gate em `PWR_G`: com Q1 aberto, Q2 conduz e descarrega o rail pelo 330 Ω |
| Sensor do rail | Q3 2N7000, R 100 kΩ (gate ao GND), R 1 kΩ (5V ao nó `SENSE`), R 1 kΩ (nó `SENSE` ao D53), LED 3 mm | gate de Q3 em `+5V_CART`; rail abaixo de ~2 V: Q3 abre, `SENSE` sobe, o LED acende e o D53 lê alto = **seguro trocar** |

O que passa a ser `+5V_CART` (chaveado): VCC dos slots de 5V, Si5351, PIC, o pull-up R2 do D7, os capacitores de 100 nF dos slots e do PIC e, nas placas com regulador de 3,3 V, a entrada do MCP1700 e o capacitor dele. O 5V direto do Mega fica no C1 (470 µF), no LED de status D1, nos pontos de teste de 5V e no Q1.

Pinos do Mega usados: **D19** (`PWR_EN`, PD2) e **D53** (`SENSE_MCU`, PB0). Nenhum slot nem núcleo do OSCR os usa.

## Pontos a conferir na bancada (nada foi montado)

- 2N7000 como detector: o limiar do gate varia de 1 a 2,5 V; o LED amarelo acende entre ~1 e ~2,5 V no rail.
- Queda do Q1 em carga (esperado ≥ 4,7 V em `+5V_CART`) e P-02 (`docs/pesquisa-comunidade.md`): SA-1 não destrava acima de ~5,2 V.
- Com o rail desligado, o VCC do cartucho deve cair abaixo de 0,5 V em até 1 s. Se não cair, o cartucho está sendo alimentado pelos pinos de sinal (`releaseCartPins()` no firmware).
- O 2N7000 do TO-92 tem pinagem S-G-D (1 = fonte, 2 = gate, 3 = dreno); outros transistores (BS170) têm outra e não servem sem rever o footprint.

## Como foi gerado

`tools/troca/`: `sch_block.py` (esquemático: peças novas, símbolos de alimentação `+5V_CART`, rótulos nos pinos D19 e D53), `pcb_block.py` (peças e nets no PCB, posições por busca de lugar livre, apaga trilhas), `route.py` (Freerouting e zonas de GND), `finish.py` (silkscreen, pads de GND sólidos, preenchimento), `boards.json` (parâmetros por placa; `tools/check_netlist.py` lê o mesmo arquivo), `docs.py` (textos das placas). `tools/render_board.sh <placa>` refaz o `render.png`. Referências novas seguem a última de cada tipo da placa (D109).
