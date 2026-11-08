# famicom_nes — Famicom e NES

![Render 3D da placa famicom_nes (KiCad, vista de cima)](render.png)

Versão mínima de duas funções: um slot **Famicom** (60p, 2,54 mm) e um slot **NES** (72p, 2,5 mm) em shield para Arduino Mega 2560 R3, 100% THT, só USB, **5 V** fixo. Os dois slots ficam **em paralelo** nos mesmos pinos do Mega (como no `six_slot_adapter` do OSCR): **um cartucho por vez, em um slot só**. Pinagem idêntica ao OSCR HW5 (`docs/pinmap.md`, recorte da `16_and_8_bits`).

**Si5351, sem PIC:** o NES usa o `CLK0` do Si5351 no pino 37; o Famicom não tem pino de clock. Sem PIC (CIC do SNES), sem R2 e sem regulador de 3,3 V.

**Estado:** v1.1, 117,1 × 79,1 mm (alongada 5 mm à esquerda e com o slot NES 5 mm mais à esquerda, para dar folga ao U1, D124). ERC 0 violações; DRC sem erros nem ligações abertas (só 4 avisos de biblioteca e os de paridade das outras placas); netlist confere com `docs/pinmap.md`; gerbers em `fab/`. Roteada pelo Freerouting (MCP) com GND roteado junto e costurado com vias; alimentação (`+5V`) com 0,8 mm. **Revisar o layout no KiCad antes de encomendar.** Nada encomendado nem montado. Montagem: `docs/montagem.md`.

## Diferenças em relação à `16_and_8_bits`

| Item | 16_and_8_bits | famicom_nes |
|---|---|---|
| Slots | SNES, NES, Famicom, Mega Drive, GBA | NES e Famicom |
| Mantido | Si5351 (U1), LED (D1, R1), C1, C3 (VCC do NES), C4 (VCC do Famicom) (agora C2 e C3, D109) | idem |
| Removido | SNES1, MD1, GBA1, PIC (U2), R2, regulador U3 e C7, C8, C9, C2, C5, C6, furos M2 | |
| Placa | 144 × 108 mm | 117,1 × 79,1 mm |

**Layout:** o NES fica entre as fileiras de pinos do Mega, deslocado 12 mm para a esquerda do centro; o Famicom fica acima do cabeçalho do Mega (a placa cresce para cima); o soquete do Si5351 fica na vertical, ao lado do header duplo do Mega, com o módulo em pé. Os 6 furos não metalizados do Mega e os 4 de canto foram mantidos.

**Rótulo:** nos dois slots o rótulo do cartucho fica para baixo (lado do USB). Conferido com a [página Cartridge connector da NESdev](https://www.nesdev.org/wiki/Cartridge_connector): os pinos 1–36 do NES e 1–30 do Famicom estão no lado do rótulo, e nos dois footprints essa é a fileira de baixo. A orientação do corpo do slot continua a confirmar com a peça (D27).

## Como foi feita

`tools/famicom_nes/place.py` sobre a cópia da `16_and_8_bits`, depois `tools/nes/sync_unconnected.py`, `autoroute` do KiCad MCP com o GND como trilha, `add_zones.py`, `stitch.py`, `widen_power.py` e `fill_zones.py` (receita da `nes/` e da D96).

```
python3 tools/check_netlist.py --board famicom_nes
kicad-cli sch erc boards/famicom_nes/hardware/dumper.kicad_sch
kicad-cli pcb drc boards/famicom_nes/hardware/dumper.kicad_pcb
tools/export_fab.sh famicom_nes v1.0
```

**Peças opcionais:** o que se perde ao retirar cada componente, e que jogos são afetados, está em [`docs/componentes-opcionais.md`](docs/componentes-opcionais.md).

## Bloco de troca de cartucho (v1.1, D126)

Circuito e motivo: `docs/bloco-troca.md` (na raiz do repositório). Peças novas desta placa:

| Ref. | Valor | Função |
|---|---|---|
| Q1 | IRF9540N (P-MOSFET, TO-220) | chave de alta do 5V dos slots (`+5V_CART`); comando no D19 (nível baixo liga) |
| R2 | 100 kΩ | gate do Q1 ao 5V (desligado com o Mega em reset) |
| R3 | 100 Ω | D19 ao gate do Q1 |
| R4, D2 | 1 kΩ, LED verde 3 mm | `+5V_CART` presente |
| Q2, R5 | 2N7000 (TO-92), 330 Ω | descarga do rail quando o Q1 abre |
| Q3, R6, R7, R8, D3 | 2N7000, 100 kΩ, 1 kΩ, 1 kΩ, LED amarelo 3 mm | sensor do rail: D3 aceso = seguro trocar; R8 leva o nó ao D53 |

Os pinos de 5V dos slots e dos circuitos que a placa tiver (Si5351, PIC, pull-up, entrada do regulador de 3,3 V) e os capacitores deles ficam em `+5V_CART`. O Q1 (TO-220) fica em pé na placa, sem dissipador (a corrente do cartucho é baixa).

## Versões: com e sem o desligamento por software (D128)

O desligamento do 5V dos slots por software (bloco de troca de cartucho, D126) é uma versão **separada**; a placa existe também sem ele.

| Versão | Bloco de troca (Q1, Q2, Q3, LEDs, D19 e D53) | Projeto KiCad | Fábrica | Renders (cima e baixo) |
|---|---|---|---|---|
| v1.0 | **não** (5V direto nos slots) | `hardware-v1.0/` | `fab/gerbers-v1.0/`, `fab/dumper-v1.0-jlcpcb.zip`, `fab/bom-v1.0.csv` | `renders/famicom_nes-v1.0-cima.png`, `renders/famicom_nes-v1.0-baixo.png` |
| v1.1 | sim | `hardware/` | `fab/gerbers/`, `fab/dumper-v1.1-jlcpcb.zip`, `fab/bom.csv` | `renders/famicom_nes-v1.1-cima.png`, `renders/famicom_nes-v1.1-baixo.png` (`render.png` = v1.1, de cima) |

A v1.0 é o projeto de antes do D126, restaurado do histórico do git; os gerbers dela foram regerados da pasta `hardware-v1.0/`. Verificação: `python3 tools/check_netlist.py --board famicom_nes --sem-troca boards/famicom_nes/hardware-v1.0/dumper.kicad_sch` (v1.0) e `python3 tools/check_netlist.py --board famicom_nes` (v1.1). Para refazer os gerbers da v1.0: `HWDIR=hardware-v1.0 GDIR=gerbers-v1.0 tools/export_fab.sh famicom_nes v1.0`. Nenhuma das duas foi encomendada, montada nem testada com cartucho.

