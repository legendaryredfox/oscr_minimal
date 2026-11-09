# Montagem — placa megadrive_sms (Mega Drive + Master System) v1.0

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Todas as referências (R1, C1...) estão no silkscreen e em `boards/megadrive_sms/docs/bom.md`.

> **Segurança:** só um cartucho por vez, **em um dos dois slots** (Mega Drive/Genesis ou Master System/Mark III). A placa não tem 3,3 V: não use adaptador de GB/GBA nela. **Esta versão (v1.0) não tem o desligamento por software:** antes de colocar ou tirar um cartucho, **desligue o cabo USB**; o silkscreen avisa "SÓ TROQUE O CARTUCHO COM O LED AMARELO ACESO".
>
> **Esta placa nunca foi montada nem testada com cartucho.** O layout foi roteado por autoroteador (Freerouting) e conferido por DRC e pela netlist, não à mão. Se algo da lista de testes (seções 5 e 6) falhar, pare e avise antes de seguir.

## 1. Lista de peças

Quantidades e valores: `boards/megadrive_sms/docs/bom.md`. Resumo:

| Grupo | Referências |
|---|---|
| Resistor 220 Ω | R1 (do LED) |
| Capacitores cerâmicos 100 nF | C2 (meio do slot MD), C3 (junto ao pino A31), C4 (junto ao pino A2), C5 (junto ao pino 1 do slot SMS) |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| LED 3 mm | D1 |
| Slot Mega Drive 64 pinos | MD1 |
| Slot Master System 50 pinos (2 × 25) | SMS1 |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Pontos de teste (opcional: tira de pinos macho 1x6, 2,54 mm) | TP1 a TP6 |
| Mecânica | 6 espaçadores M3 + pés de borracha (cantos e meio da borda de baixo) |

Não existem nesta placa: Si5351, PIC, soquete DIP-8 e R2. Se a lista de compras vier da `16_bits`, ignore essas peças.

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm.
- Solda 0,8 mm.
- Fluxo (caneta ou gel) e malha dessoldadora.
- Multímetro com continuidade.
- Alicate de corte.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Resistor R1** (220 Ω, deitado, como no silkscreen).
2. **Capacitores cerâmicos de 100 nF**: C2, C3, C4 e C5 (C5 fica ao lado do pino 1 do slot SMS, na parte de baixo da placa). Eles ficam na faixa entre o slot e a fileira de cima do Mega; C4 e C3 ficam perto das pontas do slot (pinos A2 e A31).
3. **LED D1**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
4. **Capacitor eletrolítico C1 (470 µF)**, respeitando a polaridade (o `+` está no silkscreen), no canto superior esquerdo.
5. **Pontos de teste TP1 a TP6** (fileira junto à borda de baixo, `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE`): a 2,54 mm um do outro, com o rótulo na vertical acima de cada furo. Solde uma tira de pinos macho 1x6 padrão (ou 6 pinos soltos) para ligar um analisador lógico ou uma ponta de prova. **Opcional.**
6. **Slots MD1 e SMS1.** Para cada um: solde os dois pinos das pontas, confira se o slot está reto e assentado, depois o resto. A direção da etiqueta do slot MD está nas setas `v v ETIQUETA v v` do silk; **o silk do SMS ainda não tem a direção da etiqueta** (ver a pendência abaixo); o pino 1 do slot SMS está marcado no silk. Nenhum componente alto fica na frente do slot.
7. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 6 espaçadores M3. Eles só dão altura e apoio nos pés de borracha: **não prendem o shield ao Mega**, que fica preso só pelos pinos.

## 4. Inspeção visual

- Pontes de solda entre pinos dos slots (passo de 2,54 mm, duas fileiras de 32 no MD e de 25 no SMS).
- Juntas frias (solda sem formar cone).
- Polaridade: C1 e D1.
- Os pinos macho longos de todos os pads do Mega, inclusive os sem sinal, estão soldados e retos.

## 5. Testes antes de ligar (multímetro, sem energia)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.** Repita entre os pontos de teste TP1 (5V) e TP2 (GND).
2. **Algumas linhas até o Mega** (conforme `boards/megadrive_sms/docs/pinmap.md`):

| Do slot | Para o pino do Mega | Sinal |
|---|---|---|
| A17 | A0 | endereço A1 |
| A16 | D49 | endereço A17 |
| A20 | D37 | dado D0 |
| B16 | D9 | /CAS0 (leitura de ROM, `/OE`) |
| B17 | D6 | /CE |
| B28 | D8 | /LWR |
| B29 | D7 | /UWR |
| B32 | D50 | /CART (detecção de cartucho) |

3. Pontos de teste: `/UWR` com o D7, `/CE` com o D6, `/OE` com o D9, `/WE` com o D8.
4. Pinos dos slots **sem ligação** (não podem ter continuidade com nada): no MD, B1, B3, B13, B14, B20 e B30; no SMS, 3, 5, 34, 37 a 45 e 47 a 50.
5. **D0 e D1 do Mega** (serial USB) não podem ter continuidade com o slot. D20, D21, D40 e D41 do Mega ficam livres (eram do Si5351 e do PIC nas outras placas).
6. Os GND e 5V dos slots: no MD, GND em A1, A18, A32 e 5V em A2 e A31; no SMS, GND nos pinos 19, 20 e 21 e 5V nos pinos 1 e 35, cada um com o GND e o 5V do Mega, respectivamente.
7. Slot SMS até o Mega (`pinmap.md`): pino 25 (A0) com A0; 24 (D0) com D37; 14 (D7) com D30; 2 (WR) com D8; 4 (RD) com D9; 13 (CE) com D48; 46 (Reset) com D17; 11 e 36 (M0-7 e A15) com D6.

