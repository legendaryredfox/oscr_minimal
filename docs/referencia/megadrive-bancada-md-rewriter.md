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
4. **Apagamento de setor acima de 2 MiB (byte `0x200000` em diante, palavra `0x100000`) estourou o tempo nos dois cartuchos de flash**, em qualquer setor que se tente. Palavra `0xF8000` (abaixo de 2 MiB) apaga bem. A leitura acima de 2 MiB funciona. A leitura de 8 MiB repete uma imagem de 4 MiB nos dois cartuchos: provável que `A22` (linha de endereço mais alta) não seja decodificada no cartucho ou no caminho. Causa **ainda desconhecida** (decodificação do ciclo de escrita no cartucho, ou o dumper). Vale testar o apagamento e a gravação acima de 2 MiB no `MdFlash.cpp` antes de confiar nele.
5. **Descartar bytes após o `detect`.** O dumper do md_rewriter perde bytes enviados nos 100 ms seguintes à resposta do `detect` (um `delay` antes de limpar o buffer de entrada); o app segura o próximo comando 250 ms. Não vale para o `oscr_minimal`, mas lembre se algum dia o protocolo daqui enviar comando logo após uma resposta.
6. **Um erro de bit isolado** (byte `0xAAB`, `0x04` lido como `0x00`) apareceu uma vez numa gravação de 4 MiB logo após um apagamento que falhou. A conferência pegou; não se repetiu em duas gravações limpas de 1 MiB. Mais um motivo para manter a leitura de conferência sempre ligada.
7. **Cartucho original de máscara (Rolling Thunder 2):** a leitura de 2 MiB repete a imagem de 1 MiB; o checksum do cabeçalho (`0xBEB6` calculado contra `0x11B1` no cabeçalho) não bate. Sem dump de referência não dá para dizer se é erro de leitura (duas leituras idênticas, 12,4 s) ou valor errado no cabeçalho do jogo.

## Lições de bancada (SWD, ST-Link V2 clone)

- A MCU da unidade é um **STM32F103xE** (`0x414`, 512 KiB, F_SIZE `0x200`), e não o F103VB do projeto. O firmware de 128 KiB cabe. Não há pad de NRST: o ST-Link não conecta sob reset. O chip não tem proteção de leitura.
- O fio **GND solto no header** causou horas de enlace SWD intermitente (`chipid 0x000`, "Failed to connect"). Antes de culpar alimentação, clock ou firmware, conferir o GND no header. Alimentar a placa pelo USB com só SWCLK, SWDIO e GND no ST-Link é o arranjo estável; o fio 3V3 do ST-Link só serve quando não há USB, com o slot vazio.
- Sempre fazer backup da imagem do chip antes de gravar, ler duas vezes e comparar, e exigir leitura de volta igual depois da gravação. Os scripts `tools/swd/swd.sh` e `test-swd.sh` (54 verificações, com stubs, sem hardware) fazem isso e repetem passos quando o enlace cai.
- O dumper sem placa de depuração: não existe caminho de atualização por USB, só SWD.

## Regras que o usuário deu na bancada

- Cartucho original de máscara: nunca gravar, nunca ler pelo mapeador SSF2 (escreve registros de banco no cartucho).
- Cada apagamento ou gravação em cartucho só com o aval do usuário naquele momento.
