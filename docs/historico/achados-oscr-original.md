# Achados no firmware original do OSCR e o que dá para mitigar

Levantamento de 2026-11-03. O clone em `vendor/oscr/` tem **dois** firmwares:
- `legacy/Cart_Reader/*.ino`: o firmware antigo (o que o nosso HAL copia);
- `firmware/`: o firmware novo do OSCR (C++ em `src/cores/*.cpp`, commit `d9cb26a` de 2026-07-28).

Objetivo: ver se o firmware novo resolve alguma das limitações de `docs/referencia/limites-nes.md` e `docs/referencia/limites-gb.md`. Tudo é leitura de código; nada foi testado em hardware.

## 1. Resultado em uma frase

O firmware novo é uma reescrita de estilo (classes, namespaces, UI nova) com **as mesmas sequências de barramento** do antigo. Ele não traz mapper nem acessório novo de NES ou Game Boy, não resolve nenhuma limitação por si só, e a diferença útil é a **base de dados de cartuchos** (CRDB), que não está no clone.

## 2. O que comparei

| Verificação | Resultado |
|---|---|
| Rótulos `case` da leitura de PRG do NES (`readPRG`) | **195 no antigo e 195 no novo, conjuntos idênticos** (nenhum mapper novo, nenhum removido) |
| Mapper 34 (BxROM/NINA-001) | idêntico: `write_prg_byte(0x7FFD, i); delay(200);` |
| Gravação da Flash do MBC6 (`writeSRAMFLASH_MBC6`) | **igual byte a byte** ao antigo: mesmas sequências AA/55/A0, `$00` no último endereço e espera pelo valor `$80` |
| Espera do MBC6 | o novo isolou num `waitSRAMFLASH_MBC6`: 100 tentativas com `delay(1)`, e em estouro desliga a Flash e dá erro (o antigo fazia quase o mesmo) |
| Game Boy: RTC do MBC3 | não existe nos dois |
| Game Boy: tamanhos de ROM `$52`-`$54` e MBC4 | não tratados nos dois |
| Game Boy: MMM01 acima de 1 MB | mesma lógica do antigo (deslocamento `$20` repetido) |
| Game Boy: checksum global (`$14E/$14F`) | só calculado para mostrar/comparar, como no antigo |
| Game Boy: acessórios (GBM, GBS, Pelican, Mega Memory, GameShark) | presentes nos dois (arquivos `GameBoyMem.cpp`, `GameBoySmart.cpp`), mesma situação |
| NES: submapper | o novo tem **submapper** (`NES_SUBMAPPER`) e usa para variantes (por exemplo comentários "submapper 0 only" nos mappers 91, 268 e 534); o antigo não tinha o conceito |

## 3. O que o firmware novo tem de diferente e útil

1. **CRDB (cart/ROM database).** O novo escolhe o cartucho de NES numa lista da base de dados (`crdbNESRecord`: CRC32, `id32a`, `id32b`, mapper, submapper, tamanho de PRG, CHR e RAM, cabeçalho iNES de 16 bytes, nome) e consulta uma segunda tabela, de **mapper e submapper → faixa válida de PRG, CHR e RAM** (`crdbNESMapperRecord`: `prglo/prghi`, `chrlo/chrhi`, `ramlo/ramhi`). Ou seja, o usuário não digita mapper e tamanhos: escolhe o jogo e o firmware sabe tudo, inclusive o cabeçalho iNES completo (espelhamento, bateria, NES 2.0).
2. **Os arquivos da base não estão no clone.** `vendor/oscr/firmware/databases/` está vazio; o formato é lido do cartão SD em tempo de execução. O que existe no repositório é só o leitor. **Não encontrei fonte offline dos dados** e não vou inventá-los.
3. **Submapper como parâmetro.** É o mecanismo que o antigo não tinha para variantes de VRC e de placas com ligação diferente.

## 4. Mitigações por limitação

Marcadas por quanto o original ajuda: **sim** (há código ou dado para portar), **em parte**, **não** (nada no original).

### 4.1 NES (de `limites-nes.md`)

