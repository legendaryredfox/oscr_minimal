# Montagem — placa 8_bits (NES, Famicom e Master System) v1.1

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Todas as referências (R1, C1...) estão no silkscreen e em `boards/8_bits/docs/bom.md`.

> **v1.0:** sem o seletor de tensão (seção "F1, J1 e seletor"): só o F1. **v1.1:** acrescenta o seletor 3,3 V/5 V.
>
> **Segurança:** só um cartucho por vez, de NES (72 pinos), de Famicom (60 pinos) **ou** de Master System (50 pinos), nunca dois slots ao mesmo tempo (os três estão ligados em paralelo nos mesmos pinos do Mega). Esta placa não tem 3,3 V fixo: não use adaptador de GB/GBA nela. **Para trocar de cartucho, desligue o USB.**
>
> **Esta placa nunca foi montada nem testada com cartucho.** O layout foi roteado por autoroteador (Freerouting) e conferido por DRC e pela netlist, não à mão. Se algo dos testes das seções 5 e 6 falhar, pare e avise antes de seguir.
>
> **Slots:** o de cima (acima do cabeçalho do Mega) é o **Famicom**; o do meio é o **NES**; o de baixo é o **Master System**. Famicom e NES têm o rótulo `v v ETIQUETA v v` no silkscreen; **a direção da etiqueta do SMS não foi confirmada** (confira com a peça antes de soldar).

## 1. Lista de peças

Ver `boards/8_bits/docs/bom.md` (quantidades e referências). Resumo:

| Grupo | Referências |
|---|---|
| Resistor | R1 (220 Ω); na v1.1 também R2, R3 e R4 |
| Capacitores cerâmicos 100 nF | C2 (slot NES, junto ao pino 36), C3 (slot Famicom, junto aos pinos 30 e 31), C4 (slot SMS, junto aos pinos 1 e 35); na v1.1, também C5 |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| LED 3 mm | D1 |
| Header fêmea 1x7 (Si5351) e módulo | U1 |
| Slots | NES1 (72 pinos), FC1 (Famicom, 60 pinos), SMS1 (Master System, 50 pinos) |
| Fusível | F1 (suporte de clipes 5×20 mm) |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Mecânica | 4 espaçadores M3 + pés de borracha nos cantos (sem furos de fixação no Mega) |

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm.
- Solda 0,8 mm.
- Fluxo (caneta ou gel) e malha dessoldadora.
- Multímetro com continuidade.
- Alicate de corte.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Resistor** R1 (deitado, como no silkscreen).
2. **Capacitores cerâmicos de 100 nF**: C2, C3 e C4 (na v1.1, também C5).
3. **LED (D1)**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
4. **Capacitor eletrolítico de 470 µF (C1)**, respeitando a polaridade (o `+` está no silkscreen).
5. **Header fêmea do Si5351 (U1)** (1x7), **na vertical**, ao lado do header duplo do Mega (borda direita da placa). O pino 1 (VIN, quadrado) fica em cima, sob o rótulo `Si5351`. **Ainda sem o módulo**, que fica em pé no header (sem furos de fixação nesta placa); confira que ele não encosta nos pinos do Mega nem no slot NES.
6. **Slots NES1, FC1 e SMS1.** Para cada um: solde os dois pinos das pontas, confira se o slot está reto e assentado, depois o resto. A direção da etiqueta está nas setas `v v ETIQUETA v v` do silk; ver a pendência abaixo.
7. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 4 espaçadores M3 dos cantos com os pés de borracha.

## 4. Inspeção visual

- Pontes de solda entre pinos dos slots (NES com passo de 2,5 mm, Famicom e SMS com 2,54 mm).
- Juntas frias (solda sem formar cone).
- Polaridade: C1 e D1.

## 5. Testes antes de ligar (multímetro, sem energia e sem módulos)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.**
2. **Algumas linhas até o Mega** (conforme `boards/8_bits/docs/pinmap.md`):

| Do slot | Para o pino do Mega | Sinal |
|---|---|---|
| NES 38 | A0 | M2 |
| NES 5 | D22 | PRG A8 |
| NES 14 | A7 | PRG R/W |
| NES 50 | A1 | PRG /CE |
| NES 22 | D35 | CIRAM A10 |
| NES 37 | Si5351 (U1) pino 7 (CLK0) | clock |
| Famicom 32 | A0 | M2 (o mesmo pino do Mega que o NES 38) |
| Famicom 44 | A1 | PRG /CE (o mesmo que o NES 50) |
| SMS 25 | A0 | A0 (o mesmo pino do Mega que o NES 38) |
| SMS 2 | D8 | WR |
| SMS 4 | D9 | RD |
| SMS 13 | D48 | CE |
| SMS 14 | D30 | D7 (dado) |
| SMS 46 | D17 | RESET |

3. Pinos dos slots sem ligação (devem **não** ter continuidade com nada): NES 16 a 20, 34, 35, 51 a 55, 70 e 71; Famicom 45 e 46; SMS 3, 5, 34, 37 a 45 e 47 a 50.
4. VCC e GND dos slots: NES 36, Famicom 30 e 31 e SMS 1 e 35 com o 5V depois do fusível; SMS 19, 20 e 21, NES 1 e 72 e Famicom 1 e 16 com o GND.
   Como os slots estão em paralelo, o mesmo pino do Mega aparece nos dois: confira também o NES 38 com o Famicom 32 (continuidade esperada).
