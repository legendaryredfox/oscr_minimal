# Guia passo a passo: da placa montada ao primeiro dump

Modelo: o guia do `md_rewriter` (`md_rewriter/docs/guide/`). Este guia só amarra, na ordem certa, o que já está nos outros documentos; os detalhes ficam lá. Está em português; a versão em inglês é [`guia-passo-a-passo.en.md`](guia-passo-a-passo.en.md). Também em [russo](guia-passo-a-passo.ru.md) e [chinês](guia-passo-a-passo.zh-Hans.md) (traduções sem revisão de falante nativo).

## 0. Escolha a placa e o que comprar

1. Escolha a placa em [`boards/README.md`](../../boards/README.md) (por sistemas; a versão atual de cada uma está em `boards/versoes.json`). A **v1.0** é a mínima com fusível; a **v1.1** (onde existe) tem o seletor de tensão 3,3 V/5 V.
2. Peças: `boards/<placa>/docs/bom.md` e `componentes-opcionais.md`. Peças que não têm símbolo (pinos, espaçadores, cabo USB) estão no fim da BOM.
3. Pedido da placa: `boards/<placa>/fab/PEDIDO.md` (zip da versão, conferência da pré-visualização e SHA-256). **Revise o layout no KiCad antes de pagar** (roteamento por autoroteador).

## 1. Soldagem e montagem

Siga `boards/<placa>/docs/montagem.md`: do mais baixo ao mais alto (resistores, capacitores, soquete do PIC, LED, eletrolítico, headers do Si5351, slots, pinos para o Mega por último com o shield encaixado). Depois faça a inspeção visual, **antes de ligar** confira a continuidade 5 V–GND (não pode haver curto) e só então energize **sem cartucho, sem PIC e sem Si5351**, medindo 5 V no VCC de cada slot.

## 2. Computador e firmware

1. Linux: coloque o usuário no grupo `dialout` (`sudo usermod -aG dialout $USER`, saia e entre de novo). macOS e Windows: o driver do Mega já costuma vir no sistema.
2. Grave o firmware do fork no Mega pela USB-C: `python3 host/dumper.py firmware-flash` (ou o cartão "Firmware do Arduino" da GUI; precisa do `avrdude`). Alternativa para quem usa o PlatformIO: `cd firmware/oscr && pio run -e SerialASCII -t upload` (placas com seletor de tensão: `-e SerialASCII_Volt`).
3. `python3 host/dumper.py info` tem que mostrar protocolo, versão do firmware e os sistemas.

## 3. Primeiros testes, em ordem

Detalhe completo em [`uso.md`](uso.md), seção 7.

1. **Sem cartucho:** `python3 host/dumper.py selftest` (cerca de 45 s). Aponta curtos entre pinos, o pull-up do D7 e o Si5351. Se achar problema, **pare** e confira a solda.
2. **Modo MOCK (firmware de teste):** `dump -s mock` dá CRC32 `D1DF4327`.
3. **Instale os módulos:** Si5351 e o PIC12F629 gravado com `snescic-lock-resync.hex` (só o SNES com SA-1 precisa do PIC).
4. **Mega Drive, só leitura:** `python3 tools/boards/megadrive/hwtest_md.py nocart` e depois `... cart` com um cartucho no slot. Essa suíte nunca escreve no cartucho.
5. **Primeiro dump real** com um cartucho simples (SNES LoROM ou NES mapper 0): `detect -s snes` e `dump -s snes -o jogo`; compare o CRC32 com o No-Intro.

## 4. Gravar um cartucho repro de flash

Só depois de ler e conferir. Ordem de risco: save com backup, EEPROM, flash do GBA e por último `rom-write` (apaga o chip). **Nunca grave num cartucho original de máscara.** Primeiro teste num repro sem valor.

- Mega Drive: `rom-write -s md -i jogo.md --yes`. **Cartuchos KY / FlashKit com S29GL só têm 2 MiB de flash**: acima disso a CLI recusa antes de apagar (`--ignore-cart-limit` força, se a sua placa liga os 8 MiB). O firmware confere `FFFFh` depois de apagar e o programa lê a ROM de volta e compara.
- Troque o cartucho **com o USB desligado** (o 5 V dos slots não é cortado por software).

## 5. Problemas comuns

Tabela em [`uso.md`](uso.md), seção 4. Os três mais frequentes: porta serial não aparece (grupo `dialout`), cartucho não detectado (limpe os contatos, confira o lado da etiqueta no silk) e CRC divergente (leia duas vezes com `dump --twice`).
