# Melhorias para o suporte a Mega Drive (vindas do md_rewriter)

Origem: levantamento feito em 2026-11-04 no projeto `md_rewriter` (dumper STM32F103 de Mega Drive, repositório irmão em `~/development/hardware/md_rewriter`) sobre a família **KY Technology / FlashKit MD** e sobre os repositórios de referência de programadores de Mega Drive. Aqui está só o que serve ao `oscr_minimal`. Nada neste arquivo foi implementado nem testado em cartucho.

Os arquivos de origem, para quem quiser detalhe (em `md_rewriter`): `docs/KY_SUPPORT.md`, `docs/CART_SUPPORT.md`, `docs/HARDWARE_REVIEW.md`, `docs/NEW_FIRMWARE_SPEC.md`, `references/ky_technology/REPORT.md` e `RESEARCH.md`. Clones usados: MD_Dumper, FlashKit-MD-Plus, flashkit-md-py, fkmd, MD-Flash-Cart-4MB, open-ed (em `md_rewriter/references/repos/`).

Atualização 2026-11-13: a primeira bancada do `md_rewriter` com cartuchos reais (S29GL064N com setor uniforme e com setores de 8 KiB, ROM de máscara) está em `docs/referencia/megadrive-bancada-md-rewriter.md` (D154). Mostra que ID e CFI não dão o layout dos setores e que o apagamento acima de 2 MiB falhou nos dois cartuchos de flash.

## 1. O que o `oscr_minimal` já tem para Mega Drive (verificado no código)

| Área | Estado | Onde |
|---|---|---|
| Leitura de ROM, SSF2 (`writeSSF2Map`), Sonic & Knuckles lock-on, SVP (Virtua Racing), ROM de até 16 MB | já vem do OSCR | `cores/MegaDrive.cpp` |
| Save: SRAM e EEPROM serial (tabela `eepid`, `readEEP`/`writeEEP`) | já vem do OSCR | `cores/MegaDrive.cpp` |
| `/UWR` (D7) e `/CAS2` (D3) ligados ao Mega | sim, na placa | `boards/16_bits/docs/pinmap.md` (B29, B21) |
| Gravação em flash repro | **2 chips**: MX29F1610 (`C2F1`, 2 MB) e S29GL064N (`017E`, 4 MB) | `firmware/oscr/src/dumper/MdFlash.cpp` |
| Limites da gravação | tamanho ≤ 4 MiB; laços de espera do OSCR sem limite de tempo (`busyCheck`, status do `write29GL`) | `MdFlash.cpp`, cabeçalho do arquivo |

## 2. Lacuna principal: chips de cartuchos KY / FlashKit

O cartucho FlashKit MD usa flash AMD série 29W de 32 Mbit (nos cartuchos KY, um CI com logotipo ST, modelo exato desconhecido). Hoje o `MdFlash::prepare` devolve `E_FLASH` para qualquer ID fora de `C2F1` e `017E`. Chips que faltam, com o conjunto de comandos e o que do OSCR já existe para reaproveitar:

