# firmware/

| Pasta | O que é |
|---|---|
| `oscr_serial/` | Biblioteca do protocolo serial v1 (`docs/protocolo.md`): framing, CRC32, máquina de estados, `MockBackend` e a cola Arduino (`oscr_arduino.h`). C++ portátil, testada no PC. |
| `arduino/oscr_dumper/` | Projeto **Arduino** (Mega 2560). |
| `platformio/` | Projeto **PlatformIO** (`megaatmega2560`), mesmo código. |

Os dois projetos usam a mesma biblioteca `oscr_serial` e hoje rodam em **modo MOCK** (dados sintéticos, sem cartucho).

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
Resultado medido (modo MOCK, Mega 2560): 8,6 KB de flash (3 %), 1,4 KB de RAM (17 %).

## Testar no PC

```
make -C firmware/oscr_serial test          # 16 verificações C++
python -m pytest host                      # inclui o teste cruzado Python x firmware C++
```

## O que falta

- Cópia reduzida do `Cart_Reader` do OSCR (Config.h só com SNES, NES/Famicom, Mega Drive, GBA e Si5351) e a ponte ("sink") entre a leitura real dos cartuchos e o protocolo (`Backend` por sistema). O código do OSCR usa o `myFile` do SdFat em ~280 pontos nos 4 sistemas; precisa de cuidado e de hardware para validar.
