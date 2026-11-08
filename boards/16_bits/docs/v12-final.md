# 16_bits v. 1.2 final: proteção de porta, chave de 5V, reset e furos do Mega (D108)

> **Atualização D128 (2026-11-07):** este texto descreve a v1.2 de 2026-11-06. Por pedido do usuário, o **botão de reset (SW1)** saiu de todas as versões e a **v1.2 ficou sem o circuito de desligar o 5V dos slots** (Q1, R16, R17, R18 e LED D2; o 5V vai direto aos slots). Esse circuito, completo (com descarga e LED "seguro trocar"), está só na **v1.3**. Onde este documento fala de SW1, Q1, R16 a R18, D2, `+5V_CART` ou do comando no D19, vale só para a v1.3. Ver `versoes.md`.

Em 2026-11-06 o usuário pediu para levar para a v. 1.2 tudo o que estava planejado para a v. 1.3, **menos o RP2040**, que fica sozinho na v. 1.3 (se der certo; `docs/placa-v1.3-rp2040.md`). Esta página descreve o que mudou, como montar e o que ainda **não foi testado** (nada foi montado nem medido).

> **Atualização D130 (2026-11-08):** a **v1.2 ficou sem os 12 TVS (D3 a D14)**; os resistores série R3 a R14 continuam. A **v1.3** mantém os TVS (DNP). Onde este texto fala de D3 a D14, vale só para a v1.3.

## O que entrou

| Item | Peças | Onde | Observação |
|---|---|---|---|
| Resistor série nas 12 linhas de controle | R3 a R14 (axial 0204 em pé, passo 2,54 mm) | entre o pino do Mega e o resto da rede: `D2`..`D9`, `D14`..`D17` (/WRAM, Refresh, /ASEL, EDCLK, /CE, /IRQ ou /UWR, /WR ou /LWR, /RD ou /CAS0, /PAWR ou /AS, /PARD ou /TIME, VCLK, /RESET ou /VRES ou /MRES) | O pino do Mega fica na rede `Dn_M`; o resistor liga ao slot. **Valor de fábrica 0 Ω** (fio): a placa se comporta como a anterior. Para proteger de verdade, troque por 47 a 100 Ω depois de medir os tempos na bancada (ver abaixo) |
| TVS (ou zener de 5,1 V) nas mesmas linhas | D3 a D14 (DO-35 em pé), **não montar (DNP)** | no lado do slot de cada resistor, cátodo na linha e ânodo no GND | Só para quem quiser proteção de ESD; capacitância e tempo não foram medidos |
| Pull-up de `/VRES` | R15 10 kΩ, **DNP** | `/VRES` (B27 do Mega Drive, rede `D17`) ao 5V chaveado | Só para o Open EverDrive (HW-MD-1) |
| Botão de reset | SW1 (tátil 6 mm) | `RESET` do Mega (pino RST1) ao GND, canto de baixo à esquerda | O botão do Mega fica sob o shield |
| Chave de 5V dos slots | Q1 P-MOSFET em TO-220 (IRF9540N ou equivalente), R16 100 kΩ, R17 100 Ω, R18 1 kΩ, D2 LED verde | Q1: fonte no 5V do Mega, dreno em `+5V_CART`, porta em `PWR_G`. `+5V_CART` alimenta SNES (27, 58), Mega Drive (A2, A31), Si5351, PIC, C2 a C6 e o pull-up R2 | Comando no **D19** (PD2): **nível baixo liga**. R16 mantém desligado com o Mega em reset. O LED verde acende com o 5V dos slots ligado |
| Furos M3 alinhados com o Mega | MH5, MH6, MH7 (3,2 mm, não metalizados) | (35,24; 60,2), (110,17; 60,2) e (33,97; 108,46) mm: três dos seis furos do Mega que ficam livres | Os outros três caem no meio das linhas dos slots |

Também mudaram de lugar (a placa foi roteada de novo): o PIC (U2) e o C4, os pontos de teste, o C6 e os textos do silk.

## Como o comando D19 funciona

`firmware/oscr/src/dumper/Dumper.cpp` liga o 5V dos slots no `setup()` (`cartPower(true)`: D19 saída em nível baixo, 50 ms de espera), então com o firmware desta árvore a placa se comporta como as anteriores. **Comando `POWER` (D116, só software):** grave o firmware com `pio run -e SerialASCII_Power -t upload` (em `firmware/oscr`); ele começa com o 5V **desligado** e o programa liga (a CLI e a GUI ligam sozinhas). `dumper power off` solta todos os pinos, abre o Q1 e espera 2 s (sem o transistor de descarga da v. 1.3 não há como confirmar que o rail caiu: meça com o multímetro antes de trocar o cartucho); `dumper power on` liga de novo. Com o firmware padrão (`SerialASCII`) nada muda: o 5V liga no `setup()`. A chave física, o LED "seguro trocar" e a descarga forçada ficam para a v. 1.3 (`docs/troca-de-cartucho.md`, D115).

## Antes de ligar um cartucho (testes de bancada, nada foi feito)

1. **Q1:** com o IRF9540N a Vgs = −5 V a queda no MOSFET não está no datasheet (só a −10 V). Meça com a carga (cartucho SNES ou MD) a tensão em `+5V_CART`: tem que ficar ≥ 4,7 V. Se cair demais, troque por um P-MOSFET de nível lógico em TO-220.
2. **Sem o firmware:** com o Mega sem programa (ou em reset) o `+5V_CART` tem que ficar em 0 V e o LED verde apagado.
3. **Resistores série:** monte os R3 a R14 com 0 Ω no primeiro teste. Com 47 a 100 Ω, repita o dump de um cartucho SNES e de um Mega Drive e compare o CRC32; aumente o valor só se os dumps continuarem iguais.
4. **Reset:** o botão deve reiniciar o Mega (a serial cai e volta).

## Lista de peças acrescentadas

| Ref. | Qtd | Valor | Footprint |
|---|---|---|---|
| R3 a R14 | 12 | 0 Ω (fio) ou 47 a 100 Ω, 1/4 W | `R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` |
| D3 a D14 | 12 (DNP) | TVS 5 V ou zener 5,1 V, DO-35 | `D_DO-35_SOD27_P2.54mm_Vertical_CathodeUp` |
| R15 | 1 (DNP) | 10 kΩ | `R_Axial_DIN0204...Vertical` |
| R16, R17, R18 | 3 | 100 kΩ, 100 Ω, 1 kΩ | idem |
| Q1 | 1 | IRF9540N (P-MOSFET, TO-220) | `TO-220-3_Vertical` |
| D2 | 1 | LED verde 3 mm | `LED_D3.0mm` |
| SW1 | 1 | botão tátil 6 × 6 mm, 4 pinos | `SW_PUSH_6mm` |
| Espaçadores M3 + parafusos | 3 | entre o shield e o Mega, nos furos MH5 a MH7 | |

O `+5V` do Mega agora só alimenta o LED D1, o C1, o TP1 e a fonte do Q1; tudo o mais fica no `+5V_CART`.

## O que não entrou

- Resistores série e TVS nas **linhas de endereço e de dados** (cerca de 44 redes): sem espaço na placa de duas camadas sem aumentar muito o tamanho. Só as linhas de controle estão protegidas.
- LED "seguro trocar" e descarga forçada do 5V (v. 1.3, D115; a chave física foi cancelada em D123). O comando `POWER` em software já existe (D116).
- O RP2040 no lugar do PIC (fica para a v. 1.3).