| Chip | ID (fab, dispositivo) | Tamanho | Comandos | Reaproveitamento no OSCR |
|---|---|---|---|---|
| M29W320DT/DB, M29W320ET/EB (ST) | 20 CA / CB / 56 / 57 | 4 MiB | AMD, desbloqueio 555h/2AAh | `write29GL` usa o buffer de escrita (`25h`/`29h`), que o M29W320 não tem: precisa do laço por palavra com `A0h`, como o `write29F1610` mas com 555h/2AAh |
| MX29LV320T/B (Macronix) | C2 A7 / A8 | 4 MiB | AMD 555h/2AAh | `Flash.cpp` já trata `C2A7`/`C2A8` com `writeFlash16_29LV640` (linha ~389) |
| MX29L3211 (Macronix) | C2 F9 | 4 MiB | AMD com desbloqueio **5555h/2AAAh**, programação de página de 128 palavras, sem unlock bypass | mesma sequência de endereços do `write29F1610` do `MegaDrive.cpp` (que já usa 5555h/2AAAh); só muda ID e tamanho |
| Intel PA28F400T/B | 89 70 / 89 71 | 512 KiB | Intel/Sharp: `FFh` reset, `90h` ID, `40h` programa, `20h`+`D0h` apaga bloco, status bit 7 | `eraseFlash28FXXX`, `writeFlash28FXXX`, `idFlash28FXXX` do `Flash.cpp` (J3A e LH28F0XX): conferir se servem para o PA28F400 (x16, 4 Mbit) |
| Sharp LH28F320BJE | B0 E3 | 4 MiB | família Intel/Sharp | `IC_LH28F0XX` do `Flash.cpp` |
| M29W640DB/DT/G, MX29LV640EB/ET, SST39VF6401B/6402B | 20 DF/DE/7E, C2 CB/C9, BF 6D/6C | 8 MiB | AMD 555h | `writeFlash29LV640`; o limite de 4 MiB do `check` precisa subir para 8 MiB |
| SST39VF3201/3202 | BF 5B / 5A | 4 MiB | AMD 555h, mas `30h` apaga só **2 KWord**; o bloco de 32 KWord é `50h` | não existe; erase por bloco com `50h` |
| MX26L6420 (cartucho de 8 MByte) | C2 FC | 8 MiB | | `/CE` acima de 4 MiB: conferir a decodificação do cartucho |

IDs vêm do `flashlist.csv` do MD_Dumper e de datasheets lembrados de memória: **confirmar em chip real** antes de marcar como confirmado. No `md_rewriter` só o MX29LV640EB foi confirmado (firmware 1.0 publicado).

## 3. Lições do `md_rewriter` que valem aqui

1. **Detectar o conjunto de comandos antes de gravar.** Ordem usada lá: ID com desbloqueio 555h; se o ID não está na tabela, 5555h; depois Intel. Um chip desconhecido fica no 555h. Chip já conhecido gasta os mesmos ciclos de barramento de antes.
2. **Esperar o fim de cada palavra com DQ7 (polling) e com limite de tempo**, nunca só com atraso fixo. Em 4 MiB, uma palavra perdida sem aviso só aparece na conferência. O `md_rewriter` responde `WRITE TIMEOUT` e para; o OSCR hoje trava até o PC desistir (limite já registrado em `MdFlash.cpp`).
3. **Apagamento de chip com boot sectors.** Em chip *top boot* (M29W320DT/ET, MX29LV320T) os últimos 64 KiB são **oito setores de 8 KiB**: um só `30h` apaga um deles, e uma ROM de 4 MiB alcança essa região. O mesmo vale para o início em chip *bottom boot*. Passos por 64 KiB deixam sujeira e a gravação falha depois (0 → 1).
4. **`30h` não é igual em toda SST.** Nas SST39VF6401B/6402B `30h` é Block-Erase (32 KWord); na família VF160 e provavelmente nas 3201/3202, `30h` é Sector-Erase (2 KWord) e o bloco é `50h`.
5. **Intel não tem apagar chip inteiro.** Apaga-se bloco a bloco; mapa do 28F400 (memória, **conferir no datasheet**): 16 KB, 8 KB, 8 KB, 96 KB, 3 × 128 KB (boot embaixo no -B, em cima no -T). Terminar toda operação com `FFh` para o chip voltar a ler como memória; senão a leitura devolve status.
6. **Conferir sempre lendo de volta.** Já é o desenho do `oscr_minimal` (`DUMP_ROM` depois do `WRITE_ROM`); manter, e não aceitar ROM menor que o necessário sem avisar.
7. **Sondagem escreve no cartucho.** Em cartucho que não é flash (ROM de máscara, mapeador) as escritas de sondagem são ignoradas, mas nunca foi conferido num mapeador real. Os registradores de mapeador do SSF2 ficam em `A130F1h`..`A130FFh`, do Open EverDrive em `A130E0h` e `A13000h`; as sondagens ficam longe deles.

