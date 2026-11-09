# Pedido da placa megadrive v1.1 (JLCPCB)

Placa **só Mega Drive**, 2 camadas, 107,1 × 65,1 mm. Refeita em 2026-11-07 (bloco de troca de cartucho, D126) a partir de `../hardware-v1.1/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.1-jlcpcb.zip`. SHA-256: `ddc28be2b5077ead31ffb825a9fe56c82a5b39985ca4316da6fa2f954fbc1f4c` (muda a cada exportação; confira com `sha256sum`).

Conteúdo (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 107,1 × 65,1 mm |
| Furos não metalizados | 4 (M3 de canto, 3,2 mm) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**DRC:** 0 erros, 0 ligações abertas e nenhum `starved_thermal` (os pads GND3 do Mega e A18 do slot têm conexão sólida com o plano da B.Cu, D96); só avisos de biblioteca/paridade já justificados em D71. ERC 0 violações. `tools/check_netlist.py --board megadrive` confere (63 nets, 169 ligações).

## D138 — F1, J1 e seletor de tensão (2026-11-08)

As versões abaixo foram **refeitas** com o PTC F1 (opcional; sem ele, fio ou ponte de solda nos furos) e, nas v1.1 com slot de 5 V, o seletor 3,3 V/5 V, o jumper J1 e os resistores em série (D138). Os tamanhos e SHA-256 mais acima, de antes do D138, **não valem mais**; valem estes (mude de zip só depois de rever o layout no KiCad: roteamento por autoroteador, nada encomendado):

| Versão | Arquivo | Tamanho | SHA-256 |
|---|---|---|---|
| v1.0 | `dumper-v1.0-jlcpcb.zip` | 107,1 × 75,1 mm | `93c3fd47c6ddc1017cf28b3d0fbfb0596238a8d790fdc5d3ac15ea8b1c1e59e4` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | 107,1 × 110,1 mm | `a089ee6f64045ef60b4e88409077dd5f8d1959e4f06db0e2f25f2ba9729a13cc` |
