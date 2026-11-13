# 16_and_8_bits — placa de 5 slots

![Render 3D da placa 16_and_8_bits (KiCad, vista de cima)](render.png)

**README por versão** (renders de cima e de baixo, peças, diferenças): [v1.0](hardware-v1.0/README.md), [v1.1](hardware-v1.1/README.md).

**Slots:** SNES (62p), NES (72p), Famicom (60p), Mega Drive (64p) e GBA (32p, SMD, 3,3 V). Um cartucho por vez.

**Versões (regra do usuário: v1.0 = a mínima que funciona, com fusível; outras versões = mais recursos):**

- **v1.0** (144,1 × 118,1 mm): a mínima, com o fusível F1 (D144).
- **v1.1** (144,1 × 134,1 mm): a v1.0 mais o **seletor de tensão 3,3 V/5 V** nos slots **NES, Famicom e Mega Drive** (LDO LD1117V33 U4, Q1 de bypass, Q2 de comando pelo D18, R3 a R5, C10, C11) e o J1 "TRAVA 3,3 V" (D157, D138, D147). **O SNES fica sempre em 5 V** (o SA-1 não funciona a 3,3 V), assim como o PIC e o Si5351; o GBA tem o regulador U3. Firmware: ambiente `SerialASCII_Volt`.

**Estado:** DRC 0 erros nas duas versões (só os 4 avisos de biblioteca do furo M3), netlist confere com `docs/pinmap.md`, gerbers v1.0 e v1.1 em `fab/` (`fab/PEDIDO.md`). A v1.1 foi roteada pelo Freerouting: **revisar o layout no KiCad antes de encomendar**. Nada encomendado nem montado.

| Pasta | Conteúdo |
|---|---|
| `hardware-v1.0/`, `hardware-v1.1/` | `dumper.kicad_pro/_sch/_pcb` (KiCad 10) |
| `fab/` | `gerbers-<versão>/`, `bom-<versão>.csv`, `dumper-<versão>-jlcpcb.zip`, `PEDIDO.md` |
| `docs/` | `pinmap.md` (fonte da verdade), `bom.md`, `montagem.md` |

Verificação (da raiz do repositório):

```
python3 tools/check_netlist.py --board 16_and_8_bits boards/16_and_8_bits/hardware-v1.1/dumper.kicad_sch
kicad-cli sch erc boards/16_and_8_bits/hardware-v1.1/dumper.kicad_sch
kicad-cli pcb drc boards/16_and_8_bits/hardware-v1.1/dumper.kicad_pcb
tools/export_fab.sh 16_and_8_bits v1.1
```

**Peças opcionais:** o que se perde ao retirar cada componente, e que jogos são afetados, está em [`docs/componentes-opcionais.md`](docs/componentes-opcionais.md).

## Versões

Só a **v1.0** (`hardware-v1.0/`; fábrica em `fab/gerbers-v1.0/`, `fab/dumper-v1.0-jlcpcb.zip`, `fab/bom-v1.0.csv`; renders em `hardware-v1.0/render-cima.png` e `render-baixo.png`). Ela já leva o suporte do fusível F1 (D138). O 5V dos slots vai direto do Mega e **não é cortado por software** (o bloco de troca de cartucho, D126 a D128, foi retirado em D139): para trocar o cartucho, desligue o USB. Verificação: `python3 tools/check_netlist.py --board 16_and_8_bits`.
