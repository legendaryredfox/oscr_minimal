# Mega Drive: melhorias de firmware e de hardware

Origem: o levantamento de 2026-11-04 no projeto irmão `md_rewriter` (dumper STM32F103 de Mega Drive, `~/development/hardware/md_rewriter`) sobre a família **KY Technology / FlashKit MD**, a revisão do PCB V1.0 dele e a primeira bancada dele com cartuchos reais (2026-11-13, `docs/referencia/limites.md`, seção Mega Drive). Detalhe de cada passo: `docs/decisoes.md` D86 a D88, D154, D181 a D183. **Nada deste arquivo rodou em cartucho neste projeto.**

## 1. Feito (firmware, PC e testes; nunca rodou em chip)

| # | Item | Onde |
|---|---|---|
| MD-1 | Tabela de chips (ID, tamanho, comandos, layout de boot) no lugar do `if` de dois IDs. O `DETECT` traz os quatro bytes do autoselect (`S29GL064N 017E1000`): o ID de 16 bits não diz o layout dos setores | `include/dumper/MdFlashCore.h`, `MdFlash.cpp` |
| MD-2, MD-3 | AMD 555h de 32 e 64 Mbit (M29W320, MX29LV320, M29W640, MX29LV640, SST39VF6401B/6402B) e MX29L3211 (desbloqueio 5555h/2AAAh) | idem |
| MD-4 | Apagar pelo layout: top e bottom boot em oito setores de 8 KiB, uniforme, Intel bloco a bloco | idem |
| MD-5 | Limite de tempo em `busyCheck`, no status do `write29GL` e no resto do núcleo | idem |
| MD-6, MD-7 | Intel PA28F400 (barramento do Mega Drive; o `Flash.cpp` do OSCR usa o do SNES), Sharp LH28F320BJE (D182), SST39VF3201/3202 com apagar bloco por `50h` | idem |
| MD-8 | Modelo de chip no PC (AMD 555h, 5555h, Intel; layouts bottom, top e uniforme) | `pc-tests/test_mdflash.cpp`, `md_chip_model.h` |
| MD-10 | Suíte de bancada **só leitura** (fases `host`, `nocart`, `cart`; a `host` roda no pytest). Falta rodá-la com a placa | `tools/boards/megadrive/hwtest_md.py` |
| MD-11 | 8 MiB em todas as camadas (`MdFlash.cpp`, `MD_MAX_BYTES` do host Python e Kotlin, protocolo); `test_mdflash` grava e lê 64 Mbit inteiros nos chips nativos. O S29GL (funções do OSCR, apaga o chip inteiro) não tem modelo no PC | |
| MD-12 | Apagar e gravar acima de 2 MiB com limite de tempo por setor; `blankRange` confere `FFFFh` depois de apagar (nativos e S29GL) | `MdFlashCore.h` |
| MD-13 | Aviso do limite de 2 MiB dos cartuchos KY / FlashKit pelo ID do chip (S29GL): as CLIs recusam antes de apagar (`--ignore-cart-limit` força, saída 4), a GUI avisa na confirmação. Detectar pelo padrão de leitura (SRAM de save a partir de `0x200000`) **não** foi feito | host, `gui/` |
| MD-9 (parte) | Leitura por banco do Lion King 3, Pokémon Stadium (`--mapper 1\|2`, D181) e Star Odyssey (`--mapper 3`, D183) | `MdBank.h` |
| HW-MD-2, 5, 6, 7 | `/CART` (B32) no D50 (o firmware só o lê no `DETECT`, D88), C5 e C6 junto ao A31 e ao A2, seis pontos de teste, `/UWR` e `/CAS2` conferidos no slot | `boards/16_bits` v1.2 e v1.3 |

## 2. Pendente

| # | Item | Precisa de |
|---|---|---|
| MD-9 | Pier Solar (ver seção 3), Open EverDrive (`A130E0h = 0404h` antes de gravar), EverDrive-MD v2, Magistr-16, WaterMelon (Pier Solar, Paprium), MX26L6420 (8 MByte, `/CE` acima de 4 MiB) | cartucho em mãos |
| MD-14 | Cartucho de teste de 8 MiB: S29GL064N com `A22` ligado à flash e `/CE` sem o decodificador do FlashKit, ou Open EverDrive (janelas de 4 MiB com `ROM_BANK` em `$A13000` bit 2). Critério: as duas metades diferentes na leitura e a gravação conferida nas duas | cartucho |
| MD-15 | Mapeadores acima de 4 MiB: SSF2 (até 32 MiB em páginas de 512 KiB) e bancos do Open EverDrive | cartucho |
| HW-MD-1 | Pull-up de 10 kΩ em `/VRES` (B27) para gravar o menu do Open EverDrive. Entrou na v1.2 como R15 DNP e saiu (D146); `/VRES` e `/MRES` dividem o D17 (PH0) | decisão do usuário |
| HW-MD-3, 4 | Resistores série e TVS nas linhas de endereço e dados (~40 linhas): não cabem no roteamento atual de duas camadas. A v1.3 da `16_bits` tem resistores série só nas 12 linhas de controle (R3 a R14); teste de bancada em `boards/16_bits/docs/versoes.md` | revisão com o roteamento refeito ou adaptador entre slot e placa |
| — | Aviso na GUI e na CLI de que a EEPROM do Mega Drive só vale em cartucho original e de que o NBA Jam TE rev 0 pode apagar o próprio save (`docs/referencia/limites.md`) | decisão do usuário |