## 6. Primeira energização

Sem cartucho. Conecte o Mega ao PC pelo USB-C.

- Meça **5 V** (±0,25 V) nos pinos A2 e A31 do slot MD e nos pinos 1 e 35 do slot SMS (VCC).
- Meça `/CART` (B32) em relação ao GND: deve estar em nível alto (puxado pelo firmware, `INPUT_PULLUP` em D50) ou flutuante, **nunca em curto** com o GND sem cartucho.
- O LED D1 acende e apaga pelo firmware (ativo em nível baixo, D38).

## 7. Gravar o firmware e testar

Firmware do fork do OSCR: `cd firmware/oscr && ~/.platformio/penv/bin/pio run -e SerialASCII -t upload`. Protocolo: `docs/referencia/protocolo.md`. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. `INFO` deve responder. Se não aparecer a porta serial: veja a seção 9.
3. `detect` do Mega Drive sem cartucho: o slot vazio deve ser informado como sem cartucho (D50 em nível alto).

## 8. Primeiro dump real

O firmware atual do fork lê Master System (`dumper detect -s sms`, `dump -s sms`, `--mapper 0` para o slot desta placa; `--prg` quando o cartucho não tem cabeçalho "TMR SEGA"), Game Gear e SG-1000 (só por adaptador no slot Mega Drive; D137). **Nada disso rodou em hardware:** comece pelo Mega Drive.

Use um cartucho de Mega Drive comum, de ROM mascarada de 512 KB a 1 MB e **sem valor** de coleção. Escolha o sistema Mega Drive, rode `detect` (o cabeçalho `SEGA MEGA DRIVE`/`SEGA GENESIS` deve ser lido e o D50 deve indicar cartucho presente) e depois `dump`. Compare o CRC32 com o do No-Intro (ou com a base de dados do projeto, `identify`). Repita o dump 3 vezes: os três CRC32 têm que ser iguais.

Só depois disso, e na ordem de risco de `docs/referencia/uso.md` seção 7, teste saves (SRAM com backup) e, por último, a gravação de flash (`WRITE_ROM`), em cartucho repro **sem valor**.

## 9. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho todo encaixado; um cartucho por vez; limpeza dos contatos; slot reto; VCC do slot (5 V em A2 e A31); `/CART` (B32) em nível baixo com o cartucho inserido. |
| CRC diverge | Contato oxidado (limpe com álcool isopropílico); refaça o dump 3 vezes; compare com o banco; verifique `/CAS0` (B16) e `/CE` (B17) nos pontos de teste. |
| Leitura com bytes errados em blocos | Capacitores C2, C3 e C4; solda dos pinos A19 a A30 e B22 a B25 (dados); cabo USB com queda de tensão. |
| Porta serial não aparece | Cabo USB-C só de carga (troque); no Linux, adicione-se ao grupo `dialout` (`sudo usermod -aG dialout $USER` e reinicie a sessão); clone com CH340 aparece como `/dev/ttyUSB0`; no Windows/macOS instale o driver CH340. |
| LED não acende | Polaridade (ânodo no 5V); resistor R1; o LED é ativo em nível baixo (D38). |
| `/CART` sempre baixo ou sempre alto | Solda do pino D50 e do B32; trilha de 25 mm entre eles; cartucho com contato B32 sujo. |

## Pendências (a conferir com as peças reais)

- Direção real da etiqueta do slot e se o silk bate (`docs/decisoes.md` D27).
- Medidas dos slots Mega Drive e Master System (D17, D23, D136) e se há folga para a carcaça do cartucho; o espaço entre os dois slots (cerca de 40 mm entre os centros) precisa caber a carcaça do cartucho que estiver no slot MD sem encostar no slot SMS vazio.
- **Direção da etiqueta do cartucho SMS:** não confirmada (sem informação no OSCR nem no smspower.org); confira com o slot recebido e acrescente ao silk antes de encomendar.
- Altura dos espaçadores M3 dos cantos (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
- A placa foi roteada por autoroteador: confira as trilhas no KiCad e faça o teste de continuidade da seção 5 com atenção.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

1. **Suporte do F1** (clipes para fusível 5×20 mm, furo passante) entra com os componentes baixos, na faixa de 10 mm acrescentada à borda de baixo da placa; solde os 4 furos (as duas pernas de cada clipe). O fusível **não vai soldado**: encaixe um fusível de vidro 5×20 mm de 500 mA (ação rápida) nos clipes depois dos testes, e troque-o assim quando queimar.
2. Teste antes de ligar, com o fusível encaixado: continuidade entre os dois clipes (menos de 2 Ω) e nenhuma entre 5 V e GND.
3. **Seletor (v1.1)**: solde os resistores comuns, os capacitores, o Q2, o LDO e o Q1 (TO-220 em pé) e o J1 (cabeçalho de 2 pinos, **sem o jumper**).
4. Gravar `pio run -e SerialASCII_Volt -t upload` (firmware com o seletor no D18). A placa sobe em 3,3 V (estado seguro) e os comandos de cartucho passam a **5 V** sozinhos (padrão); `dumper voltage 3v3` escolhe 3,3 V.
5. Medidas sem cartucho: em 5 V, o VCC dos slots fica entre 4,6 e 5,1 V (queda do fusível e do Q1); com `--voltage 3v3`, entre 3,2 e 3,4 V (LDO). Com o J1 fechado, `--voltage 5v` não consegue passar de 3,3 V.
6. Os slots Mega Drive, Master System são os únicos com seletor de tensão; o resto da placa (Si5351, PIC e outros slots) fica sempre em 5 V. **Confira a tensão que o cartucho suporta antes de inserir:** a placa não limita as saídas de 5 V do Mega para um cartucho de 3,3 V (D140).
