# Mega Drive: o que a bancada do md_rewriter mostrou (2026-11-13)

Origem: primeira unidade do dumper STM32 `md_rewriter` (repositório irmão, `~/development/hardware/md_rewriter`) ligada a cartuchos reais. Detalhe, tempos e arquivos: `docs/HWTEST.md`, `docs/NEW_FIRMWARE_SPEC.md` (NFW-20, NFW-21) e `docs/NEW_FIRMWARE_PLAN.md` naquele repositório. Tudo aqui foi medido em três cartuchos do usuário; é uma amostra pequena, e vale como alerta para o `MdFlash.cpp` deste projeto, que nunca rodou em chip.

## Cartuchos usados

| Cartucho | Códigos do autoselect | Observação |
|---|---|---|
| Rolling Thunder 2 (Namco, original, ROM de máscara) | `FLASHID:0000` (não é flash) | Só leitura, por pedido do usuário. 2 MiB e 8 MiB repetem a imagem de 1 MiB |
| S29GL064N, PCB Ver1.4 ("anterior" do Metal Gear) | `017E1001` | Primeiro setor de 64 KiB **uniforme** |
| Cartucho "KY technology" | `017E1000` | Oito setores de **8 KiB** no início (boot) |

Os dois cartuchos de flash respondem `017E` no ID de 16 bits, que é o que a tabela do `MdFlash.cpp` usa (`S29GL064N`).

## Achados que importam para este projeto

1. **O ID não diz o layout dos setores.** Dois cartuchos com o mesmo `017E` têm layouts diferentes. Os códigos dos ciclos 3 e 4 do autoselect (`1001` e `1000`) separaram os dois cartuchos, mas com uma amostra de cada não dá para fundamentar uma regra. A tabela CFI (palavras `0x2C..0x34`) leu `02070020007F000001` nos dois e, numa sessão posterior, `02070020007E000001` nos dois: **não distingue os layouts**. Regra adotada lá: nunca escolher o apagamento pelo ID ou pela CFI; apagar sempre com passos de 8 KiB abaixo de 64 KiB (num chip uniforme só custa tempo: 8,5 s contra 6,3 s para 2 MiB). Para o `eraseFlash` do OSCR (`MegaDrive.cpp`) vale conferir se ele apaga setor por setor ou o chip inteiro; o apagamento do chip todo não depende do layout.
2. **Apagar com um único `30h` no endereço 0 deixou 56 KiB programados** no cartucho com setores de boot: o apagamento "terminou" sem erro e a gravação seguinte deu `WRITE TIMEOUT` no primeiro bit 0 para 1. Moral: depois de apagar, **ler de volta e conferir `0xFF`** antes de gravar.
3. **A gravação precisa consultar o fim da programação (polling).** O firmware 1.0 do dumper, sem polling, só gravou uma palavra a cada duas (545 135 palavras ficaram em branco em 2 MiB). Com polling (DQ7, verificação do dado) uma passada gravou e conferiu 2 MiB. Tempo: 78,9 s de gravação, 90 a 93 s com a leitura de conferência, nos dois tipos de cartucho. Gravar dado diferente sobre dado já gravado, sem apagar, dá `WRITE TIMEOUT` em 0,4 s e o dumper continua respondendo (comportamento certo).
4. **Cartuchos flash da família KY / FlashKit guardam no máximo 2 MiB de ROM, por projeto da placa.** Apagar setor em palavra `0x100000` ou mais (byte `0x200000` em diante) estourou o tempo nos dois cartuchos de flash (`ERASE TIMEOUT!`); abaixo de 2 MiB apaga bem. A causa não é o dumper nem o firmware: lendo os repositórios de referência (`md_rewriter/references/`), a placa do cartucho FlashKit original (`cart-md-v1.2.pcb`) tem só um 74HC139 e **nenhum registrador**: o `/CE` da flash é `!( !CE_LO e !A20 )`, ou seja, a flash só é selecionada para os 2 MiB de baixo, e os 2 MiB de cima selecionam a SRAM de save (`RAM_CE`). O pino `A21` da flash está ligado ao GND e as linhas `a21` e `a22` do conector não vão a lugar nenhum. O dump do cartucho KY confirma: de `0x200000` a `0x3FFFFF` há um byte `0xFF` e um byte de RAM intercalados (os bytes ímpares formam `RAGNACENTY`, o nome do save). A leitura de 8 MiB repete 4 MiB porque `A22` não chega à flash. O programa original do FlashKit (`Cart.cs`, e a versão em Go `fkmd/cart/cart.go`) limita a ROM a 2 MiB quando há RAM e a escrita em `$A13000` não muda a janela de `0x200000`. Escritas de um registrador em `$A13000` e `$A130F1` (valores `0x00` e `0x01`, depois de um `detect` com `FLASHID:017E`) não mudaram nada no cartucho KY. **Conclusão: para jogos acima de 2 MiB é preciso outro cartucho**, como o `MD-Flash-Cart-4MB` (MX29L3211 ou MX29LV320, sem decodificador, compatível com o programador FlashKit) ou um com mapeador de bancos (Open EverDrive, SSF2). Vale para o `MdFlash.cpp` deste projeto: um cartucho dessa família aceita no máximo 2 MiB de ROM; teste o apagamento e a gravação acima disso antes de confiar nele.
5. **Descartar bytes após o `detect`.** O dumper do md_rewriter perde bytes enviados nos 100 ms seguintes à resposta do `detect` (um `delay` antes de limpar o buffer de entrada); o app segura o próximo comando 250 ms. Não vale para o `oscr_minimal`, mas lembre se algum dia o protocolo daqui enviar comando logo após uma resposta.
6. **Um erro de bit isolado** (byte `0xAAB`, `0x04` lido como `0x00`) apareceu uma vez numa gravação de 4 MiB logo após um apagamento que falhou. A conferência pegou; não se repetiu em duas gravações limpas de 1 MiB. Mais um motivo para manter a leitura de conferência sempre ligada.
7. **Cartucho original de máscara (Rolling Thunder 2):** a leitura de 2 MiB repete a imagem de 1 MiB; o checksum do cabeçalho (`0xBEB6` calculado contra `0x11B1` no cabeçalho) não bate. Sem dump de referência não dá para dizer se é erro de leitura (duas leituras idênticas, 12,4 s) ou valor errado no cabeçalho do jogo.

