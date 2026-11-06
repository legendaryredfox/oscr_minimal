# Gravar o PIC12F629 com Arduino Uno (ardpicprog)

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

## Ligações (confirmadas no esquema e no sketch do ardpicprog)

```
13 V (+) ──┬── 10 kΩ ──┬── PIC pino 4 (MCLR)
           │           └── coletor do transistor
           └── (LED vermelho + 1 kΩ ao GND, opcional)
Uno A1 ── 4,7 kΩ ── base do transistor        emissor ── GND
Uno D2 ── PIC pino 1 (Vdd)        100 nF entre o pino 1 e o pino 8, junto ao chip
Uno D4 ── PIC pino 6 (clock)
Uno D7 ── PIC pino 7 (dados)
Uno GND ── PIC pino 8 (Vss) ── GND da fonte de 13 V   (GND comum!)
PIC pinos 2, 3 e 5: sem ligação
```
A1 em nível **baixo** deixa o MCLR em 13 V (gravação); em nível alto o transistor puxa o MCLR a GND (reset). O sketch
aplica os 13 V no MCLR **antes** de ligar o Vdd, como a especificação de programação manda. Os 13 V nunca vão a um pino do Uno.

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
tools/pic/uno/instalar_ardpicprog.sh        # baixa (commit fixo), compila o programa do PC, prepara o sketch
arduino-cli compile -b arduino:avr:uno tools/pic/bin/ProgramPIC
arduino-cli upload  -b arduino:avr:uno -p /dev/ttyUSB0 tools/pic/bin/ProgramPIC     # ttyACM0 num Uno original
```
> Estado: o instalador e o sketch **não foram compilados** aqui (o ambiente não permitiu rodar código baixado).
> O sketch é de 2011 (`.pde`) e só inclui `avr/pgmspace.h`; se o compilador novo reclamar, veja a mensagem.
> Feche o monitor serial da IDE antes de usar o `ardpicprog` (ele roubaria os dados).

## Gravar (sintaxe da documentação do ardpicprog)

```
A="tools/pic/bin/ardpicprog -p /dev/ttyUSB0"   # o padrão do programa é /dev/ttyACM0; use -p

$A --list-devices                              # teste da comunicação: lista pic12f629 com *
$A -o backup-virgem.hex --skip-ones            # lê o chip (autodetecta); guarde o arquivo
$A --erase --burn -i firmware/cic_rp2040/third_party/snescic-lock-resync.hex -o lido.hex --skip-ones
python3 -I tools/pic/comparar_hex.py firmware/cic_rp2040/third_party/snescic-lock-resync.hex lido.hex
```
`--burn` já relê o chip e verifica. Sem `--force-calibration`, o programa **preserva a calibração OSCCAL** do chip
(a palavra 0x3FF) e ignora a do `.hex`: era a minha preocupação principal com o 12F629, e o programa trata disso sozinho.
O `comparar_hex.py` é a segunda conferência: ignora essa palavra e confere o resto, inclusive a configuração (`0x3FD3`).

## Problemas

- **Não detecta o chip:** confira a ligação da tabela, o GND comum e se há 13 V no pino 4 durante a leitura.
- **Nada na serial:** feche o monitor serial; confira a porta (`ls /dev/ttyACM*`; o usuário precisa estar no grupo `dialout`).
- **Erro de verificação:** grave de novo; se repetir, suspeite da fonte de 13 V (queda com carga) ou do contato na protoboard.
