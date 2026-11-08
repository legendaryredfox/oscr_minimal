# firmware/

| Pasta | O que é |
|---|---|
| `oscr/` | **Firmware atual**: fork do firmware novo do OSCR (`vendor/oscr/firmware`), sem SD, com o laço do protocolo serial em `src/dumper/`. Plano e estado: `docs/referencia/fork-oscr.md`; alterações no upstream: `oscr/README-FORK.md`. |
| `oscr/pc-tests/` | Testes do protocolo no PC (framing, CRC32, sessão, modo MOCK e modo fluxo) e o `sim_stdio` que o teste cruzado do `host/` usa. |
| `arquivo/` | **Arquivado (D76)**: o firmware próprio anterior (`oscr_serial/`, `arduino/`, `platformio/`). Ver `arquivo/README.md`. |

## Compilar e gravar o firmware atual

```
cd firmware/oscr
pio run -e SerialASCII               # compila para o Mega 2560 (o ambiente usa user.ini: só SNES, NES, Mega Drive, GB/GBC/GBA)
pio run -e SerialASCII -t upload     # grava
```

Baud do protocolo: 1.000.000 (`OSCR_DUMPER_BAUD`; para o fallback compile com `-DOSCR_DUMPER_BAUD=115200`). Última medida: 121.722 B de flash (47,9%) e 3.360 B de RAM (41,0%).
**Nunca rodou em hardware.** O firmware do OSCR só roda no AVR; o que dá para testar no PC é o protocolo.

## Testar no PC

```
make -C firmware/oscr/pc-tests test        # 16 verificações do protocolo
python -m pytest host                      # inclui o teste cruzado Python x protocolo em C++ (sim_stdio)
```
