# Pedido da placa famicom v1.1 (JLCPCB)

Placa **só Famicom**, 2 camadas, 107,1 × 65,1 mm. Refeita em 2026-11-07 (bloco de troca de cartucho, D126) a partir de `../hardware/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.1-jlcpcb.zip` (cópia idêntica: `dumper-v1.1-gerbers-jlcpcb.zip`). SHA-256: `13ea1b2a7d215de22dc108a56c1e846cad05a7e7b44f0512a6d54bd1148fb057` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 107,1 × 65,1 mm |
| Furos não metalizados | 10 (3,2 mm: 4 de canto e 6 do Mega) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**Verificação:** DRC sem erros nem ligações abertas (só avisos de biblioteca e paridade já justificados em D71); ERC 0 violações; `tools/check_netlist.py --board famicom` confere (43 nets, 139 ligações).
