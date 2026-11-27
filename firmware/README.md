# firmware/

| Pasta | O que é |
|---|---|
| `oscr/` | **Firmware atual**: fork do firmware novo do OSCR (`vendor/oscr/firmware`), sem SD, com o laço do protocolo serial em `src/dumper/`. O que muda no upstream, como o fluxo serial se comporta e o orçamento de flash: `docs/referencia/fork-oscr.md`. |
| `oscr/pc-tests/` | Testes no PC do protocolo (framing, CRC32, sessão, modo MOCK e modo fluxo), das regras puras de cada sistema (`include/dumper/*Core.h`) e o `sim_stdio` que o teste cruzado do `host/` usa. |
| `cic_rp2040/` | CIC do SNES num RP2040-Zero, no lugar do PIC12F629 (não validado; `docs/planos/placa-v1.3-rp2040.md`). |
| `arquivo/` | **Arquivado (D76)**: o firmware próprio anterior. Ver `arquivo/README.md`. |

## Compilar e gravar o firmware atual

```
cd firmware/oscr
~/.platformio/penv/bin/pio run -e SerialASCII               # compila para o Mega 2560
~/.platformio/penv/bin/pio run -e SerialASCII -t upload     # grava (ou: dumper firmware-flash, ou o cartão da GUI)
python3 ../../tools/flash_budget.py check                   # flash e RAM dentro do limite (95 % e 80 %)
```

Baud do protocolo: 1.000.000 (`monitor_speed` no `user.ini`). O firmware do OSCR só roda no AVR; no PC dá para testar o protocolo e as regras puras:

```
make -C firmware/oscr/pc-tests test
(cd host && python3 -m pytest -q)          # inclui o teste cruzado Python x protocolo em C++ (sim_stdio)
```
