# Pedido da placa gb_gba v1.1 (JLCPCB)

Placa **GBA (GB e GBC por adaptador)**, 2 camadas, 138,1 × 67,1 mm. Refeita em 2026-11-07 (bloco de troca de cartucho, D126) a partir de `../hardware/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.1-jlcpcb.zip` (cópia idêntica: `dumper-v1.1-gerbers-jlcpcb.zip`). SHA-256: `f928bfc9c66193c3f9f3617f7fd18158ec6758d843b54fa75dc92d8316996333` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 138,1 × 67,1 mm |
| Furos não metalizados | 10 de 3,2 mm (4 M3 do lado do Mega e 6 do Mega) e 2 de 2,2 mm (guias do slot GBA) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**. Pads SMD de 1 mm a 1,5 mm de passo: HASL é aceitável para solda manual; ENIG sai mais caro.

**Verificação:** DRC sem erros nem ligações abertas (só avisos de biblioteca e paridade, como na `16_and_8_bits`); ERC com 1 aviso (`lib_symbol_mismatch` do U1); `tools/check_netlist.py --board gb_gba` confere (41 nets, 120 ligações).
