# Programador de PIC12F629 em shield para Arduino Uno

Grava o **PIC12F629** (o CIC "lock" do SNES SA-1, `snescic-lock-resync.hex`) com um Arduino Uno e o
[ardpicprog](https://rweather.github.io/ardpicprog/). Resolve o problema de quem não tem PICkit: o 12F629 só grava
com Vpp de uns 12 a 13 V no MCLR, e o CH341A não gera isso.

Este shield é o circuito do ardpicprog para o PIC12F629 em DIP-8 direto (a ligação já descrita em
[`../uno/README.md`](../uno/README.md), D91), desenhado em KiCad. Há três jeitos de montar o mesmo circuito, na ordem
de comodidade: **A.** PCB do shield (este projeto KiCad), **B.** protoboard, **C.** placa perfurada.

> **Estado (2026-11-06):** nada foi encomendado, montado nem gravado em PIC. Conferido só no PC: ERC do esquemático
> sem avisos, DRC da PCB sem violações e sem pontos soltos, netlist da PCB contra a tabela de ligações do ardpicprog
> (`scripts/check_netlist.py`), e os desenhos da protoboard e da placa perfurada (`scripts/protoboard.py`,
> `scripts/perfboard.py`). A pinagem do Uno é a do footprint do Mega no projeto, cotas oficiais do Arduino; não foi
> medida num Uno real. O limite máximo de Vpp do 12F629 (DS41191) **não foi conferido**: meça o MCLR antes de pôr o chip.

![Frente da placa](docs/placa-frente.png)

Esquemático: [`docs/esquematico.pdf`](docs/esquematico.pdf).

## Como funciona

```
13 V (+) ──► D1 1N5819 ──┬── R1 10 kΩ ──┬── PIC pino 4 (MCLR)
                         │              └── coletor do Q1 (BC547)
                         └── R4 1 kΩ ── LED vermelho ── GND      (acende = há 13 V)
Uno A1 ── R2 4,7 kΩ ── base do Q1        emissor do Q1 ── GND
Uno D2 ── PIC pino 1 (Vdd)               100 nF entre o pino 1 e o GND, junto ao chip
Uno D4 ── PIC pino 6 (clock)
Uno D7 ── PIC pino 7 (dados)
Uno A5 ── R3 220 Ω ── LED amarelo ── GND (atividade)
Uno GND ── PIC pino 8 ── GND da fonte de 13 V   (GND comum!)
PIC pinos 2, 3 e 5: sem ligação
```

- A1 em nível **baixo** corta o transistor e deixa o MCLR em ~13 V (gravação); em nível alto o transistor puxa o
  MCLR a GND (reset). O sketch aplica os 13 V **antes** de ligar o Vdd. Os pinos conferem com o `ProgramPIC.pde`
  do ardpicprog (`PIN_MCLR A1`, `PIN_VDD 2`, `PIN_CLOCK 4`, `PIN_DATA 7`, `PIN_ACTIVITY A5`), então o sketch roda sem
  alteração.
- Os 13 V nunca vão a um pino do Uno. O PIC é alimentado pelo pino D2 do Uno (consumo de poucos mA).
- **D1 é um acréscimo** deste projeto (o circuito original não tem): protege contra fonte ligada ao contrário e
  derruba uns 0,3 V. Se a sua fonte já está no limite baixo de Vpp, troque D1 por um fio.
- A placa também tem um cabeçalho ICSP (J2, ordem do PICkit: 1 MCLR, 2 Vdd, 3 GND, 4 dados, 5 clock) e três pontos de
  teste (MCLR, VDD, GND) para o multímetro.

## Material

| Qtd | Peça | Ref. na PCB | Observação |
|---|---|---|---|
| 1 | Arduino Uno R3 + cabo USB | | clone com CH340 serve (aparece como `/dev/ttyUSB0`) |
| 1 | Fonte de 13 V, ≥ 100 mA, **regulada** | | meça em vazio antes (veja "Antes de ligar") |
| 1 | PIC12F629-I/P (DIP-8) virgem ou a regravar | U2 | em soquete DIP-8 |
| 1 | Soquete DIP-8 | U2 | de contato torneado, para trocar de chip muitas vezes |
| 1 | Transistor NPN pequeno: BC547 ou BC548 (ou 2N3904, 2N2222) | Q1 | pinagem abaixo |
| 1 | Diodo 1N5819 | D1 | |
| 1 | Resistor 10 kΩ | R1 | 1/4 W |
| 1 | Resistor 4,7 kΩ | R2 | |
| 1 | Resistor 220 Ω | R3 | |
| 1 | Resistor 1 kΩ | R4 | |
| 1 | Capacitor cerâmico 100 nF | C1 | |
| 1 | LED vermelho 3 mm | D2 | indica os 13 V |
| 1 | LED amarelo 3 mm | D3 | atividade |
| 1 | Borne de parafuso 5,08 mm, 2 vias | J1 | entrada da fonte; para um plugue P4 use um adaptador "jack fêmea com borne" |
| 1 | Barra de 6 pinos 2,54 mm | J2 | ICSP, opcional |
| 3 | Ponto de teste (pino ou argola) | TP1 a TP3 | opcional |
| 4 | Barras fêmea empilháveis do Uno (6, 8, 8 e 10 pinos) | A1 | só na PCB do shield |

**Pinagem do transistor.** BC547 e BC548 (TO-92, lado chato para você, pernas para baixo): C, B, E da esquerda para a
direita. 2N3904 e 2N2222: E, B, C. Na PCB o footprint é C, B, E; um 2N3904 entra **virado 180°** (lado chato para o
lado oposto ao do desenho) e assim as pernas caem certas. Na dúvida, modo diodo do multímetro: a base mede cerca de
0,6 V para as outras duas pernas com o "+" na base (NPN).

## Antes de ligar (vale para as três montagens)

1. **Meça a fonte de 13 V com o multímetro, sem carga.** Adaptadores "13 V" sem regulagem passam de 15 V em vazio.
   Alvo: cerca de 13 V no MCLR com o chip fora. Confira o Vpp máximo do 12F629 no DS41191 antes de pôr o chip.
2. Confirme a polaridade do plugue (+ no centro ou na lateral).
3. Sem o PIC no soquete, ligue só a fonte: o LED vermelho acende. Meça o **MCLR** (TP1 na PCB; pino 4 do soquete):
   com o Uno em reset (A1 alto) fica perto de 0 V; com A1 solto, ~13 V.
4. Só então ponha o PIC (entalhe/pino 1 conforme o desenho) com tudo **desligado**; ligue a fonte por último e
   desligue-a primeiro.
5. Feche o monitor serial da IDE antes de usar o `ardpicprog` (ele roubaria a porta).

## A. PCB do shield (`hardware/`)

Placa de 2 camadas, 52,6 × 53,3 mm, 100% THT, que encaixa nos headers do Uno. O lado esquerdo (conector USB-B e jack
do Uno) fica livre de propósito.

- Projeto: `hardware/shield_uno.kicad_pro` (KiCad 9 ou 10). Fabricação: `fab/shield_uno-v1.0-jlcpcb.zip` (gerbers e
  furos, 2 camadas, 1,6 mm, HASL) e `fab/bom.csv`. **Nada foi encomendado.**
- Montagem, do mais baixo ao mais alto:
  1. resistores (R1 a R4), diodo D1 (faixa para o lado do K), capacitor C1;
  2. soquete DIP-8 (entalhe para o lado do pino 1, desenhado na serigrafia);
  3. LEDs (perna curta = K, lado do quadrado) e transistor;
  4. cabeçalho ICSP, pontos de teste e borne;
  5. por último as barras empilháveis, **com o shield encaixado no Uno** para alinhar.
- **Corte as pernas rente** na face de baixo: o Uno tem o ATmega328P e outras peças ali embaixo. Se sobrar perna,
  cubra com fita isolante.
- O borne J1 fica no canto de baixo à esquerda: `+` do lado da borda esquerda, `GND` ao lado.
- Para refazer os arquivos a partir dos scripts: veja "Arquivos".

## B. Protoboard (830 pontos)

Os 13 V e o GND vêm dos trilhos; o Uno liga por 6 fios. Convenção: colunas **a–e** são uma tira por linha e **f–j** a
outra (o vão central separa as duas metades). O trilho **"+" é o de 13 V já depois do diodo D1** e o **"−" é o GND**.

```
                 vão central
          a b c d e │ f g h i j
linha 10  ● ● ● ● ● │ ● ● ● ● ●     pino 1 (e10) ................ pino 8 (f10)
linha 11            │              pino 2 (e11) ................ pino 7 (f11)
linha 12            │              pino 3 (e12) ................ pino 6 (f12)
linha 13            │              pino 4 (e13) ................ pino 5 (f13)
                       entalhe do PIC para cima (lado da linha 9)
```

Passo a passo (sempre com tudo desligado):

1. **Trilhos.** Jumper do **GND do Uno** ao trilho "−"; fio do **negativo da fonte** ao mesmo trilho.
2. **PIC.** Soquete (ou o próprio PIC, se for só testar) a cavaleiro do vão, **pino 1 em e10**, pino 4 em e13, pino 8
   em f10, pino 5 em f13.
3. **Alimentação do chip.** Jumper a10 → **Uno D2**. Capacitor de 100 nF entre b10 e o trilho "−". Jumper j10 → trilho
   "−" (pino 8).
4. **Dados e clock.** Jumper j11 → **Uno D7**; jumper j12 → **Uno D4**.
5. **Transistor Q1** na coluna a: **coletor em a13, base em a14, emissor em a15**. Quem manda é a perna, não o lado do
   corpo: BC547 e BC548 olhando o lado chato são C, B, E; 2N3904 e 2N2222 são E, B, C (confira na pinagem acima).
   Jumper b15 → trilho "−" (emissor a GND).
6. **MCLR.** A tira da linha 13 (a13 coletor, e13 pino 4) é o nó MCLR. **R1 10 kΩ** de c13 até c17; jumper d17 → trilho
   "+".
7. **Base.** **R2 4,7 kΩ** de b14 até b18; jumper a18 → **Uno A1**.
8. **Diodo e entrada de 13 V.** **D1** com o anodo em a25 e o catodo (faixa) em a29; jumper b25 → **positivo da
   fonte**; jumper b29 → trilho "+". (A linha 25 é a entrada da fonte; o trilho "+" fica com 13 V menos a queda do diodo.)
9. **LED de 13 V.** **R4 1 kΩ** de a17 até a21; **LED vermelho** com o anodo (perna longa) em b21 e o catodo (curta) em b22;
   jumper c22 → trilho "−".
10. **LED de atividade.** **R3 220 Ω** de g18 até g22; **LED amarelo** com o anodo em h22 e o catodo em h23; jumper i23 →
    trilho "−"; jumper j18 → **Uno A5**.
11. Confira com o multímetro (continuidade, tudo desligado): trilho "+" × trilho "−" **sem** continuidade; pino 8 do PIC
    com o GND do Uno; a tira da linha 13 com o pino 4.
12. Siga "Antes de ligar" (medir o MCLR com o chip fora) e depois "Gravar".

| Jumper / peça | De | Para |
|---|---|---|
| Uno D2 | a10 (pino 1, Vdd) | |
| Uno D7 | j11 (pino 7, dados) | |
| Uno D4 | j12 (pino 6, clock) | |
| Uno A1 | a18 (R2) | |
| Uno A5 | j18 (R3) | |
| Uno GND | trilho "−" | |
| GND do chip | j10 | trilho "−" |
| Emissor | b15 | trilho "−" |
| Retorno do LED vermelho | c22 | trilho "−" |
| Retorno do LED amarelo | i23 | trilho "−" |
| 13 V depois do diodo | d17 e b29 | trilho "+" |
| Positivo da fonte | b25 | |
| Negativo da fonte | trilho "−" | |

`scripts/protoboard.py` confere essa tabela contra as ligações do circuito. Protoboard tem contato fraco e capacitância
alta; para gravar um PIC serve, mas se der erro de verificação, mexa nos jumpers antes de suspeitar do chip.

## C. Placa perfurada

Placa de furos a 2,54 mm de **22 colunas × 14 linhas** (uma de 5 × 7 cm serve), com um **cabo Dupont fêmea-fêmea de 6
vias** do barramento J3 ao Uno. Fios **isolados** (kynar/wire-wrap) no lado da solda; só o trilho de GND (linha N) pode
ser fio nu. Os furos têm nome: letra da linha (A a N) e número da coluna (1 a 22).

![Placa perfurada](docs/perfboard.png)

- Desenho gerado por `scripts/perfboard.py`, que **verifica** que cada fio liga exatamente os pontos certos e que não
  há curto. Tabelas completas de furos e fios: [`docs/perfboard.md`](docs/perfboard.md).
- A figura mostra o lado dos componentes visto de cima, com os fios do lado de baixo vistos por transparência.

Ordem de montagem:

1. Soldar o **soquete DIP-8** (colunas 13 e 16, linhas D a G; entalhe para cima = pino 1 em D13), os resistores, o
   diodo, o capacitor, os LEDs, o transistor, o borne J1 e a barra J3 (A5 a A10, de cima: GND, D2, D4, D7, A1, A5),
   nos furos da tabela [`docs/perfboard.md`](docs/perfboard.md).
2. Passar os fios **na ordem da tabela de fios**, um a um, soldando as pontas e riscando na tabela. Os fios podem
   passar por cima de furos ocupados desde que sejam isolados; o trilho de GND (N5 a N21) é um fio nu soldado nos pontos
   marcados.
3. Conferir com o multímetro, tudo desligado: GND (J3 GND) com o pino 8 do soquete, o emissor do transistor e os dois
   catodos; 13 V (depois do diodo) **sem** continuidade com o GND.
4. Ligar o cabo Dupont: J3 GND, D2, D4, D7, A1, A5 aos mesmos pinos do Uno (nesta ordem na barra, da esquerda para a
   direita). Siga "Antes de ligar" e "Gravar".

Os pontos de teste e o ICSP ficam de fora nesta versão (o MCLR se mede no pino 4 do soquete).

## Gravar

O Uno precisa do sketch `ProgramPIC` do ardpicprog, e o PC do programa `ardpicprog`. Instalação e comandos estão em
[`../uno/README.md`](../uno/README.md) (compilar com `tools/pic/uno/instalar_ardpicprog.sh`, subir o sketch com
`arduino-cli`). Resumo, com o shield montado e o PIC no soquete:

```
A="tools/pic/bin/ardpicprog -p /dev/ttyUSB0"      # ttyACM0 num Uno original
$A --list-devices                                  # teste da comunicação
$A -o backup-virgem.hex --skip-ones                # lê o chip antes (guarda o OSCCAL)
$A --erase --burn -i firmware/cic_rp2040/third_party/snescic-lock-resync.hex -o lido.hex --skip-ones
python3 -I tools/pic/comparar_hex.py firmware/cic_rp2040/third_party/snescic-lock-resync.hex lido.hex
```

## Problemas

- **LED vermelho apagado:** fonte desligada, invertida (D1 bloqueia), ou R4/LED ao contrário.
- **Não detecta o chip:** confira o pino 1 do PIC, o GND comum entre fonte e Uno e se há ~13 V no pino 4 com A1 solto.
- **13 V não chegam ao MCLR:** transistor com a pinagem errada (veja "Pinagem do transistor") ou R1 solto.
- **Erro de verificação:** grave de novo; se repetir, queda da fonte sob carga ou mau contato (na protoboard).
- **Nada na serial:** feche o monitor serial; confira a porta e o grupo `dialout`.

## Arquivos

| Caminho | O que é |
|---|---|
| `hardware/` | projeto KiCad (`shield_uno.kicad_pro/_sch/_pcb`), símbolo e footprint do Uno (`uno_shield.*`) |
| `fab/` | gerbers, furos, `bom.csv` e o zip da JLCPCB |
| `docs/` | esquemático em PDF, imagem da placa, desenho e tabelas da placa perfurada |
| `scripts/gerar_sch.py` | gera o esquemático e o símbolo do Uno |
| `scripts/gerar_pcb.py`, `scripts/rotear.py` | geram a PCB (footprints, nets, contorno) e roteiam com o Freerouting, depois zonas de GND |
| `scripts/check_netlist.py` | confere a PCB contra a tabela do ardpicprog (usa `pcbnew`) |
| `scripts/exportar_fab.sh` | gerbers, furos, BOM e zip |
| `scripts/perfboard.py`, `scripts/protoboard.py` | desenho e verificação das montagens B e C |

Para refazer: `python3 scripts/gerar_sch.py`, depois, com o Python do venv do KiCad MCP (tem `pcbnew`),
`gerar_pcb.py`, `rotear.py` (precisa de `java` e `~/.kicad-mcp/freerouting.jar`) e `check_netlist.py`;
`kicad-cli sch erc` e `kicad-cli pcb drc --schematic-parity` conferem os arquivos.

## Licença e créditos

O circuito é do **ardpicprog**, de Rhys Weatherley (circuitos e documentação **CC BY-SA 2.5**,
https://rweather.github.io/ardpicprog/). Este shield é derivado dele e fica sob **CC BY-SA 2.5**. O firmware do Uno
(`ProgramPIC.pde`) e o programa do PC são GPL v3 e não estão neste repositório (o instalador baixa do upstream).
