# 16_bits — versões e o que muda entre elas (D128)

Pedido do usuário em 2026-11-07: o botão de reset sai de todas as versões; a v1.2 não leva o circuito de desligar o 5V dos slots pelo Arduino; esse circuito (o bloco de troca de cartucho) fica na v1.3. Cada versão tem o seu projeto KiCad, os seus gerbers e dois PNGs (cima e baixo) e um `README.md` dentro da pasta de hardware.

| | v1.0 | v1.2 | v1.3 |
|---|---|---|---|
| Projeto KiCad | `hardware-v1.0/` | `hardware-v1.2/` | `hardware/` |
| Gerbers e zip | `fab/gerbers-v1.0/`, `fab/dumper-v1.0-jlcpcb.zip` | `fab/gerbers-v1.2/`, `fab/dumper-v1.2-jlcpcb.zip` | `fab/gerbers/`, `fab/dumper-v1.3-jlcpcb.zip` |
| Lista de peças (CSV) | — | `fab/bom-v1.2.csv` | `fab/bom.csv` |
| PNGs | `renders/16_bits-v1.0-cima.png`, `-baixo.png` | `renders/16_bits-v1.2-cima.png`, `-baixo.png` | `renders/16_bits-v1.3-cima.png`, `-baixo.png` (`render.png` = v1.3, de cima) |
| Resistores série (0 Ω) nas 12 linhas de controle, pull-up de `/VRES` (DNP), `/CART` no D50, C5, C6, pontos de teste, furos M3 do Mega | não | sim | sim |
| TVS 5 V (DNP) nas 12 linhas de controle (D3 a D14) | não | **não** (D130) | sim |
| Botão de reset (SW1) | não | **não** | **não** |
| Desligamento do 5V por software (Q1, R16 a R18, LED verde) | não | **não** (5V direto nos slots) | sim |
| Descarga do rail e LED amarelo "seguro trocar" (Q2, Q3, R19 a R22, D16; sensor no D53) | não | não | sim |
| RP2040 no lugar do PIC | não | não | **não** (só se validar em bancada, `docs/placa-v1.3-rp2040.md`) |
| Estado | gerbers de referência; a original foi encomendada em 2026-11-06 | nada encomendado | nada encomendado |

## O que saiu da v1.2 (D128)

Do projeto da v1.2 de 2026-11-06 (D108) saíram **SW1** (botão de reset), **Q1** (IRF9540N), **R16**, **R17**, **R18**, **D2** (LED verde) e o **FLG3**. A rede `+5V_CART` deixou de existir: SNES, Mega Drive, Si5351, PIC, R2, R15 e os capacitores C2 a C6 ficam no `+5V` do Mega. No cobre, um trilho de 0,8 mm liga onde ficavam o dreno e a fonte do Q1 e uma via ocupa o lugar do pad 1 do R16; o resto do roteamento da v1.2 não mudou. Os pinos **D19** e **RST1** do Mega ficam sem ligação (marcados com "não conectar" no esquemático). Com o firmware padrão o D19 vai a nível baixo no `setup()`; sem o Q1 isso não faz nada.

Script: `tools/16_bits/sem_chave.py` (esquemático e PCB). Verificação: ERC 0 violações; DRC só com os avisos de biblioteca que a v1.2 já tinha (nenhum erro, nenhuma ligação aberta); `python3 tools/check_netlist.py --board 16_bits --sem-troca boards/16_bits/hardware-v1.2/dumper.kicad_sch` confere (79 nets, 275 ligações).

## O que a v1.3 leva (D128)

A v1.2 sem Q1 mais o bloco de troca de cartucho de `docs/bloco-troca.md`, gerado por `tools/troca/` (parâmetros da `16_bits` em `tools/troca/boards.json`): Q1 IRF9540N (chave de alta do 5V, comando no **D19**, nível baixo liga), R16 100 kΩ, R17 100 Ω, R18 1 kΩ e LED verde D15 ("5V dos slots"); Q2 2N7000 e R19 330 Ω (descarga do rail); Q3 2N7000, R20 100 kΩ, R21 1 kΩ, R22 1 kΩ e LED amarelo D16 (sensor do rail, nó `SENSE` ao **D53**). Sem chave física (D123) e sem reset. Firmware: ambiente `SerialASCII_PowerSense` (`firmware/oscr`). O contorno não mudou (108,1 × 86,1 mm). A placa foi **roteada de novo** pelo Freerouting; **revisar no KiCad antes de encomendar**. Nada montado nem testado.

## Como refazer

```
python3 tools/check_netlist.py --board 16_bits                      # v1.3 (hardware/)
python3 tools/check_netlist.py --board 16_bits --sem-troca boards/16_bits/hardware-v1.2/dumper.kicad_sch   # v1.2
HWDIR=hardware-v1.2 GDIR=gerbers-v1.2 tools/export_fab.sh 16_bits v1.2
tools/export_fab.sh 16_bits v1.3
tools/render_board.sh 16_bits v1.0 v1.2 v1.3
```

## TVS (D130)

Pedido do usuário em 2026-11-08: a v1.2 sai sem os 12 TVS 5 V (D3 a D14, que eram DNP); a v1.3 os mantém. Script: `tools/16_bits/sem_tvs.py` (esquemático e PCB; as 10 trilhas e vias que ficaram soltas saíram junto). ERC 0 violações; DRC 0 erros e nenhuma ligação aberta; `python3 tools/check_netlist.py --board 16_bits --sem-troca --sem-tvs boards/16_bits/hardware-v1.2/dumper.kicad_sch` confere (79 nets, 251 ligações).
