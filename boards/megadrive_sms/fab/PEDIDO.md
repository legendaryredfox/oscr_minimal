# Pedido da placa megadrive_sms v1.0 (JLCPCB)

Placa **Mega Drive + Master System**, 2 camadas, 107,1 × 83,1 mm, sem o bloco de troca de cartucho (v1.0: a mais barata que funciona; para trocar o cartucho, desligue o USB). Gerada em 2026-11-08 de `../hardware-v1.0/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.0-jlcpcb.zip`. SHA-256: `24286260027d1c6e6e13cb45f74fabff33d22ae1d1bd79813eb0209eba94317e` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 107,1 × 83,1 mm |
| Furos não metalizados | 6 (M3 de canto e meio da borda de baixo, 3,2 mm) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**Antes de encomendar:** a placa foi roteada por autoroteador (Freerouting) e **não foi revisada à mão no KiCad**; o silkscreen do slot SMS **não tem a direção da etiqueta** (não confirmada); o corpo dos slots é estimado (D17); medir os dois slots comprados.

**DRC:** 0 erros e 0 ligações abertas; 13 avisos `lib_footprint_mismatch` (Mega2560_R3_Shield sem os 6 furos do Mega, furos de montagem e pontos de teste, já justificados em D71). ERC 0 violações. `tools/check_netlist.py --board megadrive_sms --sem-troca` confere (56 nets, 175 ligações).
