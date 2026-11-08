# Limites do suporte a Game Boy / Game Boy Color

Levantamento de 2026-11-03, a partir de `firmware/oscr_serial/oscr_carts_gb.cpp`, de `oscr_carts.cpp` (leitura e gravação de save), das decisões D56, D60 e D61 e de `vendor/oscr/legacy/Cart_Reader/GB.ino`, `GBM.ino` e `GBS.ino`. Tudo é leitura de código e testes com cartucho simulado: **nada foi testado em hardware**. Os modelos dos testes (`SimGb`) são a minha leitura dos registradores e da sequência do OSCR, não os chips.

## 1. O que o firmware faz hoje

| Mapper (byte `$147`) | ROM | Save |
|---|---|---|
| sem mapper (`$00`, `$08`, `$09`) | sim | SRAM, se o cabeçalho informar |
| MBC1 (`$01`-`$03`) e MBC1M (6 coletâneas por título) | sim | SRAM: ler e gravar |
| MBC2 (`$05`, `$06`) | sim | 512 nibbles: ler e gravar |
| MBC3 (`$0F`-`$13`) | sim | SRAM: ler e gravar; **sem o relógio (RTC)** |
| MBC5 (`$19`-`$1E`) | até 8 MB | SRAM: ler e gravar |
| MBC6 (`$20`, Net de Get) | sim | SRAM 32 KB + Flash 1 MB: **só leitura** |
| MBC7 (`$22`) | sim | EEPROM 256 B (512 B no Command Master): ler e gravar |
| MMM01 (`$0B`-`$0D` e 4 títulos) | até 1 MB | SRAM: ler e gravar |
| TAMA5 (`$FD`) | sim | nenhum |
| GB Camera (`$FC`) | sim | SRAM: ler e gravar |
| HuC1 (`$FF`) e HuC3 (`$FE`) | sim, tratados como MBC3/MBC5 | SRAM, sem RTC nem IR |

Detalhes e testes: D56, D60, D61.

## 2. Limites do hardware desta placa

- **3,3 V.** O slot GBA fornece 3,3 V (U3). O OSCR lê GB a 5 V. A maioria dos cartuchos lê bem a 3,3 V, mas alguns de GB antigos podem falhar (leituras com bits trocados, CRC diferente a cada tentativa). Saída de hardware, se acontecer: um jumper de solda que ligue o VCC do slot ao 5V no lugar do U3, só para GB e nunca com cartucho GBA (D56). **Não foi feito.**
- **Adaptador.** GB e GBC entram só pelo slot GBA, com adaptador. O lado da etiqueta e a direção de entrada do slot continuam sem conferência física (U-18, D27, D28).
- **`Audio-In` (PH4/D7) sem ligação** (D22). O OSCR o usa como /WE alternativo em cartuchos de flash repro. Sem ele, qualquer gravação de ROM em flash (seção 4.1) está fora do alcance sem mudar a placa.
- **Reset de 400 ms.** O `GbBus::begin()` mantém o reset por 400 ms (como o `setup_GB` do OSCR). O MMM01 reinicia o cartucho uma vez por bloco de 512 KB, então uma ROM de 1 MB leva pelo menos ~1 s a mais de espera só nisso.

## 3. Limites dos mappers que já temos

### 3.1 Tamanhos

- ROM: o byte `$148` vale de 0 a 8 (32 KB a 8 MB). Valores fora disso, inclusive `$52`, `$53` e `$54` (1,1, 1,2 e 1,5 MB), dão `ERRO 0x0002`.
- Save pelo byte `$149`: 2 KB (valor 1), 8 KB (2), 32 KB (3), 128 KB (4), 64 KB (5). RAM de 2 KB conta como 1 banco de 2 KB (o OSCR não lê nada nesse caso). MBC2 é fixo em 512 x 4 bits, MBC7 em 256 ou 512 bytes, MBC6 em 1.081.344 bytes.
- O nome do jogo vem do cabeçalho: 15 caracteres se `$143` é a flag CGB, senão 16. O firmware não diz se o cartucho é GBC (o protocolo não tem esse campo); o CLI e a GUI escolhem `.gbc` depois da leitura, olhando a flag `$143` (bit 7) da ROM lida, e `.gb` nos outros casos.

### 3.2 Por mapper

