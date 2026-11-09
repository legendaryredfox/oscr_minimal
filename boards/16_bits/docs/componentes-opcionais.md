# 16_bits — componentes que podem ser retirados e o que se perde

> **Versões (D128, D139):** nenhuma versão tem a chave de 5 V (Q1, R16 a R18, D2), o botão de reset (SW1) nem o bloco de troca de cartucho. Ver `versoes.md`.

Placa SNES + Mega Drive v1.2 (`boards/16_bits/`). Tem proteção das linhas de controle (resistores em série R3 a R14; sem TVS desde a D140). Os fatos do SNES (PIC, Si5351, SA-1) são os de `boards/snes/docs/componentes-opcionais.md`.

> **Nada aqui foi testado em hardware.** Fontes: netlist de `hardware-v1.3/dumper.kicad_sch`, `docs/bom.md`, `docs/v12-final.md`, firmware.

## Peças do SNES (U1, U2, R2)

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U2** PIC12F629 (CIC) + soquete | **Perde o SA-1** | O PIC emula o CIC; o SA-1 só responde com ele rodando (D54) | Só cartuchos **SA-1** (Super Mario RPG, Kirby Super Star, Kirby's Dream Land 3, Jikkyou Oshaberi Parodius, Dragon Ball Z: Hyper Dimension e outros; lista não exaustiva em `snes/docs/componentes-opcionais.md`) |
| **U1** módulo Si5351 | **Perde o SA-1**; o PIC fica sem clock | Sai o clock mestre, o do CPU e o do CIC (que o PIC também usa) | SA-1; futuros Satellaview e SF Memory. **Mega Drive não usa** o Si5351 |
| **R2** 1 kΩ (pull-up de D7) | Sim, com cuidado | D7 é o `/IRQ` do SNES **e** o `/UWR` do Mega Drive (pino B29 do slot). Sem o pull-up, essa linha fica solta quando o pino está como entrada. A placa `megadrive/` (sem R2) mostra que o Mega Drive vive sem ele | Nenhum conhecido. Inferência; não medido |

## Linhas de controle (R3 a R14)

| Peça | Retirar? | O que deixa de funcionar |
|---|---|---|
| **R3 a R14** (0 Ω de fábrica, 12 unidades) | **Não: são ligações** | Série das linhas D2 a D9 e D14 a D17. Com 0 Ω são fios; **sem eles as linhas ficam abertas** e nenhum cartucho (SNES ou Mega Drive) lê ou grava. Trocar por 47 a 100 Ω é opcional (proteção, `docs/v12-final.md`) |

## Demais

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **D1** LED + **R1** 220 Ω | Sim | Indicação de atividade | Nenhum |
| **TP1 a TP6** | Sim | Só pontos de medida | Nenhum |
| **C2** (SNES), **C3** (Mega Drive), **C5**, **C6** (extras do Mega Drive) 100 nF | Não recomendado | Desacoplamento. Sem eles, leituras erradas (CRC variável), mais provável com ROM grande (SSF2) e SA-1 | Inferência; não medido |
| **C4** 100 nF (PIC) | Não recomendado | O PIC pode reiniciar | SA-1 |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |
| J1 (jumper TRAVA 3,3 V) | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| LDO, Q4, Q5, C do LDO | Não, se quiser 3,3 V | sem eles o slot fica só em 5 V; o seletor é a tensão padrão (5 V) com o Q4 |

> **Tensão do cartucho (D140):** a placa não tem resistores em série entre o Mega e os slots (as redes RN saíram em D140). Mesmo com o seletor em 3,3 V, as saídas do Mega continuam em 5 V; o seletor só baixa o VCC do cartucho. **Confira a tensão que o cartucho suporta antes de inserir**: um cartucho só de 3,3 V pode ser danificado.

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.2 e v1.3 (a v1.0 já foi encomendada e não muda) (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