## 4. Hardware (placa Mega 2560 de 5 V): o que da revisão do md_rewriter se aplica

> Adiado por decisão do usuário (2026-11-04): o detalhamento, a numeração (HW-MD-1 a HW-MD-8), os critérios e a ordem estão em `docs/planos/melhorias-megadrive-hardware.md`. Nenhuma mudança de hardware será feita agora.

Itens da revisão do PCB V1.0 do `md_rewriter` e o que cada um significa para o shield:

| Achado no md_rewriter | No `oscr_minimal` |
|---|---|
| H1 (USB-C sem Rd), H2–H4 (dados do projeto), M4/M5 (SWD, BOOT0), F1/LDO, cristal | não se aplicam: USB, alimentação e programação são do Arduino Mega |
| L2: `/UWR` e `/CAS2` não ligados | já ligados (D7, D3); permite escrita de palavra real nos dois bytes e seleção de EEPROM/SRAM em `200000h`–`3FFFFFh` |
| L3: MCU de 3,3 V falando com cartucho de 5 V | não existe: o Mega é 5 V; VCC do slot em 5 V direto (regra da decisão de projeto) |
| M3: sem resistor série nem ESD nas linhas do cartucho (~50 linhas) | **vale**: o shield liga as linhas direto aos pinos do Mega. Considerar resistores série de 33–100 Ω (conferir tempos do OSCR) e um conjunto de diodos TVS; é melhoria opcional de fabricação, não de firmware |
| M6: sem desacoplamento junto aos 5 V do slot | o shield já tem 100 nF por slot e 470 µF na entrada (CLAUDE.md, seção 4); conferir que o do slot MD fica a menos de 10 mm dos pinos A2/A31 |
| Open EverDrive exige pull-up de 10 kΩ em `/VRES` (pino B27 do cartucho) do programador | **conferir**: `/VRES` está em D17 (PH0), compartilhado com `/MRES` na tabela do pinmap. Sem o pull-up, programar o menu do Open-ED pode falhar |
| Master System / Game Gear exigem outro conector | fora da placa 16_bits; entra no esqueleto `8_bits/` |

## 5. Melhorias propostas, em ordem de valor

| # | Melhoria | Critério de aceitação |
|---|---|---|
| MD-1 | `MdFlash`: tabela de chips com ID, tamanho, conjunto de comandos e layout de boot; trocar o `if` de dois IDs | `DETECT` nomeia os chips da seção 2; os dois chips atuais seguem iguais byte a byte no barramento |
| MD-2 | Chips AMD 555h de 32 e 64 Mbit (M29W320, MX29LV320, M29W640, MX29LV640, SST6401B): reusar `write29GL`/`writeFlash16_29LV640`; subir o limite de tamanho para 8 MiB | gravação e leitura de volta idênticas em cartucho real; teste no PC com modelo de chip |
| MD-3 | MX29L3211 (5555h): reusar a sequência do `write29F1610` | idem; apagar por setor com o desbloqueio certo |
| MD-4 | Apagamento por layout (top e bottom boot em oito setores de 8 KiB) em vez de passos de 64 KiB | ROM de 4 MiB grava sem `WRITE TIMEOUT` em M29W320DT/ET |
| MD-5 | Limite de tempo em `busyCheck` e no status do `write29GL` (hoje sem limite) | chip com defeito ou cartucho de ROM de máscara devolve erro em segundos |
| MD-6 | Intel PA28F400 e Sharp LH28F320BJE via `Flash.cpp` (família 28FXXX) | confirmar o mapa de blocos no datasheet antes; cartucho de código-cracker ou equivalente |
| MD-7 | SST39VF3201/3202: apagar por bloco com `50h` | |
| MD-8 | Teste no PC com modelo de chip (AMD 555h, 5555h, Intel; layouts bottom, top e uniforme) para `MdFlash`, como o `md_rewriter` fez com o `MD.c` real (`firmware_1.1/tests/host`) | cobre apagar, programar, falha 0 → 1, chip lento, troca de cartucho |
| MD-9 | Open EverDrive: `A130E0h = 0404h` antes de gravar; EverDrive-MD v2, Magistr-16, WaterMelon (Pier Solar, Paprium), MX26L6420 | só com cartucho em mãos |
| MD-10 | Suíte de bancada **somente leitura** para Mega Drive (sem cartucho, com cartucho; leituras repetidas iguais, prefixo de 512K igual ao início da leitura maior, conferência do tamanho, blocos de 32 KiB distintos para detectar linha de endereço presa). A guarda recusa qualquer comando de escrita ou apagar. Modelo: `md_rewriter/tools/hwtest/hwtest.py` | roda sem hardware (fase `host`) e com ele |

## 5b. Estado da implementação (2026-11-04)

Firmware, PC e testes feitos; **nada rodou em cartucho**. Detalhe e riscos: `docs/decisoes.md` D86.

| # | Estado |
|---|---|
| MD-1 tabela de chips | feito: `include/dumper/MdFlashCore.h`. Falta expor o nome no protocolo (`MdFlash::identify` existe) |
| MD-2 AMD 555h de 32 e 64 Mbit, limite de 8 MB | feito (host, CLI, GUI e firmware) |
| MD-3 MX29L3211 (5555h) | feito no núcleo, sem confirmar em chip |
| MD-4 apagar por layout | feito (top e bottom boot em oito setores de 8 KB; uniforme; Intel por bloco) |
| MD-5 limites de tempo | feito: `busyCheck`, status do `write29GL` e todo o núcleo |
| MD-6 Intel PA28F400 | feito no núcleo com o barramento do Mega Drive (o `Flash.cpp` usa o do SNES, não serve); Sharp LH28F320BJE pendente |
| MD-7 SST39VF3201/3202 com `50h` | feito |
| MD-8 teste no PC com modelo de chip | feito: `pc-tests/test_mdflash.cpp` e `md_chip_model.h` |
| MD-9 mapeadores | pendente (precisa de cartucho) |
| MD-10 suíte de bancada só leitura | feito (2026-11-13): `tools/boards/megadrive/hwtest_md.py` (fases `host`, `nocart`, `cart`; a fase `host` roda no pytest). Falta rodá-la com a placa e cartuchos |

| MD-11 8 MiB em todas as camadas | conferido: `MdFlash.cpp` aceita até 8 MiB, `MD_MAX_BYTES` do host (Python e Kotlin) e `MAX_STREAM_BYTES` do protocolo (64 MiB) também, e a mensagem cita 8 MB; `test_mdflash` grava e lê o chip inteiro de 64 Mbit nos chips nativos. O S29GL (funções do OSCR, apaga o chip inteiro) não tem modelo no PC |
| MD-12 apagar e gravar acima de 2 MiB | feito no núcleo (`eraseRange` com limite de tempo por setor, o modelo cobre setores acima de `0x200000`); no S29GL só valem o limite de tempo do `eraseFlash` e agora a conferência de `FFFFh` (`blankRange`) |
| MD-13 aviso do limite de 2 MiB | feito pelo ID do chip (S29GL, como o `md_rewriter`): CLI Python e Kotlin recusam antes de apagar (`--ignore-cart-limit` força, saída 4), a GUI avisa na confirmação. Detectar pelo padrão de leitura (SRAM de save a partir de `0x200000`) **não** foi feito |