- **MBC1:** os bancos `$20`, `$40` e `$60` não aparecem na janela `$4000`; saem pela janela de `$0000` em modo 1. O OSCR lê o banco errado nesses três; aqui não (D56). **MBC1M** só para 6 coletâneas identificadas por título e checksum do cabeçalho; outra coletânea MBC1M sai como MBC1 comum, com os bancos trocados.
- **MBC2:** cada byte do save guarda 4 bits; na gravação só se confere o nibble baixo.
- **MBC3:** o RTC não é lido nem gravado. Um save de jogo com relógio (Pokémon Ouro/Prata/Cristal, por exemplo) sai sem os registradores de tempo. O OSCR também não os salva.
- **HuC1/HuC3:** tratados como MBC3/MBC5 para trocar banco. O infravermelho do HuC1 e o relógio do HuC3 não são tratados.
- **MBC6:** só leitura. `WRITE_SAVE` responde `0x0002`. A sequência de gravação da Flash do OSCR (páginas de 128 bytes com AA/55/A0, `$00` no último endereço e espera pelo valor `$80`; apagamento de setores de 128 KB) não foi portada porque não consegui conferir o que o chip faz em cada passo, e um erro estragaria o save de 1 MB (D61). Para portar: folha de dados do chip ou um cartucho para experimentar.
- **MBC7:** o acelerômetro não faz parte da ROM nem do save e não é lido. O tamanho da EEPROM vem de `$14E/$14F`: `BE A5` (Command Master) = 512 B, os outros = 256 B. Gravação palavra a palavra, só do que mudou, com conferência; teto de 100.000 consultas de "pronto" (D60).
- **MMM01:** recusado acima de 1 MB (`0x0002`). O OSCR repete o mesmo deslocamento (`$20`) em todo bloco acima do primeiro, o que só funciona até 1 MB, e não consegui conferir outro valor. O reconhecimento por título cobre só `BOUKENJIMA2 SET`, `BUBBLEBOBBLE SET`, `GANBARUGA SET` e `RTYPE 2 SET`; outras coletâneas MMM01 cujo menu declare outro mapper não são reconhecidas. O limite de 6 bits do deslocamento e o que cada registrador faz de fato **não** foram conferidos (o modelo do teste é a minha leitura do OSCR).
- **TAMA5:** só a ROM. Os 32 bytes de RAM interna (Tamagotchi 3 e outros) não são lidos, como no OSCR.
- **GB Camera:** só a SRAM. A câmera usa a sequência própria de CS/CLK; não há leitura de imagem.

### 3.3 Risco comum a todos

- Os tempos e as sequências de porta (`AvrGbBus`) vêm do OSCR e são conferidos no PC por registradores simulados (`test_avr_hal`), mas **não** em um cartucho real. O ponto mais provável de ajuste: atraso extra nos pulsos de CLK em `$A080` do MBC7 a 3,3 V (D60).
- O checksum do cabeçalho é a única validação de "tem cartucho". Cartucho com cabeçalho corrompido dá `status 4` (há dados, checksum errado); o OSCR deixava o usuário ignorar o erro. A opção de forçar a leitura ainda não existe (D59).

## 4. O que o OSCR faz e o firmware não

### 4.1 Cartuchos de flash e ferramentas de gravação (`ENABLE_FLASH` e `ENABLE_GBX`)

`GB.ino`, `GBM.ino` e `GBS.ino` trazem, além da leitura:
- **Gravar ROM em cartuchos flash repro** (comandos 29F016/29F032/29F033/39SF040/29F160 e CFI): dependem do `Audio-In` como /WE (seção 2) e apagam o chip.
- **Game Boy Memory Module (GBM):** ler ID, ler, apagar, conferir vazio, gravar e ler/gravar o mapeamento.
- **Game Boy Smart Card (GBS).**
- **Pelican (W29C020/28LF040), Datel Mega Memory e GameShark** (`readPelican_GB`, `readMegaMem_GB`, `readGameshark_GB` e as gravações correspondentes).

Nenhum foi portado: são acessórios raros, a maioria destrutiva na gravação, e não há como testar sem eles. O protocolo atual também não tem comando de "apagar".

### 4.2 Outros

- **M161 (Mani 4 in 1, `TETRIS SET`):** o OSCR a trata com reset a cada banco e atraso de 50 ms. Recusado com `0x0002`.
- **MBC4 (`$15`-`$17`):** o OSCR lista o nome, mas o tipo não tem leitura própria em `readROM_GB` (cai no caminho genérico). Recusado aqui.
- **Mappers de ROM que o OSCR lê pelo caminho genérico** (qualquer `$147` ≥ 5 não listado: escreve o banco em `$2100`): o firmware recusa em vez de adivinhar.
- **RTC do MBC3 e do HuC3:** nenhum dos dois salva o relógio.
- **Conferência no No-Intro:** o OSCR calcula o checksum global (`$14E/$14F`) e compara com o do arquivo. O host mostra o CRC32 do arquivo para a comparação manual; o checksum global do cabeçalho não é verificado automaticamente (D59 só verifica o checksum do cabeçalho `$14D`).

## 5. O que o simulador não prova

O `SimGb` pega erro de lógica: banco errado, ordem de escrita, tamanho, estado que sobra entre operações. **Não pega:** erro de transcrição de bit ou de endereço copiado igual nos dois lados; tempos; diferenças entre revisões de chip e entre cartuchos reais (por exemplo, clones de MBC5 que respondem diferente); EEPROM e flash que se comportam diferente do datasheet. Em todos os testes de mutação, um erro plantado derruba entre 1 e 4 verificações, com uma exceção conhecida por incremento (o reinício do MMM01 em `probe_gb`, coberto pelo `acquire`).

## 6. Ordem sugerida para o que falta

1. Validar em hardware o que já existe: GB sem mapper e MBC5 primeiro, depois MBC1 e MBC3, só então os raros (MBC7, MMM01, MBC6, TAMA5). Se a 3,3 V falhar, o jumper de 5 V (seção 2).
2. Gravação da Flash do MBC6 (precisa da folha de dados do chip ou de um cartucho).
3. RTC do MBC3, se o usuário quiser: precisa de uma convenção para guardar o relógio ao lado do `.sav` (o formato de outros emuladores usa 48 bytes extras).
4. Verificação do checksum global (`$14E/$14F`) no host e na GUI.
5. Opção de forçar a leitura com cabeçalho inválido.
6. Acessórios (GBM, GameShark, Pelican, Mega Memory): só com o acessório na mão e o `Audio-In` ligado.
