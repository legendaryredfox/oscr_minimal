# gui/ — interface gráfica (Kotlin Multiplatform)

Linux, macOS e Windows. Idiomas: **português (pt-BR), inglês, russo e chinês** (`shared/.../I18n.kt`; inglês é o reserva; novos idiomas: acrescente em `Lang` e uma tabela).

| Módulo | Conteúdo |
|---|---|
| `shared/` | Protocolo v1 (`docs/referencia/protocolo.md`): quadros, CRC32, `OscrClient` (info, detect, dump, save-read, save-write), textos da interface. Código comum, com testes (`gradle :shared:jvmTest`). |
| `cliApp/` | CLI `dumper` (JVM, sem janela) para agentes de IA e scripts. Núcleo em `shared/src/jvmMain/kotlin/oscr/cli/`; mesmo contrato da CLI Python (`docs/referencia/cli.md`). |
| `desktopApp/` | Aplicativo Compose Multiplatform Desktop + porta serial via jSerialComm. |

```
./gradlew :shared:jvmTest        # testes (protocolo, cliente com dispositivo simulado, idiomas)
./gradlew :desktopApp:run        # abre a janela
./gradlew :cliApp:installDist    # CLI em cliApp/build/install/dumper/bin/dumper (--help; --simulate funciona sem placa)
./gradlew :desktopApp:packageDistributionForCurrentOS   # .deb / .dmg / .msi do sistema atual
```

**Placa e firmware (D162):** o campo **Placa ligada** (cartão Conexão) faz o programa conferir o firmware do Arduino ao conectar, gravar o perfil da placa (`BOARD`) e, se faltar suporte, gravar o firmware de `firmware/images/` (gerado por `tools/build_images.py`) depois de um diálogo de confirmação. Lógica em `shared/.../Boards.kt` (espelha `host/oscr_host/boards.py`) e `desktopApp/.../Main.kt` (`applyBoard`, `actBoardConfirmed`). O diálogo e a gravação **não têm teste automático** na GUI; a CLI Kotlin cobre o mesmo plano (`BoardCliTest`). `tools/gui_smoke.sh` abre a janela e confere que não está em branco.

## Como rodar os programas

Todos os comandos abaixo partem da pasta `gui/` (a CLI Python, da pasta `host/`). Quem só quer testar sem placa usa `--simulate` na CLI.

### 1. Antes de tudo

- **Java (JDK) 17 ou mais novo.** O `./gradlew` baixa o resto (Gradle, Kotlin, Compose). A primeira execução baixa as dependências e demora; depois use `--offline` se não quiser rede.
- **Linux:** o usuário precisa estar no grupo `dialout` para abrir a porta serial: `sudo usermod -aG dialout $USER`, depois saia da sessão e entre de novo. **Windows e macOS antigos:** o CH340 do clone do Mega pede driver. Nenhum dos dois sistemas foi testado com a placa.
- **Hardware:** Arduino Mega 2560 com o firmware do fork gravado (item 4). A porta é a USB do Mega; o baud do protocolo é 1.000.000 (as CLIs e a GUI cuidam disso).
- Abrir a porta **reinicia o Mega**; o programa espera cerca de 2,5 s antes de falar. Não é defeito.

### 2. Janela (GUI)

```
./gradlew :desktopApp:run
```

1. Cartão **Conexão**: escolha a porta serial e clique em conectar. A lista tem um botão para recarregar as portas.
2. Campo **Placa ligada**: escolha a placa montada. O programa confere o firmware, grava o perfil da placa e, se faltar suporte, oferece gravar o firmware (pede confirmação antes).
3. Escolha o **sistema** na lista (os de slot direto vêm primeiro; sob "Precisam de adaptador" ficam os que exigem um adaptador entre o cartucho e o slot da placa; no fim, os ainda sem suporte), clique em **Detectar** e depois em ler a ROM ou o save. Sistemas com tamanho que o cartucho não informa pedem o campo de tamanho (KB); o texto de ajuda do sistema aparece acima do campo.
4. O arquivo sai com a extensão certa e o programa mostra o **CRC32** para conferir com o No-Intro. O idioma (pt-BR, en, ru, zh) e o tamanho da fonte ficam em Configurações.