| Limitação | Original ajuda? | O que fazer |
|---|---|---|
| Usuário precisa informar mapper e tamanhos | **em parte** | O novo resolve com a CRDB, que não temos. Dá para fazer o equivalente no **host/GUI**: uma tabela própria "jogo → mapper, PRG, CHR, RAM" montada com o No-Intro/NES 2.0 que o usuário já usa para comparar CRC32 (arquivo opcional, importado pelo usuário). Hoje não existe. Primeiro passo barato: **tabela mapper → faixas válidas de PRG/CHR** (o `crdbNESMapperRecord`), derivada dos limites que já conferimos em `probe_nes`, para a GUI oferecer só opções válidas. |
| iNES sem espelhamento, bateria, submapper | **em parte** | O novo copia o cabeçalho iNES da base. Sem base, dá para aceitar `--mirroring`, `--battery` e `--submapper` como opções e gravar no cabeçalho (a GUI já tem o campo de mapper). |
| Falta espera em ms (mappers 34, 60) | **sim** | O código é idêntico e simples: `NesBus::wait_ms` (sem efeito por padrão, `delay` no AVR). Libera o 34. |
| Falta pulso M2 (57), `write_reg_m59`, `write_ram_byte` (19) | **sim** | As funções existem nos dois firmwares; falta copiar para o `AvrNesBus` e para a interface. O teste só prova a lógica, não o tempo. |
| VRC2/VRC4/VRC6 dependem de variante | **em parte** | O submapper do novo é a resposta, mas a CRDB não vem junto. Mitigação: campo `submapper` no protocolo (opcional), igual ao `mapper`. Sem cartucho para testar, fica para depois. |
| Clones de MMC3 e multicartuchos | **sim, mas sem teste** | O código está nos dois firmwares e é só seguir o mesmo padrão, mas cada um é uma sequência própria e eu não consigo validar sem o cartucho. |
| Mapper 97 | **atenção** | O OSCR trata 97 junto com 180 (primeiro banco fixo em `$8000`), mas, pelo que sei da documentação do mapper (não conferi), o 97 tem o **último** banco fixo em `$8000`. Não confiei; não portei. |
| Detecção de PRG de 8 KB | **sim** | O OSCR tem um caso especial por CRC32 de 4 jogos NROM de 8 KB. Fica fora (precisa do CRC antes do dump). |

### 4.2 Game Boy (de `limites-gb.md`)

| Limitação | Original ajuda? | O que fazer |
|---|---|---|
| Gravação da Flash do MBC6 não portada | **não** (código idêntico, sem explicação nova) | O original não explica o `$00` no último endereço nem o `$80` como "pronto". **Mitigação de risco, não de dúvida**: portar com **cópia de segurança obrigatória + conferência por leitura depois de cada página + parada no primeiro erro**, marcado como experimental. O `save-write` do host já lê o save atual e guarda o backup antes de gravar (D59). Decisão do usuário. |
| Sem RTC no MBC3 | **não** | O OSCR também não salva o relógio. |
| MMM01 acima de 1 MB | **não** | Mesma lógica nos dois. |
| ROM de 1,1/1,2/1,5 MB e MBC4 | **não** | Nenhum dos dois trata. |
| Sem checksum global | **em parte** | O OSCR só compara; nós podemos **verificar no host** (soma dos bytes menos os dois do checksum), é uma conta no `verify.py` e na GUI. |
| Sem forçar a leitura com cabeçalho inválido | **em parte** | O antigo deixa o usuário "ignorar" o erro do checksum do cabeçalho; podemos oferecer `--force` (o firmware já devolve `status 4`). |
| Gravação em flash repro, GBM, GBS, Pelican, Mega Memory, GameShark | **sim, mas fora do alcance** | O código existe, mas a placa não liga o `Audio-In` (D22) e não há como testar. Hardware antes de software. |
| 3,3 V no slot GBA | **não** (o OSCR usa 5 V) | Jumper de solda para 5 V (D56), decisão de hardware. |

## 5. Próximos passos, em ordem de valor e risco

1. **`NesBus::wait_ms`** e os mappers pequenos de 4.1 (esta sessão).
2. **Host/GUI:** tabela de faixas válidas por mapper; opções de espelhamento, bateria e submapper; checksum global do GB; `--force`.
3. **Importar uma base** (No-Intro/NES 2.0 do usuário) para preencher mapper e tamanhos pelo nome do jogo.
4. **Campo `submapper`** no protocolo, antes de qualquer VRC.
5. **MBC6 com backup e conferência**, só se o usuário decidir.