Regras dos testes de 8 MiB: nunca gravar em cartucho original de máscara; cada apagamento ou gravação em cartucho só com o aval do usuário no momento; leitura de conferência sempre ligada (um erro de bit apareceu uma vez numa gravação de 4 MiB do `md_rewriter`).

## 3. Adaptador passante para o Pier Solar (na fila, depois do RP2040)

Pedido do usuário (2026-11-17): fica depois de resolvido o RP2040 (`docs/planos/placa-v1.3-rp2040.md`). Nada desenhado. O Pier Solar (T-5740) espelha os 32 KiB iniciais da ROM até acessos específicos a `0x18010` e religa o espelhamento se o 68000 deixar de executar da ROM (PoC‖GTFO 15:02, único relato em cartucho real); ninguém publicou a sequência. Pesquisa e fontes: `docs/historico/pesquisas-2026-11.md#pier-solar`.

- **Construir:** placa passante (borda de cartucho de um lado, slot de 64 pinos do outro, linhas direto), com cabeçalho para analisador lógico em `A1` a `A23`, `D0` a `D15`, `/CE`, `/CAS0`, `/CAS2`, `/AS`, `/ASEL`, `/LWR`, `/UWR`, `/TIME`, `VCLK`, `/VRES` e GND. Console de verdade de um lado, Pier Solar do outro.
- **Medir:** a sequência que desbloqueia os bancos (endereços, leitura ou escrita, ordem e tempo, em torno de `0x18010`); quanto tempo sem acesso à ROM religa o espelhamento; se o cartucho olha só endereço e `/AS` ou também o `VCLK`.
- **Depois da captura:** sequência só de endereços com tempo folgado = o Arduino basta (firmware novo); ciclos de 68000 de verdade = o RP2040 (PIO) conduz o barramento, desenho novo. `/DTACK` (B20) só importa para o Paprium e precisa de pino novo aprovado.
- Os piratas com banco (Lion King 3, Pokémon Stadium, multicarts) não precisam de hardware novo: usam `/CE`, `/LWR`, `/UWR`, `/TIME` e `/CAS2`, todos ligados (D181).

## 4. Lições do `md_rewriter` que continuam valendo

1. Detectar o conjunto de comandos antes de gravar: ID com desbloqueio 555h; fora da tabela, 5555h; depois Intel. Chip desconhecido fica no 555h.
2. Esperar cada palavra com DQ7 (polling) e limite de tempo, nunca só com atraso fixo: sem polling, o firmware 1.0 dele gravou uma palavra a cada duas.
3. Chips com boot sectors: em top boot os últimos 64 KiB são oito setores de 8 KiB (em bottom boot, os primeiros); passos de 64 KiB deixam sujeira. Nem ID nem CFI distinguem o layout: apagar em passos de 8 KiB abaixo de 64 KiB e conferir `FFFFh` antes de gravar.
4. `30h` não é igual em toda SST: Block-Erase (32 KWord) nas 6401B/6402B, Sector-Erase (2 KWord) nas VF160 e provavelmente nas 3201/3202, cujo bloco é `50h`.
5. Intel não apaga o chip inteiro: bloco a bloco, e toda operação termina com `FFh` (senão a leitura devolve status). Mapa do 28F400: conferir no datasheet.
6. Conferir sempre lendo de volta, e não aceitar ROM menor que o necessário sem avisar.
7. A sondagem escreve no cartucho: longe dos registradores de mapeador (SSF2 em `A130F1h` a `A130FFh`, Open EverDrive em `A130E0h` e `A13000h`); nunca conferido num mapeador real.
8. Cartuchos KY / FlashKit guardam no máximo 2 MiB de ROM por projeto da placa (o `/CE` da flash só vale nos 2 MiB de baixo; em cima fica a SRAM de save).

Achados do PCB do `md_rewriter` que não valem aqui (o Mega cuida de USB, alimentação e programação, e é 5 V): USB-C sem Rd, erros de dados do PCB dele, SWD e BOOT0, LDO e cristal, MCU de 3,3 V com cartucho de 5 V.

## 5. Fontes

- `md_rewriter`: `docs/KY_SUPPORT.md`, `CART_SUPPORT.md`, `HARDWARE_REVIEW.md`, `HWTEST.md`, `NEW_FIRMWARE_SPEC.md`; clones em `md_rewriter/references/repos/` (MD_Dumper, FlashKit-MD-Plus, flashkit-md-py, fkmd, MD-Flash-Cart-4MB, open-ed).
- FlashKit (Krikzz) `Device.cs`, `Cart.cs`: erase `30h`, unlock bypass, RAM em `A13000h`. FlashKit-MD-Plus (MiGeRA): `flash28*` (Intel), `flash29l*` (MX29L3211), `flash29lv*` (MX29LV320). MD_Dumper (X-death25): `flashlist.csv`. open-ed (Krikzz): `open-ed-mapper.txt` (pull-up em `/VRES`).
- Datasheet SST39VF6401B (`30h` = Block-Erase de 32 KWord): <https://www.farnell.com/datasheets/9872.pdf>
