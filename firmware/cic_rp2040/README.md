# CIC lock do SNES no RP2040 (substitui o PIC12F629)

Decisão D89 (`docs/decisoes.md`), plano da placa em `docs/planos/placa-v1.3-rp2040.md`.

O SA-1 só libera a ROM quando um CIC "lock" autentica o CIC do cartucho. O OSCR usa um PIC12F629 com
`snescic-lock-resync.hex`. Aqui o RP2040 roda **esse mesmo programa**, sem reescrevê-lo:

```
CLK2 (Si5351) ──► PIO conta 4 bordas = 1 ciclo de instrução do PIC ──► tick
tick ──► interpretador do PIC12F629 (pic12f629.h) executa 1 instrução do snescic-lock-resync.hex
pinos do PIC ◄──► GPIOs do RP2040 (pins.h), com divisores e 74HCT125 para os 5 V do slot
```

O tempo do protocolo acompanha o clock real (1 MHz na fase de destravar o SA-1, 3,072 MHz depois), como no
PIC, porque o relógio do emulador é o próprio CLK2.

## Arquivos

| Caminho | O que é |
|---|---|
| `cic_rp2040/cic_rp2040.ino` | sketch (Arduino-Pico): core 1 roda o emulador, core 0 imprime o estado na serial USB |
| `cic_rp2040/pic12f629.h` | interpretador do PIC12F629 (C++ puro; o mesmo código roda no PC e no RP2040) |
| `cic_rp2040/lock_prog.h` | `snescic-lock-resync.hex` convertido por `tools/hex2words.py` (não edite) |
| `cic_rp2040/pins.h` | pinos do RP2040 e como ligar (provisório até o esquemático da v1.3) |
| `tools/hex2words.py`, `tools/tick.pio` | conversor do `.hex`; fonte `pioasm` da base de tempo (para conferir as palavras) |
| `test/` | simulador de PC lock × key (`make test`) |
| `third_party/` | código do sd2snes (GPL v2 only, ver o README de lá) |

## Compilar e gravar

```
arduino-cli compile -b rp2040:rp2040:waveshare_rp2040_zero firmware/cic_rp2040/cic_rp2040
```
Core `rp2040:rp2040` 5.6.0, CPU 200 MHz (padrão da placa). Gravação: segurar BOOT ao ligar o USB e copiar o
`.uf2` (ou `arduino-cli upload`). Ligue o USB só para gravar e ver a serial; a alimentação em uso vem dos 5 V
da placa, por um diodo Schottky (ver o plano da v1.3).

Serial USB, 115200, uma linha por segundo: `ciclos=<n> atrasos=<n> pc=0x<hex> latch=0x<hex>`.
**`atrasos` precisa ficar em 0**: conta as vezes em que o RP2040 pegou o tick do PIC já atrasado.

## Testes de PC (`make -C test test`)

Precisa de `gputils` (`gpasm`) e `g++`. Monta o lock e o key do sd2snes, **confere que o lock montado é
idêntico ao `.hex` distribuído**, liga lock e key pelos mesmos três fios do slot e roda 3 milhões de ciclos
para as regiões D411 (NTSC) e D413 (PAL). Passa se:

1. sem conflito de barramento, o reset do host sobe, o LED do key fica alto e estável (autenticou);
2. os seeds na RAM do lock são iguais, em todas as rodadas, aos do `mangle()` do sd2snes (`cic/mangle.c`,
   referência em C independente do interpretador): 589 de 589 rodadas;
3. cada iteração dos loops de mangle gasta 76/78 (sem skip) ou 82/84 ciclos (com skip); 78 e 84 são os
   "CIC has 78/84" do próprio `.asm` (os "69/73" dos comentários dele são antigos, sem os NOPs).

Prova que o teste pega erro: mutações no interpretador (INCF soma 2, COMF sem inverter, BTFSC com skip em
1 ciclo, GOTO/CALL em 1 ciclo, DECFSZ subtraindo 2) fazem o teste falhar. Duas mutações passam e são
esperadas: carry e DC do ADD, que o programa não usa (testa o bit 4 da RAM com `btfsc`).

