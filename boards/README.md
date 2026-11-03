# boards/ — variantes de hardware

Cada pasta é uma versão mínima de hardware do OSCR, em shield para Arduino Mega 2560 R3, só USB (sem LCD, SD e RTC). Firmware, `host/` e `gui/` (raiz) são comuns; o que muda entre as placas são os slots e a pinagem.

| Pasta | Slots | Estado |
|---|---|---|
| [`16_bits/`](16_bits/) | SNES, NES, Famicom, Mega Drive, GBA | Projeto KiCad pronto, gerbers v1.0 gerados. Nada encomendado |
| [`8_bits/`](8_bits/) | NES, Famicom, Master System | Esqueleto. Pinagem do Master System ainda não levantada |
| [`gb_gba/`](gb_gba/) | GB, GBC, GBA | Esqueleto |
| [`completa/`](completa/) | Todos os slots do OSCR | Esqueleto |
| [`_lib/`](_lib/) | Símbolos e footprints compartilhados | Em uso por `16_bits/` |

## Layout de cada variante

```
boards/<variante>/
├── README.md        # slots, estado, decisões próprias
├── hardware/        # projeto KiCad (<nome>.kicad_pro/_sch/_pcb, fp-lib-table, sym-lib-table)
├── fab/             # gerbers, drill, bom.csv e zip da fábrica
└── docs/            # pinmap.md, bom.md, montagem.md da variante
```

As tabelas de bibliotecas apontam para `${KIPRJMOD}/../../_lib/`. Pinagem idêntica ao OSCR HW5 continua regra de ouro (`CLAUDE.md`, seção 3). Uma variante nova nasce copiando o esqueleto e gerando o próprio `docs/pinmap.md`; os scripts de `tools/` hoje apontam para `16_bits/`.
