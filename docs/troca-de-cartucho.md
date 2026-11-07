# Trocar o cartucho sem desligar o USB: LED e chave para ligar e desligar o shield

Pedido do usuário (2026-11-07), para sessões futuras: como normalmente não se coloca nem se tira cartucho com o USB ligado, **seria possível adicionar um LED e uma chave para ligar e desligar o shield durante a troca?**

## Resposta curta

**Sim, é possível, e metade já existe.** O que falta é software e uma decisão sobre a chave física.

## O que a `16_bits` v1.2 já tem (D108)

- **Chave de alta do 5V dos slots:** Q1 (P-MOSFET IRF9540N, TO-220) entre o 5V do Mega e a rede `+5V_CART`. `+5V_CART` alimenta SNES, Mega Drive, Si5351, PIC, C2 a C6 e o pull-up R2.
- **Comando no D19 (PD2):** nível baixo liga; R16 (100 kΩ) mantém desligado com o Mega em reset; R17 (100 Ω) em série; o firmware liga no `setup()` (`cartPower(true)` em `Dumper.cpp`).
- **LED verde D2** (com R18, 1 kΩ) acende com o 5V dos slots ligado.
- Documentação: `boards/16_bits/docs/v12-final.md`.

## O que falta para a troca ficar segura (decidido na seção "Decisões" abaixo)

1. **Comando `POWER` no protocolo** (liga/desliga) e os botões na CLI Python, na CLI Kotlin e na GUI ("Desligar cartucho para trocar" / "Ligar"). Sem ele a chave não serve (já dito em D108).
2. **Colocar todos os pinos de sinal em alta impedância antes de cortar o 5V.** Se o Mega continuar dirigindo endereço, dados e controle com o cartucho sem alimentação, a corrente entra pelos diodos de proteção do cartucho e o **alimenta pelos pinos** (o cartucho "liga pela porta"), o que anula a chave e pode danificar chips. Ou seja: a chave só de potência não basta; o firmware precisa soltar os barramentos (`DDRx = 0`, sem pull-up) e só então abrir Q1; e, ao ligar, ligar o 5V primeiro e só depois reassumir os pinos. Isto também vale para o `/CART` (D50 com pull-up interno).
3. **Resistor de descarga** no `+5V_CART` (por exemplo 1 kΩ a 10 kΩ em série com um transistor ou direto, de modo que o 5V caia em segundos com a chave aberta) e, se possível, o LED indicar "desligado = seguro trocar" (LED vermelho, ou o verde apagando só quando a tensão cair de fato). O Q1 desligado deixa o rail flutuando e os capacitores (C2 a C6, mais o eletrolítico se estiver depois de Q1) mantêm o cartucho alimentado por algum tempo.
4. **Chave física (opcional).** Duas formas:
   - **Chave como entrada do firmware** (recomendada): uma chave SPST em um pino livre com pull-up; o firmware lê a chave, solta os barramentos, abre Q1 e acende/apaga o LED. Mantém a ordem segura do item 2. A GUI e a chave físicas ficam equivalentes.
   - **Chave que atua direto no gate de Q1** (ligar `PWR_G` ao `5V` do Mega para forçar desligado): mais simples e funciona mesmo sem o computador, **mas corta o 5V sem soltar os barramentos**, o que cai no problema do item 2. Só usar se houver buffers de isolamento nas linhas (74HC/CBT), que a placa não tem.
5. **Outras placas.** A `16_and_8_bits` e a `gb_gba` têm o slot GBA a 3,3 V por um regulador (MCP1700, só para ele): a chave precisaria cortar também a entrada dele. As placas só de um sistema (`snes`, `nes`, `famicom`, `megadrive`) não têm Q1 hoje: a ideia entraria numa revisão.
6. **Aviso no silkscreen** (já existe: "NÃO COLOQUE NEM RETIRE O CARTUCHO COM USB LIGADO") deve ganhar uma variante para a placa com chave: "Desligue o cartucho (LED apagado) antes de trocar".

## Ganho extra: SA-1

A comunidade relata que cartuchos SA-1 destravam melhor depois de **desligar e deixar os capacitores descarregarem**, e que **capacitor grande no VCC do cartucho atrapalha** o tempo do destravamento (ver `docs/pesquisa-comunidade.md`, P-03 e P-04). Com `POWER` implementado, o firmware pode **fazer um ciclo de energia automático antes de cada tentativa de SA-1**.

