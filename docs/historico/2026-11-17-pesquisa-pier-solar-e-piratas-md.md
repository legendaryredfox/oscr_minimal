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
