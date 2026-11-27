# Adaptador do Magnavox Odyssey 2 / Philips Videopac para o slot SNES (F-20, D226)

O núcleo `Odyssey2.cpp` do OSCR usa o barramento do slot SNES. O endereço sai por PF (A0 a A7) e PK (A8 a A13); os dados D0 a D7 entram por PC, em ordem normal. **/PSEN** (PH6) abre a leitura: o `readData` do núcleo o baixa, espera 5 NOP, lê PC e o sobe. **CS3** (PH3) fica baixo o tempo todo; **T0** (PH0) fica alto. A troca de banco dos cartuchos de 12 e 16 KB (Videopac+) é uma escrita do número do banco (invertido) no endereço `$80` com **/CS1** (PH4) e **/WR** (PH5) baixos (`bankSwitch` do núcleo). `PH1` e `TIME` (PJ0) ficam altos e **não chegam ao cartucho**; PA e PL ficam sem ligação. O cartucho é de 5 V (`setVoltage(k5V)`; o slot SNES é 5 V fixo em todas as placas, sem regulador no adaptador). O adaptador não foi desenhado: falta o PCB (conector de 30 posições em duas fileiras de 15, 3,96 mm segundo o quadro do núcleo, "30P 3.96mm pitch connector").

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 30P 3.96mm pitch connector" no começo de `firmware/oscr/src/cores/Odyssey2.cpp` (igual ao `legacy/Cart_Reader/ODY2.ino`), com a lista CONTROL PINS (T0 no RESET, CS3 no /CS, /CS1 no /IRQ, /WR no /WR e /PSEN no /RD do slot SNES). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_odyssey2.py` confere o quadro, a lista CONTROL PINS, o pinmap e as portas que o núcleo usa.

O conector tem a fileira da frente numerada de 1 a 15 e a de trás com letras (A a R, sem I, O e Q). Os rótulos com parênteses do quadro (`A10 (P22)`, `A9 (P21)`) dão o nome do pino do 8048 no console; vale o primeiro nome.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (30P) |
|---|---|---|---|
| A0 | 17 | PF0 | G |
| A1 | 16 | PF1 | H |
| A2 | 15 | PF2 | J |
| A3 | 14 | PF3 | K |
| A4 | 13 | PF4 | L |
| A5 | 12 | PF5 | M |
| A6 | 11 | PF6 | P |
| A7 | 10 | PF7 | N |
| A8 | 9 | PK0 | R |
| A9 | 8 | PK1 | 15 |
| A10 | 7 | PK2 | 10 |
| A11 | 6 | PK3 | 14 |
| P10 | 37 | PK4 | 13 |
| P11 | 38 | PK5 | 12 |
| D0 | 19 | PC0 | 2 |
| D1 | 20 | PC1 | 3 |
| D2 | 21 | PC2 | 4 |
| D3 | 22 | PC3 | 5 |
| D4 | 50 | PC4 | 6 |
| D5 | 51 | PC5 | 7 |
| D6 | 52 | PC6 | 8 |
| D7 | 53 | PC7 | 9 |
| T0 | 26 | PH0 | 1 |
| CS3 | 49 | PH3 | E |
| /CS1 | 18 | PH4 | 11 |
| /WR | 54 | PH5 | A |
| /PSEN | 23 | PH6 | F |

Pinos fixos do conector: +5V no D (slot 27 e 58, 5 V fixo), GND no B e no C (slot 5 e 36).

## Pontos a conferir com o cartucho na mão

- **P10 e P11 (dedução, não está no quadro):** o quadro não diz onde P10 e P11 entram no slot SNES. O núcleo lê os cartuchos de 4 e 8 KB em janelas de 2 KB em `$0400`, `$1400`, `$2400` e `$3400`, isto é, mudando os bits 12 e 13 do endereço (PK4 e PK5), que não aparecem em nenhum outro pino do quadro; no console, P10 e P11 são justamente os bits da porta 1 do 8048 que trocam o banco de 2 KB desses cartuchos. Daí P10 = A12 (PK4, pino 37 do slot) e P11 = A13 (PK5, pino 38). **Confirmar com o adaptador do OSCR ou com um cartucho de 8 KB** (com a ordem trocada, o dump de 8 KB sai com as duas janelas do meio trocadas e o CRC32 não confere no No-Intro).
- **A10 (pino 10):** a maioria dos cartuchos não o liga (nota do quadro); só o Videopac 31 (Musician) e o 40 (4 in 1 Row) o usam, e é para eles o `--mapper 1`, que lê 4 KB contínuos de `$0000`.
- **T0 (pino 1):** o núcleo o conduz em nível alto o tempo todo. Se algum cartucho usar T0 como saída, um resistor em série (1 kΩ) no adaptador evita a disputa.
- **Passo e chaveamento:** o quadro diz 3,96 mm em duas fileiras de 15; medir no cartucho antes de escolher o conector (conector de borda para placa de 3,96 mm, como o de cartuchos de Famicom antigos).
- A sondagem do firmware (32 bytes de `$0400`) só separa slot vazio de cartucho; o fork não confere assinatura nem cabeçalho. O PC sempre informa o tamanho (`--prg 2|4|8|12|16`).
