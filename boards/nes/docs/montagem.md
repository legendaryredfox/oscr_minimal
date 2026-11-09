# Montagem — placa nes (só NES) v1.1

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Todas as referências (R1, C1...) estão no silkscreen e em `boards/nes/docs/bom.md`.

> **Segurança:** só um cartucho por vez, de NES (72 pinos). Esta placa não tem 3,3 V: não use adaptador de GB/GBA nela. Antes de trocar de cartucho, desligue o 5V dos slots (`dumper.py power off`, espere o LED amarelo acender) ou o USB: o silkscreen avisa "SÓ TROQUE O CARTUCHO COM O LED AMARELO ACESO".
>
> **Esta placa nunca foi montada nem testada com cartucho.** O layout foi roteado por autoroteador (Freerouting) e conferido por DRC e pela netlist, não à mão. Se algo dos testes das seções 5 e 6 falhar, pare e avise antes de seguir.
>
> **Famicom:** esta placa não tem o slot Famicom (60 pinos). Não force um cartucho Famicom no slot NES; ele tem placa própria, `boards/famicom/`. Adaptador 60→72 pinos não foi validado (D95).

## 1. Lista de peças

Ver `boards/nes/docs/bom.md` (quantidades e referências). Resumo:

| Grupo | Referências |
|---|---|
| Resistor | R1 (220 Ω) |
| Capacitor cerâmico 100 nF | C2 (slot NES, junto ao pino 36) |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| LED 3 mm | D1 |
| Header fêmea 1x7 (Si5351) e módulo | U1 |
| Slot NES 72 pinos | NES1 |
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
2. **Capacitor cerâmico de 100 nF**: C2.
3. **LED (D1)**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
4. **Capacitor eletrolítico de 470 µF (C1)**, respeitando a polaridade (o `+` está no silkscreen).
5. **Header fêmea do Si5351 (U1)** (1x7), deitado na horizontal. O pino 1 (VIN, quadrado) fica à esquerda. **Ainda sem o módulo**, que fica solto sobre o header (sem furos de fixação nesta placa).
6. **Slot NES1.** Solde os dois pinos das pontas, confira se o slot está reto e assentado, depois o resto. A direção da etiqueta está nas setas `v v ETIQUETA v v` do silk; ver a pendência abaixo.
7. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 6 espaçadores M3 nos furos do Mega e os 4 dos cantos com os pés de borracha.

## 4. Inspeção visual

- Pontes de solda entre pinos do slot NES (passo de 2,5 mm).
- Juntas frias (solda sem formar cone).
- Polaridade: C1 e D1.

## 5. Testes antes de ligar (multímetro, sem energia e sem módulos)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.**
2. **Algumas linhas até o Mega** (conforme `boards/nes/docs/pinmap.md`):

| Do slot | Para o pino do Mega | Sinal |
|---|---|---|
| NES 38 | A0 | M2 |
| NES 5 | D22 | PRG A8 |
| NES 14 | A7 | PRG R/W |
| NES 50 | A1 | PRG /CE |
| NES 22 | D35 | CIRAM A10 |
| NES 37 | Si5351 (U1) pino 7 (CLK0) | clock |

3. Pinos do slot sem ligação (devem **não** ter continuidade com nada): NES 16 a 20, 34, 35, 51 a 55, 70 e 71.
4. VCC e GND do slot: NES 36 com o 5V do Mega; NES 1 e 72 com o GND.
5. D0 e D1 do Mega (serial USB) não podem ter continuidade com o slot. D50 do Mega fica sem ligação nesta placa.

## 6. Primeira energização

Sem cartucho e sem módulo Si5351. Conecte o Mega ao PC pelo USB-C.

- Meça **5 V** (±0,25 V) no VCC do slot (NES 36).
- O LED D1 apaga/acende pelo firmware.

## 7. Instalar o módulo (com tudo desligado)

