# Empacotamento da GUI (H-6 e H-7)

O instalador da GUI leva junto as imagens do firmware e, se você colocar, o avrdude, para o `firmware-flash` e a troca automática pela placa (D162) funcionarem sem PlatformIO instalado.

## O que entra no instalador

| Arquivo | Origem | Como entra |
|---|---|---|
| `firmware/manifest.tsv` e `firmware/*.hex` | `firmware/images/`, gerada por `python3 tools/build_images.py` (a pasta é gitignored; rode antes de empacotar) | tarefa Gradle `bundleFirmwareAndAvrdude`, ligada à `prepareAppResources` do Compose |
| `avrdude/avrdude` ou `avrdude/avrdude.exe` | **você coloca** em `gui/desktopApp/avrdude/<sistema>/avrdude[.exe]`, com `<sistema>` = `linux-x64`, `macos-arm64`, `macos-x64` ou `windows-x64` (pasta gitignored) | mesma tarefa, para a pasta do sistema |

O projeto não baixa o avrdude: é binário de terceiros por sistema (GPL v2 ou posterior, compatível com o projeto, mas a escolha da versão e da fonte é sua). Sem o arquivo o instalador sai igual e a gravação cai nos caminhos de sempre.

## Como o programa instalado procura

O Compose define `compose.application.resources.dir` no programa instalado (conferido no `.cfg` do `.deb`). Em `AppResources.kt`:

- **Imagens do firmware** (`BoardPlanner.imageDir`): `--firmware-dir` > `OSCR_FIRMWARE_DIR` > `firmware/` do instalador > `firmware/images` da pasta do projeto, subindo da pasta atual.
- **`.hex` do `firmware-flash` sem `--hex`** (`FirmwareFlash.findHex`): `--hex` > `OSCR_FIRMWARE_HEX` > compilação do projeto (`.pio/build/...`) > imagem do instalador que cobre mais sistemas.
- **avrdude** (`FirmwareFlash.findAvrdude`): `--avrdude` > `AVRDUDE` > o do instalador > PATH > PlatformIO.

Fora do programa instalado (CLI Kotlin, `gradlew run`, testes, CLI Python) a propriedade não existe e nada muda. A CLI Python não é empacotada.

## Gerar os pacotes

```
python3 tools/build_images.py          # as imagens (firmware/images/)
cd gui && ./gradlew :desktopApp:packageDeb      # build/compose/binaries/main/deb/oscr-dumper_<versão>_amd64.deb
```

- **`.deb`: gerado e inspecionado aqui** (2026-11-15; cerca de 60 MB, com o JRE embutido; o `.hex` e o `manifest.tsv` estão em `/opt/oscr-dumper/lib/app/resources/firmware/`). **Nunca instalado nem aberto** numa máquina limpa. Precisa de rede na primeira vez (o `--offline` falha no `checkRuntime`). O Compose não deixa acrescentar `Depends:`: sem o avrdude embutido, o usuário instala `sudo apt install avrdude`.
- **`.dmg` e `.msi`: só em runner macOS e Windows** (`packageDmg`, `packageMsi`). Receita pronta no `build.gradle.kts`, **não testada**; falta CI (D-D).
- **AppImage:** o Compose não gera. Receita proposta, **não feita nem testada**: `createDistributable`, empacotar `build/compose/binaries/main/app/oscr-dumper` com o `appimagetool`.
- Linux: o usuário precisa estar no grupo `dialout` para abrir a porta serial.
