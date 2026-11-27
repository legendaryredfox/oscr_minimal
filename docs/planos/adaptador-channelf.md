# Adaptador do Fairchild Channel F para o slot SNES (F-20, D224)

O cartucho do Channel F **não tem barramento de endereço**: o F8 (CPU do console) pede cada byte por um código ROMC de 5 bits e o chip de memória do cartucho (3851 PSU ou equivalente) guarda o contador de programa por dentro. O núcleo `ChannelF.cpp` do OSCR imita o console: o código ROMC sai por **PF0 a PF4** (ROMC0 a ROMC4, nos pinos A0 a A4 do slot SNES), o relógio **PHI** por PH3 (pino /CS do slot), **WRITE** por PH5 (/WR) e os dados D0 a D7 entram por PC, em ordem normal. **/INTREQ** (PH4, pino /IRQ do slot) fica alto. A leitura é `setROMC(8)` (zera o PC0), `setREAD` e `readData` em sequência; o `readROM` procura o cabeçalho (`$55` seguido de `$08`, `$2B`, `$AA` ou `$BB`) em até `$4800` leituras e grava daí. `PH0`, `PH1`, `PH6` e `TIME` (PJ0) ficam altos e **não chegam ao cartucho**; PK, PL e PA ficam sem ligação. O adaptador não foi desenhado: falta o PCB (conector de 22 contatos, 2,54 mm, numa largura de 27 posições segundo o quadro do núcleo, "22P (27P Width) 2.54mm pitch connector").

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout" no começo de `firmware/oscr/src/cores/ChannelF.cpp` e a lista "CONTROL PINS" logo abaixo. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_channelf.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (22P) |
|---|---|---|---|
| ROMC0 | 17 | PF0 | 6 |
| ROMC1 | 16 | PF1 | 7 |
| ROMC2 | 15 | PF2 | 8 |
| ROMC3 | 14 | PF3 | 10 |
| ROMC4 | 13 | PF4 | 12 |
| D0 | 19 | PC0 | 3 |
| D1 | 20 | PC1 | 4 |
| D2 | 21 | PC2 | 9 |
| D3 | 22 | PC3 | 11 |
| D4 | 50 | PC4 | 14 |
| D5 | 51 | PC5 | 16 |
| D6 | 52 | PC6 | 17 |
| D7 | 53 | PC7 | 18 |
| PHI | 49 | PH3 | 13 |
| /INTREQ | 18 | PH4 | 5 |
| WRITE | 54 | PH5 | 15 |

Pinos fixos do conector: VDD (+5V) no 19 e no 20 (slot 27 e 58, 5 V fixo), GND no 1 e no 2 (slot 5 e 36). NC no 21. **VGG (+12V) no 22: o slot SNES não tem 12 V** (ver abaixo).

## Pontos a conferir com o cartucho na mão

- **VGG de +12 V (pino 22):** o quadro do núcleo mostra o pino, mas o núcleo não fala dele e nenhuma placa do projeto tem 12 V. Os 3851 PSU originais são NMOS e podem precisar do VGG; ROMs de cartuchos posteriores talvez não. **PENDENTE:** medir num cartucho; se precisar, o adaptador leva um conversor elevador de 5 V para 12 V (corrente a medir).
- **Pino /INTREQ:** o núcleo o põe como saída em nível alto (PH4). No console, /INTREQ é saída do cartucho (pedido de interrupção para o F8); com o PSU puxando o pino para baixo há disputa de nível. Um resistor em série (1 kΩ) no adaptador evita corrente alta. **PENDENTE**, conferir com o cartucho.
- O `readROM` do núcleo **não liga o cartucho** (nem o menu do OSCR o faz antes): a costura chama `cartOn` antes e `cartOff` depois. O `read16K` liga sozinho.
- **Achado no núcleo original:** `setROMSize` descarta a escolha do menu (`OSCR::UI::menu(...)` sem atribuir a `romSize`), então no OSCR o tamanho só muda pela base de dados. Aqui o PC sempre informa o tamanho (`--prg 2|3|4|6`) e a costura põe o índice direto.
- O `readROM` trata dois casos especiais: o Hangman de 3 KB (pula 1 KB de SRAM) e os de 4 KB (pula a BIOS a cada bloco). Cartucho fora desses casos e com tamanho errado sai truncado ou com lixo; o modo `--mapper 1` ("Read 16K" do OSCR) lê 16 KB brutos para comparar.
- A sondagem do firmware repete a procura do cabeçalho do `readROM`: sem cabeçalho o dump no modo 0 é recusado (`ERRO 0x0007`), o modo 1 segue.
