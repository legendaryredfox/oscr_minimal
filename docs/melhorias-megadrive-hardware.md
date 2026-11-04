# Melhorias de hardware para o Mega Drive (adiadas)

Estado (2026-11-04, mais tarde): o usuário pediu para **aplicar** parte dos itens na `16_bits`, que virou a **v. 1.2**. Aplicados e verificados por DRC, ERC e `check_netlist`: HW-MD-2, HW-MD-5 e HW-MD-6. **Não aplicados:** HW-MD-3 e HW-MD-4 (sem espaço no roteamento atual) e HW-MD-1 (não pedido). HW-MD-7 já estava verificado. Nada foi montado nem testado em cartucho. Gerbers: `boards/16_bits/fab/dumper-v1.2-jlcpcb.zip`.

Origem: revisão do PCB V1.0 do `md_rewriter` (`~/development/hardware/md_rewriter/docs/HARDWARE_REVIEW.md`, `docs/KY_SUPPORT.md`) cruzada com `boards/16_bits/docs/pinmap.md`. As melhorias de firmware correspondentes estão em `docs/melhorias-megadrive.md`.

## Placas afetadas

| Placa | Slot Mega Drive | Observação |
|---|---|---|
| `boards/16_bits/` | sim (MD1) | Alvo principal. Nada encomendado. |
| `boards/16_and_8_bits/` | sim | Mesmas linhas do slot MD; os itens valem igual. |
| `boards/completa/` (esqueleto) | previsto | Herdar os itens ao detalhar. |
| `boards/8_bits/` (esqueleto) | não | Master System e Game Gear entram aqui (item HW-MD-8). |

Regra do `CLAUDE.md` que continua valendo para todos os itens: pinagem idêntica ao OSCR HW5. Item que ligue um sinal a um pino novo do Mega precisa de aprovação do usuário e de uma linha em `docs/decisoes.md`.

## Itens

Prioridade: **A** = pode impedir uma função de Mega Drive; **B** = robustez; **C** = conveniência.

| # | Pri. | Melhoria | Por quê | Mudança | Critério de aceitação |
|---|---|---|---|---|---|
| HW-MD-1 | A (só Open EverDrive) | Pull-up de 10 kΩ em `/VRES` (B27), com pad **não montado (DNP)** por padrão | O programador do Open EverDrive exige esse pull-up para gravar o menu do cartucho. No `pinmap.md`, `/VRES` (B27) e `/MRES` (B2) vão ao mesmo pino, D17 (PH0). | 1 resistor THT de 10 kΩ de B27 a 5V, com jumper ou footprint que permita não montar. | Com o resistor montado, o PC mede B27 em 5V com o cartucho fora; sem ele, a placa se comporta como hoje. Conferir que o pull-up não atrapalha o uso de D17 como saída de reset. |
| HW-MD-2 | C | Detecção de cartucho no pino `/CART` (B32) | Hoje B32 está sem ligação. O cartucho de Mega Drive liga o pino ao GND. Permitiria o firmware recusar `WRITE_ROM`/`ERASE` sem cartucho e nunca "gravar no vazio". | Ligar B32 a um pino livre do Mega, com `INPUT_PULLUP` interno (sem componente novo). **Pino novo: precisa de aprovação.** Escolher entre os pinos livres de `boards/16_and_8_bits/docs/pinmap.md`. | `DETECT` informa "sem cartucho" com o slot vazio. Firmware compatível com a placa antiga (pino ausente = sem detecção). |
| HW-MD-3 | B | Footprints para resistor série (33–100 Ω) nas linhas de endereço e dados do slot MD (cerca de 40 linhas) | O shield liga as linhas do cartucho direto aos pinos do Mega. Um curto ou um cartucho com defeito pode queimar uma porta. O `md_rewriter` V1.0 tem o mesmo problema (achado M3). | Footprints de resistor THT (ou rede SIP) em série, populados com 0 Ω por padrão e trocáveis. Conferir antes os tempos do OSCR: os ciclos de escrita têm 62,5 ns por instrução; 100 Ω com a capacitância das trilhas pode estourar a margem. | Leitura de ROM e escrita de flash continuam idênticas byte a byte com 0 Ω. Com 33 Ω, a leitura em velocidade total passa na suíte de bancada. |
| HW-MD-4 | B | Diodos TVS / proteção de ESD nas linhas do cartucho | Cartucho tocado por quem trocou de jogo é a causa mais comum de falha de porta. | TVS de 5 V THT (ou array) nas linhas de controle (`/WE`, `/OE`, `/CE`, `/UWR`, `/LWR`, `/CAS2`, `/TIME`, `/VRES`) e, se couber, nos endereços. | Sem aumento de capacitância que quebre a leitura; ERC e DRC sem avisos. |
| HW-MD-5 | B | Desacoplamento do slot MD junto aos pinos de 5V | Achado M6 do `md_rewriter`. O shield tem 100 nF por slot (C3 no MD), mas a distância até os pinos A2 e A31 não foi medida. | Posicionar C3 a menos de 10 mm de A2 e A31, ou acrescentar um segundo capacitor de 100 nF. | Medido no layout: distância ≤ 10 mm. Sem ruído que cause erro de leitura na suíte de bancada. |
| HW-MD-6 | C | Pontos de teste: 5V, GND, `/WE` (PH5), `/CE` (PH3), `/OE` (PH6), `/UWR` (PH4) | Depurar gravação de flash com osciloscópio ou analisador lógico sem tocar nos pinos do slot. | Pinos de teste THT de 1 mm, rotulados no silkscreen em português. | Todos acessíveis com o cartucho inserido. |
| HW-MD-7 | A (**verificado 2026-11-04**) | Conferir no esquemático e no PCB que `/UWR` (B29→D7) e `/CAS2` (B21→D3) chegam ao slot MD | O `pinmap.md` já os lista, mas as notas das fontes (`-fw` em B21) indicam que o firmware do OSCR não depende de `/CAS2`. Eles habilitam escrita de palavra completa e a seleção de EEPROM/SRAM em `200000h` a `3FFFFFh`. | Só verificação (`tools/check_netlist.py --board 16_bits`); corrigir só se faltar. **Feito:** 66 nets e 213 ligações conferem com o `pinmap.md`, incluindo B21 (`/CAS2`, D3) e B29 (`/UWR`, D7). O script tinha os números antigos dos capacitores da `16_bits` (3, 5, 6) e foi corrigido para (2, 3, 4); a placa não mudou. | `check_netlist.py` sem divergências nesses dois pinos. ✅ |
| HW-MD-8 | fora do escopo desta placa | Master System e Game Gear | O conector é outro (adaptador ou slot próprio). | Tratar na variante `boards/8_bits/`. | Nada a fazer em `16_bits`. |

