# 16_bits — versões e o que muda entre elas (D128, D130, D138, D139)

Nenhuma versão tem botão de reset nem desligamento do 5V dos slots por software (o bloco de troca de cartucho, D126 a D128, foi retirado em D139: **para trocar o cartucho, desligue o USB**). Cada versão tem o seu projeto KiCad, os seus gerbers, dois PNGs (cima e baixo) e um `README.md` dentro da pasta de hardware.

| | v1.0 | v1.2 | v1.3 |
|---|---|---|---|
| Projeto KiCad | `hardware-v1.0/` | `hardware-v1.2/` | `hardware-v1.3/` |
| Gerbers e zip | `fab/gerbers-v1.0/`, `fab/dumper-v1.0-jlcpcb.zip` | `fab/gerbers-v1.2/`, `fab/dumper-v1.2-jlcpcb.zip` | `fab/gerbers-v1.3/`, `fab/dumper-v1.3-jlcpcb.zip` |
| Lista de peças (CSV) | — | `fab/bom-v1.2.csv` | `fab/bom-v1.3.csv` |
| PNGs | `hardware-v1.0/render-cima.png`, `-baixo.png` | `hardware-v1.2/render-cima.png`, `-baixo.png` | `hardware-v1.3/render-cima.png`, `-baixo.png` (`render.png` = v1.3, de cima) |
| Resistores série (0 Ω) nas 12 linhas de controle (R3 a R14) | não | **não** (retirados em D145) | sim |
| `/CART` no D50, C5, C6, pontos de teste | não | sim | sim |
| Pull-up de `/VRES` (R15, DNP) | não | sim | **não** (D140) |
| TVS 5 V (DNP) nas 12 linhas de controle (D3 a D14) | não | **não** (D130) | **não** (D140) |
| F1 (suporte de fusível 5×20 mm, D138) | sim, acrescentado em 2026-11-09 (D144; a v1.0 encomendada em 2026-11-06 não tem) | sim | sim |
| Seletor de tensão 3,3 V/5 V no slot Mega Drive e J1 (D138); sem resistores em série de 470 Ω (D140) | não | não | sim |
| Botão de reset (SW1) | não | **não** | **não** |
| RP2040 no lugar do PIC | não | não | **não** (só se validar em bancada, `docs/planos/placa-v1.3-rp2040.md`) |
| Estado | a original foi encomendada em 2026-11-06 sem F1; os arquivos agora têm o F1 (D144) | nada encomendado | nada encomendado |

## O que saiu da v1.2 (D128)

Do projeto da v1.2 de 2026-11-06 (D108) saíram **SW1** (botão de reset), **Q1** (IRF9540N), **R16**, **R17**, **R18**, **D2** (LED verde) e o **FLG3**. A rede `+5V_CART` passou a vir direto do 5V do Mega (pelo F1, desde D138): SNES, Mega Drive, Si5351, PIC, R2, R15 e os capacitores C2 a C6. Os pinos **D19** e **RST1** do Mega ficam sem ligação. Script: `tools/boards/16_bits/sem_chave.py`.

## O que a v1.3 leva (D130, D138, D139)

A v1.2 mais o seletor de tensão 3,3 V/5 V do slot Mega Drive (LDO, Q4, Q5, J1; comando no **D18**), sem o R15. Em D138 ela também tinha os 12 TVS (DNP) e as redes de 470 Ω (RN1 a RN5) em série com as linhas do slot Mega Drive; ambos saíram em D140 (`tools/troca/sem_rn.py`, mantendo o roteamento): o foco é proteger o Arduino e o shield, e a tensão que o cartucho aguenta fica por conta do usuário (aviso no silk e nos docs). O bloco de troca que a v1.3 chegou a ter em 2026-11-07 (Q1 a Q3, LEDs, D19, D53) saiu em D139 por `tools/troca/sem_bloco.py`, mantendo o roteamento. Firmware: ambiente `SerialASCII_Volt`. Roteada de novo pelo Freerouting em D140 (DRC sem ligação aberta; as antigas `/A4` e `/D17` fecharam); revisar o layout no KiCad antes de encomendar; nada montado nem testado.

## Como refazer

```
python3 tools/check_netlist.py --board 16_bits                                          # v1.3 (hardware-v1.3/)
python3 tools/check_netlist.py --board 16_bits --sem-tvs boards/16_bits/hardware-v1.2/dumper.kicad_sch   # v1.2
HWDIR=hardware-v1.2 GDIR=gerbers-v1.2 tools/export_fab.sh 16_bits v1.2
tools/export_fab.sh 16_bits v1.3
tools/render_board.sh 16_bits v1.0 v1.2 v1.3
```
