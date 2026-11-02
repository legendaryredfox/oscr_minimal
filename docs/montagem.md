# Montagem — oscr_minimal v1.0

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto, com as adaptações do GBA e do regulador de 3,3 V. Todas as referências (R1, C1...) estão no silkscreen e na `docs/bom.md`.

> **Segurança:** só um cartucho por vez. Nunca insira cartucho no slot GBA com 5V (o slot GBA é 3,3 V). Desligue o USB antes de trocar de cartucho.

## 1. Lista de peças

Ver `docs/bom.md` (quantidades e referências). Resumo:

| Grupo | Referências |
|---|---|
| Resistores | R1 (220 Ω), R2 (1 kΩ) |
| Capacitores cerâmicos 100 nF | C2, C3, C4, C5, C6, C9 |
| Capacitores 1 µF cerâmicos | C7, C8 |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| Soquete DIP-8 e PIC12F629 | U2 |
| Regulador MCP1700-3302E/TO | U3 |
| LED 3 mm | D1 |
| Header fêmea 1x7 (Si5351) e módulo | U1 |
| Slots | SNES1, NES1, FC1, MD1, GBA1 |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Mecânica | 6 espaçadores M3 de ~12 mm (Mega), 4 espaçadores M3 + pés de borracha (cantos) |

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm (e uma ponta fina de 0,5 a 1 mm só para o slot GBA).
- Solda 0,8 mm (e solda mais fina, 0,5 mm, para o GBA).
- Fluxo (caneta ou gel) e malha dessoldadora.
- Multímetro com continuidade.
- Alicate de corte.
- Lupa ou microscópio para conferir pontes no GBA.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Slot GBA (GBA1), SMD.** É a única peça SMD, então vem primeiro, com a placa livre de peças altas.
   - Encaixe os 2 pinos-guia (furos de 2,2 mm) no lugar.
   - Passe fluxo nos 32 pads de 1,5 mm de passo, solde só 2 pads das pontas, confira o alinhamento sob lupa e depois solde o resto.
   - Solde as 2 abas de blindagem (grandes).
   - Passe malha com fluxo se houver ponte entre pads.
2. **Resistores** R1 e R2 (em pé, como no silkscreen).
3. **Capacitores cerâmicos de 100 nF**: C2, C3, C4, C5, C6, C9.
4. **Soquete DIP-8 (U2)**, com o chanfro alinhado ao silkscreen e **sem o PIC**.
5. **LED (D1)**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
6. **Regulador U3 (TO-92)** com a face chata de acordo com o desenho do silkscreen, e os capacitores C7 e C8 (1 µF). Pinagem do MCP1700 TO-92: 1 = GND, 2 = entrada, 3 = saída.
7. **Capacitor eletrolítico de 470 µF (C1)**, respeitando a polaridade (o `+` está no silkscreen).
8. **Header fêmea do Si5351 (U1)** (1x7). O pino 1 (VIN, quadrado) fica na ponta indicada no silkscreen. **Ainda sem o módulo.**
9. **Slots SNES1, NES1, FC1, MD1.** Para cada um: solde os dois pinos das pontas, confira se o slot está reto e assentado, depois solde o resto. A etiqueta do cartucho fica para baixo, para o lado do USB do Mega (setas `v v ETIQUETA v v` no silk); ver a pendência abaixo.
10. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega (sem espaçadores) com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 6 espaçadores M3 nos furos do Mega.

## 4. Inspeção visual

- Pontes de solda entre pinos dos slots (principalmente SNES/NES com passo 2,5 mm e o GBA com 1,5 mm).
- Juntas frias (solda sem formar cone).
- Polaridade: C1, D1 e o chanfro do soquete U2.
- Nenhum pino do slot GBA encostando na blindagem metálica.