## Lições de bancada (SWD, ST-Link V2 clone)

- A MCU da unidade é um **STM32F103xE** (`0x414`, 512 KiB, F_SIZE `0x200`), e não o F103VB do projeto. O firmware de 128 KiB cabe. Não há pad de NRST: o ST-Link não conecta sob reset. O chip não tem proteção de leitura.
- O fio **GND solto no header** causou horas de enlace SWD intermitente (`chipid 0x000`, "Failed to connect"). Antes de culpar alimentação, clock ou firmware, conferir o GND no header. Alimentar a placa pelo USB com só SWCLK, SWDIO e GND no ST-Link é o arranjo estável; o fio 3V3 do ST-Link só serve quando não há USB, com o slot vazio.
- Sempre fazer backup da imagem do chip antes de gravar, ler duas vezes e comparar, e exigir leitura de volta igual depois da gravação. Os scripts `tools/swd/swd.sh` e `test-swd.sh` (54 verificações, com stubs, sem hardware) fazem isso e repetem passos quando o enlace cai.
- O dumper sem placa de depuração: não existe caminho de atualização por USB, só SWD.

## Esquema do dumper (EasyEDA) e ferramentas

- O projeto da placa do dumper em `md_rewriter/Hardware/PCB/` é um SQLite do EasyEDA Pro; dá para ler a netlist com Python (`documents.dataStr` é base64 de gzip, uma lista JSON por linha, `PAD_NET` liga pino e rede). Para editar o projeto no próprio EasyEDA existe a skill oficial `easyeda/easyeda-api-skill` (MIT, `npx skills add easyeda/easyeda-api-skill -g -y`).
- No dumper `A17` a `A23` vão de `PA0` a `PA6` do STM32 (pinos 23, 24, 25, 26, 29, 30, 31 do U1) para o slot. **`/UWR` e `CAS2` do slot não ligam a nenhum pino do microcontrolador**: o dumper só gera ciclos de escrita de byte baixo (`/LWR`). Não atrapalha a gravação da flash nem os registradores de mapeador do SSF2, mas um cartucho que exija `/UWR` nunca veria uma escrita válida.

## Guia de usuário do md_rewriter

O repositório `md_rewriter` tem agora um guia passo a passo (soldagem, montagem e desmontagem, instalação do firmware 1.1 por SWD e todos os testes, por GUI e CLI) em quatro idiomas: `md_rewriter/docs/guide/` (`pt-BR.md`, `en.md`, `ru.md`, `zh-Hans.md`). O dono testou os cartuchos gravados pelo md_rewriter num Mega Drive real (informado em 2026-11-13).

## Regras que o usuário deu na bancada

- Cartucho original de máscara: nunca gravar, nunca ler pelo mapeador SSF2 (escreve registros de banco no cartucho).
- Cada apagamento ou gravação em cartucho só com o aval do usuário naquele momento.