Para ver a janela sem tela (teste automático): `tools/gui_smoke.sh` na raiz do repositório, que precisa de Xvfb, xdotool e ImageMagick.

### 3. CLI Kotlin (`dumper`, sem janela)

```
./gradlew :cliApp:installDist
alias dumper=$PWD/cliApp/build/install/dumper/bin/dumper      # ou chame o caminho completo

dumper --help
dumper --simulate systems                  # lista os sistemas, sem placa
dumper --simulate dump -s mock -o teste    # dump falso, confere o fluxo inteiro
dumper ports                               # portas seriais
dumper info                                # firmware, versão do protocolo, sistemas suportados
dumper detect -s snes                      # lê só o cabeçalho do cartucho
dumper dump -s snes -o jogo                # ROM -> jogo.sfc, mostra o CRC32
dumper save-read -s snes -o jogo           # save
dumper --board 16_bits dump -s md -o jogo  # confere e prepara o firmware da placa antes
```

Sistemas em que o cartucho não diz o tamanho pedem `--prg KB` (por exemplo `dumper dump -s supervision --prg 64 -o jogo`). `dumper systems` mostra as opções de cada um. Com `--json` a saída vira uma linha de JSON e os códigos de saída têm significado fixo: `docs/referencia/cli.md`. Sem `--port` (`-p`), a CLI usa a primeira porta `ttyUSB`, `ttyACM` ou `COM` que achar.

### 4. Gravar o firmware no Arduino

Precisa do `avrdude` no PATH (ou `AVRDUDE=/caminho/avrdude`) e do `.hex`: as imagens prontas ficam em `firmware/images/` (geradas por `python3 tools/build_images.py`) e o fork compila com `cd firmware/oscr && ~/.platformio/penv/bin/pio run -e SerialASCII`.

```
dumper --port /dev/ttyUSB0 firmware-flash --hex ../firmware/images/oscr-0.2.0-completa.hex
```

Na janela, o cartão **Firmware do Arduino** faz o mesmo. Passe a porta com o caminho completo (`/dev/ttyUSB0`): o `avrdude` não abre o nome sem `/dev/`. A gravação é cortada em 300 s se travar.

### 5. CLI Python (`host/`)

```
cd ../host && python3 -m pip install pyserial
python3 dumper.py --simulate detect
python3 dumper.py dump -s snes -o jogo
```

Mesmo contrato da CLI Kotlin. Testes: `cd host && python3 -m pytest -q`.

### 6. Testes e compilação

```
./gradlew --offline :shared:jvmTest :desktopApp:compileKotlin :cliApp:compileKotlin
```

### 7. Se algo der errado

| Sintoma | O que fazer |
|---|---|
| A porta não aparece ou "permission denied" | Grupo `dialout` (Linux) e driver do CH340 (Windows/macOS). `dumper ports` mostra o que o sistema vê. |
| "Dispositivo sem resposta" logo ao conectar | Espere o reinício do Mega (2,5 s) e confira se o firmware é o do fork; reconecte. |
| "Sem cartucho" | Cartucho mal encaixado, slot errado ou sistema errado na lista. Só um cartucho por vez. |
| CRC32 diferente do No-Intro | Leia de novo e compare duas leituras; limpe os contatos do cartucho. |
| O sistema pede tamanho | Informe `--prg` (CLI) ou o campo de tamanho (GUI): o cartucho não informa. |

Roteiro de teste em bancada: `docs/referencia/teste-de-bancada.md`. Guia de uso completo: `docs/referencia/uso.md`.

Estado: o módulo `shared` e o `desktopApp` **compilam** e os testes passam. A janela **não foi executada** nem testada com a placa (sem hardware nem display aqui). O `jSerialComm` precisa ser conferido em 1.000.000 baud nos três sistemas (CH340 e ATmega16U2). No Linux o usuário precisa estar no grupo `dialout`; no Windows/macOS antigo o CH340 pede driver.