## 5. Testes antes de ligar (multímetro, sem energia e sem módulos)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.**
2. **Continuidade 3,3 V–GND** no pino 1 do GBA (3,3 V) e no GND. Também não pode ter curto.
3. **Isolação 5V–3,3 V:** a saída do regulador (pino 3 do U3) **não pode** ter continuidade com o 5V.
4. **Algumas linhas até o Mega** (conforme `docs/pinmap.md`):

| Do slot | Para o pino do Mega | Sinal |
|---|---|---|
| SNES 17 | A0 | endereço |
| SNES 19 | D37 | dado D0 |
| SNES 54 | D8 | /WR |
| NES 38 | A0 | M2 |
| NES 5 | D22 | PRG A8 |
| Famicom 32 | A0 | M2 |
| Mega Drive A17 | A0 | endereço A1 |
| Mega Drive B16 | D9 | /OE |
| GBA 6 | A0 | AD0 |
| GBA 2 | D16 | CLK |

5. Slots sem ligação (devem **não** ter continuidade com nada): GBA 31, Mega Drive B32 e os pinos listados como sem ligação em `docs/pinmap.md`.
6. D0 e D1 do Mega (serial USB) não podem ter continuidade com nenhum slot.

## 6. Primeira energização

Sem cartucho, sem PIC e sem módulo Si5351. Conecte o Mega ao PC pelo USB-C.

- Meça **5 V** (±0,25 V) no VCC de cada slot: SNES 27, NES 36, Famicom 30, Mega Drive A2.
- Meça **3,3 V** (±0,1 V) no pino 1 do slot GBA. Se medir 5 V, **desligue** e confira o U3 (pinagem).
- O LED D1 apaga/acende pelo firmware.

## 7. Instalar os módulos (com tudo desligado)

1. **Si5351 (U1):** encaixe o módulo com o pino VIN no pino 1 do header (quadrado). Confira a ordem: VIN, GND, SDA, SCL, 2, 1, 0.
2. **PIC12F629 (U2):** instale no soquete com a marca (pino 1) para o lado do chanfro. O PIC deve estar gravado com `snescic-lock-resync.hex` (ver a wiki do OSCR, "Flashing the snesCIC").

## 8. Gravar o firmware e testar

Ver `docs/protocolo.md` e `firmware/README.md` para compilar e gravar. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. Se não aparecer a porta serial: veja a seção 10.

## 9. Primeiro dump real

Use um cartucho simples: SNES LoROM ou NES mapper 0. Escolha o sistema, faça `detect` e depois `dump`. Compare o CRC32 com o do No-Intro. Só então teste Famicom, Mega Drive e GBA (este com cartucho de 3,3 V).

## 10. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho todo encaixado; um cartucho por vez; limpeza dos contatos; slot reto; pinos 1 e 2 do slot; VCC do slot (5 V ou 3,3 V no GBA). |
| CRC diverge | Contato oxidado (limpe com álcool isopropílico); sistema/mapper errado; refaça o dump 3 vezes; compare com o banco. |
| SNES SA-1 não lê | PIC no soquete, com o `.hex` certo; módulo Si5351 instalado; pinos D40/D41/CLK2. |
| Porta serial não aparece | Cabo USB-C só de carga (troque); no Linux, adicione-se ao grupo `dialout` (`sudo usermod -aG dialout $USER` e reinicie a sessão); clone com CH340 aparece como `/dev/ttyUSB0`; no Windows/macOS instale o driver CH340. |
| LED não acende | Polaridade (ânodo no 5V); resistor R1; o LED é ativo em nível baixo (D38). |
| GBA sem leitura | VCC do slot em 3,3 V; solda dos pads de 1,5 mm; cartucho GBA (não GB) neste slot. |

## Pendências (a conferir com as peças reais)

- Direção real da etiqueta de cada slot (SNES, NES, Famicom, Mega Drive, GBA) e se o silk bate (`docs/decisoes.md` D27, D28).
- Medidas dos slots e do módulo Si5351 (D17, D23).
- Altura dos espaçadores M3 (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
