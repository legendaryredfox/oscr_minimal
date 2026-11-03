# 16_bits — SNES e Mega Drive

Versão mínima da placa de 5 slots (`../16_and_8_bits/`): só os slots **SNES** (62p, 2,5 mm) e **Mega Drive** (64p, 2,54 mm). Shield para Arduino Mega 2560 R3, 100% THT, só USB, **5 V** em tudo (sem regulador de 3,3 V). Um cartucho por vez.

**Estado:** DRC 0 erros e 0 ligações abertas (8 avisos justificados, D71), netlist confere com `docs/pinmap.md`, gerbers v1.0 em `fab/`. Nada encomendado nem montado, nunca testado com cartucho.

## Diferenças em relação à `16_and_8_bits`

| Item | 16_and_8_bits | 16_bits |
|---|---|---|
| Slots | SNES, NES, Famicom, Mega Drive, GBA | SNES, Mega Drive |
| Regulador 3,3 V (U3, C7, C8, C9) | sim | não |
| Capacitores de 100 nF | C2 a C6, C9 | C3 (SNES), C5 (Mega Drive), C6 (PIC) |
| Placa | 144 × 108 mm | 108 × 86 mm |
| Furos | 4 M3 de canto, 6 do Mega, 2 M2 do Si5351 | **só os 4 M3 de canto** |
| Si5351 | header vertical, módulo ao lado | header horizontal, módulo sobre ele, sem furos |

Pinagem idêntica à da `16_and_8_bits` (e ao OSCR HW5): `docs/pinmap.md` é um recorte do dela.

**Mecânica:** o shield fica preso ao Mega só pelos pinos macho longos. Os 4 furos de canto servem para espaçadores M3 e pés de borracha, não prendem o Mega.

| Pasta | Conteúdo |
|---|---|
| `hardware/` | `dumper.kicad_pro/_sch/_pcb` (KiCad 10) |
| `fab/` | `gerbers/`, `bom.csv`, `dumper-v1.0-jlcpcb.zip`, `dumper-v1.0-gerbers-jlcpcb.zip` |
| `docs/` | `pinmap.md`, `bom.md`, `montagem.md` |

Verificação (da raiz do repositório):

```
python3 tools/check_netlist.py --board 16_bits
kicad-cli sch erc boards/16_bits/hardware/dumper.kicad_sch
kicad-cli pcb drc boards/16_bits/hardware/dumper.kicad_pcb
tools/export_fab.sh 16_bits v1.0
```
