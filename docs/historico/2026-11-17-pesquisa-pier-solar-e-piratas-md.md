# Pesquisa: Pier Solar e mappers piratas do Mega Drive (2026-11-17)

Pedido do usuário: procurar repositórios para basear o suporte (MD-9). Nada foi implementado no firmware: faltam dados que só um cartucho ou um dump confirmado dão (ver "Lacunas"). Tudo abaixo vem de emuladores, não de medição em cartucho.

## Fontes e licenças

| Fonte | Licença | Uso |
|---|---|---|
| MAME `src/devices/bus/megadrive/cart/t5740.cpp` e `rom.cpp` (github.com/mamedev/mame) | BSD-3-Clause | pode servir de base (só os fatos de registrador; o código é nosso) |
| Genesis Plus GX `core/cart_hw/md_cart.c` (github.com/ekeeke/Genesis-Plus-GX) | própria, **proíbe uso comercial** | só leitura de referência; **não copiar código**, incompatível com a GPL v3 do projeto |
| PicoDrive / pico-genesisPlus (`gwpier.c`) | não conferida | citada em PR do pico-genesisPlus; não lida |
| Sega Retro, SpritesMind (threads 37429 e 37433), nesdev | | Sega Retro bloqueou o acesso automático, SpritesMind deu timeout, nesdev deu 404: **não lidos** |
| GitLab, Codeberg, Bitbucket | | nada útil (Bitbucket só tem o repositório do Genesis Plus GX) |

## Pier Solar (T-5740, WaterMelon), segundo o MAME

- 8 janelas de 512 KiB no espaço do cartucho (`0x000000` a `0x3FFFFF`); no reset a janela *i* mostra a página *i*.
- Janelas 0 a 4 fixas. Janelas 5, 6 e 7 trocam de página com escrita de 8 bits, valor `& 0xF` (16 páginas possíveis), nos offsets `0x03`, `0x05` e `0x07` do bloco de E/S "TIME" (`$A130xx`; **a base absoluta não está no arquivo**).
- Offset `0x01`: escrita sem efeito no MAME (comentários: habilita SPI e troca de banco). Offset `0x09`: SPI (bit 0 SI, 1 SCK, 2 HOLD, 3 CS); offset `0x0B`: leitura de SO. EEPROM M95320 (4 KiB).
- Proteção: "no início cada banco aparece espelhado em 32 KiB e uma condição não especificada libera o banco inteiro"; o MAME só tem um *hack* para a leitura de `$018100`-`$0181FF`. **A condição de desbloqueio é desconhecida.**
- Detecção por cabeçalho (Genesis Plus GX): produto `T-5740`.

## Mappers piratas (MAME `rom.cpp`): o que muda para quem só lê a ROM

A maioria só devolve valores de proteção em leituras fora da ROM (Soul Blade, Bug's Life, KOF98/99, Super Mario Bros, Rockman X3, Smart Mouse, Elf Wor, Mahjong...); a ROM é linear, então o `DUMP_ROM` de hoje já deveria servir. **Trocam de banco de verdade** (a leitura linear dá dump errado):

| Mapper | Registrador (endereço de byte) | Banco |
|---|---|---|
| Realtec | `$400000`, `$402000`, `$404000` | 128 KiB (**já feito**, D179) |
| SSF2 | `$A130F3` a `$A130FF` | 512 KiB (**já feito** no OSCR) |
| Lion King 3 | escrita em `$700000` a `$7FFFFF`, valor `& 0xFF` | 32 KiB, janela de 1 MiB |
| Pokémon Stadium / Kaiju | escrita em `$700000` a `$7FFFFF`, valor `& 0x7F` | 32 KiB, mesma fórmula |
| Multicart pirata (A13) | escrita no bloco A13, deslocamento de byte `0x00` a `0x3E` | 64 KiB |
| Beggar Prince, Legend of Wukong, Star Odyssey | escrita no bloco A13 / `$E00` a `$F00`: modo de ROM e SRAM | variam |
| Super Mario World 64 | travas em `$600000` a `$67FFFF` | 64 KiB, lógica com vários registradores |

Detecção segura: por cabeçalho (produto e checksum, como o Genesis Plus GX faz), nunca escrevendo às cegas: um cartucho de flash repro aceita escritas nesses endereços.

## Lacunas (impedem implementar sem cartucho)

1. Pier Solar: base absoluta dos registradores, tamanho real da ROM e condição de desbloqueio. Sem o desbloqueio um dump linear sai espelhado em 32 KiB.
2. Piratas: a fórmula de janela do Lion King 3 / Pokémon Stadium (`(offset<<1) | (banco<<15)`) é a do MAME; não há como saber, sem cartucho, quantos valores de banco o cartucho aceita nem a ordem em que o dump deve ser montado.
3. Nada disto foi confirmado em cartucho real.

Próximo passo possível: dump de teste de um Pier Solar (ou de um dos piratas acima) para confirmar, com leitura linear, se a ROM sai espelhada e com quais escritas.

## Atualização: artigo de quem dumpou um Pier Solar real

Fonte: Brandon L. Wilson, "Pier Solar and the Great Reverser", PoC‖GTFO 15:02 (https://mcfp.felk.cvut.cz/publicDatasets/pocorgtfo/contents/articles/15-02.pdf; texto extraído com `pdftotext`). Único relato **confirmado em cartucho real** que achei. Reddit não pôde ser pesquisado (a ferramenta de busca recusa o domínio); a Krikzz forum deu 403 e a SpritesMind deu timeout.

Fatos do artigo:

- A leitura simples devolve os **primeiros 32 KiB espelhados** por todo o espaço (o mesmo resultado de um dump com o OSCR ou com qualquer leitor de barramento).
- "Os primeiros 32 KB ficam espelhados até que **acessos específicos a `0x18010`** ocorram. O espelhamento é **religado automaticamente pelo hardware se o sistema não estiver executando da ROM por mais de um tempo desconhecido**." O autor acha que o cartucho é uma FPGA e que distingue busca de instrução de leitura de dado: o dump só saiu fazendo o 68000 ficar num laço infinito *na ROM* (por Game Genie) enquanto o Z80 lia o cartucho.
- Depois do desbloqueio: **4 MB lineares** a partir de `$000000`, e os outros 4 MB (**8 MB no total**) por troca de banco "quase igual ao Super Street Fighter II" (registradores `$A130F3` a `$A130FF`, janelas de 512 KB; o autor leu o dump de 4 MB no IDA para descobrir). O checksum do cabeçalho conferiu com o dump completo.
- Save: EEPROM serial acessada por "um par de registradores" (o MAME diz SPI M95320, 4 KiB, em `$A13009` e `$A1300B` se a base for `$A13000`; a SpritesMind diz que `$A13000` a `$A1300F` é a área do Pier Solar).

Conclusão para este projeto:

- O OSCR (e este firmware) lê pelo barramento com o 68000 desligado. **Não há como reproduzir a "execução da ROM"** que o cartucho exige, nem se sabe qual sequência de acessos em `0x18010` desbloqueia. Implementar `Pier Solar` agora seria código sem como testar e provavelmente devolveria 32 KiB espelhados.
- O que **falta saber** para tentar: a sequência exata de leituras/escritas em `0x18010` (e o tempo antes de religar o espelhamento). Só se obtém com analisador lógico no barramento de um cartucho rodando no console, ou com os fontes do MAME/PicoDrive (`t5740.cpp` só tem um *hack* para `$018100` a `$0181FF`).
- Pier Solar fica **fora do alcance** do hardware atual até alguém medir essa sequência. Cartuchos de flash repro (Everdrive) só emulam o mapper do cartucho original.
