# firmware/

Estado (fase 8, parcial):

- `oscr_serial/`: camada do protocolo serial v1 (docs/protocolo.md) em C++ portátil: framing, CRC32, máquina de estados do dispositivo e `MockBackend` (sem cartucho). Testada no PC: `make -C firmware/oscr_serial test` (16 verificações) e, pelo host, contra o cliente Python (`host/tests/test_firmware_cpp.py`).
- **Ainda não feito:** sketch do Mega (`oscr_mock.ino`) e compilação com `arduino-cli` (núcleo `arduino:avr` já instalado), cópia reduzida do `Cart_Reader` do OSCR (Config.h só com SNES, NES/Famicom, Mega Drive e GBA), e a abstração "sink" que liga a leitura real dos cartuchos ao protocolo. Isso exige o hardware para validar.
