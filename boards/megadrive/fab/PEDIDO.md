# Pedido da placa megadrive v1.0 (JLCPCB)

Placa **só Mega Drive**, 2 camadas, 107,1 × 65,1 mm. Feita em 2026-11-06 a partir de `../hardware/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.0-jlcpcb.zip` (cópia idêntica: `dumper-v1.0-gerbers-jlcpcb.zip`). SHA-256: `452c86044a5bb8c53c2ac80a7c12dfcef63c0cd6c5e7f3ca3d9b32887202ef08` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 107,1 × 65,1 mm |
| Furos não metalizados | 4 (M3 de canto, 3,2 mm) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**DRC:** 0 erros, 0 ligações abertas e nenhum `starved_thermal` (os pads GND3 do Mega e A18 do slot têm conexão sólida com o plano da B.Cu, D96); só avisos de biblioteca/paridade já justificados em D71. ERC 0 violações. `tools/check_netlist.py --board megadrive` confere (56 nets, 139 ligações).
