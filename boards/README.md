# boards/ — variantes de hardware

Cada pasta é uma versão mínima de hardware do OSCR, em shield para Arduino Mega 2560 R3, só USB (sem LCD, SD e RTC). Firmware, `host/` e `gui/` (raiz) são comuns; o que muda entre as placas são os slots e a pinagem.

| Pasta | Slots | Estado |
|---|---|---|
| [`16_bits/`](16_bits/) | SNES, Mega Drive | Projeto KiCad derivado da `16_and_8_bits`, 108 × 86 mm. Gerbers v. 1.2 (D87: `/CART` no D50, C5 e C6, pontos de teste a 2,54 mm, D99) e v1.0 (a antiga `rev2`: alimentação em 0,8 mm, D97; o zip da v1.0 original, com trilhas de 0,3 mm, saiu do repositório em D110) |
| [`megadrive/`](megadrive/) | Mega Drive | Projeto KiCad criado de `16_bits` (D92), slot no centro, 107 × 65 mm, gerbers v1.0 gerados. Nada encomendado |
| [`snes/`](snes/) | SNES | Projeto KiCad criado de `16_bits` (D93), PIC12F629 em soquete, 107 × 65 mm, gerbers v1.0 gerados. Nada encomendado |
| [`nes/`](nes/) | NES | Projeto KiCad criado da `16_and_8_bits` (D95), Si5351 sem PIC, 110 × 65 mm, gerbers v1.0 gerados. Famicom em `famicom/` ou `famicom_nes/`. Nada encomendado |
| [`famicom/`](famicom/) | Famicom | Projeto KiCad criado da `16_and_8_bits` (D98), sem Si5351 nem PIC, 107 × 65 mm, gerbers v1.0 gerados. Nada encomendado |
| [`famicom_nes/`](famicom_nes/) | Famicom e NES | Projeto KiCad criado da `16_and_8_bits` (D100), Si5351 sem PIC, 112 × 79 mm, gerbers v1.0 gerados. Nada encomendado |
| [`16_and_8_bits/`](16_and_8_bits/) | SNES, NES, Famicom, Mega Drive, GBA | Projeto KiCad pronto, gerbers v1.0 gerados. Nada encomendado |
| [`8_bits/`](8_bits/) | NES, Famicom, Master System | Esqueleto. Pinagem do Master System ainda não levantada |
| [`gb_gba/`](gb_gba/) | GBA; GB e GBC por adaptador | Projeto KiCad criado de `16_and_8_bits` (D94), 138 × 67 mm, gerbers v1.0 gerados. Nada encomendado |
| [`n64/`](n64/) | N64 | Projeto KiCad criado da `16_and_8_bits` (D121), 3,3 V, Si5351 só para a EEPROM, 110,1 × 65,1 mm, gerbers v1.0 gerados. Nada encomendado |
| [`completa/`](completa/) | Todos os slots do OSCR | Esqueleto |
| [`_lib/`](_lib/) | Símbolos e footprints compartilhados | Em uso por todas as placas com projeto KiCad |

Cada placa com projeto tem um `render.png` (render 3D do KiCad, vista de cima; refazer com `kicad-cli pcb render` quando o layout mudar) e `docs/componentes-opcionais.md`: peças que podem ficar sem montar, o que deixa de funcionar e quais cartuchos são afetados.

## Layout de cada variante

```
boards/<variante>/
├── README.md        # slots, estado, decisões próprias
├── hardware/        # projeto KiCad (<nome>.kicad_pro/_sch/_pcb, fp-lib-table, sym-lib-table)
├── fab/             # gerbers, drill, bom.csv e zip da fábrica
└── docs/            # pinmap.md, bom.md, montagem.md da variante
```

As tabelas de bibliotecas apontam para `${KIPRJMOD}/../../_lib/`. Pinagem idêntica ao OSCR HW5 continua regra de ouro (`CLAUDE.md`, seção 3). Uma variante nova nasce copiando o esqueleto e gerando o próprio `docs/pinmap.md`; `tools/check_netlist.py` aceita `--board <pasta>` e `tools/export_fab.sh <pasta> <versão>` gera os arquivos da fábrica; `gen_pinmap.py` e os demais scripts gerais de `tools/` apontam para `16_and_8_bits/`. As placas de um sistema só têm scripts próprios em `tools/<placa>/` (receita completa em `boards/nes/README.md` e na D96).

Todas as placas novas (`megadrive`, `snes`, `nes`, `famicom`, `famicom_nes`, `gb_gba`, `n64`) foram roteadas por autoroteador e **não foram revisadas à mão no KiCad**; nenhuma foi encomendada, montada ou testada com cartucho.
