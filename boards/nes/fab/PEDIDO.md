# Pedido da placa nes v1.1 (JLCPCB)

Placa **só NES**, 2 camadas, 110,1 × 65,1 mm. Refeita em 2026-11-07 (bloco de troca de cartucho, D126) a partir de `../hardware-v1.1/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.1-jlcpcb.zip`. SHA-256: `4734e185b01fdd3672b79ffb2ab80cb69a9cb43745c9ef81bb92d78531d87c48` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 110,1 × 65,1 mm |
| Furos não metalizados | 10 (3,2 mm: 4 de canto e 6 do Mega) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**Verificação:** DRC sem erros nem ligações abertas (só avisos de biblioteca e paridade já justificados em D71); ERC 0 violações; `tools/check_netlist.py --board nes` confere (46 nets, 146 ligações).

## D138 — F1, J1 e seletor de tensão (2026-11-08)

As versões abaixo foram **refeitas** com o PTC F1 (opcional; sem ele, fio ou ponte de solda nos furos) e, nas v1.1 com slot de 5 V, o seletor 3,3 V/5 V, o jumper J1 e os resistores em série (D138). Os tamanhos e SHA-256 mais acima, de antes do D138, **não valem mais**; valem estes (mude de zip só depois de rever o layout no KiCad: roteamento por autoroteador, nada encomendado):

| Versão | Arquivo | Tamanho | SHA-256 |
|---|---|---|---|
| v1.0 | `dumper-v1.0-jlcpcb.zip` | 110,1 × 75,1 mm | `08e74f7d9f5d29b75b1fa4dcf1405490d5650169480e6ac8f28f136249b1df4c` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | 110,1 × 95,1 mm | `1bdaac16dc126c6b9513250695b300e93627bccff72ef8706c1579a5b3d05a1f` |
