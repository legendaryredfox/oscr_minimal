# Cartuchos regraváveis do projeto foxcarts (observação)

Projeto irmão: `~/development/hardware/foxcards` (cartuchos Famicom e, depois, NES com flash SST39SF040 em DIP, 100% THT, sem MCU no cartucho).

**Este dumper é o gravador desses cartuchos.** Gravação pelo `WRITE_ROM` do NES/Famicom (`NES.cpp`: `NESmaker_*`, `writeFlash`, mapper 30, flash `0xBFB7`), com o cartucho no slot da placa `boards/famicom/` (ou `famicom_nes/`, `completa/`).

Consequências para este repositório:

- A primeira gravação real de `WRITE_ROM` em flash NES (D77, "nunca rodou") passa a ser um marco de teste conjunto com o foxcarts. Falhas iniciais podem ser do gravador ou da PCB do cartucho.
- O foxcarts pretende suportar, além do mapper 30, outros mappers (0, 2, 3, 7, depois 1 e 4). **O OSCR só grava flash do mapper 30 (NES Maker) e da A29040B.** Para os outros, seria preciso código novo de gravação (sequências de comando e registradores de cada mapper), com a regra do D77: chamar funções do OSCR onde existirem e escrever só as costuras. Registrar como plano quando o foxcarts definir os mappers.
- Nenhuma mudança de hardware é exigida das placas atuais. A placa `famicom` ainda não foi encomendada (2026-11-18).

## Feito no gravador (D194, 2026-11-21)

- `rom-write --fill-kb 128|256|512` (CLI Python, CLI Kotlin e GUI, campo "Repetir a PRG até"): repete a PRG até o tamanho da flash, para o banco 31 (fixo em `$C000`, com o vetor de reset) não ficar vazio. Só `nesmaker`, PRG potência de 2, sem CHR. Não é automático: um cartucho de 256 KB gravaria além do chip.
- Leitura do ID da SST39SF040 com banco 0 como reserva, se a leitura do OSCR (banco 1, A14=1) falhar. **O foxcarts pode ficar com a PCB como está**; se o ID só vier com banco 0, o gravador já cobre.
- Roteiro de bancada em `docs/referencia/teste-de-bancada.md` (seção "Gravação em flash de NES"): ID, 16 KB, leitura de volta, 128 KB com `--fill-kb 512`, console.

## Outros mappers: o que o gravador precisa saber da PCB (não implementado)

O gravador consegue gravar qualquer mapper, mas só depois de a PCB definir o contrato. Hoje o foxcarts diz "`/WE` só com CPU A14=0". Perguntas que o `oscr_minimal` precisa ver respondidas antes de escrever código (conferir cada mapper no nesdev, não de memória):

1. **Grava-se sempre pelo mapper 30?** Se sim, mappers 0, 2, 3 e 7 são só modos de execução por jumper e o OSCR não precisa de código novo; basta a ROM cair no lugar certo da flash (o `--fill-kb` já resolve o caso de PRG menor que a flash; falta definir onde cai uma ROM de 32 KB do mapper 0 e como o banco fixo vira os 32 KB).
2. **Se a gravação tiver que usar o registrador do outro mapper**, cada um muda a sequência do comando:
   - **Mapper 0 / 3 (32 KB visíveis em `$8000–$FFFF`):** comando em `$D555` e `$AAAA`, que têm A14=1. A regra atual do foxcarts descarta essa escrita (só vai ao latch). Precisa de `/WE` também para A14=1 neste modo, ou o mapper 30 faz o trabalho.
   - **Mapper 2 (UNROM):** o registrador de banco fica em `$8000–$FFFF`, então o comando e o banco disputam o mesmo endereço; há bus conflict, e a flash não pode ficar com `/OE` ativo na escrita.
   - **Mapper 7 (AxROM):** banco de 32 KB por escrita em `$8000–$FFFF` (mais o bit de espelhamento); o comando de flash em `$5555`/`$2AAA` precisa estar no banco certo.
   - **Mapper 1 (MMC1):** registradores seriais de 5 escritas, com reset; cada troca de banco são 5 escritas.
   - **Mapper 4 (MMC3):** par `$8000/$8001` e A12 para os bancos de PRG; comando de flash com banco `$5555`/`$2AAA` espelhado em bancos de 8 KB.
3. **Espelhamento e CHR:** a gravação só mexe na PRG (CHR é RAM). Confirmar que nenhum modo precisa de CHR gravada.
4. **IDs da família (feito, D195):** conferidos no datasheet SST (`S71147-02-000 5/01`, preliminar): `BFB5` (SF010A, 128 KB), `BFB6` (SF020A, 256 KB), `BFB7` (SF040). O gravador aceita as três e recusa PRG maior que o chip antes de apagar. A nota 5 do datasheet exige A18 a A1 = 0 na leitura do ID (A14 = 0): o fallback do gravador (banco 0) cobre isso.

Quando o contrato fechar, a regra do D77 vale: chamar `NESmaker_*` do OSCR onde servir, e escrever só a sequência do mapper novo na costura `NesFlash.cpp`.
