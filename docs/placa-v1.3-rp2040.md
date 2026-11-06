# Placa 16_bits v. 1.3: módulo RP2040-Zero no lugar do PIC12F629

Estado (2026-11-06): **decidido pelo usuário, placa ainda não alterada.** A v1.0 encomendada usa o PIC com um
programador comprado; a v. 1.3 troca o PIC (U2) por um módulo RP2040-Zero programável por USB. O PIC sai
de vez (sem footprint de reserva). Decisão e motivos em `docs/decisoes.md` D89; o firmware do RP2040 está em
`firmware/cic_rp2040/`.

## Por que isso é mais que trocar uma peça

- O `snescic-lock-resync.hex` é código do PIC e não roda em outro chip. O RP2040 roda **o mesmo programa**
  num interpretador do PIC12F629 (`firmware/cic_rp2040/`), temporizado pelo CLK2 do Si5351. Os testes de PC
  (lock × key simulado, seeds contra o `mangle.c` do sd2snes) passam; **nada rodou num RP2040 nem num cartucho SA-1**.
- O RP2040 é 3,3 V e não tolera 5 V nos pinos; os sinais do CIC no slot e do Mega são 5 V.
- **Os dois fios de dados (slot 55 e slot 24) trocam de sentido durante a autenticação** (o programa muda
  TRISIO). Só um level shifter bidirecional serve, ou, como aqui, buffer com /OE mais divisor de leitura.
  A primeira versão deste plano tratava um como entrada e o outro como saída, e estava errada.
- Risco restante: se o RP2040 não pegar o tempo ou o SA-1 real não autenticar, a v1.3 sai sem SA-1. Por isso
  **validar na bancada da v1.0 antes de encomendar** (roteiro em `firmware/cic_rp2040/README.md`).

## Módulo (Waveshare RP2040-Zero, fonte: wiki e desenho de medidas da Waveshare)

- Placa 18,00 × 23,50 mm, passo 2,54 mm, USB-C numa das extremidades curtas (sai 4,67 mm do canto no
  desenho). Raio de canto 1 mm.
- O usuário diz que o módulo tem só os furos, sem headers soldados (a Waveshare descreve furos castelados); os pinos macho entram nesses furos.
- Borda esquerda, de cima para baixo (9): `5V, GND, 3V3, GP29, GP28, GP27, GP26, GP15, GP14`.
  Borda direita (9): `GP0 ... GP8`. Extremidade inferior (5): `GP13, GP12, GP11, GP10, GP9`.
- **A confirmar com paquímetro ou com o STEP da Waveshare** (`files.waveshare.com/upload/f/f7/RP2040_Zero_stp.zip`):
  a distância centro a centro entre as duas fileiras (o desenho dá 1,59 mm da borda ao primeiro furo, o que
  sugere cerca de 14,8 mm) e a posição exata do primeiro furo em relação à ponta da USB-C. Há clones com
  medidas um pouco diferentes: medir o módulo do usuário.
- Montagem na placa: dois headers fêmea 1×9, 2,54 mm (THT), com a USB-C para fora da borda da placa.

## Sinais (a tabela do PIC12F629 → RP2040)

Direção vista do RP2040. Atribuição de GPIO **provisória** (`firmware/cic_rp2040/cic_rp2040/pins.h`).

| PIC | Sinal | Sentido | Circuito | GPIO |
|---|---|---|---|---|
| 2 | CLK2 (Si5351; slot 56) | entrada | direto (medir o nível do módulo antes) | GP29 |
| 4 | D40 (PG1), reset de entrada | entrada | divisor 5 V → 3,3 V | GP28 |
| 6 | slot 24, dados 1 | **bidirecional** | divisor na leitura + porta B do 74HCT125 na escrita | GP27 (lê), GP14 (escreve), GP1 (/OE) |
| 7 | slot 55, dados 0 | **bidirecional** | divisor na leitura + porta A do 74HCT125 na escrita | GP26 (lê), GP15 (escreve), GP0 (/OE) |
| 5 | slot 25, reset do escravo | saída | porta C | GP2 |
| 3 | D41 (PG0), reset do host | saída | porta D | GP3 |

Dez GPIO no total. O lado do Mega (D40 = PG1, D41 = PG0) não muda: `boards/16_bits/docs/pinmap.md`.

## Circuito proposto (THT)

- **M1**: módulo RP2040-Zero em 2 headers fêmea 1×9.
- **U2** (reaproveita a referência): 74HCT125 em DIP-14, VCC 5 V, 100 nF (C7) no VCC. Portas A e B com /OE
  nos GPIO e **pull-up de 10 kΩ ao 3V3** (buffer desligado antes do firmware subir); portas C e D com /OE no GND
  e **pull-down de 10 kΩ** nas entradas (reset em nível baixo antes do firmware subir).
- **R3 a R8**: divisores de leitura (D40, slot 24, slot 55): 2,0 kΩ série + 3,3 kΩ para o GND, 3,1 V com 5 V.
- **D2**: 1N5819 (Schottky THT) dos 5 V da placa ao pino 5V do módulo, para a USB do módulo e os 5 V da placa
  não brigarem.
- O CLK2 entra direto no GP29 se o módulo Si5351 sair em 3,3 V; se sair em 5 V, divisor.
- Antes de desenhar: conferir com a placa v1.3 o espaço (o módulo ocupa 18 × 23,5 mm mais a USB-C para fora
  da borda) e o rótulo no silk de "USB do módulo: só para gravar".

## Plano

1. ~~Medidas do módulo~~ (acima; falta confirmar a distância entre fileiras).
2. ~~Porte do CIC~~ feito em `firmware/cic_rp2040/` (testado só no PC).
3. **Bancada na v1.0** com o soquete do U2, o RP2040 e o 74HCT125 numa protoboard; cartucho SA-1 real.
4. Esquemático, posicionamento (⏸ revisão visual), roteamento, DRC, `tools/check_netlist.py --board 16_bits`
   com a nova tabela, gerbers (KiCad 10.0.8 e o MCP; `nvm use 24`).
5. Atualizar `bom.md`, `montagem.md`, `pinmap.md` (seção CIC) e a tabela de decisões da seção 1 do `CLAUDE.md`
   (a linha "CIC (SNES SA1): PIC12F629 em soquete" muda).
