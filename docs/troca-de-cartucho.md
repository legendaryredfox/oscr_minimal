# Trocar o cartucho sem desligar o USB: LED e chave para ligar e desligar o shield

Pedido do usuário (2026-11-07), para sessões futuras: como normalmente não se coloca nem se tira cartucho com o USB ligado, **seria possível adicionar um LED e uma chave para ligar e desligar o shield durante a troca?**

## Resposta curta

**Sim, é possível, e metade já existe.** O que falta é software e uma decisão sobre a chave física.

## O que a `16_bits` v1.2 já tem (D108)

- **Chave de alta do 5V dos slots:** Q1 (P-MOSFET IRF9540N, TO-220) entre o 5V do Mega e a rede `+5V_CART`. `+5V_CART` alimenta SNES, Mega Drive, Si5351, PIC, C2 a C6 e o pull-up R2.
- **Comando no D19 (PD2):** nível baixo liga; R16 (100 kΩ) mantém desligado com o Mega em reset; R17 (100 Ω) em série; o firmware liga no `setup()` (`cartPower(true)` em `Dumper.cpp`).
- **LED verde D2** (com R18, 1 kΩ) acende com o 5V dos slots ligado.
- Documentação: `boards/16_bits/docs/v12-final.md`.

## O que falta para a troca ficar segura

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
