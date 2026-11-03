# Montagem — placa 16_bits (SNES e Mega Drive) v1.0

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Todas as referências (R1, C1...) estão no silkscreen e na `boards/16_bits/docs/bom.md`.

> **Segurança:** só um cartucho por vez (SNES ou Mega Drive). Esta placa não tem 3,3 V: não use adaptador de GB/GBA nela. Desligue o USB antes de trocar de cartucho.

## 1. Lista de peças

Ver `boards/16_bits/docs/bom.md` (quantidades e referências). Resumo:

| Grupo | Referências |
|---|---|
| Resistores | R1 (220 Ω), R2 (1 kΩ) |
| Capacitores cerâmicos 100 nF | C2 (SNES), C3 (Mega Drive), C4 (PIC) |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| Soquete DIP-8 e PIC12F629 | U2 |
| LED 3 mm | D1 |
| Header fêmea 1x7 (Si5351) e módulo | U1 |
| Slots | SNES1, MD1 |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Mecânica | 4 espaçadores M3 + pés de borracha (cantos). Sem espaçadores nos furos do Mega (a placa não tem esses furos) |

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm.
- Solda 0,8 mm.
- Fluxo (caneta ou gel) e malha dessoldadora.
- Multímetro com continuidade.
- Alicate de corte.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Resistores** R1 e R2 (deitados, como no silkscreen).
2. **Capacitores cerâmicos de 100 nF**: C2, C3, C4.
3. **Soquete DIP-8 (U2)**, tradicional, com o chanfro alinhado ao silkscreen e **sem o PIC**. O PIC nunca é soldado: fica no soquete para poder ser trocado ou regravado.
4. **LED (D1)**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
5. **Capacitor eletrolítico de 470 µF (C1)**, respeitando a polaridade (o `+` está no silkscreen).
6. **Header fêmea do Si5351 (U1)** (1x7), deitado na horizontal. O pino 1 (VIN, quadrado) fica à esquerda. **Ainda sem o módulo**, que fica solto sobre o header (sem furos de fixação nesta placa).
7. **Slots SNES1 e MD1.** Para cada um: solde os dois pinos das pontas, confira se o slot está reto e assentado, depois o resto. A direção da etiqueta está nas setas `v v ETIQUETA v v` do silk; ver a pendência abaixo.
8. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 4 espaçadores M3 dos cantos. Eles só dão altura e apoio nos pés de borracha: **não prendem o shield ao Mega**, que fica preso só pelos pinos.

## 4. Inspeção visual

- Pontes de solda entre pinos dos slots (principalmente o SNES, com passo de 2,5 mm).
- Juntas frias (solda sem formar cone).
- Polaridade: C1, D1 e o chanfro do soquete U2.

## 5. Testes antes de ligar (multímetro, sem energia e sem módulos)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.**
2. **Algumas linhas até o Mega** (conforme `boards/16_bits/docs/pinmap.md`):

| Do slot | Para o pino do Mega | Sinal |
|---|---|---|
| SNES 17 | A0 | endereço |
| SNES 19 | D37 | dado D0 |
| SNES 54 | D8 | /WR |
| Mega Drive A17 | A0 | endereço A1 |
| Mega Drive B16 | D9 | /OE |

3. Slots sem ligação (devem **não** ter continuidade com nada): SNES 31 e 62, Mega Drive B32 e os pinos listados como sem ligação em `boards/16_bits/docs/pinmap.md`.
4. D0 e D1 do Mega (serial USB) não podem ter continuidade com nenhum slot.

## 6. Primeira energização

Sem cartucho, sem PIC e sem módulo Si5351. Conecte o Mega ao PC pelo USB-C.

- Meça **5 V** (±0,25 V) no VCC de cada slot: SNES 27, Mega Drive A2.
- O LED D1 apaga/acende pelo firmware.

## 7. Instalar os módulos (com tudo desligado)

1. **Si5351 (U1):** encaixe o módulo com o pino VIN no pino 1 do header (quadrado). Confira a ordem: VIN, GND, SDA, SCL, 2, 1, 0.
2. **PIC12F629 (U2):** instale no soquete com a marca (pino 1) para o lado do chanfro. O PIC deve estar gravado com `snescic-lock-resync.hex` (ver a wiki do OSCR, "Flashing the snesCIC").

## 8. Gravar o firmware e testar

Ver `docs/protocolo.md` e `firmware/README.md` para compilar e gravar. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. Se não aparecer a porta serial: veja a seção 10.

## 9. Primeiro dump real

Use um cartucho simples: SNES LoROM. Escolha o sistema, faça `detect` e depois `dump`. Compare o CRC32 com o do No-Intro. Depois teste o Mega Drive.

## 10. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho todo encaixado; um cartucho por vez; limpeza dos contatos; slot reto; pinos 1 e 2 do slot; VCC do slot (5 V). |
| CRC diverge | Contato oxidado (limpe com álcool isopropílico); sistema/mapper errado; refaça o dump 3 vezes; compare com o banco. |
| SNES SA-1 não lê | PIC no soquete, com o `.hex` certo; módulo Si5351 instalado; pinos D40/D41/CLK2. |
| Porta serial não aparece | Cabo USB-C só de carga (troque); no Linux, adicione-se ao grupo `dialout` (`sudo usermod -aG dialout $USER` e reinicie a sessão); clone com CH340 aparece como `/dev/ttyUSB0`; no Windows/macOS instale o driver CH340. |
| LED não acende | Polaridade (ânodo no 5V); resistor R1; o LED é ativo em nível baixo (D38). |

## Pendências (a conferir com as peças reais)

- Direção real da etiqueta de cada slot (SNES e Mega Drive) e se o silk bate (`docs/decisoes.md` D27).
- Medidas dos slots e do módulo Si5351 (D17, D23).
- Altura dos espaçadores M3 dos cantos (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
- Posição do módulo Si5351 sobre o header (sem furos de fixação): confira que ele não encosta em peças.
