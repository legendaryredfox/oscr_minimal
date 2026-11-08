# 16_bits — componentes que podem ser retirados e o que se perde

> **Versões (D128):** a seção da chave de 5 V (Q1, R16 a R18, D2) e a linha do SW1 valem só como história da v1.2 de 2026-11-06. Hoje a **v1.2 não tem** essas peças nem o botão de reset; a **v1.3** tem o bloco de troca de `../../../docs/bloco-troca.md` (e também não tem o botão). Ver `versoes.md`.

Placa SNES + Mega Drive v1.2 (`boards/16_bits/`). É a única com chave de 5 V (Q1), proteção das linhas de controle e botão de reset. Os fatos do SNES (PIC, Si5351, SA-1) são os de `boards/snes/docs/componentes-opcionais.md`.

> **Nada aqui foi testado em hardware.** Fontes: netlist de `hardware/dumper.kicad_sch`, `docs/bom.md`, `docs/v12-final.md`, `docs/troca-de-cartucho.md`, firmware.

## Peças do SNES (U1, U2, R2)

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U2** PIC12F629 (CIC) + soquete | **Perde o SA-1** | O PIC emula o CIC; o SA-1 só responde com ele rodando (D54) | Só cartuchos **SA-1** (Super Mario RPG, Kirby Super Star, Kirby's Dream Land 3, Jikkyou Oshaberi Parodius, Dragon Ball Z: Hyper Dimension e outros; lista não exaustiva em `snes/docs/componentes-opcionais.md`) |
| **U1** módulo Si5351 | **Perde o SA-1**; o PIC fica sem clock | Sai o clock mestre, o do CPU e o do CIC (que o PIC também usa) | SA-1; futuros Satellaview e SF Memory. **Mega Drive não usa** o Si5351 |
| **R2** 1 kΩ (pull-up de D7) | Sim, com cuidado | D7 é o `/IRQ` do SNES **e** o `/UWR` do Mega Drive (pino B29 do slot). Sem o pull-up, essa linha fica solta quando o pino está como entrada. A placa `megadrive/` (sem R2) mostra que o Mega Drive vive sem ele | Nenhum conhecido. Inferência; não medido |

## Chave de 5 V e indicador (Q1, R16, R17, R18, D2)

A rede `+5V_CART` (SNES, Mega Drive, Si5351, PIC, C2 a C6, R2, R15) vem do 5 V do Mega **só através do Q1** (P-MOSFET, fonte no 5 V, dreno em `+5V_CART`). O D19 comanda a porta (R17); R16 mantém a porta em 5 V (desligado) até o firmware ligar.

| Peça | Retirar? | O que deixa de funcionar |
|---|---|---|
| **Q1** | **Só com ponte** | Sem Q1 e sem ponte, **nenhum slot, Si5351 nem PIC recebe 5 V**. Com um fio entre dreno e fonte (pads 2 e 3), a placa funciona, mas fica **sempre ligada**: perde o comando `POWER` de trocar o cartucho sem tirar o USB (D116, `docs/troca-de-cartucho.md`) e o aviso "não troque com USB ligado" volta a valer em tempo integral |
| **R16** 100 kΩ | Não | Sem o pull-up a porta flutua e Q1 pode ligar por conta própria no boot (cartucho energizado sem o firmware mandar) |
| **R17** 100 Ω | Não | Série do comando D19; sem ele um curto na porta chega direto ao pino do Mega |
| **R18** 1 kΩ + **D2** LED verde | Sim | Só o indicador de 5 V dos slots. Nenhum jogo afetado |

> **Atualização D130 (2026-11-08):** a **v1.2 ficou sem os 12 TVS (D3 a D14)**; os resistores série R3 a R14 continuam. A **v1.3** mantém os TVS (DNP). Onde este texto fala de D3 a D14, vale só para a v1.3.

## Linhas de controle (R3 a R14, D3 a D14)

| Peça | Retirar? | O que deixa de funcionar |
|---|---|---|
| **R3 a R14** (0 Ω de fábrica, 12 unidades) | **Não: são ligações** | Série das linhas D2 a D9 e D14 a D17. Com 0 Ω são fios; **sem eles as linhas ficam abertas** e nenhum cartucho (SNES ou Mega Drive) lê ou grava. Trocar por 47 a 100 Ω é opcional (proteção, `docs/v12-final.md`) |
| **D3 a D14** (TVS/zener, DNP) | Já vêm sem montar | Sem efeito. Montar só dá proteção a ESD |
| **R15** 10 kΩ (DNP) | Já vem sem montar | Seria o pull-up de `/VRES` do Open EverDrive |

## Demais

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **D1** LED + **R1** 220 Ω | Sim | Indicação de atividade | Nenhum |
| **SW1** botão de reset | Sim | Só o reset manual do Mega | Nenhum |
| **TP1 a TP6** | Sim | Só pontos de medida | Nenhum |
| **C2** (SNES), **C3** (Mega Drive), **C5**, **C6** (extras do Mega Drive) 100 nF | Não recomendado | Desacoplamento. Sem eles, leituras erradas (CRC variável), mais provável com ROM grande (SSF2) e SA-1 | Inferência; não medido |
| **C4** 100 nF (PIC) | Não recomendado | O PIC pode reiniciar | SA-1 |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |
