# Montagem — placa n64 (só N64, 3,3 V) v1.0

Segue a ordem do `CLAUDE.md` (seção 10), do mais baixo para o mais alto. Referências (R1, C1...) estão no silkscreen e em `boards/n64/docs/bom.md`.

> **Segurança:** só um cartucho, de **N64**, e só com o USB desligado ao trocar (o silkscreen avisa). O VCC do slot vem do regulador U2 (3,3 V) e **nunca** do 5V. Os sinais do Mega continuam em 5 V, como o OSCR HW5 no modo 3 V.
>
> **Esta placa nunca foi montada nem testada com cartucho.** Foi roteada por autoroteador e conferida por DRC e pela netlist, não à mão. O contorno do slot e a direção da etiqueta são estimativas (D17, D27): confira com o slot comprado antes de soldar.

## 1. Lista de peças

Ver `boards/n64/docs/bom.md`. Resumo: R1 (220 Ω), R2 (1 kΩ); C4 (100 nF); C2 e C3 (1 µF cerâmicos); C1 (470 µF/16 V); D1 (LED 3 mm); U2 (MCP1700-3302E, TO-92); U1 (header fêmea 1x7 e módulo Si5351); N64_1 (slot de 50 pinos); pinos macho longos (85 posições); 6 espaçadores M3 nos furos do Mega e 4 nos cantos com pés de borracha.

## 2. Ferramentas

Ferro com ponta chanfrada de 2 mm, solda 0,8 mm, fluxo, malha dessoldadora, multímetro com continuidade e alicate de corte.

## 3. Ordem de solda (do mais baixo para o mais alto)

1. **Resistores** R1 e R2 (R2 em pé, como no silkscreen).
2. **Capacitores cerâmicos**: C4 (100 nF) e C2, C3 (1 µF). Sem polaridade.
3. **U2 (MCP1700)**, com o lado chato voltado para o desenho do silkscreen. Pinos: 1 GND, 2 entrada (5V), 3 saída (3,3 V).
4. **LED D1**, cátodo (lado reto) ligado a R1.
5. **Eletrolítico C1**, respeitando o `+`.
6. **Header fêmea do Si5351 (U1)**; ainda sem o módulo. Pino 1 (VIN, quadrado) à esquerda.
7. **Slot N64_1**: solde os dois pinos das pontas, confira se está reto e assentado, depois o resto (50 pinos, passo 2,5 mm).
8. **Pinos macho longos por último, com o shield encaixado no Mega**, que serve de gabarito: solde 2 pinos das pontas de cada tira, confira e solde o resto. Depois fixe os espaçadores.

## 4. Inspeção visual

Pontes entre pinos do slot, juntas frias, polaridade de C1 e D1, orientação do U2.

## 5. Testes antes de ligar (sem energia e sem módulo)

1. **Continuidade 5V–GND** no header do Mega: **não pode haver curto**.
2. Algumas linhas até o Mega (`pinmap.md`): N64 pino 3 (AD15) a A15; 8 (/WRITE) a D8; 10 (/READ) a D9; 20 (RESET) a D17; 21 (EEPROM_DATA) a D7 e a R2; 33 (ALE_L) a D37; 35 (ALE_H) a D36; 19 (EEPROM_CLK) ao pino 6 (CLK1) do U1.
3. Sem ligação (não podem ter continuidade com nada): N64 13, 14, 18, 24, 38, 39, 43, 44, 45, 46 e 49.
4. VCC (9, 17, 34, 42) **não** pode ter continuidade com o 5V; GND (1, 2, 6, 22, 23, 25, 26, 27, 31, 47, 48, 50) com o GND do Mega.
5. D0 e D1 do Mega não podem ter continuidade com o slot.

## 6. Primeira energização

Sem cartucho e sem módulo. Conecte o USB-C. Meça **3,3 V** (±0,1 V) no VCC do slot (N64 pino 9) e 5 V na entrada do U2. Se o 3,3 V estiver errado, pare: não coloque cartucho.

## 7. Instalar o módulo e gravar o firmware

Encaixe o Si5351 com VIN no pino 1 (VIN, GND, SDA, SCL, 2, 1, 0). Compile e grave o firmware com `n64 = true` em `firmware/oscr/user.ini` (hoje está `false`: o N64 ainda não está ligado no firmware, protocolo, host e GUI) e teste com o modo `MOCK`.

## 8. Primeiro dump real

Quando o firmware existir: ROM de um cartucho simples, 3 dumps com o mesmo CRC32, comparado ao No-Intro. Depois SRAM/FlashRAM; por último a EEPROM (usa o `CLK1` do Si5351 e o pull-up R2).

## 9. Solução de problemas

| Sintoma | O que verificar |
|---|---|
| Cartucho não detectado | Cartucho encaixado e reto; contatos limpos; VCC de 3,3 V no slot; um cartucho por vez. |
| EEPROM não lê | Si5351 instalado na ordem certa; `CLK1` no pino 19; R2 ligado ao 3,3 V. |
| Porta serial não aparece | Cabo só de carga; grupo `dialout` no Linux; driver CH340 em clones. |
| 3,3 V errado | U2 invertido; C2 e C3 ausentes (o MCP1700 oscila). |

## Pendências

Direção da etiqueta e medidas reais do slot N64 (D17, D27); altura dos espaçadores (D25); firmware, protocolo, host e GUI do N64.
