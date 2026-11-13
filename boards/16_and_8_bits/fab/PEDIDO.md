# Pedido da placa 16_and_8_bits (JLCPCB)

Envie `dumper-v1.1-jlcpcb.zip` (a versão mais nova; gerbers em `gerbers-v1.1/`) ou `dumper-v1.0-jlcpcb.zip` (a mínima, só com o fusível). **Nada encomendado.** O layout foi roteado por autoroteador e **ainda não foi revisado à mão no KiCad**: revise antes de pagar.

Conteúdo do zip (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | v1.1: 144,1 × 134,1 mm; v1.0: 144,1 × 118,1 mm |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos não metalizados | 4 (M3 de canto, 3,2 mm) |
| Furo mínimo | 0,3 mm (vias) |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

Se a pré-visualização mostrar outra coisa, **não pague**.

## SHA-256

Mudam a cada exportação; confira com `sha256sum`.

| Versão | Arquivo | SHA-256 |
|---|---|---|
| v1.0 | `dumper-v1.0-jlcpcb.zip` | `c49f3b7641acbf031b1e719af0b4cbbab202e4d7153fa30d6169e323b5436f0b` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | `248f226fa1ca35edf7587e0797f6bab917c6a909513a8c47b93ade1f71e89acb` |

Verificação: `python3 tools/check_netlist.py --board 16_and_8_bits` (v1.1) e `python3 tools/check_netlist.py --board 16_and_8_bits boards/16_and_8_bits/hardware-v1.0/dumper.kicad_sch` (v1.0); ERC e DRC com `kicad-cli` (ver `README.md` da placa).