**Si5351 (U1):** encaixe o módulo com o pino VIN no pino 1 do header (quadrado). Confira a ordem: VIN, GND, SDA, SCL, 2, 1, 0.

## 8. Gravar o firmware e testar

Ver `docs/referencia/protocolo.md` e `firmware/README.md` para compilar e gravar. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. Se não aparecer a porta serial: veja a seção 10.

## 9. Primeiro dump real

Use um cartucho simples: NES mapper 0 (NROM), de pouco valor. Escolha o sistema, faça `detect` e depois `dump`. Compare o CRC32 com o do No-Intro e repita o dump 3 vezes (os CRC32 têm que ser iguais). Só depois teste mapeadores maiores, saves e gravação, na ordem de risco de `docs/referencia/uso.md` seção 7.

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
- Medidas do slot NES e do módulo Si5351 (D17, D23).
- Altura dos espaçadores M3 dos cantos (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
- Posição do módulo Si5351 sobre o header (sem furos de fixação): confira que ele não encosta em peças.
- A placa foi roteada por autoroteador: confira as trilhas no KiCad e faça o teste de continuidade da seção 5 com atenção.

## Bloco de troca de cartucho (v1.1)

Solde com os componentes baixos: R2 a R8 (em pé, como no silkscreen), os dois 2N7000 (Q2, Q3; o lado chato do silk é o lado chato do transistor), os LEDs D2 (verde) e D3 (amarelo) e, **por último entre os baixos**, o Q1 (TO-220, em pé, como no silkscreen).

**Firmware:** grave o ambiente `SerialASCII_PowerSense` (`pio run -e SerialASCII_PowerSense -t upload` em `firmware/oscr`): começa com o 5V dos slots desligado; o host liga com `POWER`.

Testes extras (multímetro, sem cartucho):

1. Antes de ligar: continuidade entre o dreno do Q1 (`+5V_CART`) e o VCC do slot; **nenhuma** entre `+5V_CART` e o 5V do Mega.
2. Ligado ao USB, com o firmware padrão: o 5V do Mega presente, `+5V_CART` conforme o comando `POWER` (`dumper.py power on|off`): ligado = LED verde (D2) aceso e 4,7 a 5,2 V no VCC do slot; desligado = D3 aceso e VCC abaixo de 0,5 V em até 1 s.
3. Medir a queda do Q1 em carga e o tempo de descarga; anotar nos logs. O limiar do LED amarelo varia com o 2N7000 (1 a 2,5 V).

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

1. **Suporte do F1** (clipes para fusível 5×20 mm, furo passante) entra com os componentes baixos, na faixa de 10 mm acrescentada à borda de baixo da placa; solde os 4 furos (as duas pernas de cada clipe). O fusível **não vai soldado**: encaixe um fusível de vidro 5×20 mm de 500 mA (ação rápida) nos clipes depois dos testes, e troque-o assim quando queimar.
2. Teste antes de ligar, com o fusível encaixado: continuidade entre os dois clipes (menos de 2 Ω) e nenhuma entre 5 V e GND.
3. **Seletor (v1.1)**: solde os resistores comuns, as redes RN1 a RN4 (DIP-16 com a marca no pino 1, de preferência em soquete), os capacitores, o Q5, o LDO e o Q4 (TO-220 em pé) e o J1 (cabeçalho de 2 pinos, **sem o jumper**).
4. Gravar `pio run -e SerialASCII_PowerVolt -t upload` (firmware com o seletor no D18). Liga em **5 V** por padrão; `dumper power on --voltage 3v3` liga a 3,3 V.
5. Medidas sem cartucho: em 5 V, o VCC dos slots fica entre 4,6 e 5,1 V (queda do fusível e do Q4); com `--voltage 3v3`, entre 3,2 e 3,4 V (LDO). Com o J1 fechado, `--voltage 5v` não consegue passar de 3,3 V.
6. Os slots NES são os únicos com resistores em série e seletor; o resto da placa (Si5351, PIC e outros slots) fica sempre em 5 V.
