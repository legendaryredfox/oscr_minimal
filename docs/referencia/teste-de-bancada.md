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
