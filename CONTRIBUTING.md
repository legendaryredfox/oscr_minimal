# Como contribuir

Obrigado pelo interesse. O projeto é pequeno e o que mais falta é **teste com hardware real**.

## O que ajuda mais

1. **Testar uma placa ou o firmware com cartuchos reais** e contar o resultado (abra uma issue com o modelo "Teste em hardware": placa, versão, cartucho, o que funcionou, logs). Nenhuma placa foi montada até hoje.
2. Revisar os layouts no KiCad (`boards/<placa>/hardware/`): as placas de um sistema só foram roteadas por autoroteador e não foram revisadas à mão.
3. Conferir medidas dos slots e módulos com as peças reais (`docs/decisoes.md`, D17, D23, D27).
4. Revisar traduções da GUI (ru, zh) e a documentação.

## Antes de abrir um pull request

- **Pinagem:** cada sinal de cada slot tem de ir ao mesmo pino do Mega que no OSCR HW5 (`CLAUDE.md`, seção 3). Mudanças de pinagem precisam de justificativa em `docs/decisoes.md`.
- **Hardware:** rode `python3 tools/check_netlist.py --board <placa>`, o ERC e o DRC (comandos no `README.md`) e inclua o resultado. Não commite gerbers de uma placa sem rodar `tools/export_fab.sh`.
- **Firmware e host:** `make -C firmware/oscr/pc-tests test`, `cd host && python3 -m pytest -q` e, para a GUI, `cd gui && ./gradlew :shared:jvmTest :desktopApp:compileKotlin :cliApp:compileKotlin`.
- **Código do OSCR:** reaproveite as funções do upstream em vez de reescrevê-las; o código próprio fica nas costuras (`firmware/oscr/src/dumper/`). Se divergir, explique em `docs/decisoes.md`.
- **Mudanças pequenas e localizadas.** Textos do projeto em português do Brasil; a GUI tem pt-BR, en, ru e zh.

## Licenças

Hardware: **CC BY 4.0**. Software: **GPL v3 ou posterior** (`LICENSE.md`). Ao contribuir, você concorda em licenciar sua contribuição assim e a mantém com a atribuição ao OSCR. Não envie ROMs, BIOS, chaves nem arquivos protegidos por direitos autorais de terceiros.

## Segurança

Para falha de segurança, ou defeito de hardware que possa **danificar um cartucho ou o Arduino** (nível de tensão, curto), use uma issue (sem dados pessoais) ou escreva ao mantenedor pelo perfil do GitHub. Dê a versão da placa e do firmware.
