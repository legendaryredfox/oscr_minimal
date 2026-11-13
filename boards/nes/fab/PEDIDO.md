# Pedido da placa nes (JLCPCB)

Envie `dumper-v1.1-jlcpcb.zip` (a versão mais nova; gerbers em `gerbers-v1.1/`). **Nada encomendado.** O layout foi roteado por autoroteador e **ainda não foi revisado à mão no KiCad**: revise antes de pagar.

Conteúdo do zip (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 110,1 × 95,1 mm |
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
| v1.0 | `dumper-v1.0-jlcpcb.zip` | 110,1 × 75,1 mm | `a906162ae4f79087c277c90c5536acd997b608ea2f5a26e224c134955466fb2f` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | 110,1 × 95,1 mm | `59c62a6c02a7532289534022574afa7cfce5f5c42feff3308deeab366ce07eee` |

Verificação: `python3 tools/check_netlist.py --board nes` (versão mais nova); ERC e DRC com `tools/troca/verifica.sh nes v1.1`.