## Estado (2026-11-07): `POWER` em software (D116) e firmware da chave física, do sensor e do ciclo do SA-1 (D119) feitos

**D119:** ambiente `SerialASCII_PowerHW` (`OSCR_POWER_SWITCH_HW`, `OSCR_POWER_SENSE`, `OSCR_POWER_DISCHARGE`); chave aberta recusa `POWER on` (erro `0x000C` com texto `chave`) e, com o 5V ligado, corta no próximo poll; leitura em curso aborta e gravação/apagamento ignoram a chave até o fim; o SNES repete a leitura do cabeçalho até 3 vezes com ciclo de energia (`attempts` no `DETECT`). Falta só o **hardware** (`docs/plano-chave-fisica.md`).

### Histórico: o `POWER` em software (D116)

Implementado e testado no PC (nada em hardware): `POWER` (0x0D) e `POWER_RESP` (0x89) no protocolo, erro `0x000C` "cartucho desligado", flag `INFO` bit 5 (`power_switch`), firmware (`releaseCartPins()`, `cart_power()`, ambiente `SerialASCII_Power`), CLI Python e Kotlin (`power on|off|status`, `--power auto|keep`), GUI (estado, botão "Desligar para trocar o cartucho" e ligação automática antes das ações), simuladores (`OSCR_SIM_POWER=1`) e testes. Detalhes em `docs/protocolo.md`, `docs/cli.md` e D116. **Falta** (plano completo em `docs/plano-chave-fisica.md`; v1.3 da `16_bits` e v1.1 das demais): a chave física no D18, o transistor de descarga (Q2), o LED amarelo (Q3) e o ciclo de energia automático do SA-1; o firmware já tem a espera de 2 s para o caso sem Q2.

## Decisões (usuário, 2026-11-07; D115)

Respostas do usuário às cinco perguntas: **chave física, na próxima iteração de cada placa**; `16_bits` fica para a **v1.3**; todas as demais placas (`16_and_8_bits`, `snes`, `nes`, `famicom`, `famicom_nes`, `megadrive`, `gb_gba`, e `8_bits` e `completa` quando saírem do esqueleto) ficam para a **v1.1**. O pino do Mega e os itens de LED e de comportamento do firmware ficaram a critério do projeto, seguindo boas práticas. Nada disso foi desenhado nem implementado ainda; abaixo está o que as próximas sessões devem seguir.

