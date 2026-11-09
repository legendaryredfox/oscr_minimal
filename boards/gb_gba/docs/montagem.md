# Montagem — placa gb_gba (GBA; GB e GBC por adaptador) v1.0

Este guia segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto, com as adaptações do slot GBA (SMD) e do regulador de 3,3 V. Todas as referências (R1, C1...) estão no silkscreen e em `boards/gb_gba/docs/bom.md`.

> **Segurança:** só um cartucho por vez. O slot GBA é **3,3 V**: nunca ligue o VCC dele ao 5V. Cartucho de GB e GBC só entra pelo adaptador (D56). Antes de trocar de cartucho, desligue o USB: o silkscreen avisa "TROQUE O CARTUCHO COM O USB DESLIGADO".
>
> **Esta placa nunca foi montada nem testada com cartucho.** O layout foi roteado por autoroteador (Freerouting) e conferido por DRC e pela netlist, não à mão; o `/D9` (RD do GBA) foi roteado à parte, pelo roteador A* do projeto. Se algo das seções 5 e 6 falhar, pare e avise antes de seguir.

## 1. Lista de peças

Quantidades e valores: `boards/gb_gba/docs/bom.md`. Resumo:

| Grupo | Referências |
|---|---|
| Resistor 220 Ω | R1 (do LED) |
| Capacitor cerâmico 100 nF | C4 (VCC do slot GBA) |
| Capacitores cerâmicos 1 µF | C2 (entrada 5V do regulador), C3 (saída 3,3 V) |
| Capacitor eletrolítico 470 µF/16 V | C1 |
| Regulador MCP1700-3302E/TO (TO-92) | U1 |
| LED 3 mm | D1 |
| Slot GBA 32 pads, SMD, 1,5 mm | GBA1 |
| Pinos macho longos, 85 posições | pads do shield (A1) |
| Mecânica | 4 espaçadores M3 + pés de borracha (furos do lado do Mega); a v1.0 não tem os 6 furos do Mega (D150) |

Não existem nesta placa: Si5351, PIC, R2 e os outros slots.

## 2. Ferramentas

- Ferro com ponta chanfrada de 2 mm e uma ponta fina de 0,5 a 1 mm para o slot GBA.
- Solda 0,8 mm e solda fina de 0,5 mm para o GBA.
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
2. **Resistor R1** (deitado, como no silkscreen).
3. **Capacitor cerâmico de 100 nF (C4).**
4. **LED (D1)**, respeitando a polaridade: o lado reto do LED é o cátodo e o quadrado do silkscreen marca o pino do cátodo (K, ligado ao resistor R1).
5. **Regulador U1 (TO-92)** com a face chata de acordo com o desenho do silkscreen, e os capacitores C2 e C3 (1 µF). Pinagem do MCP1700 TO-92: 1 = GND, 2 = entrada, 3 = saída.
6. **Capacitor eletrolítico de 470 µF (C1)**, respeitando a polaridade (o `+` está no silkscreen), no canto superior esquerdo.
7. **Pinos macho longos (85 posições) por último, com o shield encaixado no Mega**, que serve de gabarito de alinhamento:
    - Corte as tiras: header 1x7 (potência), 2 x 1x8 (analógicos), 1x10, 1x8 e 1x8 (digitais) e 2x18 (cantos).
    - Encaixe o shield sobre o Mega com os pinos nos furos do Mega, solde 2 pinos das pontas de cada tira, confira se tudo ficou reto e solde o resto.
    - Depois fixe os 4 espaçadores M3 do lado do Mega (v1.0: sem os 6 do centro, D150) com os pés de borracha.

## 4. Inspeção visual

- Pontes de solda entre pads do slot GBA (1,5 mm).
- Nenhum pino do slot GBA encostando na blindagem metálica.
- Juntas frias (solda sem formar cone).
- Polaridade: C1, D1 e a face chata do U1.
- Os pinos macho longos de todos os pads do Mega, inclusive os sem sinal, estão soldados e retos.

## 5. Testes antes de ligar (multímetro, sem energia)

1. **Continuidade 5V–GND** entre os pinos 5V e GND do header do Mega (por exemplo, o canto 2x18). **Não pode haver curto.**
2. **Continuidade 3,3 V–GND** entre o pino 1 do GBA (3,3 V) e o GND. Também não pode ter curto.
3. **Isolação 5V–3,3 V:** a saída do regulador (pino 3 do U1) **não pode** ter continuidade com o 5V.
4. **Algumas linhas até o Mega** (conforme `boards/gb_gba/docs/pinmap.md`):

