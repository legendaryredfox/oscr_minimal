# Teste de bancada: da placa montada ao primeiro dump (somente leitura)

Modelo: o `MANUFACTURING_TEST.md` e a matriz de validação do `n64cartreader` (`references/repos/n64cartreader/docs`), vindos da análise de `docs/historico/pesquisa-repos-referencia-2026-11-13.md` (D160, P3). Este procedimento **nunca grava nem apaga** nada num cartucho: a suíte `tools/hwtest/hwtest.py` recusa qualquer comando de escrita. Gravar (`save-write`, `rom-write`) só depois de tudo aqui passar, e sempre com o aval do usuário naquele momento (regras em `docs/referencia/uso.md`, seção 6).

## O que se precisa

- A placa montada e o Mega com o firmware do fork gravado (`docs/referencia/guia-passo-a-passo.md`), cabo USB de dados, o usuário no grupo `dialout` (Linux).
- **Cartuchos que você conhece**: um por sistema que quer testar, de preferência de baixo valor ou já copiados antes por outro leitor, cujo CRC32 ou SHA-1 você conferiu no No-Intro. Anote-os em `tools/hwtest/golden.json` (o arquivo traz um exemplo; entradas que começam com `_` são ignoradas):

```json
{"mario-kart-64": {"system": "n64", "sha256": "...", "crc32": "...", "nota": "cartucho do usuário, conferido no No-Intro"}}
```

## Ordem

1. **Sem energia** (`boards/<placa>/docs/montagem.md`, seção 5): continuidade 5 V–GND (não pode haver curto) e de algumas linhas de endereço e dados do slot ao pino do Mega.
2. **Primeira energização sem cartucho, sem PIC e sem Si5351:** 5 V no VCC de cada slot (3,3 V nos slots GBA e N64).
3. **Firmware e conexão:** `python3 host/dumper.py info` mostra protocolo, versão e os sistemas. Com `--simulate` o mesmo comando roda sem placa.
4. **Suíte, fase host** (sem placa; confere a própria guarda e a CLI contra o simulador): `python3 tools/hwtest/hwtest.py host`.
5. **Suíte, fase nocart** (placa ligada, slots vazios): `python3 tools/hwtest/hwtest.py nocart --system snes --system nes --system md --system n64` (os sistemas que a sua placa tem). Passa se: a conexão e as 10 reconexões seguidas não falham, o autoteste (`selftest`, cerca de 45 s) não acha curto, o pull-up do D7 nem falha do Si5351, e o `detect` de cada sistema diz que não há cartucho. **Se o autoteste achar algo, pare e confira a solda.**
6. **Instalar os módulos** (Si5351; PIC12F629 com `snescic-lock-resync.hex` só para o SNES com SA-1) com tudo desligado, e repetir o passo 5.
7. **Suíte, fase cart, um cartucho de cada vez** (USB desligado para trocar de cartucho):

| Sistema | Comando | Passa se |
|---|---|---|
| SNES | `python3 tools/hwtest/hwtest.py cart --system snes --golden NOME` | duas leituras iguais; checksum do cabeçalho confere; SHA-256 igual ao do dourado |
| NES / Famicom | `... --system nes --prg KB --mapper N` (as opções do `dump`) | idem; o CRC32 da ROM completa confere com o No-Intro |
| Mega Drive | `... --system md` (para o Mega Drive existe também `tools/boards/megadrive/hwtest_md.py`) | idem; espelho e blocos distintos como no relatório |
| GBA | `... --system gba --save --mapper TIPO` (o tipo sai da base do FlashGBX no relatório do `dump`) | idem; duas leituras do save iguais |
| GB / GBC | `... --system gb --save` | idem |
| Master System, Game Gear, SG-1000 | `... --system sms --mapper ADAPTADOR --prg KB` | idem; sem cabeçalho o tamanho é obrigatório |
| N64 (3,3 V) | `... --system n64 --save` (o tamanho e o tipo de save saem da base pelo CRC1; fora da base, `--prg MB --mapper TIPO`) | idem; EEPROM só lê com o Si5351 (`CLK1`) e o pull-up do D7 |

8. **Registrar:** a suíte grava `test-results/<data>-<fase>-<sistema>/report.md` e `report.json` (pasta ignorada pelo git); cole o resultado em `docs/decisoes.md` com o cartucho usado. Se o CRC32 não bater com o No-Intro, **leia outra vez** (`dump --twice`) antes de culpar o cartucho: um bit trocado a cada mil palavras já foi relatado por usuários de GBA.

