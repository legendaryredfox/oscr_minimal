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

Estado: o módulo `shared` e o `desktopApp` **compilam** e os testes passam. A janela **não foi executada** nem testada com a placa (sem hardware nem display aqui). O `jSerialComm` precisa ser conferido em 1.000.000 baud nos três sistemas (CH340 e ATmega16U2). No Linux o usuário precisa estar no grupo `dialout`; no Windows/macOS antigo o CH340 pede driver.
