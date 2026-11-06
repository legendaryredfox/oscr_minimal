# Estudo final da placa 16_bits v. 1.2 (2026-11-06)

Pedido do usuário: o projeto da v. 1.2 será fechado; fazer um último estudo para avaliar melhorias. Decisão do usuário na mesma conversa: **o RP2040 (no lugar do PIC) só entra na v. 1.3, se der certo** (`docs/placa-v1.3-rp2040.md`, D89). A v. 1.2 continua com o PIC12F629 em soquete.

O estudo foi feito só no PC: ERC, DRC com paridade, `check_netlist.py`, leitura do PCB pelo `pcbnew` (larguras, furos, distâncias) e revisão visual do silk. **Nada foi montado nem medido num Mega ou num cartucho reais.**

## 1. O que confere

| Item | Resultado |
|---|---|
| ERC | 0 violações |
| DRC (todas as severidades, com `--schematic-parity`) | 0 erros, 0 ligações abertas, 0 problemas de silk. Só avisos benignos: 11 `lib_footprint_mismatch` (A1, TP1 a TP6, MH1 a MH4: cópia do PCB difere da biblioteca), 18 campos de descrição/datasheet diferentes, `extra_footprint` (MH1 a MH4, só no PCB) e `missing_footprint` (FLG1, FLG2, só no esquemático) |
| Netlist contra `pinmap.md` | 67 nets, 225 ligações, 8 pinos de slot sem ligação, todos conferidos |
| Referências esquemático × PCB | iguais em referência, valor e footprint; sem duplicatas |
| Fabricação | 344 furos metalizados e 4 não metalizados (como diz o `PEDIDO.md`), 94 vias de 0,6/0,3 mm, trilhas de 0,3 mm (sinal) e 0,4 a 0,8 mm (5V) |
| Alimentação | 5V: 154 mm a 0,8 mm, 109 mm a 0,3 mm; a 200 mA a queda nos trechos de 0,3 mm é da ordem de 35 mV. Os 5 pinos de GND do Mega estão ligados |
| Desacoplamento | C2 a 6,1 mm do pino 27 do SNES; C3 a 10,7 mm do A2, C5 a 8,4 mm do A31 e C6 a 5,5 mm do A2 (Mega Drive) |
| Pinos sem ligação | só os que o `pinmap.md` marca: áudio do SNES (31, 62), B1, B3, B13, B14, B20, B30 do Mega Drive, e pinos do Mega que a placa não usa (D0, D1, D10 a D13, D18, D19, D39, D51 a D53, AREF, IOREF, 3V3, VIN, RST1, SDA e SCL do header duplicado) |
| LED | ânodo em 5V, cátodo no D38 por R1 de 220 Ω (cerca de 12 mA, dentro do limite do pino) |

## 2. Achados

### 2.1 C4 está longe do PIC (única violação de requisito medida)

O `CLAUDE.md` (seção 4) pede um capacitor de 100 nF **junto ao PIC**. No PCB, C4 está em (100,5; 66,0) e o PIC em U2 (pino 1, VDD, em (92,0; 46,0); pino 8, GND, em (99,6; 46,0)): **21,7 mm até o VDD e 20 mm até o GND**, por trilha de 0,3 mm. Um capacitor a essa distância filtra pouco os picos de corrente do PIC, que roda no clock do Si5351 e conversa com o SA-1. Não há aviso de DRC: é um critério de layout, não de regra.

Opções:

- **Mitigação sem mexer no cobre (recomendada para a v. 1.2):** soldar um segundo capacitor cerâmico de 100 nF no lado de baixo do soquete, entre os pinos 1 e 8 (pernas curtas, sem interferir no Mega: o espaço sob o soquete é livre). Basta uma linha na `montagem.md` e na BOM (1 capacitor a mais).
- **Correção no PCB:** mover C4 para perto do PIC e refazer duas trilhas locais, depois repetir DRC, `check_netlist` e `export_fab`. Risco baixo, mas mexe em cobre de um projeto que o usuário quer fechar.
- Na v. 1.3 o PIC sai (D89), então o problema some junto com C4, se o RP2040 der certo.

### 2.2 O aviso do USB não está no silk da 16_bits

Nas placas de um cartucho o silk agora diz "NÃO COLOQUE NEM RETIRE / O CARTUCHO COM USB LIGADO" (D104). Esta placa continua só com "UM CARTUCHO POR VEZ". É a mesma segurança (trocar de cartucho com o Mega energiado pode queimar portas), vale mais aqui porque são dois slots. **Mudança só de silk, sem tocar cobre**, no mesmo lugar do texto atual (cabe em duas linhas de 2 mm acima da linha da versão). Recomendado antes de fechar.

### 2.3 Biblioteca `_lib` fora de sincronia com o PCB

`boards/_lib/dumper.pretty/Mega2560_R3_Shield.kicad_mod` tem 91 pads (inclui 6 furos não metalizados do Mega) e o footprint dentro das placas tem 85 (decisão do usuário: só os 4 M3 de canto, D25/D34). Quem criar a v. 1.3 a partir da biblioteca recebe os 6 furos de volta. Corrigir a biblioteca (ou decidir de novo, ver 3.3) antes de começar a v. 1.3.

