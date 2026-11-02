# gui/ — interface gráfica (Kotlin Multiplatform)

Linux, macOS e Windows. Idiomas: **português (pt-BR) e inglês** (`shared/.../I18n.kt`; inglês é o reserva; novos idiomas: acrescente em `Lang` e uma tabela).

| Módulo | Conteúdo |
|---|---|
| `shared/` | Protocolo v1 (`docs/protocolo.md`): quadros, CRC32, `OscrClient` (info, detect, dump, save-read, save-write), textos da interface. Código comum, com testes (`gradle :shared:jvmTest`). |
| `desktopApp/` | Aplicativo Compose Multiplatform Desktop + porta serial via jSerialComm. |

```
./gradlew :shared:jvmTest        # testes (protocolo, cliente com dispositivo simulado, idiomas)
./gradlew :desktopApp:run        # abre a janela
./gradlew :desktopApp:packageDistributionForCurrentOS   # .deb / .dmg / .msi do sistema atual
```

Estado: o módulo `shared` e o `desktopApp` **compilam** e os testes passam. A janela **não foi executada** nem testada com a placa (sem hardware nem display aqui). O `jSerialComm` precisa ser conferido em 1.000.000 baud nos três sistemas (CH340 e ATmega16U2). No Linux o usuário precisa estar no grupo `dialout`; no Windows/macOS antigo o CH340 pede driver.
