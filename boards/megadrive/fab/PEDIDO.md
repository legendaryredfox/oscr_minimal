# Pedido da placa megadrive (JLCPCB)

Envie `dumper-v1.1-jlcpcb.zip` (a versão mais nova; gerbers em `gerbers-v1.1/`). **Nada encomendado.** O layout foi roteado por autoroteador e **ainda não foi revisado à mão no KiCad**: revise antes de pagar.

Conteúdo do zip (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 107,1 × 110,1 mm |
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
| v1.0 | `dumper-v1.0-jlcpcb.zip` | 107,1 × 75,1 mm | `93c3fd47c6ddc1017cf28b3d0fbfb0596238a8d790fdc5d3ac15ea8b1c1e59e4` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | 107,1 × 110,1 mm | `09485bc6d67fb674cd3620fbfc20c3ace786f4225bda41df10a63ba28c1c375e` |

Verificação: `python3 tools/check_netlist.py --board megadrive` (versão mais nova); ERC e DRC com `tools/troca/verifica.sh megadrive v1.1`.
