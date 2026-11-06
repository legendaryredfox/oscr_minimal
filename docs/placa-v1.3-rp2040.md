# Placa 16_bits v. 1.3: módulo RP2040-Zero no lugar do PIC12F629

Estado (2026-11-06): **decidido pelo usuário, placa ainda não alterada.** O RP2040 só entra na v. 1.3, **se der certo** na bancada; a v. 1.2 fecha com o PIC (estudo final em `boards/16_bits/docs/estudo-final-v1.2.md`). A v1.0 encomendada usa o PIC com um
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
- **Geometria dos furos (medida no STEP oficial da Waveshare**, `files.waveshare.com/upload/f/f7/RP2040_Zero_stp.zip`;
  coordenadas do módulo em mm, origem no canto do modelo; o arquivo não está no repo):
  - Duas colunas em x = 1,33 e x = 16,57: **15,24 mm centro a centro (0,6 pol)**, 1,38 mm da borda lateral.
  - 9 furos por coluna, passo 2,54 mm, em y = 22,01; 19,47; 16,93; 14,39; 11,85; 9,31; 6,77; 4,23; 1,69.
    O primeiro (y = 22,01) é o 5V à esquerda e o GP0 à direita; o último (y = 1,69) é o GP14 e o GP8.
  - Linha inferior, y = 1,69: cinco furos (GP13 a GP9) em x = 3,87; 6,41; 8,95; 11,49; 14,03.
  - Furo de 0,9 mm de diâmetro (raio 0,45 no modelo): cabe o pino macho de 0,64 mm.
  - A USB-C fica centrada (cerca de 4,4 mm de folga de um lado e 4,67 mm do outro, pelo desenho).
  - A foto do paquímetro do usuário (2026-11-06) não deu para ler com precisão (os dois verniers discordam por
    paralaxe), mas o espaçamento estimado nela (cerca de 15,4 mm) concorda com os 15,24 mm do STEP.
- Montagem na placa: dois headers fêmea 1×9, 2,54 mm (THT), 15,24 mm entre eles, com a USB-C para fora da borda da placa.

## Sinais (a tabela do PIC12F629 → RP2040)

Direção vista do RP2040. Atribuição de GPIO **provisória** (`firmware/cic_rp2040/cic_rp2040/pins.h`).

| PIC | Sinal | Sentido | Circuito | GPIO |
|---|---|---|---|---|
| 2 | CLK2 (Si5351; slot 56) | entrada | 1 kΩ em série (o CJMCU-5351 sai em cerca de 3,3 V, ver abaixo) | GP29 |
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
- **Nível do CLK2 (inferido da documentação, sem medir):** o CJMCU-5351 tem LDO de 3,3 V no Si5351 (VIN de 3 a 5 V) e as
  fichas dos vendedores dão saída de cerca de 3 V pico a pico. Além disso o próprio Si5351 não passa de 3,6 V de
  alimentação, então a saída não chega a 5 V em módulo nenhum que funcione. O CLK2 vai ao GP29 por 1 kΩ em série (protege
  contra sobretensão e toque nos jumpers); sem divisor. Conferir com o multímetro (módulo ligado, CLK2 ativo) continua
  barato e vale na bancada, mas deixou de ser pré-requisito.
- Antes de desenhar: conferir com a placa v1.3 o espaço (o módulo ocupa 18 × 23,5 mm mais a USB-C para fora
  da borda) e o rótulo no silk de "USB do módulo: só para gravar".

## Plano

1. ~~Medidas do módulo~~ (acima, do STEP da Waveshare).
2. ~~Porte do CIC~~ feito em `firmware/cic_rp2040/` (testado só no PC).
3. **Bancada na v1.0** com o soquete do U2, o RP2040 e o 74HCT125 numa protoboard; cartucho SA-1 real.
4. Esquemático, posicionamento (⏸ revisão visual), roteamento, DRC, `tools/check_netlist.py --board 16_bits`
   com a nova tabela, gerbers (KiCad 10.0.8 e o MCP; `nvm use 24`).
5. Atualizar `bom.md`, `montagem.md`, `pinmap.md` (seção CIC) e a tabela de decisões da seção 1 do `CLAUDE.md`
   (a linha "CIC (SNES SA1): PIC12F629 em soquete" muda).