| Do slot | Para o pino do Mega | Sinal |
|---|---|---|
| GBA 6 | A0 | AD0 |
| GBA 21 | A15 | AD15 |
| GBA 22 | D37 | D0/A16 |
| GBA 29 | D30 | D7/A23 |
| GBA 2 | D16 | CLK |
| GBA 3 | D8 | WR |
| GBA 4 | D9 | RD |
| GBA 5 | D6 | CS1 |
| GBA 30 | D17 | CS2/RST |

5. O pino 31 do GBA (AUD_IRQ) fica **sem ligação**: não pode ter continuidade com nada. Os pinos 32 e as duas blindagens são GND.
6. D0 e D1 do Mega (serial USB) não podem ter continuidade com o slot.

## 6. Primeira energização

Sem cartucho. Conecte o Mega ao PC pelo USB-C.

- Meça **3,3 V** (±0,1 V) no pino 1 do slot GBA. Se medir 5 V, **desligue** e confira o U1 (pinagem).
- Meça **5 V** (±0,25 V) na entrada do U1 (pino 2).
- O LED D1 acende e apaga pelo firmware (ativo em nível baixo, D38).

## 7. Gravar o firmware e testar

Firmware do fork do OSCR: `cd firmware/oscr && ~/.platformio/penv/bin/pio run -e SerialASCII -t upload`. Protocolo: `docs/referencia/protocolo.md`. Depois:

1. Rode o modo `MOCK` (sem cartucho): a CLI ou a GUI deve receber um padrão conhecido e o CRC32 deve bater.
2. `INFO` deve responder. Se não aparecer a porta serial: veja a seção 9.

## 8. Primeiro dump real

Use um cartucho de GBA comum e **sem valor** de coleção, de ROM mascarada (sem flash), e leia só a ROM. Escolha o sistema GBA, rode `detect` (o cabeçalho deve ser lido) e depois `dump`. Compare o CRC32 com o do No-Intro e repita 3 vezes (os três têm que ser iguais). Cartuchos GB e GBC: só pelo adaptador (D56), depois do GBA funcionar.

Só depois, e na ordem de risco de `docs/referencia/uso.md` seção 7, teste saves (SRAM com backup) e, por último, a gravação (`WRITE_ROM`), em cartucho repro **sem valor**.

## 9. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho todo encaixado; um cartucho por vez; limpeza dos contatos; slot reto; VCC do slot em 3,3 V; solda dos pads de 1,5 mm. |
| CRC diverge | Contato oxidado (limpe com álcool isopropílico); refaça o dump 3 vezes; compare com o banco. |
| GBA sem leitura | VCC do slot em 3,3 V; pads 2 a 5 (CLK, WR, RD, CS1) e 30 (CS2) sem ponte; cartucho GBA (não GB) neste slot, ou adaptador de GB bem encaixado. |
| Porta serial não aparece | Cabo USB-C só de carga (troque); no Linux, adicione-se ao grupo `dialout` (`sudo usermod -aG dialout $USER` e reinicie a sessão); clone com CH340 aparece como `/dev/ttyUSB0`; no Windows/macOS instale o driver CH340. |
| LED não acende | Polaridade (ânodo no 5V); resistor R1; o LED é ativo em nível baixo (D38). |
| 3,3 V errado | Pinagem do U1 (1 GND, 2 entrada, 3 saída), C2 e C3 soldados, curto no slot. |

## Pendências (a conferir com as peças reais)

- Direção real do cartucho no slot GBA (etiqueta para cima, entra pela direita) e se o silk bate (`docs/decisoes.md` D28).
- O cartucho GBA sai pela borda direita da placa e fica sobre a mesa: confira altura e apoio (pés de borracha só nos cantos do lado do Mega).
- Altura dos espaçadores M3 (D25): o USB-C e o jack do Mega têm que passar por baixo do shield.
- Via-in-fanout do GBA: o Freerouting pôs vias ao lado dos pads de 1,5 mm; confira no KiCad.
- A placa foi roteada por autoroteador: confira as trilhas no KiCad e faça o teste de continuidade da seção 5 com atenção.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

1. **Suporte do F1** (clipes para fusível 5×20 mm, furo passante) entra com os componentes baixos, na faixa de 10 mm acrescentada à borda de baixo da placa; solde os 4 furos (as duas pernas de cada clipe). O fusível **não vai soldado**: encaixe um fusível de vidro 5×20 mm de 500 mA (ação rápida) nos clipes depois dos testes, e troque-o assim quando queimar.
2. Teste antes de ligar, com o fusível encaixado: continuidade entre os dois clipes (menos de 2 Ω) e nenhuma entre 5 V e GND.