## Não se aplicam ao `oscr_minimal`

Achados do `md_rewriter` V1.0 que existem só por causa do STM32 e **não** valem aqui, porque USB, alimentação e programação são do Arduino Mega:

- H1: USB-C sem resistores Rd no CC.
- H2, H3, H4: erros de dados do projeto (pinos, rótulos, BOM) do PCB V1.0 do `md_rewriter`.
- M4, M5: SWD e BOOT0.
- F1 e LDO; cristal.
- L3: MCU de 3,3 V falando com cartucho de 5 V. O Mega é 5 V; o VCC do slot é 5 V direto.

## Resultado da v. 1.2 da `16_bits` (2026-11-04)

| Item | Resultado |
|---|---|
| HW-MD-2 `/CART` | **Feito.** B32 do MD1 ligado ao D50 do Mega (PB3; D39 era o pino do botão no OSCR, então foi evitado). Trilha de 25 mm, 2 vias. Firmware ainda não lê o pino: `INPUT_PULLUP` em PB3, baixo = cartucho presente. Placas antigas deixam o pino flutuando (pull-up interno lê alto): o firmware não pode tratar "alto" como erro sem saber a revisão da placa. |
| HW-MD-5 capacitor junto ao A2 e ao A31 | **Feito.** O C3 estava a 10,7 mm do A2 (e a 83 mm do A31). C5 (100 nF) a 8,4 mm do A31 e C6 (100 nF) a 5,5 mm do A2, sem mexer no C3. Os 5V de cada um entram a 1 a 3 mm numa trilha de 5V que já existia; o GND vem do plano. |
| HW-MD-6 pontos de teste | **Feito.** Fileira de seis pads de 2 mm acima do cabeçalho do Mega (y = 56,5 mm, x de 34 a 61 mm, passo 5,5 mm), com legenda no silk: `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE`. Cada sinal chega por uma trilha de 5 a 40 mm que sai dos pinos do Mega. Pedido do usuário: juntos, perto de qualquer borda, e juntar pesa mais do que a borda. |
| HW-MD-3 resistores série, HW-MD-4 TVS | **Não aplicado.** Todas as redes de controle (`/D6` `/D7` `/D8` `/D9` `/D3` `/D17`) são compartilhadas entre o slot Mega Drive, o slot SNES e o Mega, com 75 a 156 mm de trilha cada; abaixo do cabeçalho do Mega e no leque dos pads do slot o mapa de folgas não tem uma célula livre nas duas camadas. Inserir um resistor em série exige cortar a rede junto ao pino do Mega ou do slot e refazer o roteamento ao redor. Fica para uma revisão com o roteamento refeito (ou um adaptador entre o slot e a placa). |
| HW-MD-1 pull-up de `/VRES` | Não pedido nesta rodada. |

## Ordem sugerida, quando o hardware voltar à pauta

1. HW-MD-7 (só verificar, sem custo).
2. HW-MD-1 e HW-MD-5 (um resistor e um ajuste de posição).
3. HW-MD-3 e HW-MD-4 (precisam medir os tempos do firmware antes).
4. HW-MD-2 e HW-MD-6 (conveniência; HW-MD-2 precisa de pino novo aprovado).

## Pendências para decidir antes de qualquer mudança

- Qual pino livre do Mega usar para `/CART` (HW-MD-2).
- Se resistores série vão em todas as linhas ou só nas de controle (HW-MD-3).
- Se vale gerar uma revisão `v1.1` da `16_bits` ou esperar o primeiro teste em bancada com a placa v1.0.
