# Montagem — placa famicom (só Famicom) v1.0

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Todas as referências (R1, C1...) estão no silkscreen e em `boards/famicom/docs/bom.md`.

> **Segurança:** só um cartucho por vez, de Famicom (60 pinos). Esta placa não tem 3,3 V: não use adaptador de GB/GBA nela. Desligue o USB antes de trocar de cartucho: o silkscreen avisa "NÃO COLOQUE NEM RETIRE O CARTUCHO COM USB LIGADO".
>
> **Esta placa nunca foi montada nem testada com cartucho.** O layout foi roteado por autoroteador (Freerouting) e conferido por DRC e pela netlist, não à mão. Se algo dos testes das seções 5 e 6 falhar, pare e avise antes de seguir.
>
> **NES:** esta placa só tem o slot Famicom (60 pinos). Cartucho NES de 72 pinos vai na placa `boards/nes/`.

## 1. Lista de peças

Ver `boards/famicom/docs/bom.md` (quantidades e referências). Resumo:

| Grupo | Referências |
|---|---|
| Resistor | R1 (220 Ω) |
| Capacitor cerâmico 100 nF | C4 (slot Famicom, junto ao pino 30) |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| LED 3 mm | D1 |
| Slot Famicom 60 pinos | FC1 |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Mecânica | 6 espaçadores M3 nos furos do Mega e 4 espaçadores M3 + pés de borracha nos cantos |

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm.
- Solda 0,8 mm.
- Fluxo (caneta ou gel) e malha dessoldadora.
- Multímetro com continuidade.
- Alicate de corte.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Resistor** R1 (deitado, como no silkscreen).
2. **Capacitor cerâmico de 100 nF**: C4.
3. **LED (D1)**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
4. **Capacitor eletrolítico de 470 µF (C1)**, respeitando a polaridade (o `+` está no silkscreen).
5. **Slot FC1.** Solde os dois pinos das pontas, confira se o slot está reto e assentado, depois o resto. A direção da etiqueta está nas setas `v v ETIQUETA v v` do silk; ver a pendência abaixo.
6. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 6 espaçadores M3 nos furos do Mega e os 4 dos cantos com os pés de borracha.

## 4. Inspeção visual

- Pontes de solda entre pinos do slot Famicom (passo de 2,54 mm).
- Juntas frias (solda sem formar cone).
- Polaridade: C1 e D1.

## 5. Testes antes de ligar (multímetro, sem energia e sem módulos)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.**
2. **Algumas linhas até o Mega** (conforme `boards/famicom/docs/pinmap.md`):

| Do slot | Para o pino do Mega | Sinal |
|---|---|---|
| Famicom 32 | A0 | M2 |
| Famicom 5 | D22 | PRG A8 |
| Famicom 14 | A7 | PRG R/W |
| Famicom 44 | A1 | PRG /CE |
| Famicom 18 | D35 | CIRAM A10 |

3. Pinos do slot sem ligação (devem **não** ter continuidade com nada): Famicom 45 e 46.
4. VCC e GND do slot: Famicom 30 e 31 com o 5V do Mega; Famicom 1 e 16 com o GND.
5. D0 e D1 do Mega (serial USB) não podem ter continuidade com o slot. D50 do Mega fica sem ligação nesta placa.

## 6. Primeira energização

Sem cartucho. Conecte o Mega ao PC pelo USB-C.

- Meça **5 V** (±0,25 V) no VCC do slot (Famicom 30 e 31).
- O LED D1 apaga/acende pelo firmware.

## 7. Gravar o firmware e testar

Ver `docs/protocolo.md` e `firmware/README.md` para compilar e gravar. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. Se não aparecer a porta serial: veja a seção 9.

## 8. Primeiro dump real

Use um cartucho simples: Famicom mapper 0 (NROM), de pouco valor. Escolha o sistema, faça `detect` e depois `dump`. Compare o CRC32 com o do No-Intro e repita o dump 3 vezes (os CRC32 têm que ser iguais). Só depois teste mapeadores maiores, saves e gravação, na ordem de risco de `docs/uso.md` seção 7.

## 9. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho todo encaixado; um cartucho por vez; limpeza dos contatos; slot reto; pinos 1 e 2 do slot; VCC do slot (5 V). |
| CRC diverge | Contato oxidado (limpe com álcool isopropílico); sistema/mapper errado; refaça o dump 3 vezes; compare com o banco. |
| Mapper não lê | Mapper listado em `docs/funcoes-oscr.md`; contatos do cartucho limpos; o Famicom é lido pelo mesmo código do NES no firmware. |
| Porta serial não aparece | Cabo USB-C só de carga (troque); no Linux, adicione-se ao grupo `dialout` (`sudo usermod -aG dialout $USER` e reinicie a sessão); clone com CH340 aparece como `/dev/ttyUSB0`; no Windows/macOS instale o driver CH340. |
| LED não acende | Polaridade (ânodo no 5V); resistor R1; o LED é ativo em nível baixo (D38). |

## Pendências (a conferir com as peças reais)

- Direção real da etiqueta do slot e se o silk bate (`docs/decisoes.md` D27).
- Medidas do slot Famicom (D17, D23).
- Altura dos espaçadores M3 dos cantos (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
- A placa foi roteada por autoroteador: confira as trilhas no KiCad e faça o teste de continuidade da seção 5 com atenção.