## O que NÃO foi validado

Nada disto rodou num RP2040 nem numa placa. Falta, em ordem:

1. **Tempo no RP2040:** o contador `atrasos` tem que ficar em 0 com CLK2 a 1 MHz e a 3,072 MHz. A conta
   estimada: o ciclo do PIC a 3,072 MHz dura 1,30 µs (260 ciclos do RP2040 a 200 MHz); o `step()` tem 1 KB
   de código na RAM e cada instrução usa uma fração disso. Estimativa, não medição.
2. **A base de tempo PIO** (palavras conferidas com o `pioasm`, mas nunca rodadas).
3. **Níveis:** o CLK2 do CJMCU-5351 deve sair em cerca de 3,3 V (inferido da documentação do módulo e do limite de
   3,6 V do Si5351; conferir com o multímetro); divisores e 74HCT125 nunca foram montados; o sentido de GP0 e GP1 muda durante a autenticação, então o OE dos dois buffers é crítico.
4. **Cartucho SA-1 real** com o Mega: o firmware do Mega espera o PIC como está em `SNES.cpp` (PG1 baixo,
   500 ms, depois os clocks a 3,072 MHz); o RP2040 roda o mesmo programa, mas o conjunto nunca foi testado.
5. O simulador liga o lock a um key **simulado**. Um CIC real pode ter folgas de tempo diferentes; o
   lock-resync foi feito para tolerar isso, mas só o hardware confirma.

## Bancada na placa v1.0 (antes de encomendar a v1.3)

**Guia passo a passo para montar na protoboard, com desenhos e roteiro de teste: [`bancada/README.md`](bancada/README.md).** O resumo abaixo é a referência das ligações.

Tire o PIC do soquete U2. Pinos do soquete (do `pinmap.md`): 1 = 5 V, 2 = CLK2, 3 = D41, 4 = D40,
5 = slot 25, 6 = slot 24, 7 = slot 55, 8 = GND.

| Soquete U2 | Circuito | RP2040 |
|---|---|---|
| 2 CLK2 | 1 kΩ em série; o CJMCU-5351 sai em cerca de 3,3 V (LDO de 3,3 V no módulo; o Si5351 não passa de 3,6 V) | GP29 |
| 4 D40 | divisor 2,0 kΩ série + 3,3 kΩ para GND | GP28 |
| 6 slot 24 | divisor 2,0 kΩ / 3,3 kΩ (leitura) e saída Y da porta B do 74HCT125 | GP27 (leitura) |
| 7 slot 55 | divisor 2,0 kΩ / 3,3 kΩ (leitura) e saída Y da porta A do 74HCT125 | GP26 (leitura) |
| 5 slot 25 | saída Y da porta C | |
| 3 D41 | saída Y da porta D | |

74HCT125 (DIP-14; pino 14 = VCC, ligado aos 5 V do pino 1 do soquete; pino 7 = GND). Pinagem, /OE ativo em baixo e limites
conferidos no datasheet TI SN74HCT125 (SCLS069G): VCC 4,5 a 5,5 V, VIH mín. 2 V, VOH mín. 3,84 V a 6 mA, IOL 6 mA, tpd máx. 25 ns:

| Porta | /OE | A (entrada) | Y (saída) |
|---|---|---|---|
| A | pino 1 ← GP0 (+ pull-up 10 kΩ ao 3V3) | pino 2 ← GP15 | pino 3 → soquete 7 |
| B | pino 4 ← GP1 (+ pull-up 10 kΩ ao 3V3) | pino 5 ← GP14 | pino 6 → soquete 6 |
| C | pino 10 → GND | pino 9 ← GP2 (+ pull-down 10 kΩ) | pino 8 → soquete 5 |
| D | pino 13 → GND | pino 12 ← GP3 (+ pull-down 10 kΩ) | pino 11 → soquete 3 |

Alimentação do RP2040-Zero: pino 5V pelo catodo de um 1N5819 cujo ânodo vai ao pino 1 do soquete; GND comum.
Nunca ligue 5 V direto a um GPIO.
