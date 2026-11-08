> **Atualização (D126, 2026-11-07): o bloco foi gerado nas placas v1.1** (`snes`, `megadrive`, `nes`, `famicom`, `famicom_nes`, `gb_gba`, `16_and_8_bits`, `n64`), sem passar antes pela placa perfurada. A `16_bits` v1.3 segue esperando o RP2040. Ver `docs/referencia/bloco-troca.md`.

# Plano: bloco de troca de cartucho (`16_bits` v1.3 e demais placas v1.1), **sem chave física**

> **Revisado em 2026-11-07 (D123): a chave física (SPST, D18, trava de segurança e aborto de leitura) foi cancelada.** Fica só o controle **em software** (`POWER`, D116), o sensor do rail com o LED de "seguro trocar", a descarga forçada e o ciclo de energia do SA-1. O texto abaixo mantém o histórico; o que menciona a chave está marcado como cancelado. Firmware, host e GUI já foram atualizados.

# Plano: chave física de troca de cartucho (`16_bits` v1.3 e demais placas v1.1)

Para fazer **depois** (pedido do usuário, 2026-11-07). Continua `docs/referencia/troca-de-cartucho.md` (decisões de D115) e parte do que o `POWER` em software (D116) já entrega. **Estado (2026-11-07, D119): o firmware e o software (F1 a F8) estão feitos e testados no PC; o hardware (seções 2 e 3) e a bancada não.**

## O que já existe (não refazer)

- Protocolo `POWER`/`POWER_RESP`, erro `0x000C`, flag `INFO` bit 5, CLI Python e Kotlin, GUI, simuladores e testes (D116).
- Firmware: `releaseCartPins()`, `cart_power()`, `OSCR_POWER_SWITCH`, `OSCR_POWER_DISCHARGE_MS`, ambiente `SerialASCII_Power` em `firmware/oscr/config.d/83-dumper-power.ini`.
- Hardware só na `16_bits` v1.2: Q1 (P-MOSFET), R16, R17, R18, D2 verde, comando no D19, rede `+5V_CART` (D108). **As outras placas não têm Q1 nem `+5V_CART`.**

## Ordem de trabalho (revisada em 2026-11-07, D118)

1. **Firmware e software (F1 a F8)**, testável no PC. A chave pode ser testada na v1.2 já montada com um fio do D18 ao GND.
2. **Validação do bloco na bancada, sem placa nova:** montar o bloco da seção 2 (Q2, Q3, resistores, LED de "seguro trocar") numa placa perfurada ligada às pernas do Q1 da `16_bits` v1.2 (gate `PWR_G`, dreno `+5V_CART`), ao 5V do Mega e a um fio para o D53. Confere limiar do 2N7000, tempo de descarga, o VCC do cartucho com a chave aberta (< 0,5 V) e o ciclo do SA-1, antes de gastar placa.
3. **Hardware v1.1 das demais placas** (`snes` primeiro, pelo benefício no SA-1; depois `megadrive`, `nes`, `famicom`, `famicom_nes`, `gb_gba`, `16_and_8_bits`), com um script único generalizado. **Não esperam o RP2040.**
4. **`16_bits` v1.3**, que **leva o RP2040 junto** (decisão do usuário), **só quando o RP2040 estiver validado em bancada** (D89). Se o usuário preferir não esperar, a chave pode sair numa v1.3 com o PIC e o RP2040 virar v1.4: perguntar nessa hora.
5. Bancada de cada placa (só o usuário) e ajustes.

## 1. Firmware e software (FEITO em D119: F1 a F8, nada testado em hardware)

Feito: `include/dumper/PowerCore.h` (debounce de 20 ms, espera da descarga, tentativas com ciclo de energia; 17 verificações em `pc-tests/test_power_core.cpp`), `Backend::power_poll`/`power_abort`, `DetectInfo::attempts`, `POWER_RESP` completo, aborto de leitura com a chave aberta (gravação e apagamento ignoram), ambiente `SerialASCII_PowerHW`, simuladores (`OSCR_SIM_SWITCH`), CLI Python e Kotlin, GUI (LEDs virtuais, chave, aviso de gravação) e testes. **Ainda a confirmar em hardware:** o debounce e a leitura do D18, o D53, o tempo de descarga, o `releaseCartPins()` entre as tentativas do SA-1 e se o SA-1 melhora de fato com o ciclo.

