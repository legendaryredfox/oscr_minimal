# Montagem — placa snes (só SNES/Super Famicom) v1.0

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Todas as referências (R1, C1...) estão no silkscreen e em `boards/snes/docs/bom.md`.

> **Segurança:** só um cartucho por vez, de SNES/Super Famicom. Esta placa não tem 3,3 V: não use adaptador de GB/GBA nela. Desligue o USB antes de trocar de cartucho: o silkscreen avisa "NÃO COLOQUE NEM RETIRE O CARTUCHO COM USB LIGADO".
>
> **Esta placa nunca foi montada nem testada com cartucho.** O layout foi roteado por autoroteador (Freerouting) e conferido por DRC e pela netlist, não à mão. Se algo dos testes das seções 5 e 6 falhar, pare e avise antes de seguir.
>
> **CIC:** esta versão usa o **PIC12F629** em soquete (D89/D91). O RP2040-Zero que o substituiria (`docs/placa-v1.3-rp2040.md`) ainda não foi validado e não está nesta placa.

## 1. Lista de peças

Ver `boards/snes/docs/bom.md` (quantidades e referências). Resumo:

| Grupo | Referências |
|---|---|
| Resistores | R1 (220 Ω), R2 (1 kΩ) |
| Capacitores cerâmicos 100 nF | C2 (slot SNES, junto ao pino 27), C3 (PIC) |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| Soquete DIP-8 e PIC12F629 | U2 |
| LED 3 mm | D1 |
| Header fêmea 1x7 (Si5351) e módulo | U1 |
| Slot SNES 62 pinos | SNES1 |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Pontos de teste (opcional: tira de pinos macho 1x5, 2,54 mm) | TP1 (5V), TP2 (GND), TP3 (`/RD`), TP4 (`/WR`), TP5 (`/IRQ`) |
| Mecânica | 4 espaçadores M3 + pés de borracha (cantos). Sem espaçadores nos furos do Mega (a placa não tem esses furos) |

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm.
- Solda 0,8 mm.
- Fluxo (caneta ou gel) e malha dessoldadora.
- Multímetro com continuidade.
- Alicate de corte.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Resistores** R1 e R2 (deitados, como no silkscreen).
2. **Capacitores cerâmicos de 100 nF**: C2 e C3.
3. **Soquete DIP-8 (U2)**, tradicional, com o chanfro alinhado ao silkscreen e **sem o PIC**. O PIC nunca é soldado: fica no soquete para poder ser trocado ou regravado.
4. **LED (D1)**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
5. **Capacitor eletrolítico de 470 µF (C1)**, respeitando a polaridade (o `+` está no silkscreen).
6. **Header fêmea do Si5351 (U1)** (1x7), deitado na horizontal. O pino 1 (VIN, quadrado) fica à esquerda. **Ainda sem o módulo**, que fica solto sobre o header (sem furos de fixação nesta placa).
7. **Pontos de teste TP1, TP2, TP3, TP4, TP5** (fileira junto à borda de baixo, a 2,54 mm um do outro, rótulo na vertical acima de cada furo): solde, se quiser, uma tira de pinos macho 1x5 padrão. **Opcional.**
8. **Slot SNES1.** Solde os dois pinos das pontas, confira se o slot está reto e assentado, depois o resto. A direção da etiqueta está nas setas `v v ETIQUETA v v` do silk; ver a pendência abaixo.
9. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 4 espaçadores M3 dos cantos. Eles só dão altura e apoio nos pés de borracha: **não prendem o shield ao Mega**, que fica preso só pelos pinos.

## 4. Inspeção visual

- Pontes de solda entre pinos do slot SNES (passo de 2,5 mm).
- Juntas frias (solda sem formar cone).
- Polaridade: C1, D1 e o chanfro do soquete U2.

## 5. Testes antes de ligar (multímetro, sem energia e sem módulos)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.**
2. **Algumas linhas até o Mega** (conforme `boards/snes/docs/pinmap.md`):

| Do slot | Para o pino do Mega | Sinal |
|---|---|---|
| SNES 17 | A0 | endereço |
| SNES 19 | D37 | dado D0 |
| SNES 54 | D8 | /WR |
| SNES 23 | D9 | /RD |
| SNES 18 | D7 | /IRQ (com R2 de 1 kΩ para 5V) |
| SNES 24, 25, 55 | PIC (U2) pinos 6, 5, 7 | CIC DATA 1, RESET, DATA 0 |
| SNES 56 | PIC (U2) pino 2 e Si5351 (U1) pino 5 | CLK2 |

3. Pinos do slot sem ligação (devem **não** ter continuidade com nada): SNES 31 e 62.
4. Pontos de teste: `/RD` com o D9, `/WR` com o D8, `/IRQ` com o D7.
5. D0 e D1 do Mega (serial USB) não podem ter continuidade com o slot. D50 do Mega fica sem ligação nesta placa.

## 6. Primeira energização

Sem cartucho, sem PIC e sem módulo Si5351. Conecte o Mega ao PC pelo USB-C.

- Meça **5 V** (±0,25 V) no VCC do slot (SNES 27).
- O LED D1 apaga/acende pelo firmware.

## 7. Instalar os módulos (com tudo desligado)

1. **Si5351 (U1):** encaixe o módulo com o pino VIN no pino 1 do header (quadrado). Confira a ordem: VIN, GND, SDA, SCL, 2, 1, 0.
2. **PIC12F629 (U2):** instale no soquete com a marca (pino 1) para o lado do chanfro. O PIC deve estar gravado com `snescic-lock-resync.hex` (ver a wiki do OSCR, "Flashing the snesCIC").

## 8. Gravar o firmware e testar

Ver `docs/protocolo.md` e `firmware/README.md` para compilar e gravar. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. Se não aparecer a porta serial: veja a seção 10.

## 9. Primeiro dump real

Use um cartucho simples: SNES LoROM, sem coprocessador, de pouco valor. Escolha o sistema, faça `detect` e depois `dump`. Compare o CRC32 com o do No-Intro e repita o dump 3 vezes (os CRC32 têm que ser iguais). Só depois teste cartuchos com SA-1 (precisam do PIC e do Si5351), saves e gravação de flash, na ordem de risco de `docs/uso.md` seção 7.

## 10. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho todo encaixado; um cartucho por vez; limpeza dos contatos; slot reto; pinos 1 e 2 do slot; VCC do slot (5 V). |
| CRC diverge | Contato oxidado (limpe com álcool isopropílico); sistema/mapper errado; refaça o dump 3 vezes; compare com o banco. |
| SNES SA-1 não lê | PIC no soquete, com o `.hex` certo; módulo Si5351 instalado; pinos D40/D41/CLK2. |
| Porta serial não aparece | Cabo USB-C só de carga (troque); no Linux, adicione-se ao grupo `dialout` (`sudo usermod -aG dialout $USER` e reinicie a sessão); clone com CH340 aparece como `/dev/ttyUSB0`; no Windows/macOS instale o driver CH340. |
| LED não acende | Polaridade (ânodo no 5V); resistor R1; o LED é ativo em nível baixo (D38). |

## Pendências (a conferir com as peças reais)

- Direção real da etiqueta do slot e se o silk bate (`docs/decisoes.md` D27).
- Medidas do slot SNES e do módulo Si5351 (D17, D23).
- Altura dos espaçadores M3 dos cantos (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
- Posição do módulo Si5351 sobre o header (sem furos de fixação): confira que ele não encosta em peças.
- A placa foi roteada por autoroteador: confira as trilhas no KiCad e faça o teste de continuidade da seção 5 com atenção.
