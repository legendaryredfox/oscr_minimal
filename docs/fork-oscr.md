# Fork do firmware do OSCR: plano e estado

Decisão do usuário em 2026-11-03 (D65): em vez do firmware próprio (`firmware/oscr_serial`, D38), usar o **firmware novo do OSCR** e remover o que não usamos (cartão SD, N64 e outros consoles). O programa do computador (`host/` e `gui/`) continua no escopo e mantém o protocolo serial.

## 1. Estado

| Item | Estado |
|---|---|
| Cópia do upstream em `firmware/oscr/` | feita (commit `d9cb26a` do upstream) |
| Núcleos desligados (`user.ini`) | N64, SMS, autoteste. O resto dos consoles já vem desligado em `atmega2560` |
| Compila para o Mega (`pio run -e SerialASCII`) | sim: 124.660 B de flash (49,1%), 2.676 B de RAM |
| Troca do SD por saída serial | **não feita** |
| Comandos do protocolo ligados aos núcleos | **não feito** |
| Validação em hardware | nenhuma |

## 2. O acoplamento com o SD

Todos os núcleos gravam por `OSCR::Storage::Shared` (`include/api/Storage.h`, implementação AVR em `src/arch/avr/generic/Storage.cpp`): `createFile`/`createFolder`, `open`, `sharedFile.write/read/seek/close`, `buffer` compartilhado. Usos por núcleo: SNES 92, NES 72, MD 83, GBA 93, GB 146 (linhas citando `Storage::`). Como o acesso é por essa API, a troca é em um ponto.

Pontos que o plano precisa resolver:
1. **Gravar (ler ROM/save do cartucho):** `File::write` vira quadros `DATA` do protocolo, e `createFile`/`close` viram `BEGIN` (com o nome e a extensão que o núcleo escolheu) e `END` com o CRC32. O CRC32 do arquivo já é calculado pelo `File` (`crcState`).
2. **Ler (gravar save no cartucho):** `File::read` vira um pedido de bloco ao PC. O PC precisa mandar o arquivo sob demanda.
3. **`seek`/`size`/`available`:** usados por conferência e por barras de progresso; em fluxo serial só existe sequencial, então os pontos que dependem de `seek` precisam ser achados (um por um) e adaptados.
4. **Menus:** os núcleos são dirigidos por menus (`OSCR::UI`). Com `io:serial` o menu aparece como texto e as escolhas vêm de comandos digitados. Para o nosso protocolo é preciso chamar as funções dos núcleos (por exemplo ler ROM do SNES) **sem o menu**, ou deixar o PC dirigir o menu serial.
5. **Base de dados (CRDB):** usa o SD também. Sem SD, a identificação do cartucho por base de dados some (o mapper/tamanho do NES voltam a ser informados pelo usuário, como hoje).
6. **Configurações, logs e atualizador:** também usam o SD; desligar.

## 3. Ordem sugerida

1. Um `Storage` alternativo (`src/arch/avr/serial/Storage.cpp`) com a mesma interface, que escreve numa porta serial em quadros do protocolo, só para **ler ROM** de um console (começar pelo Mega Drive ou pelo GBA, que têm menos opções), em modo `OSCR_MOCK` quando possível.
2. Ligar `DETECT` e `DUMP_ROM` do protocolo a esse caminho; testar com o `host/dumper.py`.
3. Ler save; depois gravar save (o caminho de leitura do arquivo).
4. Console por console: SNES, NES/Famicom, GB/GBC/GBA. Os que dependem de opções (mapper e tamanhos do NES) passam pelas opções do protocolo.
5. Quando o fork cobrir o que o firmware próprio cobre, **arquivar** `firmware/oscr_serial` (decisão do usuário: arquivar e aposentar), mantendo o protocolo (`oscr_proto`/`oscr_session`) e o modo MOCK onde ainda servirem de teste.

## 4. Riscos

- Nenhum teste existente no PC cobre o código do OSCR: ele não roda fora do AVR. Os testes com cartucho simulado (990 verificações) são do nosso código e deixam de valer para o fork.
- O tamanho do firmware com tudo ligado fica perto de 125 KB de flash dos 253 KB; sobra espaço para o protocolo.
- O firmware do OSCR é grande (SNES 2.921 linhas, NES 5.305, MD 3.065, GBA 3.137, GB 3.619). Cada console precisa de leitura antes de ser ligado ao protocolo.
