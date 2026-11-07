# Pedido da placa n64 v1.0 (JLCPCB)

Placa **só N64**, 2 camadas, 110,1 × 65,1 mm. Feita em 2026-11-07 a partir de `../hardware/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.0-jlcpcb.zip` (cópia idêntica: `dumper-v1.0-gerbers-jlcpcb.zip`). SHA-256: `55828fb0ba3fcdcfc598a11a7e45a5c9d77e05ba58282c1d4149a7358cd292f1` (muda a cada exportação; confira com `sha256sum`).

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 110,1 × 65,1 mm |
| Furos não metalizados | 10 (3,2 mm: 4 de canto e 6 do Mega) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**Verificação:** DRC sem erros nem ligações abertas (só 4 avisos de biblioteca dos furos de fixação); `tools/check_netlist.py --board n64` confere (30 nets, 96 ligações, 11 pinos de slot sem ligação). Roteada por autoroteador, **não revisada à mão no KiCad**. Reproduzir: `tools/n64/build_pcb.sh`.
