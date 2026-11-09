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

## D138 — F1, J1 e seletor de tensão (2026-11-08)

As versões abaixo foram **refeitas** com o PTC F1 (opcional; sem ele, fio ou ponte de solda nos furos) e, nas v1.1 com slot de 5 V, o seletor 3,3 V/5 V, o jumper J1 e os resistores em série (D138). Os tamanhos e SHA-256 mais acima, de antes do D138, **não valem mais**; valem estes (mude de zip só depois de rever o layout no KiCad: roteamento por autoroteador, nada encomendado):

| Versão | Arquivo | Tamanho | SHA-256 |
|---|---|---|---|
| v1.0 | `dumper-v1.0-jlcpcb.zip` | 107,1 × 93,1 mm | `0b5e1133abde33d4618e6f427d10e2e5c000ddddfc946eb2239481b897d62ad7` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | 107,1 × 128,1 mm | `92449a472fcef5dda7c4866e00ee2fcfdd0d7150a2d8f1d2032a5b4d9e0c5a7c` |
