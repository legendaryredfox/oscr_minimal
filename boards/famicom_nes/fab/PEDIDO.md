# Pedido da placa famicom_nes v1.1 (JLCPCB)

Placa **Famicom + NES**, 2 camadas, 117,1 × 79,1 mm. Refeita em 2026-11-07 (D124) a partir de `../hardware-v1.1/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.1-jlcpcb.zip`. SHA-256: `62a12edc95a34283508c19c4b81015b4dc37fc9d3e0c1bb268a28bf655039bb1` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 117,1 × 79,1 mm |
| Furos não metalizados | 10 (3,2 mm: 4 de canto e 6 do Mega) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**Verificação:** DRC sem erros nem ligações abertas (só avisos de biblioteca e paridade já justificados em D71); ERC 0 violações; `tools/check_netlist.py --board famicom_nes` confere (46 nets, 206 ligações).

## D138 — F1, J1 e seletor de tensão (2026-11-08)

As versões abaixo foram **refeitas** com o PTC F1 (opcional; sem ele, fio ou ponte de solda nos furos) e, nas v1.1 com slot de 5 V, o seletor 3,3 V/5 V, o jumper J1 e os resistores em série (D138). Os tamanhos e SHA-256 mais acima, de antes do D138, **não valem mais**; valem estes (mude de zip só depois de rever o layout no KiCad: roteamento por autoroteador, nada encomendado):

| Versão | Arquivo | Tamanho | SHA-256 |
|---|---|---|---|
| v1.0 | `dumper-v1.0-jlcpcb.zip` | 117,1 × 89,1 mm | `252ae60d8d6469a341f4f588f4046594c4c7152f607cf31ad2385d06c1f95576` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | 117,1 × 109,1 mm | `77c0170277251f4a815d7863e6a90712685a175a7c26cdca88cc879f36034281` |
