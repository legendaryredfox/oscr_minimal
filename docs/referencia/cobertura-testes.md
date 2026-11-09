# Cobertura de testes (medida em 2026-11-08, D137)

Números medidos nesta data, depois de ligar o Master System, o Game Gear e o SG-1000. **Cobertura de linhas não é prova de que funciona:** nenhum teste abaixo toca o cartucho. O que depende de hardware está na seção 5.

## 1. Resumo

| Parte | Testes | Cobertura de linhas | Como medir |
|---|---|---|---|
| Host Python (`host/oscr_host`) | 224 (pytest) | **90 %** (2320 linhas, 238 sem cobertura) | `cd host && python3 -m pytest -q --cov=oscr_host --cov-report=term` (precisa do `pytest-cov`) |
| Kotlin compartilhado (`gui/shared`: protocolo, cliente, CLI, banco, regras) | 131 (`jvmTest`) | **91,7 %** das linhas (2673 de 2914), **65,3 %** dos ramos (1661 de 2542) | ver seção 3 |
| GUI (`gui/desktopApp`, Compose) | 0 testes automáticos; só compila | não medida | abrir a janela (display virtual, ver `docs/continuacao.md` seção 0.4) |
| Firmware nos núcleos do OSCR e no `Dumper.cpp` | **nenhum teste no PC** | 0 % medido | só roda no AVR |

## 2. Python (por módulo)

Pior cobertura: `cli/__main__.py` 0 % (só a linha de entrada), `cli/ui.py` 76 % (cores e arte ASCII em terminal interativo), `cli/common.py` 76 %, `transport.py` 77 % (porta serial real), `cmd_flash.py` 81 %, `cmd_rom.py` 84 %, `output.py` 83 %. Acima de 95 %: `parser.py`, `romimage.py`, `database.py`, `protocol.py`, `cmd_db.py`, `cmd_power.py`, `errors.py`. O que o simulador (`sim.py`) não cobre de propósito: sistemas reais (ele só responde ao `MOCK`), gravação de flash, leitura de porta real.

## 3. Kotlin

Medido com o JaCoCo do cache do Gradle, por um *init script* fora do repositório (não há plugin de cobertura nos `build.gradle.kts`; nada foi acrescentado ao projeto):

```
./gradlew --offline --init-script jacoco.init.gradle :shared:cleanJvmTest :shared:jacocoReport
```

(o script aplica o plugin `jacoco` ao módulo `:shared`, liga o agente em todo `Test` e registra uma tarefa `jacocoReport` sobre `build/classes/kotlin/jvm/main`; relatório CSV/XML em `shared/build/reports/jacoco/`).

| Pacote | Linhas | Ramos |
|---|---|---|
| `oscr` (protocolo, cliente, regras, banco, I18n) | 97,2 % (2026 de 2085) | 72,8 % (959 de 1317) |
| `oscr.cli` (CLI Kotlin) | 78,0 % (647 de 829) | 57,3 % (702 de 1225) |

Menor cobertura por classe (linhas cobertas / total): `ImageMsg` 11/43, `CmdFlash` 49/89, `CmdDump` 37/66, `FirmwareFlash` 22/34 (o avrdude de verdade; os testes usam um falso), `CmdRom` 41/53, `Cli` 37/46, `Ui` 63/74. O `desktopApp` (`Main.kt`) e a ponte serial (`SerialTransport.kt`, jSerialComm) não entram na medida.

## 4. Firmware em C++ no PC

| Programa | Verificações | O que cobre |
|---|---|---|
| `test_proto` | 36 | quadros, CRC32, sessão (modo MOCK e modo fluxo), `oscr_session.cpp` |
| `test_mdflash` | 734 | `MdFlashCore.h` contra um modelo de chip de flash de Mega Drive |
| `test_snes_plan` | 21 | `SnesPlan.h`: plano de gravação do CFI de 1, 2 ou 4 chips |
| `test_sms` | 28 | `SmsCore.h` (D137): slot vazio, cabeçalho "TMR SEGA", Fantasy Zone, tamanhos, adaptadores Retrode/Retron/Raphnet |

Medida: `g++ -std=c++17 --coverage -O0` em cada teste e `gcov` nos cabeçalhos `include/dumper/*.h` e `src/dumper/oscr_*.cpp`. O `oscr_session.cpp` aparece com 50,7 % porque o `test_proto` só exercita parte dele; o resto roda pelo `host/tests/test_firmware_cpp.py` (o cliente Python contra o C++ real, via `sim_stdio`), que **não entra** nesse número.

## 5. O que nenhum teste cobre

1. **Todo o acesso ao cartucho:** as sequências de porta dos núcleos do OSCR (`SNES.cpp`, `NES.cpp`, `MegaDrive.cpp`, `GameBoy*.cpp`, `SMS.cpp`, `Flash.cpp`), o `Dumper.cpp` (a costura com o protocolo, incluindo a escolha do adaptador do SMS) e as rotinas de gravação de flash (`NesFlash`, `SnesFlash`, `MdFlash`, `GbaFlash`, `GbFlash`, `FlashProg`). Compilam para o AVR (`pio run -e SerialASCII`), mas só rodam em hardware.
2. **Tempos e tensões:** limites de tempo dos laços, descarga do rail, 5 V e 3,3 V nos slots.
3. **Porta serial real** a 1.000.000 baud (Linux, macOS e Windows), `avrdude` real, GUI aberta de verdade.
4. **Traduções ru e zh** (revisão nativa) e leitor de tela.
5. **Placas:** nada montado; ERC, DRC e `check_netlist.py` conferem o desenho, não a placa física.

## 6. Como melhorar

- Mover mais lógica do `Dumper.cpp` para cabeçalhos puros (como `SmsCore.h` e `SnesPlan.h`) para testá-la no PC.
- Testes da GUI (`desktopApp`) com um backend simulado.
- Pôr a medida de cobertura no CI (hoje o CI do GitHub falha por cobrança, não por código).
- Primeiro teste em hardware: `docs/referencia/uso.md`, seção 7.