5. D0 e D1 do Mega (serial USB) não podem ter continuidade com o slot. D50 do Mega fica sem ligação nesta placa.

## 6. Primeira energização

Sem cartucho e sem módulo Si5351. Conecte o Mega ao PC pelo USB-C.

- Meça **5 V** (±0,25 V) no VCC dos slots (NES 36; Famicom 30 e 31; SMS 1 e 35).
- O LED D1 apaga/acende pelo firmware.

## 7. Instalar o módulo (com tudo desligado)

**Si5351 (U1):** encaixe o módulo com o pino VIN no pino 1 do header (quadrado). Confira a ordem: VIN, GND, SDA, SCL, 2, 1, 0.

## 8. Gravar o firmware e testar

Ver `docs/referencia/protocolo.md` e `firmware/README.md` para compilar e gravar. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. Se não aparecer a porta serial: veja a seção 10.

## 9. Primeiro dump real

Use um cartucho simples: NES ou Famicom mapper 0 (NROM), ou um Master System pequeno, de pouco valor. O slot SMS usa `--mapper 0` (fiação do `mastersystem_adapter`); **o núcleo SMS do firmware nunca rodou em hardware**. Escolha o sistema, faça `detect` e depois `dump`. Compare o CRC32 com o do No-Intro e repita o dump 3 vezes (os CRC32 têm que ser iguais). Só depois teste mapeadores maiores, saves e gravação, na ordem de risco de `docs/referencia/uso.md` seção 7.

## 10. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho todo encaixado; um cartucho por vez; limpeza dos contatos; slot reto; pinos 1 e 2 do slot; VCC do slot (5 V). |
| CRC diverge | Contato oxidado (limpe com álcool isopropílico); sistema/mapper errado; refaça o dump 3 vezes; compare com o banco. |
| Mapper não lê | Módulo Si5351 instalado e na ordem certa; pino 37 do slot com o CLK0; mapper listado em `docs/referencia/funcoes-oscr.md`. |
| Porta serial não aparece | Cabo USB-C só de carga (troque); no Linux, adicione-se ao grupo `dialout` (`sudo usermod -aG dialout $USER` e reinicie a sessão); clone com CH340 aparece como `/dev/ttyUSB0`; no Windows/macOS instale o driver CH340. |
| LED não acende | Polaridade (ânodo no 5V); resistor R1; o LED é ativo em nível baixo (D38). |

## Pendências (a conferir com as peças reais)

- Direção real da etiqueta do slot e se o silk bate (`docs/decisoes.md` D27).
- Medidas dos slots NES, Famicom e SMS e do módulo Si5351 (D17, D23). Folga entre o corpo do SMS e os furos de canto de baixo.
- Direção da etiqueta do slot SMS (o silk não a mostra).
- Altura dos espaçadores M3 dos cantos (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
- Posição do módulo Si5351 sobre o header (sem furos de fixação): confira que ele não encosta em peças.
- A placa foi roteada por autoroteador: confira as trilhas no KiCad e faça o teste de continuidade da seção 5 com atenção.

## F1, J1 e seletor de tensão (D138)

1. **Suporte do F1** (clipes para fusível 5×20 mm, furo passante) entra com os componentes baixos, junto à borda de baixo, à esquerda do slot SMS; solde os 4 furos (as duas pernas de cada clipe). O fusível **não vai soldado**: encaixe um fusível de vidro 5×20 mm de 500 mA (ação rápida) nos clipes depois dos testes, e troque-o assim quando queimar.
2. Teste antes de ligar, com o fusível encaixado: continuidade entre os dois clipes (menos de 2 Ω) e nenhuma entre 5 V e GND.
3. **Só na v1.1, seletor:** solde R2, R3 e R4, os capacitores C5 e C6 (o eletrolítico com a polaridade do silk), o Q2 (TO-92), o LDO U2 e o Q1 (TO-220 em pé) e o J1 (cabeçalho de 2 pinos, **sem o jumper**).
4. Gravar `pio run -e SerialASCII_Volt -t upload` (firmware com o seletor no D18). A placa sobe em 3,3 V (estado seguro) e os comandos de cartucho passam a **5 V** sozinhos (padrão); `dumper voltage 3v3` escolhe 3,3 V.
5. Medidas sem cartucho: em 5 V, o VCC dos slots fica entre 4,6 e 5,1 V (queda do fusível e do Q1); com `--voltage 3v3`, entre 3,2 e 3,4 V (LDO). Com o J1 fechado, `--voltage 5v` não consegue passar de 3,3 V.
6. Os três slots (NES, Famicom e SMS) ficam no VCC do seletor; o Si5351 fica sempre em 5 V. **Confira a tensão que o cartucho suporta antes de inserir:** a placa não limita as saídas de 5 V do Mega para um cartucho de 3,3 V (D140).
