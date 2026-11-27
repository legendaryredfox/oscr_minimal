# Limites conhecidos: NES/Famicom, Game Boy e Mega Drive

O que cada sistema lê e grava hoje está na tabela da seção 3 de `docs/referencia/uso.md` e nas opções de `docs/referencia/protocolo.md`. Aqui fica só o que o formato, a placa ou o código **não fazem**, ou o que não dá para provar sem cartucho. **Nada foi testado em hardware.** Os testes no PC conferem a lógica (banco, tamanho, ordem das escritas), não os tempos nem os chips reais.

## NES / Famicom

- **O cartucho não tem cabeçalho.** O usuário informa `mapper`, `prg_kb` e `chr_kb` (o NROM se detecta pelo espelhamento). Informar errado dá um arquivo errado, e o CRC32 não avisa: só a comparação com o No-Intro mostra. A GUI e o host sugerem os valores pela base de jogos quando acham o título.
- **Onde achar mapper e tamanhos (H-2, P-10):** NESCartDB (`https://nescartdb.com`; a GUI tem o botão "Procurar mapper e tamanhos no NESCartDB" no cartão "Opções NES/Famicom"), No-Intro e `nes.dnsabr.com`. Confira o CRC32 do dump contra a base depois da leitura.
- **Clones de MMC3 com bloco externo** (12, 37, 44, 45, 47, 49, 52, 115, 116, 126, 134, 176, 224, 245, 268, 315, 351, 366, 422, 534, 995 a 999) e **multicartuchos** (15, 28, 31, 35/90/209/211, 36, 38, 40 a 43, 46, 50, 55 a 63, 104, 105, 107, 111 a 114, 120, 125, 142, 148, 157, 162, 163, 168, 174, 175, 178...): cada um é uma sequência própria de escritas; só com o cartucho na mão, um de cada vez.
- Mappers que mantêm estado entre operações (MMC1, MMC5, VRC) são reiniciados a cada leitura; o OSCR assume alimentação nova a cada uma. O 207 "às vezes precisa de power cycle" (comentário do OSCR).
- FamicomBox exige ligar os pinos 69-71 e 70-36 do conector NES; adaptador FC-NES que ligue os pinos de som de expansão não deve ser usado (relato da comunidade, não testado aqui).

## Game Boy / Game Boy Color

- **3,3 V.** GB e GBC entram pelo slot GBA, com adaptador, a 3,3 V; o OSCR lê GB a 5 V. A maioria dos cartuchos lê bem a 3,3 V; se um GB antigo falhar (bits trocados, CRC diferente a cada leitura), a saída de hardware seria um jumper que ligue o VCC do slot ao 5 V só para GB, nunca com GBA (D56). **Não foi feito.**
- **MBC1M** só para as 6 coletâneas identificadas por título e checksum; outra coletânea sai como MBC1 comum, com os bancos trocados. **MMM01** até 1 MB e só as 4 coletâneas reconhecidas por título.
- **MBC6:** `save-write` grava a SRAM de 32 KB e a flash de 1 MB pela `writeSRAMFLASH_MBC6` do OSCR (D186): destrutivo e nunca rodou; um erro estraga o save de 1 MB, então faça o `save-read` antes.
- **Não lidos:** o infravermelho do HuC1 e o relógio do HuC3; os 32 bytes de RAM interna do TAMA5; a imagem da GB Camera (só a SRAM); o acelerômetro do MBC7 (não é ROM nem save). O RTC do MBC3 é lido e gravado (D192), o que o OSCR não faz.
- O checksum do cabeçalho (`$14D`) é a única validação de "tem cartucho": cabeçalho corrompido dá `status 4`. O checksum global (`$14E/$14F`) não é conferido; o host mostra o CRC32 para a comparação manual.
- Ponto mais provável de ajuste em bancada: atraso nos pulsos de CLK em `$A080` do MBC7 a 3,3 V (D60).

## Mega Drive

