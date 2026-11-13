# Pedido da placa famicom (JLCPCB)

Envie `dumper-v1.1-jlcpcb.zip` (a versão mais nova; gerbers em `gerbers-v1.1/`). **Nada encomendado.** O layout foi roteado por autoroteador e **ainda não foi revisado à mão no KiCad**: revise antes de pagar.

Conteúdo do zip (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 107,1 × 105,1 mm |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos não metalizados | 4 (M3 de canto, 3,2 mm) |
| Furo mínimo | 0,3 mm (vias) |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

Se a pré-visualização mostrar outra coisa, **não pague**.

## F1, J1 e seletor de tensão (D138)

O suporte do fusível F1 está em todas as versões (opcional; troca sem solda). O seletor 3,3 V/5 V, o jumper J1 e os resistores em série estão nas placas com slot de 5 V que têm v1.1. O 5V dos slots **não é cortado por software** (D139): troque o cartucho com o USB desligado. Circuito: `docs/referencia/seletor-tensao.md`. Os SHA-256 mudam a cada exportação; confira com `sha256sum`.

| Versão | Arquivo | Tamanho | SHA-256 |
|---|---|---|---|
| v1.0 | `dumper-v1.0-jlcpcb.zip` | 107,1 × 75,1 mm | `8079149dac27d3d13c2cd7a687c9d1b4a02841b090c1f115d89644639edd02e3` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | 107,1 × 105,1 mm | `b3ff9a53a6507cbf8f803cf482ec80108160b2167732fae0abe3fa788aa5c96c` |

Verificação: `python3 tools/check_netlist.py --board famicom` (versão mais nova); ERC e DRC com `tools/troca/verifica.sh famicom v1.1`.
