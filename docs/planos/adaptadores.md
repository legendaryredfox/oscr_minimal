# Adaptadores da F-20 para o slot SNES

Um adaptador por sistema, na ordem em que entraram no firmware (D201 a D228). Cada seção diz como o núcleo do OSCR usa o barramento, a tensão, a fonte conferida, a tabela "sinal → pino do slot SNES → porta AVR → pino do conector" e o que falta conferir com o cartucho na mão. **Nenhum adaptador foi desenhado nem montado; nenhum núcleo rodou em hardware.**

Regras que valem para todos:
- Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). O VCC do slot SNES é **5 V fixo em todas as placas**: os sistemas de 3,3 V (Neo Geo Pocket, Supervision, Pokémon Mini e V.Smile) precisam de regulador próprio no adaptador, alimentado pelo 5 V do slot (27 e 58).
- Cada tabela é conferida por `tools/check_adaptador_<sistema>.py` contra o quadro de pinagem no cabeçalho do núcleo, o pinmap e as portas que o código usa; o verificador lê só a sua seção (a âncora `adaptador-<chave>` antes de cada uma). Atari 5200 e 7800 usam `check_adaptador_atari.py`; Atari 8 bits e Lynx, `check_adaptador_atari8_lynx.py`.

- [Adaptador do ColecoVision para o slot SNES (F-20, D204)](#adaptador-coleco)
- [Adaptador do Neo Geo Pocket para o slot SNES (F-20, D203)](#adaptador-ngp)
- [Adaptador do Vectrex para o slot SNES (F-20, D205)](#adaptador-vectrex)
- [Adaptador do Atari 2600 para o slot SNES (F-20, D206)](#adaptador-a2600)
- [Adaptador do Atari 5200 para o slot SNES (F-20, D209)](#adaptador-a5200)
- [Adaptador do Atari 7800 para o slot SNES (F-20, D209)](#adaptador-a7800)
- [Adaptador do Atari 8 bits (400/800/XL/XE) para o slot SNES (F-20, D210)](#adaptador-a8bit)
- [Adaptador do Atari Lynx para o slot SNES (F-20, D210)](#adaptador-lynx)
- [Adaptador do Atari Jaguar (F-20, D211): PENDENTE, o slot não tem todos os pinos](#adaptador-jaguar)
- [Adaptador do Emerson Arcadia 2001 para o slot SNES (F-20, D215)](#adaptador-arcadia)
- [Adaptador do RCA Studio II para o slot SNES (F-20, D216)](#adaptador-rca2)
- [Adaptador do Tomy Pyuuta para o slot SNES (F-20, D217)](#adaptador-pyuuta)
- [Adaptador do Watara Supervision para o slot SNES (F-20, D218)](#adaptador-supervision)
- [Adaptador do Casio PV-1000 para o slot SNES (F-20, D219)](#adaptador-pv1000)
- [Adaptador do Bally Astrocade para o slot SNES (F-20, D223)](#adaptador-astrocade)
- [Adaptador do Fairchild Channel F para o slot SNES (F-20, D224)](#adaptador-channelf)
- [Adaptador do Magnavox Odyssey 2 / Philips Videopac para o slot SNES (F-20, D226)](#adaptador-odyssey2)
- [Adaptador do Pokémon Mini para o slot SNES (F-20, D227)](#adaptador-pokemini)
- [Adaptador do V.Smile para o slot SNES (F-20, D228)](#adaptador-vsmile)

<a id="adaptador-coleco"></a>

## Adaptador do ColecoVision para o slot SNES (F-20, D204)

O núcleo `Colecovision.cpp` do OSCR (D201) usa o barramento do slot SNES: A0 a A7 em PF, A8 a A14 em PK0 a PK6, D0 a D7 em PC e os quatro seletores de chip em PH3 a PH6 (`/8000` no `/Cart`, `/A000` no `/IRQ`, `/C000` no `/WR`, `/E000` no `/RD`; comentário do próprio núcleo: "CHIP SELECT PINS ... SNES /CS, /IRQ, /WR, /RD"). O adaptador só liga o conector do cartucho ao slot.

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 30P 2.54mm pitch connector" no início de `firmware/oscr/src/cores/Colecovision.cpp` (ímpares no lado de trás, pares na frente; os pinos 13 e 29 são GND). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_coleco.py` confere as três coisas (quadro do núcleo, `pinmap` e portas que o núcleo escreve). Não vi nenhum desenho de adaptador do OSCR para o ColecoVision: a tabela vem só do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (30P) |
|---|---|---|---|
| A0 | 17 | PF0 | 7 |
| A1 | 16 | PF1 | 9 |
| A2 | 15 | PF2 | 11 |
| A3 | 14 | PF3 | 15 |
| A4 | 13 | PF4 | 17 |
| A5 | 12 | PF5 | 21 |
| A6 | 11 | PF6 | 23 |
| A7 | 10 | PF7 | 25 |
| A8 | 9 | PK0 | 28 |
| A9 | 8 | PK1 | 26 |
| A10 | 7 | PK2 | 16 |
| A11 | 6 | PK3 | 14 |
| A12 | 37 | PK4 | 24 |
| A13 | 38 | PK5 | 19 |
| A14 | 39 | PK6 | 20 |
| D0 | 19 | PC0 | 5 |
| D1 | 20 | PC1 | 3 |
| D2 | 21 | PC2 | 1 |
| D3 | 22 | PC3 | 4 |
| D4 | 50 | PC4 | 6 |
| D5 | 51 | PC5 | 8 |
| D6 | 52 | PC6 | 10 |
| D7 | 53 | PC7 | 12 |
| /8000 | 49 | PH3 | 18 |
| /A000 | 18 | PH4 | 22 |
| /C000 | 54 | PH5 | 2 |
| /E000 | 23 | PH6 | 27 |
| GND | 5 e 36 | - | 13 e 29 |
| VCC | 27 e 58 | - | 30 |

Pinos do slot sem uso: os demais. **Tensão: o ColecoVision é 5 V**, o VCC do slot SNES é 5 V fixo; não há o problema do adaptador do NGP (D203). Falta o desenho do PCB: conector de 30 posições, passo de 2,54 mm, 2 fileiras (conferir a peça e o chaveamento), e a espessura de 1,2 mm no slot SNES (nota do OSCR para o adaptador do NGP; confirmar para este).

<a id="adaptador-ngp"></a>

## Adaptador do Neo Geo Pocket para o slot SNES (F-20, D203)

O núcleo `NeoGeoPocket.cpp` do OSCR (D202) usa os mesmos pinos do slot SNES: A0 a A15 em PF e PK, A16 a A20 em PL0 a PL4 (BA0 a BA4 do slot), D0 a D7 em PC, `/CE0` em PH3 (`/Cart`), `/CE1` em PH0 (`/RESET`), `/OE` em PH6 (`/RD`), `/WE` em PH5 (`/WR`) e `PWR` em PH4 (`/IRQ`, entrada com pull-up). **O adaptador é só um cartão que liga o conector do cartucho do NGP a esses pinos do slot.**

### Fonte da tabela (conferida)

Esquemático do adaptador do OSCR: `pcb/adapters/ngp_adapter_schematic.png` e `ngp_adapter.zip` (Gerber), repositório `sanni/cartreader`, commit `bd3eaa106b6e4cbdffbfa89a3fb5fedf3e028b17` (hardware CC BY 4.0). Os números foram lidos na imagem ampliada e cruzados com `boards/16_and_8_bits/docs/pinmap.md` (SNES) e com os comentários e a configuração de portas do núcleo; `python3 tools/check_adaptador_ngp.py` refaz essa conferência. O conector do NGP tem **36 posições** (numeração do esquemático do OSCR); a geometria dele (36 furos de 0,65 mm, duas fileiras defasadas, passo de 1,27 mm por fileira e 2 mm entre fileiras) está no arquivo de furação do Gerber do OSCR. Nenhum número de pino foi tirado de memória.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector NGP |
|---|---|---|---|
| A0 | 17 | PF0 | 2 |
| A1 | 16 | PF1 | 10 |
| A2 | 15 | PF2 | 11 |
| A3 | 14 | PF3 | 12 |
| A4 | 13 | PF4 | 13 |
| A5 | 12 | PF5 | 14 |
| A6 | 11 | PF6 | 15 |
| A7 | 10 | PF7 | 16 |
| A8 | 9 | PK0 | 20 |
| A9 | 8 | PK1 | 21 |
| A10 | 7 | PK2 | 32 |
| A11 | 6 | PK3 | 22 |
| A12 | 37 | PK4 | 23 |
| A13 | 38 | PK5 | 24 |
| A14 | 39 | PK6 | 25 |
| A15 | 40 | PK7 | 26 |
| A16 | 41 | PL0 | 27 |
| A17 | 42 | PL1 | 35 |
| A18 | 43 | PL2 | 17 |
| A19 | 44 | PL3 | 33 |
| A20 | 45 | PL4 | 34 |
| D0 | 19 | PC0 | 6 |
| D1 | 20 | PC1 | 7 |
| D2 | 21 | PC2 | 8 |
| D3 | 22 | PC3 | 9 |
| D4 | 50 | PC4 | 28 |
| D5 | 51 | PC5 | 29 |
| D6 | 52 | PC6 | 30 |
| D7 | 53 | PC7 | 31 |
| /CE0 | 49 | PH3 | 4 |
| /CE1 | 26 | PH0 | 3 |
| /OE | 23 | PH6 | 5 |
| /WE | 54 | PH5 | 19 |
| PWR | 18 | PH4 | 1 |
| GND | 5 e 36 | - | 36 |
| VCC | 27 e 58 | - | 18 |

Pinos do slot sem uso: 24, 25 (CIC), 46 a 48 (BA5 a BA7), 55 a 57 (CIC e CPU clock). Nota do OSCR: a placa do adaptador precisa ter **1,2 mm** de espessura, ou não entra no slot SNES.

### Problema: o VCC do slot SNES é 5 V em todas as placas daqui

O esquemático do OSCR liga o VCC do NGP (pino 18) aos pinos 27 e 58 do slot, porque a placa do OSCR (VSelect) põe 3,3 V ali. **Nenhuma placa deste repositório tem seletor no slot SNES**: o `pinmap` diz "VCC 5V (fixo)" e o `seletor-tensao.md` lista o seletor só nos slots NES, Famicom, Mega Drive e SMS (o SNES fica em 5 V por causa do SA-1). Usar o adaptador do OSCR sem mudança poria **5 V no VCC das flashes do NGP (3,3 V)**. Os sinais do Mega são de 5 V em qualquer caso (D140), como no OSCR com o VSelect; isso fica igual.

Opções (precisa de decisão do usuário):

1. **Adaptador novo com regulador de 3,3 V na própria placa** (LDO THT, por exemplo MCP1700 ou LD1117V33, mais capacitores) alimentado pelos pinos 27 e 58 (5 V) e ligado só ao pino 18 do NGP. É o único que funciona em todas as placas com slot SNES (`snes`, `16_bits`, `16_and_8_bits`, `completa`). Exige desenho de PCB novo (conector de 36 posições, bordas de 1,2 mm no slot).
2. **Gerber do OSCR como está** (1,2 mm), só em placa que dê 3,3 V no slot SNES: nenhuma hoje. Não serve sem alterar uma placa.
3. **Gerber do OSCR com o VCC cortado e ligado a um 3,3 V externo** (modificação à mão). Serve para o primeiro teste; não é produto.

### O que falta

- Decidir a opção (recomendação: 1).
- Escolher o conector do cartucho do NGP (o OSCR usa um soquete de borda cortado; a geometria está no furo do Gerber deles, a peça comercial não foi identificada).
- Desenhar o PCB (1,2 mm, JLCPCB) e o esquemático em KiCad em `boards/adaptadores/ngp/`, com a atribuição ao OSCR (CC BY 4.0) no silkscreen e no README.
- Medir em bancada: continuidade de cada linha, 3,3 V no pino 18, e só então um cartucho.

<a id="adaptador-vectrex"></a>

## Adaptador do Vectrex para o slot SNES (F-20, D205)

O núcleo `Vectrex.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, A8 a A15 em PK, D0 a D7 em PC, `/CART` em PH3 (`/Cart`, pino 49), `PB6` em PH5 (`/WR`, pino 54, a troca de banco dos cartuchos de 64 KB) e `R/W` em PH6 (`/RD`, pino 23). O adaptador liga o conector de 36 pinos do cartucho a esses pinos.

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 36P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/Vectrex.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_vectrex.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o Vectrex: a tabela vem do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (36P) |
|---|---|---|---|
| A0 | 17 | PF0 | 17 |
| A1 | 16 | PF1 | 15 |
| A2 | 15 | PF2 | 13 |
| A3 | 14 | PF3 | 11 |
| A4 | 13 | PF4 | 9 |
| A5 | 12 | PF5 | 7 |
| A6 | 11 | PF6 | 5 |
| A7 | 10 | PF7 | 3 |
| A8 | 9 | PK0 | 6 |
| A9 | 8 | PK1 | 8 |
| A10 | 7 | PK2 | 14 |
| A11 | 6 | PK3 | 10 |
| A12 | 37 | PK4 | 29 |
| A13 | 38 | PK5 | 31 |
| A14 | 39 | PK6 | 33 |
| A15 | 40 | PK7 | 16 |
| D0 | 19 | PC0 | 19 |
| D1 | 20 | PC1 | 21 |
| D2 | 21 | PC2 | 23 |
| D3 | 22 | PC3 | 26 |
| D4 | 50 | PC4 | 24 |
| D5 | 51 | PC5 | 22 |
| D6 | 52 | PC6 | 20 |
| D7 | 53 | PC7 | 18 |
| /CART | 49 | PH3 | 32 |
| PB6 | 54 | PH5 | 35 |
| R/W | 23 | PH6 | 30 |

Pinos fixos do conector: +5V nos 2 e 4 (slot 27 e 58, 5 V fixo, sem problema de tensão), GND nos 25, 27 e 28 (slot 5 e 36). Sem ligação ao Mega (o núcleo não os usa): `/HALT` (1), `/NMI` (34), `/IRQ` (36).

### Achado: `/OE` (pino 12 do conector) não chega ao slot SNES daqui

O comentário do núcleo diz "`/OE` (PH1) = SNES CPUCLK" (pino 57 do slot). Neste repositório o pino 57 do slot SNES é o `CPU_Clock_57`, ligado ao **Si5351 CLK1**; o PH1 só está nos slots Mega Drive (B19 `VCLK`) e GBA (`CLK_2`). Então o Mega não consegue dirigir o `/OE` do Vectrex pelo slot SNES. **O núcleo mantém o `/OE` em nível baixo o tempo todo** (`cartOn`: "Set /OE LOW", e nenhuma leitura o muda), então a proposta é **ligar o pino 12 do conector ao GND no próprio adaptador**, o que é elétricamente o mesmo. Isto é uma dedução do código, não está confirmado em cartucho; conferir em bancada (continuidade pino 12 a GND e uma leitura de um jogo de 4 KB). O pino 57 do slot fica sem ligação no adaptador (senão o clock do Si5351 iria ao `/OE`).

Falta o desenho do PCB (conector de 36 posições, 2 fileiras, 2,54 mm, chaveamento e espessura no slot SNES a confirmar).

<a id="adaptador-a2600"></a>

## Adaptador do Atari 2600 para o slot SNES (F-20, D206)

O núcleo `Atari2600.cpp` do OSCR usa só o barramento de endereços e dados do slot SNES: A0 a A7 em PF, A8 a A12 em PK0 a PK4 e D0 a D7 em PC. **Não há sinal de controle**: o cartucho de 2600 não tem `/CE` nem `/OE` (a ROM é selecionada pelo A12), e o núcleo deixa PH0 a PH6 em nível alto sem ligá-los a nada ("Set Control Pins to Output [UNUSED]"). O adaptador liga o conector de 24 pinos do cartucho a esses pinos.

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 24P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/Atari2600.cpp` (fileira de cima 24 a 13 no lado da etiqueta, de baixo 1 a 12). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_a2600.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o 2600: a tabela vem do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (24P) |
|---|---|---|---|
| A0 | 17 | PF0 | 8 |
| A1 | 16 | PF1 | 7 |
| A2 | 15 | PF2 | 6 |
| A3 | 14 | PF3 | 5 |
| A4 | 13 | PF4 | 4 |
| A5 | 12 | PF5 | 3 |
| A6 | 11 | PF6 | 2 |
| A7 | 10 | PF7 | 1 |
| A8 | 9 | PK0 | 22 |
| A9 | 8 | PK1 | 21 |
| A10 | 7 | PK2 | 19 |
| A11 | 6 | PK3 | 20 |
| A12 | 37 | PK4 | 18 |
| D0 | 19 | PC0 | 9 |
| D1 | 20 | PC1 | 10 |
| D2 | 21 | PC2 | 11 |
| D3 | 22 | PC3 | 13 |
| D4 | 50 | PC4 | 14 |
| D5 | 51 | PC5 | 15 |
| D6 | 52 | PC6 | 16 |
| D7 | 53 | PC7 | 17 |

Pinos fixos do conector: +5V no 23 (slot 27 e 58, 5 V fixo; **sem problema de tensão**) e GND nos 12 e 24 (slot 5 e 36). Nenhum outro pino do conector é usado.

Falta o desenho do PCB (conector de 24 posições, 2 fileiras, 2,54 mm, chaveamento e espessura no slot SNES a confirmar). Cartuchos com mapper de RAM ou com `writeData` (3E, E7, FA, FE, X07 e outros) escrevem no cartucho pelo barramento de dados: o 2600 não tem pino de escrita, o OSCR usa o endereço para isso, então o adaptador não precisa de `/WE`.

<a id="adaptador-a5200"></a>

## Adaptador do Atari 5200 para o slot SNES (F-20, D209)

O núcleo `Atari5200.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, A8 a A13 em PK0 a PK5 e D0 a D7 em PC, mais dois selects: `/4000` (PH5, ROM em $4000-$7FFF) e `/8000` (PH6, ROM em $8000-$BFFF). Os dois ficam em PH5 e PH6, que no slot SNES são os pinos 54 e 23. O núcleo deixa PH0, PH1, PH3 e PH4 em nível alto sem ligá-los a nada.

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 36P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/Atari5200.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_atari.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o 5200: a tabela vem do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector |
|---|---|---|---|
| A0 | 17 | PF0 | 19 |
| A1 | 16 | PF1 | 20 |
| A2 | 15 | PF2 | 17 |
| A3 | 14 | PF3 | 21 |
| A4 | 13 | PF4 | 22 |
| A5 | 12 | PF5 | 16 |
| A6 | 11 | PF6 | 15 |
| A7 | 10 | PF7 | 27 |
| A8 | 9 | PK0 | 29 |
| A9 | 8 | PK1 | 31 |
| A10 | 7 | PK2 | 33 |
| A11 | 6 | PK3 | 35 |
| A12 | 37 | PK4 | 34 |
| A13 | 38 | PK5 | 32 |
| D0 | 19 | PC0 | 1 |
| D1 | 20 | PC1 | 2 |
| D2 | 21 | PC2 | 3 |
| D3 | 22 | PC3 | 4 |
| D4 | 50 | PC4 | 5 |
| D5 | 51 | PC5 | 6 |
| D6 | 52 | PC6 | 7 |
| D7 | 53 | PC7 | 8 |
| /4000 | 54 | PH5 | 10 |
| /8000 | 23 | PH6 | 9 |

Pinos fixos do conector: +5V no 26 (slot 27 e 58, 5 V fixo; **sem problema de tensão**) e GND nos 12, 13, 14, 23, 24 e 25 (slot 5 e 36). `INTERLOCK` (18 e 36) e `AUD` (30) ficam sem ligação no adaptador: o `INTERLOCK` é só a ponte que o próprio cartucho faz entre os pinos 18 e 36, e o OSCR não lê áudio. Os pinos 11 e 28 não são ligados (N/C).

Falta o desenho do PCB (conector de 36 posições, 2 fileiras, 2,54 mm, chaveamento e espessura no slot SNES a confirmar). O cartucho do 5200 tem de 4 a 40 KB: o campo `prg` do protocolo informa o tamanho nos mappers que pedem (padrão: 4, 8, 16 ou 32 KB); o mapper do Bounty Bob (2) troca de banco lendo endereços e o do dois chips (1) não precisa de tamanho.

<a id="adaptador-a7800"></a>

## Adaptador do Atari 7800 para o slot SNES (F-20, D209)

O núcleo `Atari7800.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, A8 a A15 em PK0 a PK7 e D0 a D7 em PC, mais `R/W` (PH6), `HALT` (PH0) e o relógio `CLK`. Com `clockgen = true` (o caso desta placa) o relógio de 2 MHz vem da saída CLK1 do Si5351, que no slot SNES é o pino 57 ("CPU clock"); sem o Si5351 o núcleo usa PH1 como saída, mas PH1 não chega ao slot, então **o 7800 exige o módulo Si5351 instalado**. `HALT` e `R/W` ficam em PH0 e PH6, pinos 26 e 23 do slot. A escrita de bancos (`writeData` e `bankSwitch`) usa o `R/W` e o `CLK`: o PAL16 do cartucho SuperGame trava o endereço com 8 pulsos de `CLK`.

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 32P 2.54mm pitch (USE 36P CONNECTOR)" no começo de `firmware/oscr/src/cores/Atari7800.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_atari.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o 7800: a tabela vem do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector |
|---|---|---|---|
| A0 | 17 | PF0 | 26 |
| A1 | 16 | PF1 | 25 |
| A2 | 15 | PF2 | 24 |
| A3 | 14 | PF3 | 23 |
| A4 | 13 | PF4 | 22 |
| A5 | 12 | PF5 | 21 |
| A6 | 11 | PF6 | 20 |
| A7 | 10 | PF7 | 19 |
| A8 | 9 | PK0 | 12 |
| A9 | 8 | PK1 | 11 |
| A10 | 7 | PK2 | 9 |
| A11 | 6 | PK3 | 10 |
| A12 | 37 | PK4 | 8 |
| A13 | 38 | PK5 | 15 |
| A14 | 39 | PK6 | 16 |
| A15 | 40 | PK7 | 17 |
| D0 | 19 | PC0 | 27 |
| D1 | 20 | PC1 | 28 |
| D2 | 21 | PC2 | 29 |
| D3 | 22 | PC3 | 3 |
| D4 | 50 | PC4 | 4 |
| D5 | 51 | PC5 | 5 |
| D6 | 52 | PC6 | 6 |
| D7 | 53 | PC7 | 7 |
| R/W | 23 | PH6 | 1 |
| HALT | 26 | PH0 | 2 |
| CLK | 57 | - | 32 |

Pinos fixos do conector: +5V no 13 (slot 27 e 58, 5 V fixo; **sem problema de tensão**) e GND nos 14 e 30 (slot 5 e 36). `IRQ` (31) e `AUD` (18) ficam sem ligação.

Falta o desenho do PCB (conector de 32 posições em 2 fileiras de 16, 2,54 mm, o quadro do núcleo manda usar um de 36; chaveamento e espessura no slot SNES a confirmar).

<a id="adaptador-a8bit"></a>

## Adaptador do Atari 8 bits (400/800/XL/XE) para o slot SNES (F-20, D210)

O núcleo `Atari8.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, A8 a A12 em PK0 a PK4 e D0 a D7 em PC, mais os selects `/S4` (PH6, ROM em $8000-$9FFF), `/S5` (PH3, ROM em $A000-$BFFF), `R/W` (PH5) e `/CCTL` (PL0, o bloco de controle $D500 que troca de banco). Conector do cartucho de 30 pinos (15 por lado, pinos `A` a `S` no lado da etiqueta e 1 a 15 no lado de baixo).

### Fonte (conferida)

Pinagem do cartucho: o quadro "Left Slot Cartridge Pinout, 30P 2.54mm pitch" no começo de `firmware/oscr/src/cores/Atari8.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_atari8_lynx.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR: a tabela vem do núcleo e do `pinmap`. Nos cartuchos do slot direito (8 KB) o `/S4` deles vem no pino 12, que no conector esquerdo é o `/S5`: o núcleo já trata isso (`atari8right`, lê com o `/S5`), então o mesmo adaptador serve.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector |
|---|---|---|---|
| A0 | 17 | PF0 | 5 |
| A1 | 16 | PF1 | 4 |
| A2 | 15 | PF2 | 3 |
| A3 | 14 | PF3 | 2 |
| A4 | 13 | PF4 | C |
| A5 | 12 | PF5 | D |
| A6 | 11 | PF6 | E |
| A7 | 10 | PF7 | F |
| A8 | 9 | PK0 | H |
| A9 | 8 | PK1 | J |
| A10 | 7 | PK2 | P |
| A11 | 6 | PK3 | N |
| A12 | 37 | PK4 | K |
| D0 | 19 | PC0 | 10 |
| D1 | 20 | PC1 | 9 |
| D2 | 21 | PC2 | 8 |
| D3 | 22 | PC3 | L |
| D4 | 50 | PC4 | 6 |
| D5 | 51 | PC5 | 7 |
| D6 | 52 | PC6 | 11 |
| D7 | 53 | PC7 | M |
| /S4 | 23 | PH6 | 1 |
| /S5 | 49 | PH3 | 12 |
| R/W | 54 | PH5 | R |
| /CCTL | 41 | PL0 | 15 |
| PHI2 | 57 | - | S |

Pinos fixos do conector: +5V no `13` (slot 27 e 58, 5 V fixo; **sem problema de tensão**) e GND no `B` (slot 5 e 36). `RD4` (`A`) e `RD5` (`14`) são entradas que o núcleo configura mas **não lê**: ficam sem ligação no adaptador. Nada mais é usado. O `PHI2` (pino `S`) está na tabela como `-` (Si5351, pino 57).

### PHI2 (D213)

O `PHI2` (pino `S`, o relógio do 6502, 1,79 MHz) vai ao **pino 57 do slot SNES**, que é o CLK1 do Si5351 (o mesmo que o 7800 usa). O núcleo pulsa PH1 na troca de banco (`bankSwitch`), mas PH1 não chega ao slot; no lugar disso a costura do firmware programa o CLK1 em 1,7897725 MHz (relógio NTSC) enquanto lê um cartucho que troca de banco (XE de 32, 64 e 128 KB no slot esquerdo) e o desliga depois. Com o relógio correndo solto o pulso do núcleo é irrelevante: a escrita em `$D5xx` fica de pé por mais de um período (cerca de 1 us contra 0,56 us). **Exige o módulo Si5351 instalado** para 32, 64 e 128 KB (sem ele o firmware recusa a leitura com `E_CARTUCHO_IO`). No de 16 KB o firmware liga o relógio se o Si5351 existir (o Necromancer troca de banco; os de 16 KB comuns não precisam e a leitura não exige o módulo). Cartuchos de 8 KB e o Bounty Bob (40 KB, troca por leitura de endereço) não dependem do `PHI2`. Não conferido em hardware: se o cartucho trocar de banco só em borda de subida isolada, o relógio solto pode precisar de ajuste.

Falta o desenho do PCB (conector de 30 posições, 2,54 mm; o do slot direito usa o mesmo adaptador com os pinos em outra ordem, chaveamento e espessura no slot SNES a confirmar).

<a id="adaptador-lynx"></a>

## Adaptador do Atari Lynx para o slot SNES (F-20, D210)

O núcleo `AtariLynx.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, os bits seguintes do endereço em PK e PL, D0 a D7 em PC, `/OE` (PH6, pino 9 do Arduino) e `/WE` (PH5, pino 8 do Arduino; só a gravação de flash escreve). O `/CE` do cartucho fica no GND (o núcleo diz: "CE is tied low, not accessible"). O cartucho do Lynx não é lido pelo slot de 2,54 mm: o adaptador do OSCR ("SNES-Lynx adapter") liga o conector de cartucho do Lynx (34 posições, quadro no núcleo) ao slot SNES.

### Fonte (conferida) e o que ficou PENDENTE

Pinagem do cartucho: o quadro no começo de `firmware/oscr/src/cores/AtariLynx.cpp` (34 pinos). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_atari8_lynx.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o Lynx.

**Só entram na tabela os sinais cuja ligação o núcleo confirma.** `setAddr` faz `PORTF = addr`, `PORTK = addr >> 8` e `PORTL = (addr >> 16) & 0xF`, e o comentário do núcleo diz "A11 doesn't exist" e "AUDIN connected to L3". Os bits 11 a 18 do endereço do núcleo são o **número do bloco** (256 blocos), e o quadro do cartucho nomeia as linhas de bloco `A12` a `A19`: **qual linha do cartucho recebe qual bit** (PK3 a PK7 e PL0 a PL3) e se `A19` (pino 22) e `AUDIN` (pino 32) vão ambos a PL3 não está no código, e eu não inventei: ficam PENDENTES até conferir com um adaptador do OSCR ou com o usuário.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector |
|---|---|---|---|
| A0 | 17 | PF0 | 17 |
| A1 | 16 | PF1 | 11 |
| A2 | 15 | PF2 | 12 |
| A3 | 14 | PF3 | 13 |
| A4 | 13 | PF4 | 15 |
| A5 | 12 | PF5 | 16 |
| A6 | 11 | PF6 | 14 |
| A7 | 10 | PF7 | 18 |
| A8 | 9 | PK0 | 28 |
| A9 | 8 | PK1 | 29 |
| A10 | 7 | PK2 | 30 |
| D0 | 19 | PC0 | 7 |
| D1 | 20 | PC1 | 5 |
| D2 | 21 | PC2 | 3 |
| D3 | 22 | PC3 | 2 |
| D4 | 50 | PC4 | 4 |
| D5 | 51 | PC5 | 6 |
| D6 | 52 | PC6 | 8 |
| D7 | 53 | PC7 | 9 |
| /OE | 23 | PH6 | 10 |
| /WE | 54 | PH5 | 27 |

PENDENTES (não ligados até confirmar): `A12` a `A19` (pinos 26, 25, 24, 23, 19, 20, 21 e 22 do conector) e `AUDIN` (32). Pinos fixos: GND no 1 (slot 5 e 36); `VCC` nos 31 e 33 e `SWVCC` no 34 (slot 27 e 58, 5 V fixo; **sem problema de tensão**, mas o que o `SWVCC` pede não está no código). **Sem os bits altos o adaptador só enxerga os 2 KB do primeiro bloco: não serve para ler cartucho** até resolver os PENDENTES.

<a id="adaptador-jaguar"></a>

## Adaptador do Atari Jaguar (F-20, D211): PENDENTE, o slot não tem todos os pinos

O núcleo `AtariJaguar.cpp` do OSCR lê 32 bits por vez e **gera o endereço com 74HC595 em cascata** (3 bytes deslocados por `shiftOutFAST`), então o adaptador do Jaguar leva os dois chips de ROM (U1 nos bits 0 a 15 e U2 nos bits 16 a 31 do dado) e os registradores de deslocamento. A leitura de ROM está no firmware (D211); **o adaptador não foi projetado porque nenhum slot da placa tem todos os pinos que o núcleo usa**.

### Fonte (conferida) e o conflito

Portas e sinais: o quadro "HARDWARE PROFILE" e o código de `firmware/oscr/src/cores/AtariJaguar.cpp` (`cartOn`, `shiftOutFAST`, `readData`). Pinos do slot: `boards/16_and_8_bits/docs/pinmap.md`. `python3 tools/check_adaptador_jaguar.py` confere a tabela abaixo e o conflito. **Não há pinagem do conector do cartucho do Jaguar no núcleo** (só portas), então a coluna do conector do cartucho não existe aqui: falta o desenho do adaptador do OSCR (não está em `vendor/oscr/`).

Sinais no slot SNES (todos os que existem lá):

| Sinal | Porta AVR | Pinos do slot SNES |
|---|---|---|
| D0 a D7 (ROM U1, bits 0-7) | PF0 a PF7 | 17, 16, 15, 14, 13, 12, 11, 10 |
| D8 a D15 (ROM U1, bits 8-15) | PK0 a PK7 | 9, 8, 7, 6, 37, 38, 39, 40 |
| D16 a D23 (ROM U2, bits 0-7) | PL0 a PL7 | 41, 42, 43, 44, 45, 46, 47, 48 |
| D24 a D31 (ROM U2, bits 8-15) | PC0 a PC7 | 19, 20, 21, 22, 50, 51, 52, 53 |
| SRCLR do 74HC595 | PE4 | 32 |
| SRCLK do 74HC595 | PE5 | 33 |
| RCLK do 74HC595 | PG5 | 2 |
| OEH | PH3 | 49 |
| OEL | PH4 | 18 |
| CE | PH5 | 54 |
| WE | PH6 | 23 |
| EEPDO (EEPROM, entrada) | PA5 | 61 |
| EEPSK (EEPROM) | PA6 | 3 |
| EEPCS (EEPROM) | PA7 | 34 |

**Falta no slot SNES: `SER` do 74HC595 em PE3** (o núcleo escreve `PORTE |= (1 << 3)`). PE3 só chega ao slot Mega Drive (pino B15, `EDCLK`); o slot SNES tem PJ0 no pino 4, que não é PE3. **E o slot Mega Drive não tem PL7** (D23 do Jaguar). Resultado: **nenhum slot da placa tem PE3 e PL7 ao mesmo tempo**; nas fontes do `pinmap` (esquemático, `ods` e `six_slot_adapter`) o pino 4 do SNES é PJ0 e o B15 do Mega Drive é PE3. Como o OSCR original liga o Jaguar não consegui apurar: o núcleo comenta `ADDR (PE3-PJ0)`, sem dizer qual dos dois.

Caminhos (nenhum foi feito; decisão do usuário):
1. **Slot SNES com `SER` em PJ0 (pino 4):** troca no núcleo de `PORTE bit 3` para `PORTJ bit 0` (macros `SER_SET`/`SER_CLEAR` e o `DDRE` de `cartOn`, 3 linhas) e ligar o `SER` do adaptador ao pino 4. Desvio da regra de reuso, a justificar em `docs/decisoes.md`.
2. **Slot Mega Drive** e aceitar D23 sem ligação: o dado do bit 23 sai errado; não serve.
3. Uma placa nova com o Jaguar (não está no escopo).

<a id="adaptador-arcadia"></a>

## Adaptador do Emerson Arcadia 2001 para o slot SNES (F-20, D215)

O núcleo `Arcadia2001.cpp` do OSCR usa o barramento do slot SNES só para leitura: A0 a A7 em PF, A8 a A13 em PK (A14 e A15 ficam sem uso), D0 a D7 em PC. Os pinos de controle (`PH0`, `PH1`, `PH3` a `PH6`) e `TIME` (PJ0) vão a nível alto e **não chegam ao cartucho**; os endereços A16 a A23 (PL) e os dados PA ficam sem ligação. O cartucho é de 5 V (o slot SNES é 5 V fixo em todas as placas), então não há problema de tensão. O adaptador não foi desenhado: falta o PCB (conector de 30 posições, 2 fileiras, 2,54 mm, chaveamento a confirmar).

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 30P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/Arcadia2001.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_arcadia.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (30P) |
|---|---|---|---|
| A0 | 17 | PF0 | 6 |
| A1 | 16 | PF1 | 8 |
| A2 | 15 | PF2 | 10 |
| A3 | 14 | PF3 | 12 |
| A4 | 13 | PF4 | 14 |
| A5 | 12 | PF5 | 16 |
| A6 | 11 | PF6 | 18 |
| A7 | 10 | PF7 | 20 |
| A8 | 9 | PK0 | 22 |
| A9 | 8 | PK1 | 24 |
| A10 | 7 | PK2 | 26 |
| A11 | 6 | PK3 | 28 |
| A12 | 37 | PK4 | 30 |
| A13 | 38 | PK5 | 1 |
| D0 | 19 | PC0 | 13 |
| D1 | 20 | PC1 | 17 |
| D2 | 21 | PC2 | 15 |
| D3 | 22 | PC3 | 3 |
| D4 | 50 | PC4 | 5 |
| D5 | 51 | PC5 | 7 |
| D6 | 52 | PC6 | 9 |
| D7 | 53 | PC7 | 11 |

Pinos fixos do conector: +5V no 4 (slot 27 e 58, 5 V fixo), GND nos 2, 25 e 27 (slot 5 e 36). Sem ligação (NC no quadro): 19, 21, 23 e 29.

### Pontos a conferir com o cartucho na mão

- O quadro do núcleo rotula o pino 1 como `A13 (A12)` e o pino 30 como `A12 (/EN)`: as duas linhas são endereço no barramento e o **A12 faz o papel de habilitar (`/EN`)** a ROM, em placas diferentes de cartucho. O núcleo conduz A0 a A13, então o pino 1 vai ao PK5 (A13) e o pino 30 ao PK4 (A12), como na tabela. Se algum cartucho ligar o pino 1 ao A12 em vez do A13, a leitura de 4 KB ou mais sai trocada; só se vê no hardware.
- A ROM é lida em `$0000-$0FFF` e `$2000-$2FFF` (2 KB por trecho): o console enxerga assim o cartucho, e o `readROM` do OSCR segue essa ordem.

<a id="adaptador-rca2"></a>

## Adaptador do RCA Studio II para o slot SNES (F-20, D216)

O núcleo `RCAStudio2.cpp` do OSCR usa o barramento do slot SNES só para leitura. O Studio II tem 8 linhas de endereço multiplexadas: o núcleo põe o byte alto de A8 a A15 em PF (PORTF), trava com **TPA** (PH6), e depois põe o byte baixo (A0 a A7) em PF; os dados D0 a D7 entram por PC. O **/MRD** (PH3) abre a leitura. O resto dos pinos de controle (`PH0`, `PH1`, `PH4`, `PH5`) e `TIME` (PJ0) vão a nível alto e **não chegam ao cartucho**; PK, PL e PA ficam sem ligação. O cartucho é de 5 V (o slot SNES é 5 V fixo em todas as placas). O adaptador não foi desenhado: falta o PCB (conector de 22 posições, 3,96 mm, chaveamento a confirmar).

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 22P 3.96mm pitch connector" no começo de `firmware/oscr/src/cores/RCAStudio2.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_rca2.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (22P) |
|---|---|---|---|
| A0 | 17 | PF0 | 11 |
| A1 | 16 | PF1 | 12 |
| A2 | 15 | PF2 | 13 |
| A3 | 14 | PF3 | 14 |
| A4 | 13 | PF4 | 16 |
| A5 | 12 | PF5 | 17 |
| A6 | 11 | PF6 | 18 |
| A7 | 10 | PF7 | 20 |
| D0 | 19 | PC0 | 10 |
| D1 | 20 | PC1 | 9 |
| D2 | 21 | PC2 | 8 |
| D3 | 22 | PC3 | 5 |
| D4 | 50 | PC4 | 4 |
| D5 | 51 | PC5 | 3 |
| D6 | 52 | PC6 | 2 |
| D7 | 53 | PC7 | 1 |
| /MRD | 49 | PH3 | 21 |
| TPA | 23 | PH6 | 19 |

Pinos fixos do conector: +5V no 15 (slot 27 e 58, 5 V fixo), GND no 7 (slot 5 e 36).

### Pontos a conferir com o cartucho na mão

- **ROMCS (22) e ROM_DISABLE (6) não são conduzidos pelo núcleo.** O quadro os lista, mas o `readROM` do OSCR só mexe em /MRD e TPA. Se o cartucho precisar de ROMCS em nível ativo para colocar dados no barramento, o adaptador tem que prendê-lo (GND ou +5 V, conforme a polaridade do cartucho) e deixar ROM_DISABLE no nível que não desabilita a ROM. A polaridade não está no núcleo: **PENDENTE**, só se vê com o cartucho.
- O quadro rotula `/MRD (PH3) - SNES /CS` e `TPA (PH6) - SNES /RD`: nesta tabela o /MRD vai ao pino 49 (PH3) e o TPA ao pino 23 (PH6) do slot, como no pinmap.
- O `readROM` do OSCR lê só `$0400` a `$07FF` (1 KB no índice 1; 512 bytes no índice 0). O menu do OSCR rotula os dois índices como "1" e "2", mas lê 512 B e 1 KB. Cartuchos de 2 KB (mapeados até `$0BFF`) saem truncados em 1 KB; corrigir isso exigiria mexer no núcleo (D216).

<a id="adaptador-pyuuta"></a>

## Adaptador do Tomy Pyuuta para o slot SNES (F-20, D217)

O núcleo `TomyPyuuta.cpp` do OSCR usa o barramento do slot SNES só para leitura. O endereço de 16 bits sai por PF (A0 a A7 do slot, byte baixo) e PK (A8 a A15, byte alto); os dados D0 a D7 entram por PC. **/DBIN** (PH4) abre a leitura e **/CS0** (PH3) e **/CS1** (PH6) escolhem a janela: /CS0 em `$8000-$BFFF` (8 e 16 KB), /CS1 em `$4000-$7FFF` (os 16 KB a mais dos cartuchos de 32 KB, jogos 3D). O `/RESET` (PH0) é levado a nível alto pelo núcleo. O resto dos pinos de controle (`PH1`, `PH5`) e `TIME` (PJ0) vão a nível alto e **não chegam ao cartucho**; PL e PA ficam sem ligação. O cartucho é de 5 V (o slot SNES é 5 V fixo em todas as placas). O adaptador não foi desenhado: falta o PCB (conector de 36 posições, 2,54 mm, duas fileiras, chaveamento a confirmar).

### Ordem dos bits (a armadilha deste sistema)

O Pyuuta usa a numeração do TMS9995: **A0 é o bit mais significativo e A15 o menos; D0 é o bit mais significativo do byte e D7 o menos**. O núcleo põe o endereço `addr` em PF/PK e lê o dado em PC com o bit 0 como o menos significativo. Por isso a fiação do adaptador **inverte** a ordem: o pino A15 do cartucho vai a PF0 e o A0 a PK7; D7 vai a PC0 e D0 a PC7. A tabela abaixo já está nessa ordem. O comentário do núcleo diz o mesmo ("PCB ADAPTER WIRED FOR DIFFERENCE").

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 36P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/TomyPyuuta.cpp` (duas colunas: pinos pares à esquerda, ímpares à direita). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_pyuuta.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (36P) |
|---|---|---|---|
| A0 | 40 | PK7 | 31 |
| A1 | 39 | PK6 | 27 |
| A2 | 38 | PK5 | 25 |
| A3 | 37 | PK4 | 24 |
| A4 | 6 | PK3 | 30 |
| A5 | 7 | PK2 | 28 |
| A6 | 8 | PK1 | 26 |
| A7 | 9 | PK0 | 22 |
| A8 | 10 | PF7 | 20 |
| A9 | 11 | PF6 | 18 |
| A10 | 12 | PF5 | 16 |
| A11 | 13 | PF4 | 14 |
| A12 | 14 | PF3 | 12 |
| A13 | 15 | PF2 | 10 |
| A14 | 16 | PF1 | 23 |
| A15 | 17 | PF0 | 8 |
| D0 | 53 | PC7 | 17 |
| D1 | 52 | PC6 | 15 |
| D2 | 51 | PC5 | 13 |
| D3 | 50 | PC4 | 11 |
| D4 | 22 | PC3 | 9 |
| D5 | 21 | PC2 | 7 |
| D6 | 20 | PC1 | 5 |
| D7 | 19 | PC0 | 3 |
| /CS0 | 49 | PH3 | 35 |
| /CS1 | 23 | PH6 | 21 |
| /DBIN | 18 | PH4 | 29 |
| /RESET | 26 | PH0 | 4 |

Pinos fixos do conector: +5V no 19 (slot 27 e 58, 5 V fixo), GND no 1 e no 2 (slot 5 e 36).

### Pontos a conferir com o cartucho na mão

- **Pinos que o núcleo não conduz:** J1-6 (6), /WE/CPUCLK (32), SOUND (33), /INT4 /EC (34) e CRUIN (36). Só a leitura de ROM não precisa deles; se o cartucho depender de algum (por exemplo CPUCLK para o decodificador), o adaptador tem que prendê-lo no nível certo. **PENDENTE**, depende do cartucho.
- A janela `$8000-$9FFF` (/CS0) vale para todos os tamanhos. O cartucho de 16 KB lê `$A000-$BFFF` também em /CS0, o de 32 KB lê `$4000-$7FFF` em /CS1.
- A sondagem do firmware (32 bytes de `$8000` com /DBIN e /CS0 baixos) só separa slot vazio de cartucho: a ROM do Pyuuta não tem assinatura.

<a id="adaptador-supervision"></a>

## Adaptador do Watara Supervision para o slot SNES (F-20, D218)

O núcleo `Supervision.cpp` do OSCR usa o barramento do slot SNES só para leitura. O endereço sai por PF (A0 a A7), PK (A8 a A15) e PL (`addr >> 16`, o A16 em PL0); os dados D0 a D7 entram por PC. **/RD** (PH6) fica baixo durante a leitura e **/WR** (PH5) fica alto o tempo todo. Os outros pinos de controle (`PH0`, `PH1`, `PH3`, `PH4`) e `TIME` (PJ0) vão a nível alto e **não chegam ao cartucho**. O adaptador não foi desenhado: falta o PCB (conector de 40 posições, 2,5 mm, duas fileiras, chaveamento a confirmar).

### Tensão: 3,3 V (mesmo problema do Neo Geo Pocket, D203)

O núcleo pede 3,3 V (`setVoltage(k3V3)`), apesar de o quadro do cartucho rotular o pino 40 como "+5V". O VCC do slot SNES é **5 V fixo em todas as placas**: ligar o pino 40 direto a ele contraria o núcleo e pode estragar o cartucho. O adaptador precisa do próprio regulador de 3,3 V (LDO), alimentado pelo 5 V do slot (27 e 58) e ligado ao pino 40 do conector. **PENDENTE:** confirmar a tensão real do cartucho (o console usa pilhas e o rótulo do quadro diz 5 V; a decisão do núcleo é 3,3 V).

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 40P 2.5mm pitch connector" no começo de `firmware/oscr/src/cores/Supervision.cpp` (duas colunas: pinos 1 a 20 à esquerda, 40 a 21 à direita). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_supervision.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (40P) |
|---|---|---|---|
| A0 | 17 | PF0 | 2 |
| A1 | 16 | PF1 | 3 |
| A2 | 15 | PF2 | 4 |
| A3 | 14 | PF3 | 5 |
| A4 | 13 | PF4 | 6 |
| A5 | 12 | PF5 | 7 |
| A6 | 11 | PF6 | 8 |
| A7 | 10 | PF7 | 9 |
| A8 | 9 | PK0 | 10 |
| A9 | 8 | PK1 | 11 |
| A10 | 7 | PK2 | 12 |
| A11 | 6 | PK3 | 13 |
| A12 | 37 | PK4 | 14 |
| A13 | 38 | PK5 | 15 |
| A14 | 39 | PK6 | 16 |
| A15 | 40 | PK7 | 17 |
| A16 | 41 | PL0 | 18 |
| D0 | 19 | PC0 | 34 |
| D1 | 20 | PC1 | 33 |
| D2 | 21 | PC2 | 32 |
| D3 | 22 | PC3 | 31 |
| D4 | 50 | PC4 | 30 |
| D5 | 51 | PC5 | 29 |
| D6 | 52 | PC6 | 28 |
| D7 | 53 | PC7 | 27 |
| /RD | 23 | PH6 | 1 |
| /WR | 54 | PH5 | 35 |

Pinos fixos do conector: VCC no 40 (3,3 V do LDO do adaptador, ver acima), GND no 22 e PWR GND no 21 (slot 5 e 36).

### Pontos a conferir com o cartucho na mão

- **A17 a A19 e os pinos de link (L0 a L3, conector 20, 24, 23 e 19) não estão na tabela.** O `readROM` do OSCR lê 512 KB com `addr >> 16` indo até 7 (PL0 a PL2), mas o quadro só tem **A16**. O comentário do núcleo diz que só a variante MAGNUM levou L0 a L3 ao cartucho como bits extras de banco. Como os cartuchos de 512 KB trocam de banco, e por quais pinos, é **PENDENTE**: depende do cartucho. Os de 32 e 64 KB não usam isso.
- Os pinos `nc` (25, 26, 36 a 39) ficam sem ligação.
- A leitura de 32 KB começa em `$8000`; a de 64 KB e a de 512 KB, em `$0000`. A sondagem do firmware lê 32 bytes de `$8000` e só separa slot vazio de cartucho.

<a id="adaptador-pv1000"></a>

## Adaptador do Casio PV-1000 para o slot SNES (F-20, D219)

O núcleo `CasioPV1000.cpp` do OSCR usa o barramento do slot SNES só para leitura. O endereço de 16 bits sai por PF (A0 a A7, byte baixo) e PK (A8 a A15, byte alto); os dados D0 a D7 entram por PC, sem inversão de bits (ordem normal). **/RD** (PH6) abre a leitura e **/CS1** (PH4) ou **/CS2** (PH3) escolhem a ROM: /CS1 para o cartucho de 8 KB, /CS2 para o de 16 KB (o `readROM` baixa um deles por vez e lê `$0000` em diante). **/WR** (PH5) fica alto o tempo todo. `PH0` e `PH1` (também altos) e `TIME` (PJ0) **não chegam ao cartucho**; PL e PA ficam sem ligação. O cartucho é de 5 V (`setVoltage(k5V)`; o slot SNES é 5 V fixo em todas as placas, sem regulador no adaptador). O adaptador não foi desenhado: falta o PCB (conector de 36 posições em duas fileiras de 18, 2,54 mm; o quadro do núcleo chama de "36P 2.54mm pitch").

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 36P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/CasioPV1000.cpp` (fileira B, a da frente, à esquerda; fileira A, a de trás, à direita). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_pv1000.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (36P) |
|---|---|---|---|
| A0 | 17 | PF0 | B10 |
| A1 | 16 | PF1 | A10 |
| A2 | 15 | PF2 | B09 |
| A3 | 14 | PF3 | A09 |
| A4 | 13 | PF4 | B08 |
| A5 | 12 | PF5 | A08 |
| A6 | 11 | PF6 | B07 |
| A7 | 10 | PF7 | A07 |
| A8 | 9 | PK0 | B06 |
| A9 | 8 | PK1 | A06 |
| A10 | 7 | PK2 | B05 |
| A11 | 6 | PK3 | A05 |
| A12 | 37 | PK4 | B04 |
| A13 | 38 | PK5 | A04 |
| A14 | 39 | PK6 | B03 |
| A15 | 40 | PK7 | A03 |
| D0 | 19 | PC0 | B14 |
| D1 | 20 | PC1 | A14 |
| D2 | 21 | PC2 | B13 |
| D3 | 22 | PC3 | A13 |
| D4 | 50 | PC4 | B12 |
| D5 | 51 | PC5 | A12 |
| D6 | 52 | PC6 | B11 |
| D7 | 53 | PC7 | A11 |
| /CS1 | 18 | PH4 | B15 |
| /CS2 | 49 | PH3 | A15 |
| /RD | 23 | PH6 | A16 |
| /WR | 54 | PH5 | B16 |

Pinos fixos do conector: +5V em B01 e B18 (slot 27 e 58, 5 V fixo), GND em A01 e A18 (slot 5 e 36).

### Pontos a conferir com o cartucho na mão

- **Pinos que o núcleo não conduz:** CON (B17) e /IORQ (A17), mais os dois NC (B02 e A02). Só a leitura de ROM não precisa deles; se o cartucho depender de /IORQ ou de CON (por exemplo para desabilitar a ROM), o adaptador tem que prendê-los no nível certo. **PENDENTE**, depende do cartucho.
- O núcleo pressupõe ROM de 8 KB só com /CS1 e de 16 KB só com /CS2, e lê `$0000` em diante nos dois casos. Cartucho com RAM extra ou outro mapeamento não é coberto.
- A sondagem do firmware (32 bytes de `$0000`, primeiro com /CS1 baixo e, se vier vazio, com /CS2 baixo) só separa slot vazio de cartucho: a ROM do PV-1000 não tem assinatura. Fica a conferir se os dois /CS juntos num cartucho de 8 KB causam conflito de barramento (a sondagem só baixa um por vez).
- O PV-2000 usa o mesmo cartucho no quadro do núcleo (título "PV-1000/PV-2000"), mas só o PV-1000 foi levado em conta.

<a id="adaptador-astrocade"></a>

## Adaptador do Bally Astrocade para o slot SNES (F-20, D223)

O núcleo `BallyAstrocade.cpp` do OSCR usa o barramento do slot SNES só para leitura. O endereço sai por PF (A0 a A7) e PK (A8 a A12; o núcleo escreve o byte alto inteiro em PK, mas A13 a A15 ficam sempre em 0 e não chegam ao cartucho); os dados D0 a D7 entram por PC, em ordem normal. **/ENABLE** (PH3) abre a leitura: o `readData` do núcleo o baixa, espera 5 NOP, lê PC e o sobe. `PH0`, `PH1`, `PH4`, `PH5`, `PH6` e `TIME` (PJ0) ficam altos e **não chegam ao cartucho**; PL e PA ficam sem ligação. O cartucho é de 5 V (`setVoltage(k5V)`; o slot SNES é 5 V fixo em todas as placas, sem regulador no adaptador). O adaptador não foi desenhado: falta o PCB (conector de 26 posições numa fileira, 2,54 mm segundo o quadro do núcleo, "26P 2.54mm pitch connector").

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 26P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/BallyAstrocade.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_astrocade.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (26P) |
|---|---|---|---|
| A0 | 17 | PF0 | 9 |
| A1 | 16 | PF1 | 8 |
| A2 | 15 | PF2 | 7 |
| A3 | 14 | PF3 | 6 |
| A4 | 13 | PF4 | 5 |
| A5 | 12 | PF5 | 4 |
| A6 | 11 | PF6 | 3 |
| A7 | 10 | PF7 | 2 |
| A8 | 9 | PK0 | 24 |
| A9 | 8 | PK1 | 23 |
| A10 | 7 | PK2 | 20 |
| A11 | 6 | PK3 | 19 |
| A12 | 37 | PK4 | 22 |
| D0 | 19 | PC0 | 10 |
| D1 | 20 | PC1 | 11 |
| D2 | 21 | PC2 | 12 |
| D3 | 22 | PC3 | 14 |
| D4 | 50 | PC4 | 15 |
| D5 | 51 | PC5 | 16 |
| D6 | 52 | PC6 | 17 |
| D7 | 53 | PC7 | 18 |
| /ENABLE | 49 | PH3 | 21 |

Pinos fixos do conector: +5V no 25 (slot 27 e 58, 5 V fixo), GND no 1, no 13 e no 26 (slot 5 e 36).

### Pontos a conferir com o cartucho na mão

- **Passo e chaveamento do conector:** o quadro do núcleo diz 26 posições a 2,54 mm numa fileira; medir no cartucho antes de escolher o conector. O lado "BOTTOM"/"TOP" do quadro define a face do cartucho que encosta em cada fileira de contatos.
- O núcleo lê `$0000` em diante com /ENABLE baixo e não aciona outro sinal: cartucho que dependa de outro pino (por exemplo um chip select vindo do console) não é coberto. A tabela não tem nenhum pino que o núcleo deixe sem conduzir.
- O `readROM` lê 2, 4 ou 8 KB (tabela `BALLY` do núcleo): o PC sempre informa o tamanho (`--prg 2|4|8`). Um cartucho menor que o tamanho pedido sai espelhado; um maior sai truncado.
- A sondagem do firmware (32 bytes de `$0000`) só separa slot vazio de cartucho; o fork não confere assinatura nem cabeçalho.

<a id="adaptador-channelf"></a>

## Adaptador do Fairchild Channel F para o slot SNES (F-20, D224)

O cartucho do Channel F **não tem barramento de endereço**: o F8 (CPU do console) pede cada byte por um código ROMC de 5 bits e o chip de memória do cartucho (3851 PSU ou equivalente) guarda o contador de programa por dentro. O núcleo `ChannelF.cpp` do OSCR imita o console: o código ROMC sai por **PF0 a PF4** (ROMC0 a ROMC4, nos pinos A0 a A4 do slot SNES), o relógio **PHI** por PH3 (pino /CS do slot), **WRITE** por PH5 (/WR) e os dados D0 a D7 entram por PC, em ordem normal. **/INTREQ** (PH4, pino /IRQ do slot) fica alto. A leitura é `setROMC(8)` (zera o PC0), `setREAD` e `readData` em sequência; o `readROM` procura o cabeçalho (`$55` seguido de `$08`, `$2B`, `$AA` ou `$BB`) em até `$4800` leituras e grava daí. `PH0`, `PH1`, `PH6` e `TIME` (PJ0) ficam altos e **não chegam ao cartucho**; PK, PL e PA ficam sem ligação. O adaptador não foi desenhado: falta o PCB (conector de 22 contatos, 2,54 mm, numa largura de 27 posições segundo o quadro do núcleo, "22P (27P Width) 2.54mm pitch connector").

### Fonte (conferida)

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

### Pontos a conferir com o cartucho na mão

- **VGG de +12 V (pino 22):** o quadro do núcleo mostra o pino, mas o núcleo não fala dele e nenhuma placa do projeto tem 12 V. Os 3851 PSU originais são NMOS e podem precisar do VGG; ROMs de cartuchos posteriores talvez não. **PENDENTE:** medir num cartucho; se precisar, o adaptador leva um conversor elevador de 5 V para 12 V (corrente a medir).
- **Pino /INTREQ:** o núcleo o põe como saída em nível alto (PH4). No console, /INTREQ é saída do cartucho (pedido de interrupção para o F8); com o PSU puxando o pino para baixo há disputa de nível. Um resistor em série (1 kΩ) no adaptador evita corrente alta. **PENDENTE**, conferir com o cartucho.
- O `readROM` do núcleo **não liga o cartucho** (nem o menu do OSCR o faz antes): a costura chama `cartOn` antes e `cartOff` depois. O `read16K` liga sozinho.
- **Achado no núcleo original:** `setROMSize` descarta a escolha do menu (`OSCR::UI::menu(...)` sem atribuir a `romSize`), então no OSCR o tamanho só muda pela base de dados. Aqui o PC sempre informa o tamanho (`--prg 2|3|4|6`) e a costura põe o índice direto.
- O `readROM` trata dois casos especiais: o Hangman de 3 KB (pula 1 KB de SRAM) e os de 4 KB (pula a BIOS a cada bloco). Cartucho fora desses casos e com tamanho errado sai truncado ou com lixo; o modo `--mapper 1` ("Read 16K" do OSCR) lê 16 KB brutos para comparar.
- A sondagem do firmware repete a procura do cabeçalho do `readROM`: sem cabeçalho o dump no modo 0 é recusado (`ERRO 0x0007`), o modo 1 segue.

<a id="adaptador-odyssey2"></a>

## Adaptador do Magnavox Odyssey 2 / Philips Videopac para o slot SNES (F-20, D226)

O núcleo `Odyssey2.cpp` do OSCR usa o barramento do slot SNES. O endereço sai por PF (A0 a A7) e PK (A8 a A13); os dados D0 a D7 entram por PC, em ordem normal. **/PSEN** (PH6) abre a leitura: o `readData` do núcleo o baixa, espera 5 NOP, lê PC e o sobe. **CS3** (PH3) fica baixo o tempo todo; **T0** (PH0) fica alto. A troca de banco dos cartuchos de 12 e 16 KB (Videopac+) é uma escrita do número do banco (invertido) no endereço `$80` com **/CS1** (PH4) e **/WR** (PH5) baixos (`bankSwitch` do núcleo). `PH1` e `TIME` (PJ0) ficam altos e **não chegam ao cartucho**; PA e PL ficam sem ligação. O cartucho é de 5 V (`setVoltage(k5V)`; o slot SNES é 5 V fixo em todas as placas, sem regulador no adaptador). O adaptador não foi desenhado: falta o PCB (conector de 30 posições em duas fileiras de 15, 3,96 mm segundo o quadro do núcleo, "30P 3.96mm pitch connector").

### Fonte (conferida)

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

### Pontos a conferir com o cartucho na mão

- **P10 e P11 (dedução, não está no quadro):** o quadro não diz onde P10 e P11 entram no slot SNES. O núcleo lê os cartuchos de 4 e 8 KB em janelas de 2 KB em `$0400`, `$1400`, `$2400` e `$3400`, isto é, mudando os bits 12 e 13 do endereço (PK4 e PK5), que não aparecem em nenhum outro pino do quadro; no console, P10 e P11 são justamente os bits da porta 1 do 8048 que trocam o banco de 2 KB desses cartuchos. Daí P10 = A12 (PK4, pino 37 do slot) e P11 = A13 (PK5, pino 38). **Confirmar com o adaptador do OSCR ou com um cartucho de 8 KB** (com a ordem trocada, o dump de 8 KB sai com as duas janelas do meio trocadas e o CRC32 não confere no No-Intro).
- **A10 (pino 10):** a maioria dos cartuchos não o liga (nota do quadro); só o Videopac 31 (Musician) e o 40 (4 in 1 Row) o usam, e é para eles o `--mapper 1`, que lê 4 KB contínuos de `$0000`.
- **T0 (pino 1):** o núcleo o conduz em nível alto o tempo todo. Se algum cartucho usar T0 como saída, um resistor em série (1 kΩ) no adaptador evita a disputa.
- **Passo e chaveamento:** o quadro diz 3,96 mm em duas fileiras de 15; medir no cartucho antes de escolher o conector (conector de borda para placa de 3,96 mm, como o de cartuchos de Famicom antigos).
- A sondagem do firmware (32 bytes de `$0400`) só separa slot vazio de cartucho; o fork não confere assinatura nem cabeçalho. O PC sempre informa o tamanho (`--prg 2|4|8|12|16`).

<a id="adaptador-pokemini"></a>

## Adaptador do Pokémon Mini para o slot SNES (F-20, D227)

O núcleo `PokemonMini.cpp` do OSCR usa o barramento do slot SNES só para leitura. O cartucho tem o endereço **multiplexado e travado no próprio cartucho**: o `readData` do núcleo põe A10 a A17 em PF e A18 a A20 em PK0 a PK2 e dá um pulso em **HALE** (PH0); depois põe A0 a A7 em PF e A8 e A9 em PK0 e PK1 e sobe **LALE** (PH4). Com LALE alto, sobe **OE** (PH6), espera 5 NOP, lê D0 a D7 em PC e desce OE e LALE. **CS** (PH3) fica alto o tempo todo (os sinais de controle do cartucho são ativos em nível alto); **WE** (PH5) fica baixo. `PH1`, `TIME` (PJ0), PA e PL vão a nível alto e **não chegam ao cartucho**. A leitura tem sempre 512 KB (o núcleo: "ALL ROMS ARE 512K"). O adaptador não foi desenhado: falta o PCB.

### Tensão: 3,3 V (mesmo problema do Neo Geo Pocket e do Supervision, D203 e D218)

O núcleo pede 3,3 V (`setVoltage(k3V3)`) e o quadro do cartucho rotula os três VCC como "VCC (3.3V)". O VCC do slot SNES é **5 V fixo em todas as placas**: ligar os VCC do cartucho direto a ele pode estragar o cartucho. O adaptador precisa do próprio regulador de 3,3 V (LDO THT, por exemplo MCP1700 ou LD1117V33, mais capacitores), alimentado pelo 5 V do slot (27 e 58) e ligado aos pinos B1, A1 e A7 do conector. Os sinais do Mega são de 5 V em qualquer caso (D140), como anotado para o Neo Geo Pocket.

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 32P 0.5mm pitch" no começo de `firmware/oscr/src/cores/PokemonMini.cpp` (fileira de cima B1 a B17, de baixo A1 a A15), com a lista CONTROL PINS (HALE no RESET, CS no /CS, LALE no /IRQ, WE no /WR e OE no /RD do slot SNES). O comentário do `cartOn` do núcleo troca os nomes (`LALE(PH0)`, `HALE(PH4)`), mas os `#define` e a lista CONTROL PINS dizem HALE = PH0 e LALE = PH4, e é isso que o código faz. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_pokemini.py` confere o quadro, a lista CONTROL PINS, o pinmap e as portas que o `readData` usa.

Nos rótulos `A0/A10` a `A9/A19`, o primeiro nome é o bit que vai na fase de LALE e o segundo o da fase de HALE; o A20 só existe na fase de HALE e vai no A10 do slot (PK2), como diz o núcleo.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (32P) |
|---|---|---|---|
| A0/A10 | 17 | PF0 | B7 |
| A1/A11 | 16 | PF1 | A6 |
| A2/A12 | 15 | PF2 | B6 |
| A3/A13 | 14 | PF3 | A5 |
| A4/A14 | 13 | PF4 | B5 |
| A5/A15 | 12 | PF5 | A4 |
| A6/A16 | 11 | PF6 | B4 |
| A7/A17 | 10 | PF7 | A3 |
| A8/A18 | 9 | PK0 | B3 |
| A9/A19 | 8 | PK1 | A2 |
| A20 | 7 | PK2 | B2 |
| D0 | 19 | PC0 | B10 |
| D1 | 20 | PC1 | A9 |
| D2 | 21 | PC2 | B11 |
| D3 | 22 | PC3 | A10 |
| D4 | 50 | PC4 | B12 |
| D5 | 51 | PC5 | A11 |
| D6 | 52 | PC6 | B13 |
| D7 | 53 | PC7 | A12 |
| HALE | 26 | PH0 | B8 |
| CS | 49 | PH3 | A14 |
| LALE | 18 | PH4 | B9 |
| WE | 54 | PH5 | B15 |
| OE | 23 | PH6 | B14 |

Pinos fixos do conector: VCC no B1, no A1 e no A7 (3,3 V do LDO do adaptador, ver acima); GND no A8, no A15 e no B17 (slot 5 e 36). Sem ligação: IRQ (A13) e CARD_N (B16), que o núcleo não usa.

### Pontos a conferir com o cartucho na mão

- **Conector:** o quadro diz "32P 0.5mm pitch" para o cartucho e "33P 1.0mm pitch" para o conector SMD do console; medir a borda do cartucho antes de escolher a peça. A borda tem a fileira de cima e a de baixo deslocadas (o "--" entre A7 e A8 no quadro).
- **CARD_N (B16):** pelo nome, é a detecção de cartucho do console; o núcleo não o lê. Deixar sem ligação até medir no cartucho.
- **Sinais ativos em nível alto:** CS, OE e WE do cartucho são o contrário do slot SNES (/CS, /RD, /WR). O núcleo já os conduz assim; o adaptador liga direto, sem inversor.
- A sondagem do firmware (32 bytes de `$2100`, o primeiro endereço que o console lê do cartucho) só separa slot vazio de cartucho; o fork não confere assinatura. O save do Pokémon Mini fica no console, não no cartucho.

<a id="adaptador-vsmile"></a>

## Adaptador do V.Smile para o slot SNES (F-20, D228)

O núcleo `VSmile.cpp` do OSCR usa o barramento do slot SNES só para leitura, em palavras de 16 bits. O `read_rom_word` do núcleo põe o endereço de palavra em PF (A1 a A8), PK (A9 a A16) e PL0 a PL5 (A17 a A22), espera 1 µs, sobe **CSB2** (PH4), desce **CSB1** (PH6) e **OE** (PH3), lê D0 a D7 em PC e D8 a D15 em PA e sobe OE e CSB1. O segundo chip dos cartuchos de 6 MB é lido com CSB2 baixo e CSB1 alto (`read_rom2_word`); o segundo chip dos V.Motion de 16 MB, com CSB1 e CSB2 baixos (`read_rom3_word`). Os sinais de controle são ativos em nível baixo. O `cartOn` põe PH3, PH4 e PH6 como saída e os outros bits de PH como entrada com pull-up; PL6 e PL7 também ficam como entrada. O tamanho vem sempre do PC: 4, 6, 8 ou 16 MB (tabela `romSizes` do núcleo). O adaptador não foi desenhado: falta o PCB.

### Tensão: 3,3 V (mesmo problema do Neo Geo Pocket, do Supervision e do Pokémon Mini, D203, D218 e D227)

O núcleo pede 3,3 V (`setVoltage(k3V3)`). O VCC do slot SNES é **5 V fixo em todas as placas**: ligar os VCC do cartucho direto a ele pode estragar o cartucho. O adaptador precisa do próprio regulador de 3,3 V (LDO THT, por exemplo MCP1700 ou LD1117V33, mais capacitores), alimentado pelo 5 V do slot (27 e 58) e ligado aos pinos 24, 25 e 27 do conector. Os sinais do Mega são de 5 V em qualquer caso (D140), como anotado para o Neo Geo Pocket.

### Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge pinout, 48P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/VSmile.cpp` (pinos 25 a 48 do lado da frente, 1 a 24 do lado de trás), com a lista de portas logo abaixo (D0-D7 em PORTC, D8-D15 em PORTA, A1-A8 em PORTF, A9-A16 em PORTK, A17-A22 em PORTL). As portas de controle vêm dos `#define` de `firmware/oscr/include/cores/VSmile.h` (OE no /CART, CSB1 no /RD e CSB2 no /IRQ do slot SNES). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES); D8 a D15 usam os pinos PA0 a PA7 do slot SNES (28, 59, 29, 60, 30, 61, 3 e 34). `python3 tools/check_adaptador_vsmile.py` confere o quadro, os `#define`, o pinmap e as portas que o núcleo usa.

O cartucho não tem A0: o endereço é de palavra. O `read_rom_word` monta a palavra com PC no byte alto (`(PINC << 8) | PINA`), e o `readROM` grava o byte alto primeiro; no arquivo, os bytes pares vêm de D0 a D7 e os ímpares de D8 a D15.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (48P) |
|---|---|---|---|
| A1 | 17 | PF0 | 12 |
| A2 | 16 | PF1 | 13 |
| A3 | 15 | PF2 | 38 |
| A4 | 14 | PF3 | 14 |
| A5 | 13 | PF4 | 39 |
| A6 | 12 | PF5 | 15 |
| A7 | 11 | PF6 | 40 |
| A8 | 10 | PF7 | 16 |
| A9 | 9 | PK0 | 42 |
| A10 | 8 | PK1 | 18 |
| A11 | 7 | PK2 | 43 |
| A12 | 6 | PK3 | 19 |
| A13 | 37 | PK4 | 44 |
| A14 | 38 | PK5 | 20 |
| A15 | 39 | PK6 | 45 |
| A16 | 40 | PK7 | 21 |
| A17 | 41 | PL0 | 37 |
| A18 | 42 | PL1 | 41 |
| A19 | 43 | PL2 | 17 |
| A20 | 44 | PL3 | 46 |
| A21 | 45 | PL4 | 22 |
| A22 | 46 | PL5 | 47 |
| D0 | 19 | PC0 | 31 |
| D1 | 20 | PC1 | 30 |
| D2 | 21 | PC2 | 29 |
| D3 | 22 | PC3 | 4 |
| D4 | 50 | PC4 | 5 |
| D5 | 51 | PC5 | 6 |
| D6 | 52 | PC6 | 7 |
| D7 | 53 | PC7 | 32 |
| D8 | 28 | PA0 | 35 |
| D9 | 59 | PA1 | 34 |
| D10 | 29 | PA2 | 33 |
| D11 | 60 | PA3 | 8 |
| D12 | 30 | PA4 | 9 |
| D13 | 61 | PA5 | 10 |
| D14 | 3 | PA6 | 36 |
| D15 | 34 | PA7 | 11 |
| OE | 49 | PH3 | 2 |
| CSB1 | 23 | PH6 | 48 |
| CSB2 | 18 | PH4 | 28 |

Pinos fixos do conector: VCC no 24, no 25 e no 27 (3,3 V do LDO do adaptador, ver acima); GND no 3 e no 23 (slot 5 e 36).

**PENDENTE: WE (1) e RAMCS (26).** O núcleo não conduz nenhum dos dois e o quadro não diz o que fazer com eles. Pelo nome, são a escrita e a seleção da RAM do cartucho; deixados soltos, podem flutuar e ligar a RAM no barramento durante a leitura. Candidatos: WE no /WR do slot (54, PH5), que o `cartOn` deixa como entrada com pull-up (nível alto, inativo); RAMCS no VCC do adaptador por um resistor. Conferir com o cartucho na mão ou com o adaptador da comunidade antes de fechar o PCB.

### Pontos a conferir com o cartucho na mão

- **WE e RAMCS:** ver acima.
- **Conector:** o quadro diz 48 pinos a 2,54 mm, com uma divisão entre os pinos 14/38 e 15/39 (a linha `|---------|` no quadro); medir a borda do cartucho antes de escolher a peça.
- **Tamanho:** o cartucho não informa. Pela base do OSCR (`legacy/sd/vsmilecart.txt`), 67 de 74 jogos têm 8 MB; os de 6 MB (Alphabet Park Adventure, Care Bears) têm dois chips; os de 16 MB são do V.Motion (Cars 2, Shrek Forever After, Super WHY!, Toy Story 3).
- A sondagem do firmware (16 palavras do início do primeiro chip) só separa slot vazio de cartucho; o fork não confere assinatura. O V.Smile não tem save no cartucho.