## Critérios de aprovação da placa

- Fase host e fase nocart sem nenhuma falha.
- Em cada sistema que a placa tem: duas leituras idênticas e, com cartucho dourado, o hash igual.
- Nenhum aviso de tensão (`VOLT`) sem explicação: cartucho de 3,3 V nunca em 5 V.

## Problemas conhecidos (do n64cartreader e do nosso projeto)

- **Reencaixe depois de trocar o cartucho:** se a EEPROM do N64 disser que não há save depois de uma troca, tire e encaixe de novo o cartucho e repita o `detect` antes de ler o save.
- **Linha de dados da EEPROM (D7, `EEPROM_DATA` do N64):** divide o pull-up R2 (5 V) com o `/IRQ` do SNES; só um cartucho por vez, e na placa só de N64 o R2 pode ser retirado (`boards/completa/README.md`, pendência 5).
- **Porta que some ao gravar o firmware:** o Mega reinicia; espere um instante e repita o `info`.

## Gravação em flash de NES (cartucho foxcarts, mapper 30)

Primeira gravação real de `WRITE_ROM` em flash NES (D77, nunca rodou em hardware), junto com o projeto irmão `foxcarts` (`~/development/hardware/foxcarts`, ver `docs/planos/cartuchos-foxcarts.md`). Falha pode ser do gravador, do firmware ou da PCB do cartucho: este roteiro separa os três. Placa do gravador com slot Famicom (`famicom`, `famicom_nes` ou `completa`), cartucho só no slot, **sem outro cartucho** (D2: um por vez).

Antes: a leitura (`dump`) já aprovada na mesma placa com um cartucho comum (roteiro acima). Sem isso não se sabe se o erro é de gravação.

| # | Passo | Passa se | Se falhar |
|---|---|---|---|
| 1 | `python3 host/dumper.py --board famicom board` (ou o campo "Placa ligada" da GUI) e `info` | firmware responde, `write_rom` verdadeiro | firmware antigo: `firmware-flash` |
| 2 | **ID da flash:** gravar uma imagem de 16 KB (`dumper rom-write -s nes --chip nesmaker -i teste16.nes --yes`, arquivo iNES de mapper 30 com 1 banco) | passa do `prepare` sem `E_FLASH`; começa a apagar | `E_FLASH` = o ID `0xBFB7` não veio, nem pela leitura do OSCR (banco 1) nem pela do firmware (banco 0, D194): medir com multímetro `/WE`, `/OE`, `/CE` e A14 da flash; ver o `docs/referencia/flash-sst39sf040.md` do foxcarts |
| 3 | **Leitura de volta:** a própria gravação lê o cartucho depois (`--no-verify` desliga; deixe ligado) | `verify` ok, CRC32 lido igual ao do arquivo | `first_diff` aponta o byte da primeira diferença: anotar o deslocamento (banco = deslocamento / 16384) para o foxcarts |
| 4 | **Repetir o dump à mão:** `dumper dump -s nes --mapper 30 --prg 16 -o volta.nes` e comparar o CRC32 | igual ao do passo 3 | a conferência do passo 3 lê pelo mesmo caminho do `dump`: se o passo 3 passou e este não, olhar o cabeçalho iNES sintético |
| 5 | **Vários bancos:** imagem de 128 KB com `--fill-kb 512` (`rom-write ... --fill-kb 512`) | `verify` ok com 512 KB; `mirrored_from_kb` = 128 no `--json` | anotar o primeiro banco que diverge (`first_diff` / 16384): bancos a partir do 1 apontam para A14 a A18 da flash e o latch de banco; só o banco 31, para o banco fixo em `$C000` |
| 6 | **No console:** colocar o cartucho no Famicom com uma ROM de teste (tela fixa) | a ROM de teste roda | ROM gravada e conferida mas o console não roda = vetor de reset (banco 31), espelhamento ou CHR-RAM, não é do gravador |

Tempo esperado: apagar setor de 4 KB (cerca de 18 ms cada) e gravar byte a byte; 512 KB leva alguns minutos. Mande o `--json` e o `verify` de cada passo, e a saída do `board`, para anotar em `docs/decisoes.md`. Não confirmado em hardware: o tempo de espera depois de cada comando e se o `/WE` do cartucho respeita os 40 ns mínimos (a escrita do OSCR dura cerca de 1 µs, bem acima).
