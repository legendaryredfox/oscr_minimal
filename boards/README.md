# boards/ — variantes de hardware

Cada pasta é uma versão mínima de hardware do OSCR, em shield para Arduino Mega 2560 R3, só USB (sem LCD, SD e RTC). Firmware, `host/` e `gui/` (raiz) são comuns; o que muda entre as placas são os slots e a pinagem.

| Pasta | Slots | Estado |
|---|---|---|
| [`16_bits/`](16_bits/) | SNES, Mega Drive | Projeto KiCad derivado da `16_and_8_bits`, 108 × 86 mm. **Versões v1.0, v1.2 (sem TVS) e v1.3 (TVS, seletor de tensão e resistores em série), D128 e D139.** Gerbers v. 1.2 (D87: `/CART` no D50, C5 e C6, pontos de teste a 2,54 mm, D99) e v1.0 (a antiga `rev2`: alimentação em 0,8 mm, D97; o zip da v1.0 original, com trilhas de 0,3 mm, saiu do repositório em D110) |
| [`megadrive/`](megadrive/) | Mega Drive | Projeto KiCad criado de `16_bits` (D92), slot no centro, 107 × 65 mm, gerbers v1.1 gerados. **v1.1 com o seletor de tensão 3,3 V/5 V (D138).** Nada encomendado |
| [`snes/`](snes/) | SNES | Projeto KiCad criado de `16_bits` (D93), PIC12F629 em soquete, 107 × 65 mm, só a v1.0 (o SA-1 precisa de 5 V: sem seletor). Nada encomendado |
| [`nes/`](nes/) | NES | Projeto KiCad criado da `16_and_8_bits` (D95), Si5351 sem PIC, 110 × 65 mm, gerbers v1.1 gerados. Famicom em `famicom/` ou `famicom_nes/`. **v1.1 com o seletor de tensão 3,3 V/5 V (D138).** Nada encomendado |
| [`famicom/`](famicom/) | Famicom | Projeto KiCad criado da `16_and_8_bits` (D98), sem Si5351 nem PIC, 107 × 65 mm, gerbers v1.1 gerados. **v1.1 com o seletor de tensão 3,3 V/5 V (D138).** Nada encomendado |
| [`famicom_nes/`](famicom_nes/) | Famicom e NES | Projeto KiCad criado da `16_and_8_bits` (D100), Si5351 sem PIC, 117 × 79 mm (D124), gerbers v1.1 gerados. **v1.1 com o seletor de tensão 3,3 V/5 V (D138).** Nada encomendado |
| [`16_and_8_bits/`](16_and_8_bits/) | SNES, NES, Famicom, Mega Drive, GBA | Projeto KiCad pronto, só a v1.0 (o seletor de tensão da D138 ainda não foi roteado nesta placa). Nada encomendado |
| [`megadrive_sms/`](megadrive_sms/) | Mega Drive, Master System | Projeto KiCad criado da `megadrive` v1.0 (D136), 107,1 × 83,1 mm, **v1.0 sem o bloco de troca**, gerbers v1.0 gerados. Nada encomendado. Pendências: direção da etiqueta do SMS, núcleo SMS no firmware |
| [`8_bits/`](8_bits/) | NES, Famicom, Master System | Esqueleto. Pinagem do Master System ainda não levantada |
| [`gb_gba/`](gb_gba/) | GBA; GB e GBC por adaptador | Projeto KiCad criado de `16_and_8_bits` (D94), 138 × 67 mm, gerbers v1.0 gerados. Nada encomendado |
| [`n64/`](n64/) | N64 | Projeto KiCad criado da `16_and_8_bits` (D121), 3,3 V, Si5351 só para a EEPROM, 110,1 × 65,1 mm, só a v1.0 (placa de 3,3 V: sem seletor). Nada encomendado |
| [`completa/`](completa/) | Todos os slots do OSCR | Esqueleto |
| [`_lib/`](_lib/) | Símbolos e footprints compartilhados | Em uso por todas as placas com projeto KiCad |

Cada placa com projeto tem um `render.png` (render 3D do KiCad, vista de cima, da versão mais nova) e, **dentro da pasta de cada versão** (`hardware-v1.0/` etc.), `render-cima.png` e `render-baixo.png` (1768 × 1064, print do render 3D do KiCad) ao lado do `README.md` da versão; refazer com `tools/render_board.sh <placa> <versões...>` e `docs/componentes-opcionais.md`: peças que podem ficar sem montar, o que deixa de funcionar e quais cartuchos são afetados.

## Troca de cartucho, F1 e seletor de tensão (D138, D139)

O 5V dos slots **não é cortado por software** em nenhuma placa: o bloco de troca de cartucho (Q1, Q2, Q3, LEDs verde e amarelo, D19 e D53; D126 a D128) foi retirado em D139. Para trocar o cartucho, **desligue o USB**. Ficaram o F1 (suporte de fusível 5×20 mm de 500 mA, em todas as versões), e nas v1.1 com slot de 5 V o seletor 3,3 V/5 V, o jumper J1 "TRAVA 3,3 V" e os resistores de 470 Ω em série. Circuito e peças: [`docs/referencia/seletor-tensao.md`](../docs/referencia/seletor-tensao.md).

## Como os esquemáticos são desenhados

Para leitura humana (D122): os circuitos locais (LED, resistores, capacitores, Si5351, PIC, regulador, pull-ups) têm **fios diretos** entre os pinos; a alimentação usa **símbolos** `+5V`, `+3V3`, `+5V_CART` e `GND`; **rótulos de net só nos barramentos longos** entre o Mega e os slots. As folhas são geradas por `tools/sch/regen.py` (preserva peças, referências e UUIDs, só refaz o desenho); `tools/sch/verify.py` confere que a conectividade ficou idêntica e `tools/sch/sync_names.py` alinha os nomes de net do PCB (a geometria não muda).

## Layout de cada variante

```
boards/<variante>/
├── README.md        # slots, estado, decisões próprias
├── hardware-v1.0/   # uma pasta por versão (hardware-v1.1/ ...): projeto KiCad (dumper.kicad_pro/_sch/_pcb, fp-lib-table, sym-lib-table) e README.md da versão
├── fab/             # por versão: gerbers-<versão>/, bom-<versão>.csv e dumper-<versão>-jlcpcb.zip
└── docs/            # pinmap.md, bom.md, montagem.md da variante
```

As tabelas de bibliotecas apontam para `${KIPRJMOD}/../../_lib/`. Pinagem idêntica ao OSCR HW5 continua regra de ouro (`CLAUDE.md`, seção 3). Uma variante nova nasce copiando o esqueleto e gerando o próprio `docs/pinmap.md`; `tools/check_netlist.py` aceita `--board <pasta>` e `tools/export_fab.sh <pasta> <versão>` gera os arquivos da fábrica; `gen_pinmap.py` e os demais scripts gerais de `tools/` apontam para `16_and_8_bits/`. As placas de um sistema só têm scripts próprios em `tools/<placa>/` (receita completa em `boards/nes/README.md` e na D96).

Todas as placas novas (`megadrive`, `snes`, `nes`, `famicom`, `famicom_nes`, `gb_gba`, `n64`) e as v1.1 foram roteadas por autoroteador (na v1.1, o roteamento inteiro foi refeito) e **não foram revisadas à mão no KiCad**; nenhuma foi encomendada, montada ou testada com cartucho.