| # | Tarefa | Detalhe |
|---|---|---|
| F1 | ~~Chave no D18 como trava~~ | **CANCELADO (D123).** O firmware não lê mais o D18 (código, debounce e testes removidos). |
| F2 | ~~Chave aberta no meio de uma operação~~ | **CANCELADO (D123).** Sem chave, não há o que abortar; o host é quem liga e desliga o 5V (`POWER`). |
| F3 | **Sensor do rail** | Hoje o LED amarelo (Q3) é só analógico. Proposta: ligar o nó do Q3 a um pino livre (**D53, PB0**: não é do ICSP nem de slot; entrada sem pull-up, 1 kΩ em série). Firmware: depois de abrir Q1, esperar o sensor ou 500 ms (2 s sem o sensor); `POWER_RESP.rail` e `features` bit 1. Build: `OSCR_POWER_SENSE=1`. |
| F4 | **Descarga forçada** | Só informa: `features` bit 2 com `OSCR_POWER_DISCHARGE=1` (tempo de espera 500 ms em vez de 2 s). |
| F5 | **Ciclo de energia do SA-1** | Antes de cada tentativa de destravamento: desligar, esperar 500 ms, ligar, esperar 50 ms; até 3 tentativas. Achar no `SNES.cpp` do upstream (`firmware/oscr/src/cores/`) onde o SA-1 é detectado e onde a falha vira "cabeçalho inválido" (status 4); o gancho fica em `Dumper.cpp` (`prepare`/`detect` do SNES). Só em placa com `power_switch`. Registrar quantas tentativas foram precisas no log da GUI e na CLI (`attempts`). |
| F6 | **CLI e GUI** | Mostrar `switch` e `rail_low` (hoje `null`); a GUI ganha um LED virtual (verde = 5V, amarelo = seguro trocar) e o aviso de chave aberta; `power status` explica por que não liga. Textos nos 4 idiomas. |
| F7 | **Simuladores e testes** | `SimDevice` e `MockDevice` com chave e sensor (`OSCR_SIM_SWITCH=open|closed`); `PowerBackend` do `pc-tests` com a trava e o abort; teste do ciclo do SA-1 (3 falhas, 4ª ok). |
| F8 | **Docs** | `docs/referencia/protocolo.md` (campos de `POWER_RESP`), `docs/referencia/cli.md`, nova decisão (D118). |

**Pino do sensor (F3): D53 (decidido, seção 4).** As alternativas D10 a D13 são do LED do OSCR/Mega.

## 2. Bloco de troca (hardware, igual em todas as placas)

Conforme D115. Referências **sequenciais depois da última da placa** (regra de D109). Valores:

| Peça | Valor | Liga | Notas |
|---|---|---|---|
| Q2 | 2N7000, TO-92 | dreno em `+5V_CART` por R_dis; fonte no GND; gate em `PWR_G` | descarga: alto em `PWR_G` = Q1 aberto = Q2 conduz |
| R_dis | 330 Ω | `+5V_CART` ao dreno do Q2 | em placa com GBA, mais 330 Ω do `3V3` ao mesmo dreno |
| Q3 | 2N7000, TO-92 | gate em `+5V_CART`; fonte no GND; dreno no nó `SENSE` | detector de rail baixo (limiar ~2 V) |
| R (gate do Q3) | 100 kΩ | gate do Q3 ao GND | garante "rail baixo" com o rail flutuando |
| R_up | 1 kΩ | 5V do Mega ao nó `SENSE` | |
| LED amarelo 3 mm | — | nó `SENSE` ao GND | aceso = seguro trocar (rail < ~2 V) |
| R (sensor) | 1 kΩ | nó `SENSE` ao pino do sensor (F3) | |

Placas **sem Q1** (todas menos a `16_bits`) precisam também do bloco de D108: Q1 (IRF9540N, TO-220), R16 100 kΩ, R17 100 Ω, R18 1 kΩ, LED verde, a rede `+5V_CART` (0,8 mm) e a troca de quais cargas ficam nela: VCC dos slots de 5V, Si5351, PIC, bypass, pull-ups e (nas placas com GBA) a entrada do MCP1700. O 5V do Mega continua alimentando só o LED amarelo, R_up e o Q1.

**BOM extra por placa (sem a chave, D123):** 2 × 2N7000, 1 LED de "seguro trocar", resistores 330 Ω (1, ou 2 com GBA), 1 kΩ (2), 100 kΩ (1); mais, nas placas sem Q1, Q1, 100 kΩ, 100 Ω, 1 kΩ e LED verde.

## 3. Como fazer cada placa (receita)

Seguir D108 e `boards/nes/README.md`/D96 (scripts por placa):

