# Pedido da placa gb_gba v1.0 (JLCPCB)

Placa **GBA (GB e GBC por adaptador)**, 2 camadas, 138,1 × 67,1 mm. Feita em 2026-11-06 a partir de `../hardware/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.0-jlcpcb.zip` (cópia idêntica: `dumper-v1.0-gerbers-jlcpcb.zip`). SHA-256: `3d1fd5b528b9de56e8a3b3d7c10a63c0fc83b4b7ab7318605e05fd451560f4ff` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 138,1 × 67,1 mm |
| Furos não metalizados | 4 de 3,2 mm (M3) e 2 de 2,2 mm (guias do slot GBA) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**. Pads SMD de 1 mm a 1,5 mm de passo: HASL é aceitável para solda manual; ENIG sai mais caro.

**Verificação:** DRC sem erros nem ligações abertas (só avisos de biblioteca e paridade, como na `16_and_8_bits`); ERC com 1 aviso (`lib_symbol_mismatch` do U3); `tools/check_netlist.py --board gb_gba` confere (34 nets, 88 ligações).
