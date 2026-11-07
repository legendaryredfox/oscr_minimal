# 16_and_8_bits — placa de 5 slots

**Slots:** SNES (62p), NES (72p), Famicom (60p), Mega Drive (64p) e GBA (32p, SMD, 3,3 V). Um cartucho por vez.

**Estado:** DRC 0 erros e 4 avisos justificados, netlist confere com `docs/pinmap.md`, gerbers v1.0 em `fab/`. Nada encomendado nem montado.

| Pasta | Conteúdo |
|---|---|
| `hardware/` | `dumper.kicad_pro/_sch/_pcb` (KiCad 10) |
| `fab/` | `gerbers/`, `bom.csv`, `dumper-v1.0-jlcpcb.zip`, `dumper-v1.0-gerbers-jlcpcb.zip` |
| `docs/` | `pinmap.md` (fonte da verdade), `bom.md`, `montagem.md` |

Verificação (da raiz do repositório):

```
python3 tools/check_netlist.py --board 16_and_8_bits
kicad-cli sch erc boards/16_and_8_bits/hardware/dumper.kicad_sch
kicad-cli pcb drc boards/16_and_8_bits/hardware/dumper.kicad_pcb
```

**Peças opcionais:** o que se perde ao retirar cada componente, e que jogos são afetados, está em [`docs/componentes-opcionais.md`](docs/componentes-opcionais.md).
