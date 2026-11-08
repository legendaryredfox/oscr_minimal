# tools/historico/pcb_v12 — como a placa `16_bits` v. 1.2 foi alterada (D87)

Registro dos scripts usados em 2026-11-04. O KiCad MCP não tem roteador com folga de cobre, então a placa foi alterada por script do `pcbnew`. **Servem de referência e de ponto de partida; não são uma ferramenta pronta**: as posições (C5, C6, fileira dos pontos de teste) estão fixas para a placa v1.0 e os scripts adicionam as peças, então rodá-los de novo na v. 1.2 duplicaria tudo.

Ambiente: o Python do venv do KiCad MCP (`~/development/llms/KiCAD-MCP-Server/.venv/bin/python`, com `pcbnew`, `numpy` e `scipy`). O primeiro argumento de cada script é ignorado (deixe `.`); os demais estão no começo de cada arquivo.

| Arquivo | O que faz |
|---|---|
| `pcbgrid.py` | Mapa de obstáculos em grade de 0,1 mm por camada (trilhas, pads, vias), distâncias por EDT, folga de 0,2 mm mais margem, roteador A* de duas camadas com vias, Dijkstra a partir de uma rede. |
| `pcbops.py` | Adiciona footprints (ligados ao símbolo do esquemático pelo uuid) e converte um caminho do roteador em trilhas e vias. |
| `sch_v12.py` | Edição de texto do esquemático: símbolo `Connector:TestPoint` embutido, C5, C6, TP1 a TP6 e rótulos. O `/CART` e a troca de `Value` e `in_bom` dos TPs foram feitos à parte (ver D87). |
| `findcap3.py` | Busca de lugar livre para um capacitor de 100 nF perto de um pino (pads livres, patio, pinos e textos de silk, distância de roteamento até o 5V). |
| `stage1.py` | C5 e C6 e a ligação de 5V de cada um. |
| `stage2.py` | `/CART`: nets novas e rota de B32 do MD1 até o D50 do Mega. |
| `stage3d.py` | Pontos de teste: escolhe a fileira e a ordem com menor soma de trilha e roteia. |

Depois de cada etapa: `python3 tools/fill_zones.py <placa>` (as zonas) e `kicad-cli pcb drc --schematic-parity` (o DRC tem que ficar igual ao da v1.0: 3 `starved_thermal` e 5 avisos de biblioteca justificados em D71).

Lições: (1) a grade de 0,1 mm erra até 0,06 mm, então a margem de folga tem que ser maior que isso (um pad ficou a 0,146 mm de uma trilha com a margem de 0,02 mm); (2) o destino do roteador tem que ser o centro do pad, não o retângulo dele (uma trilha parou na quina do pad D50); (3) corpo de peça THT não pode cobrir pino de outra peça (o C5 caiu em cima do pino A13 do Mega).