Também de 2026-11-13, vindo da bancada do `md_rewriter`: `MdFlashCore::blankRange` confere `FFFFh` depois de apagar (nativos e S29GL; falha vira `E_CARTUCHO_IO` ou `kNotBlank`), e o nome do chip do `DETECT` traz os quatro bytes do autoselect (`S29GL064N 017E1000`): o ID de 16 bits não diz o layout dos setores.

## 6. Fontes

- `md_rewriter/docs/KY_SUPPORT.md`, `CART_SUPPORT.md`
- FlashKit (Krikzz) `Device.cs`, `Cart.cs`: erase `30h`, unlock bypass, RAM em `A13000h`
- FlashKit-MD-Plus (MiGeRA): `flash28*` (Intel), `flash29l*` (MX29L3211, 5555h/2AAAh), `flash29lv*` (MX29LV320)
- MD_Dumper (X-death25): `flashlist.csv` com IDs, tamanhos e algoritmos
- open-ed (Krikzz): `open-ed-mapper.txt`, programar o menu exige pull-up em `/VRES`
- Datasheet SST39VF6401B (`30h` = Block-Erase de 32 KWord): <https://www.farnell.com/datasheets/9872.pdf>

## Requisito do usuário (2026-11-13): cartuchos de Mega Drive de até 8 MiB

O `oscr_minimal` deve **ler, apagar, gravar e verificar cartuchos de Mega Drive de até 8 MiB** (64 Mbit), em todas as camadas: núcleo `MdFlashCore.h`, `MdFlash.cpp`, protocolo, CLI Python, CLI Kotlin e GUI. O `md_rewriter` não serve de modelo para esse limite: os dois cartuchos flash que ele testou (KY e um segundo S29GL064N) guardam **no máximo 2 MiB** por projeto da placa (`docs/referencia/megadrive-bancada-md-rewriter.md`, item 4), então o 8 MiB só pode ser provado aqui com outro cartucho.

| # | Item | Critério |
|---|------|----------|
| MD-11 | Conferir cada camada do caminho de gravação e de leitura até 8 MiB (limites de tamanho do `MdFlash.cpp`, do protocolo `WRITE_ROM`/`DUMP`, dos CLIs e da GUI; o núcleo já tem `kW64 = 0x400000` palavras) | teste no PC com modelo de chip de 64 Mbit: apagar, gravar e ler 8 MiB inteiros; a mensagem de erro de tamanho cita 8 MiB |
| MD-12 | Apagamento e gravação **acima de 2 MiB** com polling e limite de tempo | o modelo cobre setores acima de `0x200000`; a falha de um setor vira erro em segundos, não trava |
| MD-13 | Detectar a família KY / FlashKit que só deixa 2 MiB (palavra `0x100000` em diante lê a SRAM de save, bytes `0xFF` intercalados com RAM) e **avisar antes de apagar ou gravar** mais de 2 MiB, como o `md_rewriter` 1.3 faz no app e na CLI (`ChipDb::boardLimitBytes`, `--ignore-cart-limit`) | cartucho dessa família: aviso e nada apagado; cartucho sem o limite: segue normal |
| MD-14 | Cartucho de teste de 8 MiB: S29GL064N com `A22` ligado à flash e `/CE` sem o decodificador do FlashKit, ou Open EverDrive (janelas de 4 MiB com `ROM_BANK` em `$A13000` bit 2, 8 MiB no total) | leitura de 8 MiB com as duas metades diferentes (não repetidas) e gravação verificada nas duas |
| MD-15 | Mapeadores acima de 4 MiB: SSF2 (até 32 MiB por páginas de 512 KiB, já lido pelo `md_rewriter` só no modelo) e bancos do Open EverDrive | só com cartucho em mãos |

Regras que valem para os testes de 8 MiB: nunca gravar em cartucho original de máscara; cada apagamento ou gravação em cartucho só com o aval do usuário no momento; leitura de conferência sempre ligada (um erro de bit apareceu uma vez numa gravação de 4 MiB do `md_rewriter`).

