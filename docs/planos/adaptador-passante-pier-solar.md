# Adaptador passante para capturar o barramento do Mega Drive (Pier Solar)

Estado (2026-11-17): **na fila, depois de resolvido o RP2040** (`docs/planos/placa-v1.3-rp2040.md`; pedido do usuário). Nada desenhado.

## Para quê

O Pier Solar (T-5740) espelha os 32 KiB iniciais da ROM até acessos específicos a `0x18010` e religa o espelhamento se o 68000 deixar de executar da ROM (PoC‖GTFO 15:02, único relato em cartucho real). Ninguém publicou a sequência exata. Sem ela o firmware não tem como desbloquear o cartucho. Pesquisa e fontes: `docs/historico/2026-11-17-pesquisa-pier-solar-e-piratas-md.md`.

## O que construir

Placa passante de cartucho do Mega Drive: borda de cartucho de um lado, slot de 64 pinos do outro, todas as linhas ligadas direto, com cabeçalho de pinos para analisador lógico em `A1` a `A23`, `D0` a `D15`, `/CE`, `/CAS0`, `/CAS2`, `/AS`, `/ASEL`, `/LWR`, `/UWR`, `/TIME`, `VCLK`, `/VRES` e GND. Console de verdade de um lado, Pier Solar do outro.

## O que medir

1. A sequência de acessos que desbloqueia os bancos (endereços, leitura ou escrita, ordem e temporização, em torno de `0x18010`).
2. Quanto tempo sem acesso à ROM religa o espelhamento.
3. Se o cartucho olha só endereço e `/AS` ou também o relógio (`VCLK`).

## Decisões que dependem da captura

- Se a sequência for só de endereços e puder ser repetida em temporização folgada, o Arduino basta (firmware novo, sem hardware novo).
- Se pedir ciclos de 68000 de verdade, o RP2040 (PIO) passa a conduzir o barramento do cartucho; isso é desenho novo, não a troca do PIC da v1.3.
- `/DTACK` (B20) só importa para o Paprium; ligar a um pino livre do Mega exige aprovação (regra de pinagem do `CLAUDE.md`).

## Fora do escopo

Os piratas com banco (Lion King 3, Pokémon Stadium, multicarts) não precisam de hardware novo: usam `/CE`, `/LWR`, `/UWR`, `/TIME` e `/CAS2`, todos ligados (D181).
