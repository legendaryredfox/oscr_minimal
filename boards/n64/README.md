# n64 — Nintendo 64

![Render 3D da placa n64 (KiCad, vista de cima)](render.png)

**README por versão** (renders de cima e de baixo, peças, diferenças): [v1.0](hardware-v1.0/README.md), [v1.1](hardware-v1.1/README.md).

**Slots:** N64 (50 pinos, cartucho de 3,3 V; footprint `N64_Slot` do OSCR, a trazer para `_lib/`)

**Estado:** v1.1, 110,1 × 65,1 mm. ERC com 1 aviso de biblioteca (U2, o mesmo das outras placas); DRC sem erros nem ligações abertas (só 4 avisos de biblioteca dos furos); netlist confere com `docs/pinmap.md` (30 nets, 96 ligações); gerbers em `fab/`. Roteada pelo Freerouting, **não revisada à mão no KiCad**; nada encomendado nem montado. Reproduzir: `tools/boards/n64/build_pcb.sh` (PCB) e `tools/boards/n64/make_sch.py` (esquemático). Aprovado pelo usuário em 2026-11-07 ("confere tudo e pode fazer no kicad"). **Fase 1 do `CLAUDE.md`:** `docs/pinmap.md` gerado por `tools/boards/n64/gen_pinmap.py` cruzando `pinout.ods`, `n64_adapter` + `six_slot_adapter` e `N64.ino`: 50 pinos, 0 divergências entre as fontes. 

## O que o pinmap mostra

- Sinais: `AD0` a `AD15` em A0 a A15 (portas F e K), `/READ` em D9, `/WRITE` em D8, `ALE_L` em D37, `ALE_H` em D36, `RESET` em D17, `EEPROM_DATA` em D7 (com pull-up de 1 kΩ para o 3,3 V no adaptador do OSCR). `EEPROM_CLK` (pino 19) vem do `CLK1` do Si5351 (2 MHz).
- Tensão: `VCC` (pinos 9, 17, 34, 42) em **3,3 V**. Mesmo regulador do GBA (MCP1700, `gb_gba/`) e sinais do Mega em 5 V, como o OSCR HW5 e a família já fazem no slot GBA.
- Sem ligação (como no OSCR): `12V` (13, 38), `NC` (14, 39), `CIC_to_PIF` (18), `L_AUDIO` (24), `PIF_to_CIC` (43), `R4300_CLK` (44), `NMI` (45), `Video_CLK` (46), `R_AUDIO` (49). O CIC do N64 **não** é lido por esta placa.

## O que a placa leva e o que cada peça faz

Detalhe em `docs/componentes-opcionais.md`. Resumo:

| Peça | Sem ela |
|---|---|
| Regulador 3,3 V + 2 capacitores | Slot sem energia: nada lê |
| Si5351 (só `CLK1`) | Não lê as **EEPROMs** de save (4K e 16K); ROM e SRAM/Flash seguem |
| Pull-up de 1 kΩ no D7 | EEPROM não lê com confiança |

## Pendências

1. Medidas reais do slot N64 comprado (CLAUDE.md, seção 5), contorno do footprint (estimativa) e direção da etiqueta (D27; o silk diz "a confirmar").
2. Firmware: religar o núcleo em `firmware/oscr/user.ini` (`n64 = true`), id no protocolo, host e GUI.
3. Revisar o layout no KiCad antes de encomendar.

Montagem: `docs/montagem.md`; compra: `docs/bom.md`.

O `CLAUDE.md` (seção 4) deixava o N64 fora das placas anteriores; esta placa nasce a pedido do usuário (2026-11-07).

Regras gerais: `CLAUDE.md`. Layout da pasta: `boards/README.md`.

**Peças opcionais:** [`docs/componentes-opcionais.md`](docs/componentes-opcionais.md).

## Bloco de troca de cartucho (v1.1, D126)

Circuito e motivo: `docs/referencia/bloco-troca.md` (na raiz do repositório). Peças novas desta placa:

| Ref. | Valor | Função |
|---|---|---|
| Q1 | IRF9540N (P-MOSFET, TO-220) | chave de alta do 5V dos slots (`+5V_CART`); comando no D19 (nível baixo liga) |
| R3 | 100 kΩ | gate do Q1 ao 5V (desligado com o Mega em reset) |
| R4 | 100 Ω | D19 ao gate do Q1 |
| R5, D2 | 1 kΩ, LED verde 3 mm | `+5V_CART` presente |
| Q2, R6 e R7 | 2N7000 (TO-92), 330 Ω (o R7 descarrega o 3,3 V) | descarga do rail quando o Q1 abre |
| Q3, R8, R9, R10, D3 | 2N7000, 100 kΩ, 1 kΩ, 1 kΩ, LED amarelo 3 mm | sensor do rail: D3 aceso = seguro trocar; R10 leva o nó ao D53 |

Os pinos de 5V dos slots e dos circuitos que a placa tiver (Si5351, PIC, pull-up, entrada do regulador de 3,3 V) e os capacitores deles ficam em `+5V_CART`. O Q1 (TO-220) fica em pé na placa, sem dissipador (a corrente do cartucho é baixa).

## Versões: com e sem o desligamento por software (D128)

O desligamento do 5V dos slots por software (bloco de troca de cartucho, D126) é uma versão **separada**; a placa existe também sem ele.

| Versão | Bloco de troca (Q1, Q2, Q3, LEDs, D19 e D53) | Projeto KiCad | Fábrica | Renders (cima e baixo) |
|---|---|---|---|---|
| v1.0 | **não** (5V direto nos slots) | `hardware-v1.0/` | `fab/gerbers-v1.0/`, `fab/dumper-v1.0-jlcpcb.zip`, `fab/bom-v1.0.csv` | `hardware-v1.0/render-cima.png`, `hardware-v1.0/render-baixo.png` |
| v1.1 | sim | `hardware-v1.1/` | `fab/gerbers-v1.1/`, `fab/dumper-v1.1-jlcpcb.zip`, `fab/bom-v1.1.csv` | `hardware-v1.1/render-cima.png`, `hardware-v1.1/render-baixo.png` (`render.png` = v1.1, de cima) |

A v1.0 é o projeto de antes do D126, restaurado do histórico do git; os gerbers dela foram regerados da pasta `hardware-v1.0/`. Verificação: `python3 tools/check_netlist.py --board n64 --sem-troca boards/n64/hardware-v1.0/dumper.kicad_sch` (v1.0) e `python3 tools/check_netlist.py --board n64` (v1.1). Para refazer os gerbers da v1.0: `HWDIR=hardware-v1.0 GDIR=gerbers-v1.0 tools/export_fab.sh n64 v1.0`. Nenhuma das duas foi encomendada, montada nem testada com cartucho.

