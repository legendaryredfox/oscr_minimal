# Gravar o PIC12F629 (CIC do SNES) com o PICkit 2

Para a placa `16_bits` v1.0, que leva o PIC no soquete U2. A v1.3 troca o PIC por um RP2040
(`docs/placa-v1.3-rp2040.md`); este guia vale para a v1.0 e para qualquer PIC12F629 do OSCR.

O PIC só é preciso para cartuchos SNES com SA-1. Hex a gravar:
`firmware/cic_rp2040/third_party/snescic-lock-resync.hex` (do sd2snes, GPL v2).

## Material

Kit PICkit 2 (clone) com adaptador ZIF e cabo USB, mais os PIC12F629-I/P virgens (DIP-8).
O 12F629 só grava com alta tensão (Vpp de uns 12 V no pino 4). O PICkit 2 original gera essa tensão; **alguns
clones não**. Sintoma: o programa não reconhece o chip (ID não lido) mesmo com tudo ligado certo.

## Instalação (uma vez)

O `pk2cmd` é da Microchip e tem licença **não livre**: ele NÃO está neste repositório e não deve ir para ele.
O script baixa do upstream na sua máquina (fontes em `vendor/pk2cmd/`, binário em `tools/pic/bin/`, ambos
ignorados pelo git):

```
sudo apt install libusb-dev build-essential git        # cabeçalho e compilador
tools/pic/instalar_pk2cmd.sh                           # baixa (commit fixo), compila, confere que o .dat lista o 12F629
sudo cp tools/pic/60-pickit.rules /etc/udev/rules.d/ && sudo udevadm control --reload && sudo udevadm trigger
```
Reconecte o PICkit 2. `lsusb` deve mostrar `04d8:0033` (se mostrar outro ID, acrescente-o em `60-pickit.rules`).

> Estado: o instalador e as regras **não foram executados** (o ambiente onde foram escritos não permitiu compilar
> código baixado). Os fontes e o `.dat` foram baixados e inspecionados: o `PK2DeviceFile.dat` contém "PIC12F629".
> Se a compilação falhar com o compilador novo, o script tenta de novo com `-fpermissive`; o log fica em
> `tools/pic/bin/build.log`.

## Ligação

Coloque o PIC no ZIF **seguindo o desenho da placa adaptadora** (canto do pino 1; nunca deixe o DIP-8 solto no meio
do soquete). Ligação ICSP do PIC12F629, para conferir:

| Pino do PIC | Sinal | PICkit 2 (conector de 6 pinos) |
|---|---|---|
| 4 (GP3) | MCLR/Vpp | 1 |
| 1 | Vdd | 2 |
| 8 | Vss | 3 |
| 7 (GP0) | PGD (dados) | 4 |
| 6 (GP1) | PGC (clock) | 5 |

## Comandos

Sintaxe do `pk2cmd` v1.20; **confirme cada opção com `tools/pic/bin/pk2cmd -?`** (não rodei aqui). `-B` aponta a
pasta do device file.

```
P="tools/pic/bin/pk2cmd -Btools/pic/bin -PPIC12F629"

$P -I                      # lê o ID do chip: se falhar, veja "Problemas"
$P -GFbackup-virgem.hex    # lê tudo para um arquivo ANTES de gravar (guarda o OSCCAL, ver abaixo)
$P -Ffirmware/cic_rp2040/third_party/snescic-lock-resync.hex -M     # grava
$P -Ffirmware/cic_rp2040/third_party/snescic-lock-resync.hex -Y     # verifica
$P -GFlido.hex             # lê de volta
python3 -I tools/pic/comparar_hex.py firmware/cic_rp2040/third_party/snescic-lock-resync.hex lido.hex
```
Alimente o alvo pelo PICkit 2 a 5 V (opções `-T` e `-A`, ver `-?`).

O `comparar_hex.py` é a conferência independente: compara as 1024 palavras de programa e a de configuração
(esperada `0x3FD3`: oscilador externo EC, WDT, PWRTE, MCLRE e proteções desligados) com o `.hex` original. Fica de
fora só a palavra `0x3FF`, que guarda a **calibração de fábrica OSCCAL** (`RETLW xx`). O PIC do OSCR roda com
clock externo e provavelmente não precisa dela, mas o apagamento geral a destrói: o `backup-virgem.hex` (guarde-o)
tem o valor. O comparador avisa se a palavra `0x3FF` lida não for um `RETLW` (`0x34xx`).

## Problemas

- **ID não lido / chip não encontrado:** troque o PIC de posição no ZIF, confira a ligação acima, confira com um
  multímetro se o pino 4 (MCLR) chega a cerca de 12 V durante a gravação. Sem os 12 V, o clone não serve para este
  chip; plano B: Arduino Uno com o ardpicprog (`docs/continuacao.md` e a conversa de 2026-11-06), ou comprar o PIC
  já gravado.
- **`PICkit 2 not found`:** regra de USB não instalada (acima) ou cabo; teste uma vez com `sudo`.
- **Verificação falha:** grave de novo; se repetir, veja a alimentação do alvo e o cabo.
