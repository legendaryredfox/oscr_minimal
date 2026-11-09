# 16_and_8_bits — placa de 5 slots

![Render 3D da placa 16_and_8_bits (KiCad, vista de cima)](render.png)

**README por versão** (renders de cima e de baixo, peças, diferenças): [v1.0](hardware-v1.0/README.md).

**Slots:** SNES (62p), NES (72p), Famicom (60p), Mega Drive (64p) e GBA (32p, SMD, 3,3 V). Um cartucho por vez.

**Estado:** DRC 0 erros e 4 avisos justificados, netlist confere com `docs/pinmap.md`, gerbers v1.0 em `fab/`. Nada encomendado nem montado.

| Pasta | Conteúdo |
|---|---|
| `hardware-v1.0/` | `dumper.kicad_pro/_sch/_pcb` (KiCad 10) |
| `fab/` | `gerbers-v1.0/`, `bom-v1.0.csv`, `dumper-v1.0-jlcpcb.zip` |
| `docs/` | `pinmap.md` (fonte da verdade), `bom.md`, `montagem.md` |

Verificação (da raiz do repositório):

```
python3 tools/check_netlist.py --board 16_and_8_bits
kicad-cli sch erc boards/16_and_8_bits/hardware-v1.0/dumper.kicad_sch
kicad-cli pcb drc boards/16_and_8_bits/hardware-v1.0/dumper.kicad_pcb
```

**Peças opcionais:** o que se perde ao retirar cada componente, e que jogos são afetados, está em [`docs/componentes-opcionais.md`](docs/componentes-opcionais.md).

## Versões

Só a **v1.0** (`hardware-v1.0/`; fábrica em `fab/gerbers-v1.0/`, `fab/dumper-v1.0-jlcpcb.zip`, `fab/bom-v1.0.csv`; renders em `hardware-v1.0/render-cima.png` e `render-baixo.png`). Ela já leva o suporte do fusível F1 (D138). O 5V dos slots vai direto do Mega e **não é cortado por software** (o bloco de troca de cartucho, D126 a D128, foi retirado em D139): para trocar o cartucho, desligue o USB. Verificação: `python3 tools/check_netlist.py --board 16_and_8_bits`.
