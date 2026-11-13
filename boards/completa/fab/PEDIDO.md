# Pedido da placa completa (JLCPCB)

Envie `dumper-v1.1-jlcpcb.zip` (a versão mais nova; gerbers em `gerbers-v1.1/`) ou `dumper-v1.0-jlcpcb.zip` (a mínima, só com o fusível). **Nada encomendado.** O layout foi roteado por autoroteador e **ainda não foi revisado à mão no KiCad**: revise antes de pagar.

Conteúdo do zip (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | v1.1: 144,1 × 168,1 mm; v1.0: 144,1 × 152,1 mm (acima de 100 × 100 mm: faixa de preço maior) |
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
| v1.0 | `dumper-v1.0-jlcpcb.zip` | `bebde132860ab2c762bb7b38b82e9e0dce26975412819e7b504abcd8a62d3d3d` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | `b0dd4cd1d2007dba31a9ca294da64e2401e3d73a33a3283486913f6bfc175f88` |

Verificação: `python3 tools/check_netlist.py --board completa` (v1.1) e `python3 tools/check_netlist.py --board completa boards/completa/hardware-v1.0/dumper.kicad_sch` (v1.0); ERC e DRC com `kicad-cli` (ver `README.md` da placa).
