# Seletor de tensão, F1 e J1 (D138; sem desligamento por software, D139)

O 5V dos slots **vai direto do Mega e não é cortado por software** em nenhuma placa. O bloco de troca de cartucho (Q1, Q2, Q3, LEDs verde e amarelo, D19 e D53; D115 a D128) foi retirado em D139: **para trocar o cartucho, desligue o USB.** O que ficou de proteção e de tensão está abaixo.

## F1: fusível

Fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega (`+5V` -> F1 -> `+5V_CART`). Queda de 0,1 a 0,2 V a 200 mA (o SA-1 do SNES não destrava acima de ~5,2 V: segue abaixo). **Opcional**: sem fusível no suporte a placa fica sem 5 V (um fio no lugar também serve). O suporte (cerca de 24 × 6,5 mm) fica numa faixa de 10 mm acrescentada à borda de baixo de cada placa. Está em todas as versões, exceto na `16_bits` v1.0 (já encomendada).

## Seletor 3,3 V/5 V (v1.1 com slot de 5 V e `16_bits` v1.3)

- LDO LD1117V33 (TO-220) com entrada em `+5V_CART` e saída em `VCC_CART`. O Q4 (IRF9540N) liga `+5V_CART` a `VCC_CART` quando o D18 está baixo (5 V); aberto, o LDO dá 3,3 V.
- Q5 (2N7000) e 220 Ω seguram o `VCC_CART` em 3,3 V quando os sinais de 5 V injetam corrente.
- 100 kΩ entre o gate do Q4 e `+5V_CART`: com o Mega em reset o Q4 fica aberto (3,3 V, o estado seguro de hardware). O comando do D18 passa por 1 kΩ.
- Só o VCC dos slots com seletor e os capacitores deles ficam no `VCC_CART`; Si5351, PIC e pull-ups ficam no `+5V_CART`.
- **Sem resistores em série (D140):** as redes DIP-16 de 470 Ω (RN) e os TVS DNP da `16_bits` saíram. As saídas do Mega vão direto aos slots, também no modo 3,3 V: o seletor só baixa o VCC do cartucho, os sinais continuam em 5 V. **Confira a tensão que o cartucho suporta antes de inserir**; um cartucho só de 3,3 V pode ser danificado. A proteção que fica é a do Arduino e do shield (fusível F1 e, na `16_bits`, os resistores série R3 a R14 das linhas de controle).
- **J1 "TRAVA 3,3 V":** entre o gate do Q4 e `+5V_CART`; fechado, o Q4 nunca conduz e o 5 V fica impossível, mesmo com erro de software ou de GUI. É a única defesa independente do firmware contra 5 V no VCC do cartucho. Opcional.

Placas com seletor: `megadrive`, `nes`, `famicom`, `famicom_nes`, `megadrive_sms` (v1.1) e `16_bits` (v1.3, slot Mega Drive). Sem seletor: `snes` (o SA-1 precisa de 5 V), os slots de 5 V da `16_and_8_bits` (o seletor ainda não foi roteado nela), `gb_gba` e `n64` (3,3 V).

## Firmware e programa do PC

- Ambiente `SerialASCII_Volt` (`pio run -e SerialASCII_Volt -t upload` em `firmware/oscr`); as placas sem seletor usam `SerialASCII`.
- Como o 5V nunca é cortado, **abrir a porta reinicia o Mega** e o seletor sobe em **3,3 V** (o estado de VCC mais baixo: o cartucho não recebe 5 V no VCC antes de o host escolher; os sinais do Mega seguem em 5 V, ver acima). Antes de um comando que precisa do cartucho, a CLI e a GUI passam a **5 V** (padrão dos flashcarts comuns, D138), a menos que o usuário tenha escolhido 3,3 V (`--voltage 3v3`, botão da GUI).
- Passar de 3,3 V (escolhido) para 5 V mostra um alerta e pede confirmação (`--allow-5v` em script). Falha de leitura nunca muda a tensão sozinha.
- Protocolo: comando `VOLT` (`docs/referencia/protocolo.md`). CLI: `dumper voltage status|3v3|5v` e a opção `--voltage auto|3v3|5v`.

## Pontos a conferir na bancada (nada foi montado)

- Corrente injetada pelos sinais de 5 V no `VCC_CART` a 3,3 V, limiar do Q4/Q5 e queda do fusível são cálculos, não medidas.
- Em 5 V, o VCC dos slots deve ficar entre 4,6 e 5,1 V; em 3,3 V, entre 3,2 e 3,4 V.
- Trocar de tensão com o cartucho no slot não é seguro por si só: o 5V não é cortado. Troque o cartucho só com o USB desligado.

## Como foi gerado

`tools/troca/`: `v138.py` (F1, J1, seletor e resistores em série a partir da v1.0; estes saíram em D140), `sch_block.py` e `pcb_block.py` (esquemático e PCB), `route.py` e `finish.py` (Freerouting e acabamento), `sem_bloco.py` (retirou o bloco de troca das v1.1 já roteadas, D139, mantendo o roteamento: o Q1 virou um jumper de cobre), `sem_rn.py` (retirou as redes RN e as peças DNP das v1.1 e da `16_bits` v1.3 já roteadas, D140: cada par de furos vira uma ponte de cobre achada por um roteador A* próprio, com trilha de 0,3 mm ou, nos espaços apertados, 0,2 mm; o que não coube fica aberto para fechar à mão), `verifica.sh` (DRC e ERC), `boards.json` (parâmetros por placa). `tools/check_netlist.py` lê o `d138.json` de cada versão.

## Por que LDO + Q4 + Q5 e não o TPS2113 do OSCR (D147)

O OSCR (módulo VSelect) usa o **TPS2113**, um chip que escolhe entre duas fontes de 5 V. Aqui ficamos com LDO + Q4 + Q5 por estes motivos:

- **Só existe em SMD** (TSSOP-8, pitch 0,65 mm). O projeto é 100% THT (a única exceção é o slot do GBA). Soldar à mão é difícil, e a montagem na fábrica cobra taxa de setup e peça "estendida" na JLCPCB; o README do VSelect diz que não compensa para menos de 10 módulos.
- **Ele não gera o 3,3 V**, só escolhe entre duas fontes. O LDO continuaria necessário.
- **O custo da peça é parecido** com o do nosso conjunto (estimativa de memória, sem consulta de preço).

Alternativas THT avaliadas e descartadas: relé de sinal DPDT (maior, tem bobina, mais caro), diodo-OR de Schottky (perde 0,3 a 0,5 V e não troca 3,3/5 V), chave analógica CD4066 (resistência de dezenas de ohms, alta demais para o VCC), chave SPDT ou jumper (manual; o J1 já cumpre esse papel) e módulo SMD pronto em header (peça extra). O que o TPS2113 teria a mais (comutação sem queda, limite de corrente ajustável) fica para uma versão futura, se valer o SMD.

