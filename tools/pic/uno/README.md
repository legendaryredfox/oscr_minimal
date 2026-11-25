# Gravar o PIC12F629 com Arduino Uno

Plano B, sem comprar programador. O circuito também existe como shield de PCB, em protoboard e em placa perfurada, em [`../shield_uno/README.md`](../shield_uno/README.md) (D102). Baseado no ardpicprog de Rhys Weatherley (GPL v3; circuitos e documentação
CC BY-SA 2.5), https://rweather.github.io/ardpicprog/. O 12F629 está na lista dele, com autodetecção.
Hex a gravar: `firmware/cic_rp2040/third_party/snescic-lock-resync.hex`.

## Material

| Peça | Observação |
|---|---|
| Arduino Uno + cabo USB, protoboard, jumpers | |
| Fonte de 13 V | veja "Antes de ligar" |
| 1× transistor NPN pequeno (BC548, BC547, 2N3904, 2N2222) | confira a pinagem do SEU modelo (abaixo) |
| 4,7 kΩ (base), 10 kΩ (MCLR), 100 nF (Vdd do PIC) | |
| Opcional: LED vermelho + 1 kΩ do +13 V ao GND; LED amarelo + 220 Ω no A5 | o vermelho mostra que há 13 V |
| PIC12F629-I/P virgem | direto na protoboard |

## Ligações

```
13 V (+) ──┬── 10 kΩ ──┬── PIC pino 4 (MCLR)
           │           └── coletor do transistor
           └── (LED vermelho + 1 kΩ ao GND, opcional)
Uno A1 ── 4,7 kΩ ── base do transistor        emissor ── GND
Uno D8  ── PIC pino 1 (Vdd)       100 nF entre o pino 1 e o pino 8, junto ao chip
Uno D9  ── PIC pino 6 (clock)
Uno D10 ── PIC pino 7 (dados)
Uno GND ── PIC pino 8 (Vss) ── GND da fonte de 13 V   (GND comum!)
PIC pinos 2, 3 e 5: sem ligação
```
A1 em nível **baixo** deixa o MCLR em 13 V (gravação); em nível alto o transistor puxa o MCLR a GND (reset). O sketch
aplica os 13 V no MCLR **antes** de ligar o Vdd, como a especificação de programação manda. Os 13 V nunca vão a um pino do Uno.

**Os pinos D8, D9 e D10 exigem o sketch com patch** (o padrão do instalador, abaixo). O sketch original do ardpicprog usa D2, D4 e
D7: com a fiação em um conjunto e o sketch no outro, o chip não responde (ID `0x3FFF`). A fiação D8/D9/D10 é a das figuras do
shield, da protoboard e da placa perfurada (D221); A1 e A5 são iguais nos dois sketches.

## Antes de ligar

1. **Meça a fonte de 13 V com o multímetro, sem carga.** Alguns adaptadores "13 V" sem regulagem passam de 15 V
   sem carga. Alvo: cerca de 13 V; fique dentro do Vpp do datasheet de programação (DS41191; não verifiquei os
   limites exatos: confira o máximo antes de ligar o chip).
2. Confirme a polaridade do plug (+ no centro ou na lateral).
3. **Pinagem do transistor:** BC547/BC548 (TO-92, lado plano para você, pernas para baixo) = C, B, E da esquerda
   para a direita; 2N3904 e 2N2222 (TO-92) = E, B, C. Quem tem dúvida: modo diodo do multímetro; a base mede
   cerca de 0,6 V para as duas outras pernas com o + na base (NPN).
4. Sem o PIC no soquete, ligue só a fonte e meça o pino 4 com o A1 em reset (deve ficar perto de 0 V) e depois
   solto (13 V).

## Testar o Uno (feito em 2026-11-06 com o Uno do usuário)

Clone com conversor CH340: aparece como **`/dev/ttyUSB0`**, não `ttyACM0` (um Uno original aparece como `ttyACM0`). Use a
porta que `arduino-cli board list` mostrar e troque nos comandos abaixo. O usuário precisa estar no grupo `dialout` (estava).

