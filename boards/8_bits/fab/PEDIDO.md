# Pedido da placa 8_bits (JLCPCB)

Envie `dumper-v1.1-jlcpcb.zip` (a versão mais nova; gerbers em `gerbers-v1.1/`) ou `dumper-v1.0-jlcpcb.zip` (a mínima, só com o fusível). **Nada encomendado.** O layout foi roteado por autoroteador e **ainda não foi revisado à mão no KiCad**: revise antes de pagar.

Conteúdo do zip (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | v1.1: 117,1 × 109,1 mm; v1.0: 117,1 × 97,1 mm |
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
| v1.0 | `dumper-v1.0-jlcpcb.zip` | `60670e0ee7dcf3916d61b947fa92cdeef64799536415624c71c7c4ac07c38fde` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | `d273abfd62472c5629368bc7c4657a2bc503009fa2e238e20f8048e74ff2592c` |

Verificação: `python3 tools/check_netlist.py --board 8_bits` (v1.1) e `python3 tools/check_netlist.py --board 8_bits boards/8_bits/hardware-v1.0/dumper.kicad_sch` (v1.0); ERC e DRC com `kicad-cli` (ver `README.md` da placa).
