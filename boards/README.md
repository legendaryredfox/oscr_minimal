# boards/ — variantes de hardware

Cada pasta é uma versão mínima de hardware do OSCR, em shield para Arduino Mega 2560 R3, só USB (sem LCD, SD e RTC). Firmware, `host/` e `gui/` (raiz) são comuns; o que muda entre as placas são os slots e a pinagem.

| Pasta | Slots | Estado |
|---|---|---|
| [`16_bits/`](16_bits/) | SNES, Mega Drive | Projeto KiCad derivado da `16_and_8_bits`, 108 × 86 mm. Gerbers v. 1.2 gerados (D87: `/CART` no D50, C5 e C6, pontos de teste). Nada encomendado |
| [`megadrive/`](megadrive/) | Mega Drive | Projeto KiCad criado de `16_bits` (D92), slot no centro, 107 × 65 mm, gerbers v1.0 gerados. Nada encomendado |
| [`snes/`](snes/) | SNES | Projeto KiCad criado de `16_bits` (D93), PIC12F629 em soquete, 107 × 65 mm, gerbers v1.0 gerados. Nada encomendado |
| [`nes/`](nes/) | NES | Projeto KiCad criado da `16_and_8_bits` (D95), Si5351 sem PIC, 110 × 65 mm, gerbers v1.0 gerados. Famicom fora. Nada encomendado |
| [`famicom/`](famicom/) | Famicom | Projeto KiCad criado da `16_and_8_bits` (D98), sem Si5351 nem PIC, 107 × 65 mm, gerbers v1.0 gerados. Nada encomendado |
| [`famicom_nes/`](famicom_nes/) | Famicom e NES | Projeto KiCad criado da `16_and_8_bits` (D100), Si5351 sem PIC, 112 × 79 mm, gerbers v1.0 gerados. Nada encomendado |
| [`16_and_8_bits/`](16_and_8_bits/) | SNES, NES, Famicom, Mega Drive, GBA | Projeto KiCad pronto, gerbers v1.0 gerados. Nada encomendado |
| [`8_bits/`](8_bits/) | NES, Famicom, Master System | Esqueleto. Pinagem do Master System ainda não levantada |
| [`gb_gba/`](gb_gba/) | GBA; GB e GBC por adaptador | Projeto KiCad criado de `16_and_8_bits` (D94), 138 × 67 mm, gerbers v1.0 gerados. Nada encomendado |
| [`completa/`](completa/) | Todos os slots do OSCR | Esqueleto |
| [`_lib/`](_lib/) | Símbolos e footprints compartilhados | Em uso por `16_bits/` e `16_and_8_bits/` |

## Layout de cada variante

```
boards/<variante>/
├── README.md        # slots, estado, decisões próprias
├── hardware/        # projeto KiCad (<nome>.kicad_pro/_sch/_pcb, fp-lib-table, sym-lib-table)
├── fab/             # gerbers, drill, bom.csv e zip da fábrica
└── docs/            # pinmap.md, bom.md, montagem.md da variante
```

As tabelas de bibliotecas apontam para `${KIPRJMOD}/../../_lib/`. Pinagem idêntica ao OSCR HW5 continua regra de ouro (`CLAUDE.md`, seção 3). Uma variante nova nasce copiando o esqueleto e gerando o próprio `docs/pinmap.md`; `tools/check_netlist.py` aceita `--board <pasta>`; os outros scripts de `tools/` apontam para `16_and_8_bits/`.