| Tema | Decisão | Por quê |
|---|---|---|
| Pino da chave | **D18 (PD3, INT3)**; o comando do 5V continua no **D19 (PD2)** | D18 e D19 não são usados por nenhum slot em nenhuma placa (`pinmap.md`) e nenhum núcleo do OSCR escreve em PD2/PD3 (D108). Vizinhos no Mega (TX1/RX1), roteamento curto. D18 tem interrupção externa (INT3), útil para reagir à chave com o laço ocupado. Evitados: D0/D1 (USB), D10 a D13 (LED do OSCR e do Mega), D39 (botão do OSCR), D50 a D53 (SPI e ICSP) |
| Tipo de chave | SPST deslizante THT, passo 2,54 mm. **Fechada ao GND = ligado permitido; aberta (ou fio solto) = desligado** | À prova de falha: se o contato se soltar, a placa desliga |
| Ligação da chave | D18 com pull-up interno; **1 kΩ em série** (ESD) e **100 nF** do pino ao GND; debounce de 20 ms no firmware | Chave exposta na borda da placa; sem componente de pull-up externo |
| Papel da chave | **Trava de segurança (interlock)**, não só um pedido: `5V dos slots = chave ligada E pedido do software`. Chave aberta desliga na hora e o firmware recusa comandos que precisam do cartucho com o erro `0x000C` "cartucho desligado" | Evita divergência entre posição da chave e estado real; o hardware vence o software |
| Ordem ao desligar | (1) soltar todos os pinos de sinal dos slots (`DDRx = 0`, `PORTx = 0`, inclusive o pull-up do `/CART`); (2) abrir Q1 (D19 alto); (3) Q2 descarrega o rail; (4) esperar até o rail cair ou 500 ms | Sem (1), o Mega alimenta o cartucho pelos pinos (ver item 2 acima) |
| Ordem ao ligar | confirmar pinos soltos; D19 baixo; esperar 50 ms; só então reassumir os barramentos do sistema escolhido | Evita corrente de partida pelos pinos |
| Descarga | **Q2 (2N7000, TO-92) com R_dis 330 Ω** de `+5V_CART` ao GND; gate de Q2 em `PWR_G` (alto = Q1 aberto = Q2 conduz) | τ ≈ 0,1 s com ~470 µF (conferir se o eletrolítico fica antes ou depois de Q1); pico de ~15 mA, só durante o desligamento; sem consumo com o 5V ligado |
| LED | Mantém **D2 verde** = 5V dos slots presente. Acrescenta **LED amarelo "SEGURO TROCAR"**, aceso só quando o rail cai abaixo de ~2 V: **Q3 (2N7000)** com gate em `+5V_CART` (pull-down de 100 kΩ), dreno com R_up 1 kΩ ao 5V do Mega, LED do dreno ao GND | O LED mostra a tensão real, não o comando; assim ninguém troca com o rail ainda cheio |
| Boot do firmware | **Começa desligado.** O host liga explicitamente; a GUI liga ao usar uma ação e mostra o estado; a CLI tem `--power auto` (padrão: liga antes e mantém) e `power on\|off\|status`. `INFO` ganha a flag `power_switch` | Estado inicial determinístico e seguro; o fluxo do usuário quase não muda |
| SA-1 | **Ciclo de energia automático** antes de cada tentativa de destravamento: desliga, espera 500 ms, liga, espera 50 ms, tenta; até 3 tentativas. Só em placa com a flag `power_switch` | P-03 e P-04 de `docs/pesquisa-comunidade.md` |
| Isolamento | **Sem buffers de isolamento** (74HC/CBT): barramentos soltos por firmware + resistores série das linhas de controle (D108). Reavaliar só se o teste de aceitação falhar | Buffers aumentam a placa, atrasam o sinal e fogem do "mínimo THT" |
| Slot GBA (3,3 V) | Entrada do MCP1700 em `+5V_CART` (já é); o sensor do LED amarelo lê o **3V3** nessas placas; resistor de descarga extra no 3V3 | O LDO segura a carga do slot GBA por mais tempo |
| Placas sem Q1/Q2/Q3 | `POWER` funciona em software (v1.2 da `16_bits` tem Q1): sem Q2 o rail decai pelo próprio consumo; o firmware espera 2 s e avisa que não há confirmação de descarga | Dá para usar o recurso antes de existir a v1.3 |

**Teste de aceitação (só o usuário, em hardware):** com o cartucho de SRAM inserido, USB ligado e a chave aberta, o VCC do cartucho deve ficar abaixo de 0,5 V em até 1 s e o LED amarelo deve acender; depois de ligar, medir o 5V (≤ 5,2 V, P-02). Se o VCC ficar acima de 0,5 V, o cartucho está sendo alimentado pelos pinos: rever a ordem de desligamento ou considerar buffers.

**Ordem de implementação:** (1) protocolo e firmware `POWER` + `INFO.power_switch`, CLI Python e Kotlin, GUI e simulador (serve à v1.2 da `16_bits`); (2) hardware v1.3 da `16_bits`; (3) v1.1 das demais; (4) ciclo de energia do SA-1 depois do teste do hardware.

## Riscos e o que não foi conferido

- Queda do IRF9540N com Vgs = −5 V e a corrente de cartuchos com SRAM e flash: **não medida** (D108, "Não conferido").
- Diodos de proteção dos cartuchos: o comportamento exato da alimentação pelos pinos depende do cartucho (a análise acima é de projeto, não medida).
- O silkscreen de uma placa **com** a chave desligada não impede o usuário de ligar o USB antes: o **hot-plug do USB continua sendo uma decisão do usuário**; a chave só protege o cartucho quando o firmware/PC desliga o 5V antes da troca.

## Proposta de passos (para quando for implementar)

1. Protocolo: `POWER` (`on`/`off`, resposta com o estado e o status de descarga), erro `0x000C` "cartucho ligado" se um comando de leitura chegar com o 5V desligado.
2. Firmware (`Dumper.cpp`): `cartPower(bool)` solta/assume os barramentos na ordem certa; `INFO` informa se a placa tem a chave (flag).
3. CLI Python e Kotlin: `power on|off|status` (e `--json`); a GUI ganha um botão grande "Trocar cartucho" que desliga, mostra o LED virtual e pergunta "Cartucho trocado? Ligar" (com aviso de 3,3 V).
4. Hardware: resistor de descarga e, se o usuário quiser, a chave física lida pelo firmware (pino livre a definir); revisar o silkscreen.
5. Testes: simulador do `POWER` no `pc-tests` e no host; o hardware só pode ser testado pelo usuário.
