# Montagem — placa megadrive (só Mega Drive) v1.0

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Todas as referências (R1, C1...) estão no silkscreen e em `boards/megadrive/docs/bom.md`.

> **Segurança:** só um cartucho por vez, de Mega Drive/Genesis. A placa não tem 3,3 V: não use adaptador de GB/GBA nela. Desligue o USB antes de trocar de cartucho.
>
> **Esta placa nunca foi montada nem testada com cartucho.** O layout foi roteado por autoroteador (Freerouting) e conferido por DRC e pela netlist, não à mão. Se algo da lista de testes (seções 5 e 6) falhar, pare e avise antes de seguir.

## 1. Lista de peças

Quantidades e valores: `boards/megadrive/docs/bom.md`. Resumo:

| Grupo | Referências |
|---|---|
| Resistor 220 Ω | R1 (do LED) |
| Capacitores cerâmicos 100 nF | C3 (meio do slot), C5 (junto ao pino A31), C6 (junto ao pino A2) |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| LED 3 mm | D1 |
| Slot Mega Drive 64 pinos | MD1 |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Pontos de teste (opcional: tira de pinos macho 1x6, 2,54 mm) | TP1 a TP6 |
| Mecânica | 4 espaçadores M3 + pés de borracha (cantos) |

Não existem nesta placa: Si5351, PIC, soquete DIP-8, R2, C2 e C4. Se a lista de compras vier da `16_bits`, ignore essas peças.

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm.
- Solda 0,8 mm.
- Fluxo (caneta ou gel) e malha dessoldadora.
- Multímetro com continuidade.
- Alicate de corte.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Resistor R1** (220 Ω, deitado, como no silkscreen).
2. **Capacitores cerâmicos de 100 nF**: C3, C5 e C6. Eles ficam na faixa entre o slot e a fileira de cima do Mega; C6 e C5 ficam perto das pontas do slot (pinos A2 e A31).
3. **LED D1**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
4. **Capacitor eletrolítico C1 (470 µF)**, respeitando a polaridade (o `+` está no silkscreen), no canto superior esquerdo.
5. **Pontos de teste TP1 a TP6** (fileira junto à borda de baixo, `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE`): a 2,54 mm um do outro, com o rótulo na vertical acima de cada furo. Solde uma tira de pinos macho 1x6 padrão (ou 6 pinos soltos) para ligar um analisador lógico ou uma ponta de prova. **Opcional.**
6. **Slot MD1.** Solde os dois pinos das pontas, confira se o slot está reto e assentado, depois o resto. A direção da etiqueta está nas setas `v v ETIQUETA v v` do silk; ver a pendência abaixo. Nenhum componente alto fica na frente do slot.
7. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 4 espaçadores M3 dos cantos. Eles só dão altura e apoio nos pés de borracha: **não prendem o shield ao Mega**, que fica preso só pelos pinos.

## 4. Inspeção visual

- Pontes de solda entre pinos do slot (passo de 2,54 mm, duas fileiras de 32).
- Juntas frias (solda sem formar cone).
- Polaridade: C1 e D1.
- Os pinos macho longos de todos os pads do Mega, inclusive os sem sinal, estão soldados e retos.

## 5. Testes antes de ligar (multímetro, sem energia)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.** Repita entre os pontos de teste TP1 (5V) e TP2 (GND).
2. **Algumas linhas até o Mega** (conforme `boards/megadrive/docs/pinmap.md`):

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
4. Pinos do slot **sem ligação** (não podem ter continuidade com nada): B1, B3, B13, B14, B20 e B30.
5. **D0 e D1 do Mega** (serial USB) não podem ter continuidade com o slot. D20, D21, D40 e D41 do Mega ficam livres (eram do Si5351 e do PIC nas outras placas).
6. Os GND e 5V do slot: GND em A1, A18, A32; 5V em A2 e A31, cada um com o GND do Mega e com o 5V do Mega, respectivamente.

## 6. Primeira energização

Sem cartucho. Conecte o Mega ao PC pelo USB-C.

- Meça **5 V** (±0,25 V) nos pinos A2 e A31 do slot (VCC).
- Meça `/CART` (B32) em relação ao GND: deve estar em nível alto (puxado pelo firmware, `INPUT_PULLUP` em D50) ou flutuante, **nunca em curto** com o GND sem cartucho.
- O LED D1 acende e apaga pelo firmware (ativo em nível baixo, D38).

## 7. Gravar o firmware e testar

Firmware do fork do OSCR: `cd firmware/oscr && ~/.platformio/penv/bin/pio run -e SerialASCII -t upload`. Protocolo: `docs/protocolo.md`. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. `INFO` deve responder. Se não aparecer a porta serial: veja a seção 9.
3. `detect` do Mega Drive sem cartucho: o slot vazio deve ser informado como sem cartucho (D50 em nível alto).

## 8. Primeiro dump real

Use um cartucho de Mega Drive comum, de ROM mascarada de 512 KB a 1 MB e **sem valor** de coleção. Escolha o sistema Mega Drive, rode `detect` (o cabeçalho `SEGA MEGA DRIVE`/`SEGA GENESIS` deve ser lido e o D50 deve indicar cartucho presente) e depois `dump`. Compare o CRC32 com o do No-Intro (ou com a base de dados do projeto, `identify`). Repita o dump 3 vezes: os três CRC32 têm que ser iguais.

Só depois disso, e na ordem de risco de `docs/uso.md` seção 7, teste saves (SRAM com backup) e, por último, a gravação de flash (`WRITE_ROM`), em cartucho repro **sem valor**.

## 9. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho todo encaixado; um cartucho por vez; limpeza dos contatos; slot reto; VCC do slot (5 V em A2 e A31); `/CART` (B32) em nível baixo com o cartucho inserido. |
| CRC diverge | Contato oxidado (limpe com álcool isopropílico); refaça o dump 3 vezes; compare com o banco; verifique `/CAS0` (B16) e `/CE` (B17) nos pontos de teste. |
| Leitura com bytes errados em blocos | Capacitores C3, C5 e C6; solda dos pinos A19 a A30 e B22 a B25 (dados); cabo USB com queda de tensão. |
| Porta serial não aparece | Cabo USB-C só de carga (troque); no Linux, adicione-se ao grupo `dialout` (`sudo usermod -aG dialout $USER` e reinicie a sessão); clone com CH340 aparece como `/dev/ttyUSB0`; no Windows/macOS instale o driver CH340. |
| LED não acende | Polaridade (ânodo no 5V); resistor R1; o LED é ativo em nível baixo (D38). |
| `/CART` sempre baixo ou sempre alto | Solda do pino D50 e do B32; trilha de 25 mm entre eles; cartucho com contato B32 sujo. |

## Pendências (a conferir com as peças reais)

- Direção real da etiqueta do slot e se o silk bate (`docs/decisoes.md` D27).
- Medidas do slot Mega Drive (D17, D23) e se a faixa entre o slot e o 2x18 da direita tem folga para a carcaça do cartucho.
- Altura dos espaçadores M3 dos cantos (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
- A placa foi roteada por autoroteador: confira as trilhas no KiCad e faça o teste de continuidade da seção 5 com atenção.