1. Congelar o estado atual (`hardware-v1.0` ou `hardware-v1.2`) e `fab/` anterior, como já foi feito (D110).
2. Esquemático por edição de texto com `tools/historico/revisao/schlib.py` e `v12b_sch.py` como modelo; **generalizar** num script único `tools/historico/revisao/bloco_troca_sch.py <placa>` (lista de redes que passam a `+5V_CART` por placa).
3. PCB: posições das peças novas (`v12b_pcb.py`), contorno maior se faltar espaço (as placas de um sistema são de 65 mm de altura), furos e silkscreen (`v12_silk.py`, `silk_aviso_usb.py`): trocar o aviso para "Desligue o cartucho (LED amarelo aceso) antes de trocar" e a revisão para `v1.3` (`16_bits`) ou `v1.1`.
4. Roteamento: Freerouting (`v12b_route.py`), zonas (`tools/fill_zones.py`), costura de GND com cuidado (D108).
5. Verificação: ERC, DRC (0 erros, 0 não roteadas), `tools/check_netlist.py --board <pasta>` com as configurações novas (VCC dos slots em `+5V_CART`, D18, D19 e o pino do sensor), ERC da `snes` pelo MCP se der.
6. Fábrica: `tools/export_fab.sh <pasta> <versão>`, BOM, `fab/PEDIDO.md` com o SHA-256, `docs/bom.md`, `docs/montagem.md` (ordem de solda: 2N7000 e resistores com os baixos, chave por último; teste de aceitação), README da placa e `boards/README.md`.
7. Decisão nova em `docs/decisoes.md` por placa ou uma geral (D118+), `docs/pinmap.md` regenerado (`tools/gen_pinmap.py`), commit e push nos dois remotos.

## 4. Decisões (usuário e projeto, 2026-11-07; D118)

| # | Tema | Decisão | Quem |
|---|---|---|---|
| 1 | ~~F2: chave aberta no meio de uma operação~~ | **Cancelado (D123).** | usuário |
| 2 | F3: sensor do rail | **Sim, no D53 (PB0)**: nó `SENSE` do Q3 por 1 kΩ, entrada sem pull-up; alto = rail baixo = seguro trocar. Sem o sensor (placas sem o bloco) `rail` fica `0xFF` | projeto |
| 3 | ~~Chave~~ | **Cancelada (D123):** a placa não leva chave física. | usuário |
| 4 | Tamanho das placas | **Pode crescer** (usuário). Crescer o mínimo, de preferência para baixo (o lado da chave), mantendo os furos M3 alinhados com os do Mega e o encaixe nos headers | usuário |
| 5 | RP2040 na v1.3 da `16_bits` | **Sim, mas não agora** (usuário): a v1.3 só começa com o RP2040 validado em bancada (D89); ver a ordem acima | usuário |
| 6 | Ordem das placas | Bloco validado em perfboard na v1.2 → v1.1 das demais (`snes` primeiro) → `16_bits` v1.3 com o RP2040 | projeto |
| 7 | LED | verde (D2, 5V presente, só na `16_bits`) + o LED de **"seguro trocar"** (nó `SENSE`), mantido por pedido do usuário (D123). O plano o chamava de amarelo e o pedido o chamou de verde: **cor a confirmar**; 3 mm THT. | usuário |

**Perguntar na hora, se surgir:** a v1.3 da `16_bits` sem o RP2040 se o RP2040 atrasar; tamanho final de cada contorno; se alguma placa de um sistema deve ficar sem a chave (por exemplo a `famicom`, sem Si5351 nem PIC, só tem o ganho da troca segura).

## 5. Teste de aceitação (bancada, só o usuário)

- Chave aberta, USB ligado, cartucho de SRAM inserido: o VCC do cartucho cai abaixo de 0,5 V em até 1 s e o LED amarelo acende. Se o VCC do cartucho ficar acima de 0,5 V, o cartucho está sendo alimentado pelos pinos: rever a ordem de desligamento (F1) ou considerar buffers de isolamento.
- Chave fechada: `power status` mostra ligado, o LED verde acende, o amarelo apaga; 5V do slot ≤ 5,2 V (P-02 de `docs/historico/pesquisa-comunidade.md`).
- Abrir a chave durante uma leitura (aborta) e durante uma gravação de flash (F2: ignora e avisa), num cartucho sem valor.
- Cartucho SA-1 (PGA Tour 96 ou outro): comparar a taxa de sucesso com e sem o ciclo de energia (F5).
- Medir a queda do Q1 em carga (≥ 4,7 V em `+5V_CART`, já pendente em `v12-final.md`).
- Teste das placas de um sistema: pelo menos um cartucho de cada slot depois do ciclo `power off` / `power on`.

## 6. Riscos

- Cortar o 5V com o Mega dirigindo os pinos alimenta o cartucho pelos pinos (mitigado pelo `releaseCartPins()`; confirmar na bancada).
- Gravação de flash interrompida pela chave (F2).
- O 2N7000 em TO-92 como detector tem limiar variável (1 a 2,5 V): o LED amarelo acende em tensão entre ~1 e ~2,5 V; documentar e medir.
- Placas pequenas podem não ter espaço sem refazer o contorno e o roteamento (o autoroteador já tem as 6 placas novas sem revisão manual, ver `boards/README.md`).
