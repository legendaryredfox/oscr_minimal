# Upstream `oscartreader/oscr-firmware`: o que mudou desde `d9cb26a` (D-3, P-15)

Conferido em 2026-11-15 clonando `https://github.com/oscartreader/oscr-firmware` (topo `e5a0832`, 2026-11-11) e rodando `git diff d9cb26a..HEAD`. Três commits: `c7bdaf8` (2026-11-09, "Bug fixes + bootloader updates + syncing with oscr-databases"), `0ec02fc` (2026-11-09, BS-X: soltar /WP, #14) e `e5a0832` (2026-11-11, "Various fixes, additions, and optimizations"). 61 arquivos, +1361 −738. **Nada foi aplicado ao fork.** O diff foi lido por trechos (núcleos que o fork usa, mais config e scripts); o que está em bootloader, `databases` e núcleos que o fork desliga só foi visto pelo nome do arquivo.

## Resumo

Quase tudo é limpeza sem mudança de comportamento. A lista abaixo separa o que importa.

| Mudança | Onde | Efeito no fork | Decisão proposta |
|---|---|---|---|
| `putWord(idx, word, Endian)` novo no `Storage::Shared`; os núcleos trocam as duas linhas "byte alto, byte baixo" por ele | `include/api/Storage.h`, `src/arch/avr/generic/Storage.cpp`; `MegaDrive`, `N64`, `GameBoy`, `GameBoyAdvance`, `Flash`, `Atari*` etc. | Mesmo resultado nos bytes. O fork tem os núcleos antigos e o `StreamFile` no lugar do SD; trazer só aumenta o diff sem ganho | **Não trazer.** Se um dia sincronizar os núcleos inteiros, vem junto |
| `int` virou `uint8_t` ou `uint16_t` em laços e parâmetros (`pulse_clock`, `printFlash`, `bytesRead`...) | muitos núcleos (`MegaDrive`, `NES`, `SMS`, `GameBoy`...) | Economiza alguns bytes de flash e RAM; sem mudança de comportamento (conferi `NES.cpp`, `SMS.cpp`, `MegaDrive.cpp`) | **Não trazer** sozinho; entra com a sincronização |
| `GameBoy.cpp`: leitura do título por `untilAddr` no lugar de `x` | `src/cores/GameBoy.cpp` ~1092 | Equivalente (para o nome em 0x0134 a 0x0143, ou até 0x0142 com CGB flag 0x80/0xC0) | Não trazer |
| `Flash.h` separa `HAS_FLASH8` e `HAS_FLASH16` | `include/cores/Flash.h`, `config.d` | O fork usa `flash = true` e `flash16 = true` no `user.ini`; a separação poderia tirar um pedaço do flash 8 bits se um dia só o 16 bits for preciso. Hoje não | Só olhar se faltar flash |
| BS-X: `writeBank(0x0D, 0x5000, 0x80)` solta o /WP para apagar páginas protegidas | `src/cores/Satellaview.cpp` (#14) | O fork **não liga** Satellaview/BS-X (F-11 pendente) | **Trazer junto com o F-11**, quando o BS-X entrar |
| `config.d/20-boards-atmega2560.ini`: `board_bootloader.hfuse` 0xDC → 0xDE; `scripts/build_flags.py`: protocolo padrão `avrisp` → `stk500v1`; bootloaders urboot novos e `urboot-oscr.patch` | `config.d`, `scripts`, `bootloader/` | Só vale para a gravação do bootloader nas placas OSCR originais; o Mega Arduino do fork usa o bootloader dele (D131, `firmware-flash` com `avrdude -c wiring`) | Não se aplica |
| `include/common/crdb/nes.h` e submódulo `databases` sincronizados com `oscr-databases` | `include/common/crdb`, `databases` | O fork não usa as bases em SD; o `database.py` do host tem as dele (D135 tornou a base CRDB desnecessária) | Não se aplica |
| `scripts/crutils.py` +235 linhas, `decode_bootloader.py` reescrito | `scripts/` | Ferramentas de build do upstream; o fork usa as dele | Não se aplica |

## Núcleos que o fork não liga e que mudaram

`Atari2600`, `Atari5200`, `Atari7800`, `Atari8`, `AtariJaguar`, `CPS3`, `CasioLoopy`, `ChannelF`, `Commodore64`, `Intellivision`, `Leapster`, `LittleJammerPro`, `MSX`, `PCEngine`, `TI99`, `TRS80`, `VIC20`, `VirtualBoy`, `SFM`. Só importam quando o F-20 ligar o sistema correspondente (D-C: só os que cabem nos slots existentes); nessa hora o núcleo vem **da versão atual do upstream**, não da antiga.

## Conclusão

Nenhuma correção de bug que afete o que o fork usa. O upstream seguiu em refatoração e em ferramentas de build. Próxima conferência: quando entrar o F-11 (BS-X) ou o F-20, ou quando o `oscr-firmware` passar de `e5a0832`.