### 2.4 Sem proteção de porta, sem reset, sem chave de alimentação

Já documentados em `docs/melhorias-megadrive-hardware.md` (HW-MD-3 e HW-MD-4 não coube) e agora sem custo de decisão para a v. 1.2: ficam para a v. 1.3. Ver a seção 3.

## 3. Melhorias para a v. 1.3 (o RP2040 já obriga a refazer o roteamento)

Como a v. 1.3 refaz o roteamento de qualquer jeito, é a hora de pagar o que não coube na v. 1.2:

1. **Resistores série (33 a 100 Ω) e TVS nas linhas do cartucho** (HW-MD-3, HW-MD-4). Reservar o espaço desde o posicionamento, pelo menos nas linhas de controle (`/WE`, `/OE`, `/CE`, `/UWR`, `/LWR`, `/CAS2`, `/TIME`, `/VRES`) e em rede SIP nas de endereço e dados; conferir antes os tempos do firmware (62,5 ns por instrução, ver HW-MD-3).
2. **Chave de alimentação dos slots** (MOSFET P de lado alto, desligado por padrão, comandado por um pino do Mega): o firmware só liga o cartucho quando o PC pede e a GUI avisa "pode trocar o cartucho". Torna a troca com USB ligado segura em vez de só avisada. Exige pino novo (**precisa de aprovação do usuário** e linha em `decisoes.md`), pull-ups (hoje R2 em /IRQ) ligados ao 5V chaveado e firmware que deixe os pinos em alta impedância com o slot desligado (senão os diodos de ESD do cartucho o alimentam por um pino de sinal).
3. **Furos M3 alinhados com os do Mega** (dois ou três), para o shield não depender só do atrito dos 85 pinos: puxar um cartucho do slot levanta o shield e esse esforço hoje passa pelos pinos e pelo Mega. É a decisão do usuário (D25) de ficar só com os 4 furos de canto; registrar o motivo da mudança se ela for reaberta.
4. **Botão de reset** (o pad `RST1` do Mega está sem ligação e o botão do Mega fica sob o shield).
5. **Pull-up de `/VRES` com pad DNP** (HW-MD-1), só se for usar o Open EverDrive.
6. Se o RP2040 entrar: o level shifter bidirecional dos dois fios do CIC (slot 55 e 24) e a trilha do `CLK2`; ver `docs/placa-v1.3-rp2040.md`.

## 4. Pendências que só o hardware responde (inalteradas)

Medidas reais dos slots e do módulo Si5351 (D17, D23), lado da etiqueta (D27, D28), altura dos espaçadores (o USB-C e o jack do Mega têm que passar por baixo), e o footprint do Mega contra uma placa real (as cotas vêm do desenho oficial da Arduino, D14 em `decisoes.md`, mas ninguém mediu um Mega físico).

## 5. Aplicado na v. 1.2 (2026-11-06, D107, a pedido do usuário: "aplique todos os fixes relevantes", "pode aplicar também melhorias no cobre")

| Achado | O que foi feito | Verificação |
|---|---|---|
| 2.1 C4 longe do PIC | C4 movido para (92; 43,5)–(97; 43,5), acima do soquete: **2,5 mm do VDD e 3,6 mm do GND** (antes 21,7 e 20 mm). 5V pelo pino 1 por uma trilha de 0,5 mm; GND pela zona de cobre que passa junto ao pino 8. O pad antigo era também a passagem do 5V e do GND entre camadas: duas vias (0,6/0,3 mm) no lugar. Rótulo do U2 movido para a direita; silk e pátio do C4 só acima do soquete (o corpo de 2,5 mm toca a borda do soquete por 0,2 mm; aviso na `montagem.md`). `tools/revisao/v12_c4.py` | DRC 0 erros, 0 abertos; `check_netlist` 67 nets e 225 ligações; ERC 0 |
| 2.2 aviso do USB | duas linhas "NÃO COLOQUE NEM RETIRE / O CARTUCHO COM USB LIGADO" junto a "UM CARTUCHO POR VEZ" (menor), data do silk 2026-11-06. `tools/revisao/v12_silk.py` | DRC de silk limpo; prévia refeita |
| 2.3 `_lib` | variante `Mega2560_R3_Shield_4MH` (85 pads) em `boards/_lib/`, para a v. 1.3; as placas atuais continuam com o `Mega2560_R3_Shield` (o aviso `lib_footprint_mismatch` do A1 é esperado) | só arquivo e README |
| Fabricação | gerbers, zip, prévias e SHA-256 refeitos; 346 furos metalizados (344 + 2 vias novas), 4 não metalizados, 96 vias | `tools/export_fab.sh 16_bits v1.2` |

**Não aplicado:** resistores série e TVS, chave de alimentação, furos M3 do Mega, reset e pull-up de `/VRES` (seção 3): exigem refazer o roteamento ou pino novo aprovado; ficam para a v. 1.3. O C4 a 2,5 mm do VDD dispensa o capacitor extra sob o soquete.