```
# não destrutivo: lê a assinatura pelo bootloader (esperado: 1E 95 0F, ATmega328P, 115200 baud, Optiboot)
~/.arduino15/packages/arduino/tools/avrdude/*/bin/avrdude -C ~/.arduino15/packages/arduino/tools/avrdude/*/etc/avrdude.conf \
    -c arduino -p m328p -P /dev/ttyUSB0 -b 115200 -n -v

# fim a fim: compila e grava um sketch de teste (LED pisca, serial "vivo N" por segundo e eco). Troca o sketch do Uno.
arduino-cli compile -b arduino:avr:uno tools/pic/uno/teste_uno
arduino-cli upload  -b arduino:avr:uno -p /dev/ttyUSB0 tools/pic/uno/teste_uno
```
Resultado no Uno do usuário: assinatura `1E 95 0F` a 115200 baud (a 57600 não responde), compilação e gravação ok, serial a
115200 baud com "vivo 1, 2, 3..." e eco de `A` e `B`. Nada do circuito do PIC estava ligado.

## Instalação (uma vez)

```
sudo apt install git build-essential        # se ainda não tiver
tools/pic/uno/instalar_ardpicprog.sh        # baixa (commit fixo), compila o programa do PC, prepara o sketch com os patches
arduino-cli compile -b arduino:avr:uno tools/pic/bin/ProgramPIC
arduino-cli upload  -b arduino:avr:uno -p /dev/ttyUSB0 tools/pic/bin/ProgramPIC     # ttyACM0 num Uno original
```
O instalador aplica por padrão os dois patches (pinos D8/D9/D10 e UART por polling). Se você já tinha rodado uma versão
anterior dele, **rode de novo**: a cópia antiga em `tools/pic/bin/ProgramPIC/` pode estar sem os patches. Para o sketch original
do upstream (D2/D4/D7): `PROGRAMPIC_PORTB=0 PROGRAMPIC_POLLING=0`.

> Feche o monitor serial da IDE antes de gravar (ele roubaria os dados).

## Ler, gravar e conferir (`pic_texto.py`)

```
H=firmware/cic_rp2040/third_party/snescic-lock-resync.hex
python3 tools/pic/pic_texto.py ler backup.hex          # ID, configuração e OSCCAL, lidos duas vezes: GUARDE este arquivo
python3 tools/pic/pic_texto.py gravar $H --simular     # não escreve nada
python3 tools/pic/pic_texto.py gravar $H               # grava, confere, falha se BG ou OSCCAL mudarem
python3 tools/pic/pic_texto.py conferir $H
```
(`--porta /dev/ttyACM0` num Uno original.) **Não use `ardpicprog --erase` nem `--burn`**: veja a seção seguinte.

## Uno com UART defeituoso: ler e gravar em texto (D214, 2026-11-24)

No Uno do usuário (clone CH340, assinatura `1E 95 0F`) o `ardpicprog` com o sketch original **não funciona**, mesmo com a fiação
conferida (Vdd em D8, clock em D9, dados em D10). Medido em 2026-11-24, com o chip virgem no soquete e 13 V no MCLR:

| Sketch no Uno | Resultado do `ardpicprog -o x.hex` |
|---|---|
| original (só os pinos trocados) | "does not have an identifier" ou "Read from device failed", sempre |
| só `DELAY_THLD0` de 5 para 2000 µs | detecta o chip; a leitura falha |
| só UART por polling | não detecta; a leitura falha |
| os dois juntos (`PROGRAMPIC_POLLING=1`) | detecta; lê com sucesso só 2 de 8 vezes |

