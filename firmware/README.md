# firmware/

| Pasta | O que é |
|---|---|
| `oscr_serial/` | Biblioteca do protocolo serial v1 (`docs/protocolo.md`): framing, CRC32, máquina de estados, `MockBackend` e a cola Arduino (`oscr_arduino.h`). C++ portátil, testada no PC. |
| `arduino/oscr_dumper/` | Projeto **Arduino** (Mega 2560). |
| `platformio/` | Projeto **PlatformIO** (`megaatmega2560`), mesmo código. |

Os dois projetos usam a mesma biblioteca `oscr_serial`. O padrão lê os cartuchos reais (SNES, NES/Famicom, Mega Drive, GBA); para o **modo de teste** (dados sintéticos, sem cartucho) compile com `-DOSCR_MOCK` (PlatformIO: ambiente `megaatmega2560_mock`; arduino-cli: `--build-property build.extra_flags=-DOSCR_MOCK`).

## Compilar

```
# Arduino (arduino-cli, núcleo arduino:avr)
arduino-cli compile --fqbn arduino:avr:mega --library firmware/oscr_serial firmware/arduino/oscr_dumper
arduino-cli upload  -p /dev/ttyUSB0 --fqbn arduino:avr:mega firmware/arduino/oscr_dumper

# PlatformIO
cd firmware/platformio && pio run && pio run -t upload
```

Na IDE do Arduino: copie `firmware/oscr_serial` para a pasta de bibliotecas e abra `arduino/oscr_dumper/oscr_dumper.ino`.
Baud: 1.000.000 (padrão); para o fallback use `-DOSCR_BAUD=115200` (PlatformIO: `build_flags`).
Tamanho medido no Mega 2560: real 12,9 KB de flash (5 %) e 1,6 KB de RAM (19 %); modo de teste 8,6 KB e 1,4 KB.

## Testar no PC

```
make -C firmware/oscr_serial test          # 16 verificações do protocolo + 98 de cartuchos simulados (inclui mappers de NES)
python -m pytest host                      # inclui o teste cruzado Python x firmware C++
```

## Como a leitura dos cartuchos foi feita

Não há tela, SD, RTC nem outros consoles: o firmware tem só o que o dumper usa.

- `oscr_bus.h`: interfaces de barramento por sistema (`SnesBus`, `NesBus`, `MdBus`, `GbaBus`).
- `oscr_carts.cpp`: `CartBackend`, a lógica de cabeçalhos, tamanhos, mapeamento de endereços e SRAM. Testada no PC (`tests/test_carts.cpp`) com cartuchos simulados.
- `oscr_avr_buses.h`: HAL do ATmega2560, com as sequências de porta/bit do OSCR (`SNES.ino`, `NES.ino`, `MD.ino`, `GBA.ino`, GPL v3), conferidas com `docs/pinmap.md`.

**Não validado em hardware** (sem cartuchos nem placa). Roteiro de validação: `docs/uso.md`, seção 7.
Decisão: o `Cart_Reader` do OSCR (um monolito de menus de ~3.800 linhas com ~280 usos do SD) **não** foi copiado nem adaptado; só serviu de referência (`vendor/`, fora do git). Detalhes em `docs/decisoes.md` (D38).
