# Montagem — placa 16_bits (SNES e Mega Drive) v. 1.2

> **Atualização D130 (2026-11-08):** a **v1.2 ficou sem os 12 TVS (D3 a D14)**; os resistores série R3 a R14 continuam. A **v1.3** mantém os TVS (DNP). Onde este texto fala de D3 a D14, vale só para a v1.3.


> **Versões (D128):** este guia foi escrito para a v1.2 de 2026-11-06. A v1.2 atual **não tem** Q1, R16 a R18, D2 nem SW1 (pule esses itens e o passo 4b); a v1.3 tem o bloco de troca (Q1, Q2, Q3, R16 a R22, D15 verde e D16 amarelo) e **também não tem o botão**. Lista de cada versão: `fab/bom-v1.2.csv` e `fab/bom-v1.3.csv`; resumo em `versoes.md`.

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Todas as referências (R1, C1...) estão no silkscreen e na `boards/16_bits/docs/bom.md`.

> **Segurança:** só um cartucho por vez (SNES ou Mega Drive). Esta placa não tem 3,3 V: não use adaptador de GB/GBA nela. Desligue o USB antes de trocar de cartucho: o silkscreen avisa "NÃO COLOQUE NEM RETIRE O CARTUCHO COM USB LIGADO". A chave de 5V (Q1) existe: com o firmware `SerialASCII_Power`, `dumper power off` corta o 5V para trocar o cartucho (veja `docs/v12-final.md`; sem sensor, confira com o multímetro que o 5V do cartucho caiu antes de trocar).

## 1. Lista de peças

Ver `boards/16_bits/docs/bom.md` (quantidades e referências). Resumo:

| Grupo | Referências |
|---|---|
| Resistores | R1 (220 Ω), R2 (1 kΩ); **R3 a R14** (série das linhas de controle, 0 Ω de fábrica); R16 (100 kΩ), R17 (100 Ω), R18 (1 kΩ) da chave de 5V; R15 (10 kΩ, **não montar**) |
| Diodos | D3 a D14 (TVS ou zener 5,1 V, **não montar**) |
| Chave de 5V e reset | Q1 (P-MOSFET TO-220), D2 (LED verde 3 mm), SW1 (botão tátil 6 mm) |
| Capacitores cerâmicos 100 nF | C2 (SNES), C3 (Mega Drive), C4 (PIC, acima do soquete), C5 e C6 (extras do slot Mega Drive, junto aos pinos A31 e A2) |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| Soquete DIP-8 e PIC12F629 | U2 |
| LED 3 mm | D1 (status), D2 (verde, 5V dos slots) |
| Header fêmea 1x7 (Si5351) e módulo | U1 |
| Slots | SNES1, MD1 |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Mecânica | 4 espaçadores M3 + pés de borracha (cantos) e **3 espaçadores M3 com parafusos** nos furos MH5, MH6 e MH7, alinhados com furos do Mega (v. 1.2 final, D108) |

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm.
- Solda 0,8 mm.
- Fluxo (caneta ou gel) e malha dessoldadora.
- Multímetro com continuidade.
- Alicate de corte.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Resistores** R1 e R2 (deitados, como no silkscreen) e os de 2,54 mm (em pé, como no desenho): **R3 a R14 como 0 Ω** (um fio ou resistor de 0 Ω; troque por 47 a 100 Ω só depois dos testes da v12-final), R16, R17 e R18. **Não monte R15 nem D3 a D14** (DNP).
2. **Capacitores cerâmicos de 100 nF**: C2, C3, C4, C5, C6. O **C4** fica logo acima do soquete do PIC (D107): o corpo toca de leve a borda do soquete, então solde-o com as pernas dobradas rente e o corpo um pouco inclinado para cima, sem forçar o soquete.
3. **Soquete DIP-8 (U2)**, tradicional, com o chanfro alinhado ao silkscreen e **sem o PIC**. O PIC nunca é soldado: fica no soquete para poder ser trocado ou regravado.
4. **LEDs (D1 e D2)**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
4b. **Q1** (TO-220, em pé, lado do metal para a borda direita da placa; pinos G, D, S de cima para baixo) e o **botão SW1**.
5. **Capacitor eletrolítico de 470 µF (C1)**, respeitando a polaridade (o `+` está no silkscreen).
6. **Header fêmea do Si5351 (U1)** (1x7), deitado na horizontal. O pino 1 (VIN, quadrado) fica à esquerda. **Ainda sem o módulo**, que fica solto sobre o header (sem furos de fixação nesta placa).
7. **Slots SNES1 e MD1.** Para cada um: solde os dois pinos das pontas, confira se o slot está reto e assentado, depois o resto. A direção da etiqueta está nas setas `v v ETIQUETA v v` do silk; ver a pendência abaixo.
8. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 4 espaçadores M3 dos cantos (altura e apoio nos pés de borracha) e, **com o shield já encaixado**, os 3 espaçadores M3 entre o shield e o Mega nos furos MH5, MH6 e MH7 (parafuso por baixo do Mega e outro por cima do shield; só aperte depois de conferir que os pinos estão assentados). Assim o shield não levanta ao puxar um cartucho.

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

Ver `docs/referencia/protocolo.md` e `firmware/README.md` para compilar e gravar. Depois:

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

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

1. **Suporte do F1** (clipes para fusível 5×20 mm, furo passante) entra com os componentes baixos, na faixa de 10 mm acrescentada à borda de baixo da placa; solde os 4 furos (as duas pernas de cada clipe). O fusível **não vai soldado**: encaixe um fusível de vidro 5×20 mm de 500 mA (ação rápida) nos clipes depois dos testes, e troque-o assim quando queimar.
2. Teste antes de ligar, com o fusível encaixado: continuidade entre os dois clipes (menos de 2 Ω) e nenhuma entre 5 V e GND.
3. **Seletor (v1.3)**: solde os resistores comuns, as redes RN1 a RN5 (DIP-16 com a marca no pino 1, de preferência em soquete), os capacitores, o Q5, o LDO e o Q4 (TO-220 em pé) e o J1 (cabeçalho de 2 pinos, **sem o jumper**).
4. Gravar `pio run -e SerialASCII_PowerVolt -t upload` (firmware com o seletor no D18). Liga em **5 V** por padrão; `dumper power on --voltage 3v3` liga a 3,3 V.
5. Medidas sem cartucho: em 5 V, o VCC dos slots fica entre 4,6 e 5,1 V (queda do fusível e do Q4); com `--voltage 3v3`, entre 3,2 e 3,4 V (LDO). Com o J1 fechado, `--voltage 5v` não consegue passar de 3,3 V.
6. Os slots Mega Drive são os únicos com resistores em série e seletor; o resto da placa (Si5351, PIC e outros slots) fica sempre em 5 V.