Duas causas independentes: (1) o `HardwareSerial` por interrupção trava neste Uno ao enviar rajadas (um sketch de teste que só manda
2081 bytes perdeu bytes e o Uno ficou mudo, **com o Uno nu, sem fio nenhum**; com polling chegou limpo 8 de 8); (2) logo depois de
ligar o Vdd o primeiro comando precisa de mais que 5 µs (sem isso a configuração vinha como `0000`). Mesmo com os dois ajustes, o
fluxo **binário** (`READBIN`) chega com cabeçalhos de pacote trocados e bytes sobrando; a causa **não foi achada**. O fluxo em
**texto** (`READ`) saiu válido e correto em 26 de 26 leituras, e o texto detecta a corrupção (token que não é hexadecimal de 4
dígitos). Por isso existe o `pic_texto.py`, hoje o caminho padrão.

- `programpic-uart-polling.patch`: UART sem interrupção (TX e RX por polling) e `DELAY_THLD0` de 5 para 2000 µs.
  **Com este sketch o `WRITEBIN` do `ardpicprog` não serve** (o RX por polling não tem buffer): grave só com o `pic_texto.py`.
- `programpic-pinos-portb.patch`: Vdd em D8, clock em D9 e dados em D10 em vez de D2, D4 e D7. É a fiação usada na bancada
  (cinco PICs gravados com ela) e a de toda a documentação. **Não foi provado que os pinos ajudem** com o defeito acima (o
  estudo foi todo em D8/D9/D10).
- `pic_texto.py gravar` **não apaga**: exige a memória de programa em branco (ou já igual ao hex), grava 4 palavras por
  comando, relê cada trecho e no fim compara tudo. Não escreve a calibração OSCCAL (`0x3FF`) e grava a configuração com
  `WRITE FORCE`, mantendo os bits BG (`0x3000`) lidos duas vezes antes de escrever; falha se BG ou OSCCAL mudarem (D220:
  o `WRITE` sem `FORCE`, que lê os BG uma única vez, apagou um bit num chip). A comparação da configuração ignora os bits 11 a 9, que este chip lê sempre como 0 (gravar `0x3FD3` dava `ERROR` no
  `WRITE` do sketch, embora o resto da palavra ficasse gravado: o chip ficou com `0x11D3`).
- **Restaurar a calibração de um chip** (feito uma vez, D220, com o backup do `pic_texto.py ler` em mãos): `ERASE NOPRESERVE`
  no sketch (o `ERASE` comum regravaria os BG errados), conferir que tudo ficou vazio e os BG voltaram a `11`, e devolver com
  `WRITE FORCE` o OSCCAL (`0x3FF`), as palavras reservadas (`0x2004`, `0x2005`) e a configuração com os BG de fábrica
  (`0x2007`); só então gravar. Só limpa bits: um bit zerado a mais só volta com outro apagamento. Não há comando pronto para isso.
- **O apagamento (`ERASE`) falhou** e deixou um chip com os bits BG trocados (`0x11FF` virou `0x31FF`; o valor de fábrica era `01`).
  Recuperei com `WRITE FORCE 2007 11FF` no sketch (só limpa o bit 13). **Antes de apagar um PIC, guarde a configuração**
  (`pic_texto.py ler`) e, se os BG mudarem, devolva-os.
- **Não ponha capacitor grande (10 µF) no pino 1 do PIC**: o Vdd sai direto de um pino do Uno e a corrente de partida pode passar do
  limite do ATmega. Na bancada o capacitor coincidiu com resets do Uno; não foi isolado como causa.
- Cuidado com a numeração do PIC (entalhe e pino 1): o usuário confundiu a numeração numa parte dos testes, e isso atrapalha o
  diagnóstico. Os desenhos de `../shield_uno/docs/` mostram o chip com o entalhe para baixo.

## Problemas

- **Não detecta o chip** (ID `0x3FFF` ou `0x0000`): confira se o sketch gravado usa os mesmos pinos da fiação, a ligação acima,
  o GND comum, as soldas/contatos e se há 13 V no pino 4 **durante** a leitura (com o Uno parado o pino 4 fica perto de 0 V).
- **Nada na serial:** feche o monitor serial; confira a porta (`ls /dev/ttyACM*`; o usuário precisa estar no grupo `dialout`).
- **Erro de verificação:** grave de novo; se repetir, suspeite da fonte de 13 V (queda com carga) ou do contato na protoboard.