Conferido em 2026-11-15 lendo `firmware/oscr/src/cores/MegaDrive.cpp` contra os relatos da pesquisa da comunidade (`docs/historico/pesquisa-comunidade.md`, P-09). Só leitura do código.

| Relato (P-09) | Situação no código | Onde |
|---|---|---|
| EEPROM serial identificada pelo checksum do cabeçalho (0x18E) | **Tratado:** tabela `eepid` com 38 checksums (Acclaim tipos 1 e 2, Capcom, Sega, EA, Codemasters) e o tipo e o tamanho de cada um | `MegaDrive.cpp`, `eepid` |
| Acclaim "tipo 2" tem PAL antes da EEPROM e exige init | **Tipo próprio** (`eepType` 2). Não conferi se a init cobre o PAL em todos os jogos | `EepromReadData`, `EepromWriteData` |
| Codemasters usa PAL e precisa de CLK | **Tratado:** tipo 5, leitura em `0x1C0000`. As placas ligam o CLK: B19 (VCLK) vai ao D16 (PH1), como no OSCR HW5; confira na montagem a continuidade | `writeWord_CM`, `pulse_clock` |
| Vários Codemasters repetem o checksum do Micro Machines 96 | **Tratado** para `0x165E` e `0x168B` (lê a palavra em 0x00; sem `0x444E`, sem EEPROM). **Não tratado** para `0x7E50` (Micro Machines 2) | `MegaDrive.cpp` |
| EEPROM só em cartuchos originais; repro não tem | **Não tratado:** um repro com o mesmo checksum de um jogo da tabela é lido como se tivesse EEPROM | sem código |
| NBA Jam Tournament Edition rev 0 apaga o próprio save | **Sem proteção:** o firmware lê e grava normalmente; faça backup antes | sem código |
| 32X lê como cartucho comum; Sega CD | sem caminho especial; do Sega CD só o cartucho de RAM de backup (128 e 512 KB) | `MegaDrive.cpp` |

### Bancada do `md_rewriter` (2026-11-13)

O dumper STM32 irmão (`~/development/hardware/md_rewriter`, `docs/HWTEST.md`) foi ligado a três cartuchos do usuário: Rolling Thunder 2 (ROM de máscara; 2 MiB e 8 MiB repetem a imagem de 1 MiB), um S29GL064N com primeiro setor uniforme (`017E1001`) e um "KY technology" com oito setores de 8 KiB no início (`017E1000`). Vale como alerta para o `MdFlash.cpp`, que nunca rodou em chip:

1. **O ID não diz o layout dos setores:** os dois de flash respondem `017E`, e a CFI (palavras `0x2C..0x34`) também não os separa. Apagar sempre com passos de 8 KiB abaixo de 64 KiB.
2. **Um único `30h` no endereço 0 deixou 56 KiB programados** no cartucho com setores de boot, sem erro; a gravação seguinte estourou o tempo no primeiro bit 0 para 1. Depois de apagar, ler de volta e conferir `FFFFh` (feito: `blankRange`).
3. **Sem polling a gravação perde palavras:** sem ele, uma palavra a cada duas ficou em branco; com DQ7 uma passada gravou e conferiu 2 MiB (79 s de gravação, 90 a 93 s com a conferência). Gravar por cima sem apagar dá `WRITE TIMEOUT` em 0,4 s, como deve.
4. **Cartuchos KY / FlashKit guardam no máximo 2 MiB de ROM, por projeto da placa:** o `/CE` da flash é `!( !CE_LO e !A20 )` (um 74HC139, nenhum registrador), os 2 MiB de cima selecionam a SRAM de save e `A21`/`A22` não chegam à flash. O dump do KY mostra de `0x200000` a `0x3FFFFF` um byte `0xFF` intercalado com a RAM (`RAGNACENTY`). Para jogos maiores é preciso outro cartucho (`MD-Flash-Cart-4MB`, Open EverDrive, SSF2). O host e a GUI avisam pelo ID do chip (MD-13, `docs/planos/melhorias-megadrive.md`).
