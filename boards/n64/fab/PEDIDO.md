# Pedido da placa n64 v1.1 (JLCPCB)

Placa **só N64**, 2 camadas, 110,1 × 65,1 mm. Refeita em 2026-11-07 (bloco de troca de cartucho, D126) a partir de `../hardware-v1.1/dumper.kicad_pcb`. **Nada encomendado.**

Envie `dumper-v1.1-jlcpcb.zip`. SHA-256: `1342b0243aef01ecef97d0dda59db4f83d4de5b966ef55e75e658653a755d274` (muda a cada exportação; confira com `sha256sum`).

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | 110,1 × 65,1 mm |
| Furos não metalizados | 10 (3,2 mm: 4 de canto e 6 do Mega) |
| Furo mínimo | 0,3 mm (vias) |

Se a pré-visualização mostrar outra coisa, **não pague**.

**Verificação:** DRC sem erros nem ligações abertas (só 4 avisos de biblioteca dos furos de fixação); `tools/check_netlist.py --board n64` confere (30 nets, 96 ligações, 11 pinos de slot sem ligação). Roteada por autoroteador, **não revisada à mão no KiCad**. Reproduzir: `tools/boards/n64/build_pcb.sh`.

## D138 — F1, J1 e seletor de tensão (2026-11-08)

As versões abaixo foram **refeitas** com o PTC F1 (opcional; sem ele, fio ou ponte de solda nos furos) e, nas v1.1 com slot de 5 V, o seletor 3,3 V/5 V, o jumper J1 e os resistores em série (D138). Os tamanhos e SHA-256 mais acima, de antes do D138, **não valem mais**; valem estes (mude de zip só depois de rever o layout no KiCad: roteamento por autoroteador, nada encomendado):

| Versão | Arquivo | Tamanho | SHA-256 |
|---|---|---|---|
| v1.0 | `dumper-v1.0-jlcpcb.zip` | 110,1 × 75,1 mm | `47f3ac7b60d2041d8f3dcffce919e33e8c06db024f041eb5e2dd7aca21bc5369` |
| v1.1 | `dumper-v1.1-jlcpcb.zip` | 110,1 × 90,1 mm | `6e4d2da8718ced8585b221005fc3b7caff320ec94a4324a2f2c8e7ee1bc436ea` |
