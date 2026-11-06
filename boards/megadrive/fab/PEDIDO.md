# Pedido da placa megadrive v1.0 (JLCPCB)

Placa **só Mega Drive**, 2 camadas, 107,1 × 65,1 mm. Feita em 2026-11-06 a partir de `../hardware/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.0-jlcpcb.zip` (cópia idêntica: `dumper-v1.0-gerbers-jlcpcb.zip`). SHA-256: `488b710ccd711d32a06d287abe745bdccc401f6ea7179fb0c80f0ebf753cc014` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 107,1 × 65,1 mm |
| Furos não metalizados | 4 (M3 de canto, 3,2 mm) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**DRC:** 0 erros de roteamento, 0 ligações abertas; 2 `starved_thermal` na B.Cu (pads GND3 do Mega e A18 do slot, ligados também pela F.Cu) e avisos de biblioteca/paridade já justificados em D71. ERC 0 violações. `tools/check_netlist.py --board megadrive` confere (56 nets, 139 ligações).
