# Mega Drive: o que o firmware trata e o que não (D-5, P-09)

Conferido em 2026-11-15 lendo `firmware/oscr/src/cores/MegaDrive.cpp` (o do fork, igual ao upstream `d9cb26a` nesta parte; o upstream atual só refatorou tipos, ver `docs/historico/upstream-oscr-firmware-2026-11-15.md`) contra os relatos da pesquisa (`docs/historico/pesquisa-comunidade.md`, P-09: posts 857 a 860 do fórum do Arduino). **Só leitura do código; nada foi testado com cartucho.**

| Relato (P-09) | Situação no código | Onde |
|---|---|---|
| EEPROM serial identificada pelo checksum do cabeçalho (0x18E) | **Tratado:** tabela `eepid` com **38 checksums** (3 Acclaim tipo 1, 9 tipo 2, 2 Capcom, 10 Sega, 7 EA, 7 Codemasters) e o tipo e o tamanho de cada um | `MegaDrive.cpp` linhas 49 a 94 e 1111 a 1123 |
| Acclaim "tipo 2" tem PAL antes da EEPROM e exige init | **Tratado como tipo próprio** (`eepType` 2, com `writeWord_SDA` e `writeWord_SCL` separados). Não conferi se a sequência de init cobre o PAL em todos os jogos; só o código existe | `EepromReadData`, `EepromWriteData`, tipo 2 |
| Codemasters usa PAL e precisa de CLK (o shield do autor do relato não tinha o pino CLK) | **Tratado:** tipo 5 com `writeWord_CM` e leitura em `0x1C0000`. **Nossas placas ligam o CLK:** o pino B19 do slot (VCLK) vai ao D16 (PH1) no `pinmap.md`, o mesmo pino do OSCR HW5, e o firmware dá os pulsos de CLK (`pulse_clock`) | `MegaDrive.cpp` ~2430; `boards/*/docs/pinmap.md`, seção Mega Drive |
| Vários Codemasters repetem o checksum do Micro Machines 96; separar pelo primeiro DWORD | **Tratado** para os checksums `0x165E` e `0x168B`: lê a palavra em 0x00 e, se não for `0x444E` (início de `0x444E4C44`), trata como sem EEPROM. **Não tratado:** `0x7E50` (Micro Machines 2) está na tabela sem essa checagem, e o código só corrige o tamanho dele quando `cartSize` vale 0x20000 | `MegaDrive.cpp` 1137 a 1150 e 911 a 920 |
| Só as versões J-Cart do Micro Machines têm EEPROM serial | **Tratado pela tabela:** os três Micro Machines da tabela são "(J-Cart)". Uma versão sem J-Cart com o mesmo checksum é distinguida só pela checagem do DWORD acima (e só para dois dos três checksums) | tabela `eepid` |
| EEPROM só em cartuchos originais; repro não tem | **Não tratado:** o firmware não distingue original de repro. Um repro com o mesmo cabeçalho (checksum) de um jogo da tabela é lido como se tivesse EEPROM, e o resultado é lixo ou erro de leitura. O usuário precisa saber qual cartucho tem | sem código |
| NBA Jam Tournament Edition rev 0 apaga o próprio save | **Sem proteção:** o jogo está na tabela como Acclaim tipo 2 (`0xCC3F`) e o firmware lê e grava normalmente. A advertência é do relato; o código não avisa. Faça backup antes de gravar | sem código |
| 32X lê como cartucho comum | **Tratado por omissão:** nenhum caminho especial; os dois NBA Jam / NFL 32X da tabela têm EEPROM | tabela `eepid` |
| Sega CD (disco) | **Fora de escopo.** Só o cartucho de RAM de backup (`bramSize`, 128 KB e 512 KB) é lido | `MegaDrive.cpp` "CD Backup RAM" |

## O que isso pede do projeto

- Aviso na GUI e na CLI de que a EEPROM do Mega Drive só vale em original e de que o NBA Jam TE rev 0 pode apagar o save: **não feito** (decisão do usuário; vai para `docs/planos` se quiser).
- O caminho de Codemasters depende do CLK (PH1): confira na montagem que o pino B19 do slot tem continuidade com o D16 do Mega.
