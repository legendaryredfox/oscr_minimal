# firmware/arquivo/ — firmware próprio arquivado (D76)

O firmware que escrevi antes do fork do OSCR (D38). **Não evolui mais**: o firmware do projeto é `firmware/oscr/` (D65). Fica aqui para consulta e porque ainda compila e passa nos testes.

| Pasta | O que é |
|---|---|
| `oscr_serial/` | Biblioteca C++ portátil: protocolo, `CartBackend` (SNES, NES, Mega Drive, GBA, GB/GBC), HAL do AVR e cartuchos simulados. Testes: `make -C firmware/arquivo/oscr_serial test` (16 do protocolo + 19 do Si5351 + 41 do HAL do AVR + 990 de cartuchos simulados). |
| `arduino/oscr_dumper/` | Sketch Arduino que usa a biblioteca. |
| `platformio/` | Projeto PlatformIO equivalente. |

Para que serve ainda:
- **Referência de lógica**: as tabelas de mappers do NES, cabeçalhos, tamanhos e protocolos seriais do Mega Drive e do GBA estão em `oscr_serial/oscr_carts_*.cpp`, com testes por cartucho simulado. Úteis para conferir o que o fork faz.
- **Comparação em hardware**: se o fork falhar num cartucho, dá para gravar este firmware (`arduino-cli compile --fqbn arduino:avr:mega --library firmware/arquivo/oscr_serial firmware/arquivo/arduino/oscr_dumper`) e ver se o problema é do fork ou da placa.

O protocolo serial é o mesmo (`docs/protocolo.md`); o `host/` e a `gui/` falam com os dois.
