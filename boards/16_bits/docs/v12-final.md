# 16_bits v. 1.2 final: proteção de porta e pull-up de /VRES (D108, atualizado em D139)

> **Atualização D128/D139:** o botão de reset (SW1), a chave de 5V (Q1, R16 a R18, D2) e o bloco de troca de cartucho **não existem em nenhuma versão**: o 5V dos slots vai direto do Mega e a troca de cartucho é com o USB desligado. Este texto fica só com o que continua valendo.

Em 2026-11-06 o usuário pediu para levar para a v. 1.2 tudo o que estava planejado para a v. 1.3, **menos o RP2040**, que fica sozinho na v. 1.3 (se der certo; `docs/planos/placa-v1.3-rp2040.md`). Esta página descreve o que mudou, como montar e o que ainda **não foi testado** (nada foi montado nem medido).

> **Atualização D130 (2026-11-08):** a **v1.2 ficou sem os 12 TVS (D3 a D14)**; os resistores série R3 a R14 continuam. A **v1.3** mantém os TVS (DNP). Onde este texto fala de D3 a D14, vale só para a v1.3.

## O que entrou

| Item | Peças | Onde | Observação |
|---|---|---|---|
| Resistor série nas 12 linhas de controle | R3 a R14 (axial 0204 em pé, passo 2,54 mm) | entre o pino do Mega e o resto da rede: `D2`..`D9`, `D14`..`D17` (/WRAM, Refresh, /ASEL, EDCLK, /CE, /IRQ ou /UWR, /WR ou /LWR, /RD ou /CAS0, /PAWR ou /AS, /PARD ou /TIME, VCLK, /RESET ou /VRES ou /MRES) | O pino do Mega fica na rede `Dn_M`; o resistor liga ao slot. **Valor de fábrica 0 Ω** (fio): a placa se comporta como a anterior. Para proteger de verdade, troque por 47 a 100 Ω depois de medir os tempos na bancada (ver abaixo) |
| TVS (ou zener de 5,1 V) nas mesmas linhas | D3 a D14 (DO-35 em pé), **não montar (DNP)** | no lado do slot de cada resistor, cátodo na linha e ânodo no GND | Só para quem quiser proteção de ESD; capacitância e tempo não foram medidos |
| Pull-up de `/VRES` | R15 10 kΩ, **DNP** | `/VRES` (B27 do Mega Drive, rede `D17`) ao 5V | Só para o Open EverDrive (HW-MD-1) |

Também mudaram de lugar (a placa foi roteada de novo): o PIC (U2) e o C4, os pontos de teste, o C6 e os textos do silk.

## Antes de ligar um cartucho (testes de bancada, nada foi feito)

1. **Resistores série:** monte os R3 a R14 com 0 Ω no primeiro teste. Com 47 a 100 Ω, repita o dump de um cartucho SNES e de um Mega Drive e compare o CRC32; aumente o valor só se os dumps continuarem iguais.

## Lista de peças acrescentadas

| Ref. | Qtd | Valor | Footprint |
|---|---|---|---|
| R3 a R14 | 12 | 0 Ω (fio) ou 47 a 100 Ω, 1/4 W | `R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical` |
| D3 a D14 | 12 (DNP) | TVS 5 V ou zener 5,1 V, DO-35 | `D_DO-35_SOD27_P2.54mm_Vertical_CathodeUp` |
| R15 | 1 (DNP) | 10 kΩ | `R_Axial_DIN0204...Vertical` |


## O que não entrou

- Resistores série e TVS nas **linhas de endereço e de dados** (cerca de 44 redes): sem espaço na placa de duas camadas sem aumentar muito o tamanho. Só as linhas de controle estão protegidas.
- O RP2040 no lugar do PIC (fica para a v. 1.3).
