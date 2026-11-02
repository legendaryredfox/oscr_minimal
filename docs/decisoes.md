# Log de decisões e desvios

## Fase 1 — referência e pinmap (2026-11-02)

### Ambiente
- **MCP kicad** não conectava: faltava `dist/index.js`. Corrigido com `git pull` (v2.8.2 → v2.8.3), `npm install`, `npm run build` em `~/development/llms/KiCAD-MCP-Server`. Handshake testado em node 18 e 24. KiCad instalado: 9.0.9.
- `kicad-cli` usado para exportar as netlists do OSCR (`sch export netlist --format kicadxml`), via `tools/gen_pinmap.py`.

### D1 — Upstream mudou de estrutura (desvio da seção 2 do CLAUDE.md)
`github.com/oscartreader/cartreader` não existe. O upstream atual é dividido:
- `oscartreader/oscr-firmware`: firmware novo (reescrito, `src/` + `include/`, PlatformIO). Clonado em `vendor/oscr/firmware/`.
- `oscartreader/oscr-hardware`: **repositório vazio**.
- `sanni/cartreader`: repositório antigo, com `pinout.ods`, `hardware/` (KiCad) e `Cart_Reader/*.ino`. Clonado em `vendor/oscr/legacy/`.

Pinmap foi extraído do `legacy/` (única fonte com as 3 fontes juntas). Do firmware novo só conferi o LED (PD7).
**Decidido (usuário, 2026-11-02):** a base do firmware é o original (`legacy/Cart_Reader`), removendo só o que não for usado. `vendor/oscr/firmware/` (oscr-firmware) fica só como referência.

### D0 — Git
Usuário: sem git por enquanto. Sem `git init`; as "fases" não geram commit até ele pedir.

### D2 — HW5 usa "Mega Pro", este projeto usa Mega R3
O footprint do HW5 é `MEGA2560_PRO_MINI`. Os nomes dos pinos (`D22`, `A0`…) são os nomes Arduino do ATmega2560, idênticos no Mega R3. A tabela porta/bit AVR do script foi conferida contra a coluna `ATMega2560` do `pinout.ods` (sem divergência).

### D3 — Tensão
HW5 tem chave 3V/5V (`SW1`) e TPS2113 para escolher USB/bateria. Aqui: VCC dos slots direto no 5V (decisão da seção 1). Sem `U1` (TPS2113), `SW1`, `SW2`, `BT1`, `DS3231` (RTC), LCD (`J8`, `J9`), GBA (`J10`), SMD. No adaptador, o pino 3 do header liga em VCC; no `six_slot_adapter` essa net é +12V (só N64). Irrelevante: sem N64.

### D4 — /CART do Mega Drive em D40 (divergência entre fontes)
- `six_slot_adapter`: `MD1.B32 (/CART)` ligado em **D40**.
- `megadrive_adapter`: B32 **sem ligação**. `pinout.ods`: coluna Megadrive vazia em D40. `MD.ino`: não usa PG1 (D40).
- D40 também é "Reset In" do CIC SNES (pino 4 do PIC).

**Decidido (usuário, 2026-11-02):** B32 sem ligação, como no adaptador individual e no firmware. Evita dividir D40 entre MD e PIC.

### D5 — D0/D1
O HW5 leva `D0`/`D1` (RX0/TX0, serial USB) até J4.2/J4.3, mas os 4 adaptadores deixam esses pinos sem ligação no slot. Aqui `D0`/`D1` **não** vão a nenhum slot, pois são a USB do Mega.

### D6 — Diferenças só de nome (mesmo pino)
- SNES `D42..D49`: `ods` diz `A23..A16`; esquemático diz `BA7..BA0`. Mesmo pino físico (PL7..PL0).
- Mega Drive `D6`, `D7`, `D8`, `D9`: `ods` diz `CS`, `WR HIGH`, `WR LOW`, `OE`; esquemático diz `/CE_0`, `/UWR`, `/LWR`, `/CAS0`.
- SNES `D6`: `ods` `CS`, esquemático `/Cart`.

### D7 — `-fw` no Mega Drive
`MD.ino` não toca em `D2`, `D3`, `D5` (PE4, PE5, PE3: `/YS`, `/CAS2`, `EDCLK`). O HW5 e o `ods` os ligam. Mantidos como no HW5.

### D8 — Clock
- Só o SNES (SA-1) usa o Si5351 no firmware (`SNES.ino`). NES/Famicom/MD não.
- `nes_adapter` liga `CLK0` ao pino 37 (`CLK`) do NES; `famicom_adapter` e `megadrive_adapter` não ligam CLK0..2 ao slot. `ods` não lista CLK0 na coluna NES. Mantido como no adaptador NES (inofensivo).
- Pinagem do header do Si5351 no HW5 (`J7`, 7 pinos): 1=VCC, 2=GND, 3=SDA(D20), 4=SCL(D21), 5=CLK2, 6=CLK1, 7=CLK0. **PENDENTE:** o módulo indicado (AliExpress 1005012905974177) não pôde ser lido (a página carrega por JavaScript; o fetch só trouxe o rodapé do site). Falta a ordem dos pinos, o passo e as dimensões do módulo. Nada foi presumido.

### D9 — Pull-up
`pinout.ods` marca `D7 (1K Pullup)`. Só o `six_slot_adapter` tem o resistor (`R1`, 1 kΩ, VCC → D7, junto à linha /IRQ do SNES). Será incluído.

### D10 — LED de status
HW5: `D1` (3 mm) com ânodo em VCC e cátodo via `R1` 220 Ω em **D38 (PD7)**: **ativo em nível baixo** (`statusLED(true)` faz `PORTD &= ~(1<<7)`). No HW5, D38 também vai ao `VSNS` do TPS2113 e ao botão 1 (LCD). Aqui só o LED.

### D11 — Pinos do slot sem ligação
SNES 31/62 (áudio), NES `EXP_0..9` e `Security1..4`, e os não ligados dos outros slots ficam sem ligação, como no OSCR.

### D12 — Famicom
Não há coluna Famicom no `pinout.ods`: a coluna NES foi usada (os sinais PRG/CHR/M2/IRQ/CIRAM são os mesmos). Sources: esquemático `famicom_adapter` + `six_slot_adapter` + `NES.ino`.

## Fase 2 — footprints (2026-11-02)

### D13 — Slots de cartucho
Usuário: usar os mesmos slots e espaçamentos do OSCR. Copiados de `!OSCR.pretty` / `!OSCR.kicad_sym`. Conferido por script:

| Slot | Pads | Passo | Entre fileiras | Pad / furo |
|---|---|---|---|---|
| SNES | 62 | 2,5 mm (salto de 7,5 mm no meio) | 5,0 mm | 1,524 / 0,762 mm |
| NES | 72 | 2,5 mm | 5,0 mm | 1,524 / 0,762 mm |
| Famicom | 60 | 2,54 mm | 5,08 mm | 1,524 / 0,762 mm |
| Mega Drive | 64 | 2,54 mm | 5,08 mm | 1,524 / 0,762 mm |

Anel = 0,381 mm (mínimo 0,25 ✓). Nomes dos pads = pinos do símbolo (verificado: conjuntos idênticos). Os footprints originais **só têm pads**: sem contorno do corpo, sem 3D. Os courtyards são só a caixa dos pads + 1,3 mm (7,5 × 87,5 SNES, 7,5 × 90 NES, 7,6 × 76,2 Famicom, 7,6 × 81,3 Mega Drive).
**PENDENTE:** largura × profundidade × altura do corpo real de cada slot comprado. Preciso antes da fase 4 (posicionamento).

### D14 — Mega 2560 R3
Footprint e símbolo gerados por script com as cotas oficiais do Arduino (usuário confirmou usar o Mega oficial): contorno 101,6 × 53,34 mm, furos de 3,2 mm em (13,97; 2,54), (15,24; 50,8), (66,04; 7,62), (66,04; 35,56), (90,17; 50,8), (96,52; 2,54). Origem no canto inferior esquerdo. Headers: potência (7), analógicos A0..A15, digitais D0..D21 + SCL/SDA/AREF/GND, 2x18 (5V, D22..D53, GND) = 85 pads. Sem ICSP. Motivo de não reaproveitar a biblioteca `alarm-siren` já instalada no KiCad: não achei a licença dela localmente; as cotas são fatos do desenho oficial.
Todos os pads de header devem ter pino macho longo (rigidez mecânica), mesmo os sem sinal.

### D15 — Módulo Si5351 (fotos do usuário)
Header de 7 furos, na ordem (de VIN, pino quadrado, até a ponta): **VIN, GND, SDA, SCL, 2, 1, 0**. Igual ao `J7` do HW5 (VCC, GND, SDA, SCL, CLK2, CLK1, CLK0). Header fêmea 1x7, 2,54 mm. As saídas CLK0..2 também têm pads retangulares na borda, não usados.
**PENDENTE:** dimensões da placa do módulo e posição dos furos de fixação (para a fase 4).

### D16 — Peças THT padrão
Footprints do KiCad: resistores `R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` (220 Ω LED, 1 kΩ D7), LED `LED_D3.0mm`, eletrolítico `CP_Radial_D8.0mm_P3.50mm` (470 µF/16 V, como no HW5), cerâmicos 100 nF disco THT, PIC `DIP-8_W7.62mm_Socket`.

### D17 — Medidas dos slots e cartuchos (pesquisa; usuário autorizou best guess)
GitHub: só achei forks do próprio OSCR (`oscrusergroup/hardware`, `elettronike/EN022_CARTRIDGE_READER`) e um footprint de cartucho SNES de 46 pinos (`pdaehne/SNES-LoROM-Cartridge-wo-Save`, outro assunto). GitLab: nada. Nenhum projeto publica o corpo dos slots; só os pads. Então:

**Corpo do slot (ESTIMATIVA, ±3 mm, medir quando chegar):** 12 mm no eixo das fileiras × (vão dos pads + 8 mm) no comprimento × ~16 mm de altura acima da placa. Os courtyards dos footprints usam isso: SNES 12 × 93, NES 12 × 95,5, Famicom 12 × 81,7, Mega Drive 12 × 86,7 mm.

**Layout de referência (medido no `six_slot_adapter.kicad_pcb` do OSCR, 100 × 100 mm):** 6 slots paralelos, fileiras de pads a cada 15,7 a 20,9 mm (NES→Famicom 16,7; Famicom→SNES 17,7; SNES→N64 20,9; N64→Mega Drive 15,7; Mega Drive→SMS 16). Como só um cartucho fica inserido por vez, as carcaças podem se sobrepor acima da placa. **Passo mínimo adotado: 17 mm** entre fileiras de slots vizinhos.

**Carcaças (para a zona livre acima dos slots):**

| Cartucho | Dimensões (A × L × E, mm) | Fonte |
|---|---|---|
| SNES NTSC | 88 × 136 × 20 | Wikipedia (Game Pak) |
| SNES PAL/JP | 86 × 130 × 20 | Wikipedia |
| NES | 133 × 120 × ~20 | espelho da Wikipedia (12 × 13,3 × 2 cm); nesdev não tem a carcaça |
| Famicom | 108 × ~70 × 17 | ConsoleMods / Wikipedia (largura 69-71, discordam) |
| Mega Drive | **sem fonte**; chute ~ 108 × 56 × 20 | memória; medir |

Placas (nesdev): NES 100 mm de largura, borda 93,5 mm, 14,5 mm de profundidade, 1,2 mm de espessura. Famicom: placa 90 mm, borda 78,4 mm, 1,27 mm de espessura. Os 85 mm do vão de pads do SNES e 87,5 do NES são compatíveis.

Os cartuchos são mais largos que o vão dos slots (sobram ~ 20 mm de cada lado no NES). Nada alto pode ficar sob esse balanço, na altura do topo do slot.

### D18 — Si5351 com pin headers (usuário)
Módulo entra por header fêmea 1x7 2,54 mm (pinos machos do módulo). Sem furos de fixação na placa. Dimensões do módulo (listagens: ~31 × 22 mm, Adafruit/clones): reservar 32 × 23 mm de área sem peças altas ao redor do header. Estimativa.

## Fase 3 — esquemático (2026-11-02)

### D19 — KiCad atualizado de 9.0.9 para 10.0.8 (autorizado pelo usuário)
Motivo: o MCP (v2.8.3) grava esquemáticos no formato do KiCad 10 (`version 20260101`), que o `kicad-cli` 9.0.9 não abria. PPA `ppa:kicad/kicad-10.0-releases` adicionado, PPA 9.0 removido, pacotes 9.x removidos. Conferido: `kicad-cli version` = 10.0.8; `pcbnew` do venv do MCP = 10.0.8. As tabelas globais de bibliotecas do 10.0 (`~/.config/kicad/10.0/{fp,sym}-lib-table`) não existiam; copiadas de `/usr/share/kicad/template/`. As bibliotecas do projeto (`hardware/lib`) foram geradas em formato 9 e abrem no 10.
O CLAUDE.md pede "KiCad 9.0+": 10.0.8 atende.

### D20 — Limites do MCP descobertos
- Cada chamada tem limite de 30 s. `batch_connect` com ~35 pinos estoura; usar lotes de até 25.
- Quando uma chamada estoura no meio da gravação, o `.kicad_sch` pode ficar com **0 bytes** (a escrita não é atômica). Aconteceu uma vez; o esquemático foi recriado do zero (nada perdido além de tempo; sem git, sem backup). Regra: copiar o `.kicad_sch` para o scratchpad a cada 2-3 lotes.
- `create_project` gerou o `.kicad_sch` com formato 10, ok agora.

### D21 — Esquemático (`hardware/dumper.kicad_sch`, folha A0)
- Ref. `A1` = Mega2560_R3_Shield; `SNES1`, `NES1`, `FC1`, `MD1` = slots; `U1` = Si5351 (header 1x7); `U2` = PIC12F629 em soquete DIP-8; `D1`+`R1` LED em D38 (ânodo no +5V, ativo em nível baixo); `R2` 1 kΩ pull-up em D7; `C1` 470 µF/16 V; `C2..C5` 100 nF (um por slot); `C6` 100 nF (PIC); `FLG1/FLG2` = PWR_FLAG em +5V/GND.
- Ligações por rótulo de net, mesmo nome do HW5 (`D22`, `A0`, `CLK0`, `+5V`, `GND`, `CIC_DATA_0/1`, `CIC_RESET`, `LED_K`). Mega: 5V1/5V3/5V4 em +5V; GND1, GND2, GND3, GND5, GND6 em GND.
- 45 pinos marcados "sem ligação": os dos slots que o OSCR deixa livres, B32 do Mega Drive (D4), e os pinos do Mega não usados (D0, D1, D10..D13, D18, D19, D39, D50..D53, 3V3, VIN, RST1, IORF, AREF, SCL, SDA).
- Os caps de 100 nF foram colocados em +5V/GND sem posição física; "junto ao VCC de cada slot" é restrição da fase 4.

### Verificações
- ERC (`kicad-cli sch erc`): **0 violações** (0 erros, 0 avisos).
- `tools/check_netlist.py`: **OK**, 66 nets e 333 ligações conferem com `docs/pinmap.md`; 25 pinos de slot sem ligação conferidos. Teste negativo (uma etiqueta trocada de D37 para D36 numa cópia) é detectado: o script lista 3 divergências e sai com código 1.

## Fase 4 — posicionamento (2026-11-02)

### D22 — GBA incluído (pedido do usuário), com ressalvas
- Slot: footprint do OSCR (`!OSCR.pretty/GBA_Slot`, SMD: 32 pads de 5 × 1 mm a 1,5 mm + 2 pads de blindagem + 2 furos-guia de 2,2 mm; corpo ~17,5 × 57 mm). **É a única peça SMD da placa**, aprovada pelo usuário ao pedir o GBA. Soldar com ferro de ponta fina e fluxo (pads de 1 mm). Símbolo próprio (`dumper:GBA_Slot`) para casar os nomes dos pads de blindagem.
- Alimentação: `U3` MCP1700-3302E/TO (TO-92, 3,3 V, 250 mA) com `C7` 1 µF na entrada (5V), `C8` 1 µF na saída e `C9` 100 nF no VCC do slot. O VCC do GBA (`+3V3`) nunca encosta no 5V (o verificador checa).
- Lógica: o Mega fala a 5V com o cartucho a 3,3 V, direto, sem conversor, como no HW5 (conferi: não há conversor de nível na netlist do `main_pcb_hw5`). É o comportamento do OSCR; risco aceito. Um conversor seria um módulo (usuário pediu para evitar).
- Pinos: GBA1.1=VCC(3V3), 2=CLK→D16, 3=WR→D8, 4=RD→D9, 5=CS1→D6, 6..21=AD0..AD15→A0..A15, 22..29=D0_A16..D7_A23→D37..D30, 30=RST_CS2→D17, 32 e blindagens=GND. Fonte: `main_pcb_hw5` J10 + ods coluna GBA + `GBA.ino` (usa PH0, PH3, PH5, PH6).
- **Desvio:** o pino 31 (AUD_IRQ → D7) fica **sem ligação**. No HW5 vai ao D7; aqui D7 tem o pull-up de 1 kΩ para 5V (do SNES) e levaria 5V a um pino de cartucho 3,3 V. `GBA.ino` não usa PH4 (D7).
- O slot GBA também aceita cartuchos GB com adaptador, como no OSCR. Não foi verificado aqui.
- CLAUDE.md atualizado: tabela de decisões (tecnologia, tensão, slots) e seção 4.

### D23 — Placa e layout
- Placa **144 × 108 mm** (retângulo, 2 camadas). Origem do quadro "Mega": canto inferior esquerdo do Mega; PCB = (20 + x_m, 20 + 91 − y_m). Calculado por `tools/plan_layout.py`.
- Mega R3 (footprint) em x_m 0..101,6 / y_m 0..53,34. Slots paralelos ao lado maior, pino 1 à esquerda (como o OSCR), em y_m: Mega Drive −8, Famicom 21,6, NES 61, SNES 82. Os centros respeitam as faixas proibidas pelos furos do Mega (porcas de 7 mm); por isso os slots ficam fora da faixa do Mega (y_m −1..11, 32..39, 47..54), exceto o Famicom que cabe entre elas.
- Passo mínimo entre slots vizinhos: 21 mm (NES→SNES); com cartuchos de 20 mm de espessura sobra 1 mm entre carcaças, mesmo com os quatro inseridos.
- Faixa direita (x_m 102..144): GBA (x_m 114..141, y_m −10..48), coluna de peças (Si5351 header, PIC DIP-8, LED, R1, R2, C1, U3, C6..C9), módulo Si5351 acima (reserva ~23 × 33 mm, centro do header em y_m 74).
- 4 furos de canto M3 (3,2 mm) a 3 mm da borda, para os pés. Furos do Mega (6) no footprint do shield.
- Caps de 100 nF de cada slot ao lado do corpo do slot, perto do pino de VCC (SNES 27, NES 36, Famicom 30, Mega Drive A2).

### D24 — Silkscreen
Texto: "UM CARTUCHO POR VEZ"; "SNES / NES / FAMICOM / MEGA DRIVE v1.0 2026-11-02"; "Projeto original: github.com/sanni/cartreader"; "Adaptado por: github.com/legendaryredfox/oscr_minimal" (link informado pelo usuário, com `oscr`); "Based on Open Source Cartridge Reader by sanni — CC BY 4.0"; nomes dos slots e pino 1 nos footprints; "GBA 3V3 / SOMENTE GBA - 3,3 V"; "Si5351 pino 1 = VIN".
**Pendente:** lado da etiqueta do cartucho em cada slot (CLAUDE.md seção 5). Não dá para inferir do OSCR nem do footprint; confirmar com o slot físico. Silk de pino 1 do header do Si5351, do DIP-8 e do LED vêm dos footprints padrão do KiCad.

### D25 — Mecânica (a validar)
Shield apoiado nos 6 furos do Mega com espaçadores M3 fêmea-fêmea de ~12 mm (o USB-B e o jack do Mega chegam a ~11 mm) e pinos macho longos (cauda ≥ 10 mm) em todos os pads de header. O conjunto não tem parafuso por cima dos furos internos do Mega (x=66,04), porque ficam entre os slots. O Mega fica mais alto que a mesa: os pés de borracha dos cantos da placa precisam de espaçadores de comprimento a definir na fase 7.

### D26 — DRC (`kicad-cli pcb drc`, sem trilhas ainda)
0 erros. 12 avisos, justificados: 5 `silk_overlap` e 2 `silk_over_copper` (referências/contorno de silk perto de pads; ajustar na fase 5), 4 `lib_footprint_mismatch` (furos de fixação criados pelo MCP; pad NPTH de 4,2 mm vs 3,2 mm da biblioteca; sem efeito), 1 `silk_edge_clearance`. 306 ligações ainda não roteadas (esperado: fase 5).

### D27 — Orientação da etiqueta (resposta do usuário)
Usuário: o cartucho fica "de frente" para o USB; a posição dos slots não importa, desde que a direção esteja indicada no silk; os slots devem ser paralelos, exceto o GB/GBA.
Como os slots correm no sentido do lado maior do Mega, o cartucho entra de perfil; a etiqueta só pode olhar para os lados de cima ou de baixo da placa. Escolhi **para baixo** (lado em que ficam o USB e o jack do Mega, no canto inferior esquerdo). Silk: "ETIQUETA DO CARTUCHO PARA BAIXO (LADO DO USB)" e "v v ETIQUETA v v" no lado de baixo de cada slot (SNES, NES, Famicom, Mega Drive). O GBA fica sem indicação.
**A CONFIRMAR com o slot físico:** a direção real da etiqueta depende da peça (de que lado do slot o cartucho encaixa em relação ao pino 1). Se estiver ao contrário, basta girar o slot 180° (o pino 1 vai para a outra ponta; as nets não mudam) ou trocar o texto. Também falta definir a direção do GBA.

### D28 — GBA/GB entra na horizontal (usuário)
O cartucho GBA/GB fica **paralelo à placa**. Pelo footprint do OSCR, os pads de sinal estão na traseira (x local −7,5..−2,5) e as abas de blindagem na frente (+16,25); então a boca do slot abre para **+x** (direita da placa) e o cartucho sai pela borda direita, sem passar sobre outras peças. A etiqueta fica **para cima**. Silk: "GBA: ETIQUETA P/ CIMA" e "ENTRA PELA DIREITA" (substitui o "ETIQUETA GBA >>>" anterior, que estava errado). A direção "de costas para as placas" do usuário bate com isso: o cartucho se afasta dos outros slots. A confirmar com o slot físico.

## Requisito novo (2026-11-02): GUI multiplataforma
GUI para Linux, macOS e Windows em Kotlin Multiplatform (pedido do usuário). Entra na fase 8 junto com firmware e `host/`. CLAUDE.md atualizado (estrutura do repositório e seção 9). Escolhas técnicas (Compose Multiplatform Desktop, jSerialComm) são sugestões a validar; nada foi implementado. Não afeta o hardware: a USB do Mega e o baud de 1.000.000 continuam iguais (conferir se o jSerialComm abre 1 Mbaud nos três sistemas).

**Idiomas da GUI (usuário, 2026-11-02):** português e inglês na primeira versão, expansão depois. Strings em recursos por idioma (em Compose Multiplatform, o sistema de recursos `composeResources` com `strings.xml` por locale), inglês como fallback; troca de idioma na GUI. Mensagens do firmware/protocolo continuam em códigos, traduzidos só na GUI.

### D29 — Silkscreen em português do Brasil (usuário)
Todos os textos de silk em pt-BR. O único que estava em inglês era a atribuição; agora: "Baseado no Open Source Cartridge Reader de sanni — CC BY 4.0" (a atribuição à obra e à licença continua presente). Os demais já estavam em português ("UM CARTUCHO POR VEZ", "Projeto original", "Adaptado por", "ETIQUETA ...", "SOMENTE GBA - 3,3 V", "Si5351 pino 1 = VIN"). CLAUDE.md seção 5 atualizado. Textos que vêm de footprints padrão do KiCad (referências R1, C1 etc.) não são mensagens.

### D30 — Interface com o PC: USB-C (usuário, 2026-11-02)
A ligação ao computador deve ser USB-C. A foto do Mega que o usuário mostrou é um clone com conector **USB-C** no canto inferior esquerdo (ao lado do jack de energia), então o shield não ganha conector USB; a porta é a do Mega. O shield (borda esquerda em x_m 0, igual à do Mega) não cobre o conector, que fica para fora da borda. Pontos a confirmar quando o Mega chegar:
- Se for o clone da foto, o conversor USB-serial costuma ser um CH340 (aparece como `/dev/ttyUSB0`, não `ttyACM0`); a GUI e a CLI devem listar os dois tipos de porta. Para 1.000.000 baud o CH340 serve (aceita até 2 Mbaud); o ATmega16U2 do Mega oficial também.
- Mega oficial usa USB-B: nesse caso precisa de cabo USB-C para USB-B (ou adaptador). Não há mudança de hardware.
- O CH340 precisa de driver no Windows e no macOS antigo; documentar na GUI/README.

## Fase 5 — roteamento (2026-11-02)

### D31 — Resultado
- **Método:** DSN exportado pelo MCP (`export_dsn`, com as classes de net), Freerouting 2.x rodado fora do MCP (`java -jar ~/.kicad-mcp/freerouting.jar -de ... -do ... -mp 60`) e SES importado (`import_ses`). Motivo: o limite de 30 s por chamada do MCP já zerou um `.kicad_sch` (D20); o roteador leva ~10 min. `check_freerouting` OK (Java 26, jar em `~/.kicad-mcp`).
- **Freerouting:** 306 ligações → 0 sem rota e 0 violações em 594 s (11 passadas).
- **Trilhas:** 3.097 segmentos; alimentação (`+5V`, `+3V3`) com 0,8 mm (87 segmentos); sinal com 0,3 mm (2.849); GND com 0,3 mm (144) além dos planos. **17 segmentos de sinal ficaram com 0,23 mm**: o roteador estreitou onde precisava passar entre pads de passo 1,5 mm (GBA) e de 2,5 mm. Está acima do mínimo da regra de projeto (0,2 mm) e do mínimo da JLCPCB (0,127 mm); mantido.
- **Vias:** 336 de 0,6/0,3 mm e 1 de 0,8/0,4 mm (alimentação), mais 73 vias de costura de GND (grade de 8 mm, margem de 1,5 mm da borda). Uma via de costura duplicada com uma via do roteador foi removida (hole_to_hole).
- **Planos de GND** nas duas camadas (F.Cu e B.Cu), folga 0,3 mm, largura mínima 0,2 mm, alívio térmico nos pads THT. Quatro pads de GND ficaram com conexão sólida (`MD1.A1`, `MD1.A32`, `NES1.1`, `U3.1`) porque o alívio térmico ficava sem raios ("starved thermal"). Isso dificulta um pouco soldar esses pinos: usar ferro mais quente.
- **Preenchimento das zonas** feito por `tools/fill_zones.py` (o refill do MCP via SWIG pode travar). Nomes de nets da PCB alinhados à netlist por `tools/sync_net_names.py` (a PCB usava `+5V`, o esquemático `/+5V`; os pinos sem ligação ganharam as nets `unconnected-(...)`).

### Verificações finais da fase 5
- **DRC** (`kicad-cli pcb drc --schematic-parity`): **0 erros**, 0 ligações abertas, **4 avisos justificados**: `lib_footprint_mismatch` nos 4 furos de canto (criados pelo MCP com pad NPTH de 4,2 mm; sem efeito na fabricação).
- **Paridade esquemático × PCB:** 23 diferenças só cosméticas: 17 campos Datasheet/Description vazios nos footprints, 2 `PWR_FLAG` sem footprint (normal) e 4 furos de canto só na PCB (normal). Nenhum `net_conflict`.
- **ERC:** 0 violações. **`tools/check_netlist.py`:** OK (67 nets, 375 ligações, 26 pinos sem ligação conferidos).
- Placa final **144,1 × 108,0 mm**.

### Pendente para a fase 6 (e para você)
- Abrir `hardware/dumper.kicad_pcb` no KiCad e olhar o roteamento a olho (o Freerouting não separa sinais rápidos; o barramento é lento, mas confira os CLK0..2 do Si5351 e o D7/D16).
- Gerbers e `docs/bom.md` na fase 6. Confirmar medidas de slots e módulo antes de fabricar (D17, D23, D27).

## Fase 6 — fabricação (2026-11-02)

### D32 — Arquivos e verificação
- `hardware/fab/dumper-v1.0-jlcpcb.zip`: F.Cu, B.Cu, F/B máscara, F/B silk, Edge.Cuts (formato Protel/`.gtl`...), `PTH.drl` e `NPTH.drl` (Excellon métrico, separados). Sem camadas de pasta (montagem manual). Também em `hardware/fab/gerbers/`: `.gbrjob` e mapas de furação (fora do zip). `hardware/fab/bom.csv` vem do esquemático; `docs/bom.md` é a BOM completa.
- Conferido com `gerbonara`: 7 camadas reconhecidas, contorno **144,05 × 108,05 mm**, 915 furos metalizados (= 530 vias + 385 pads THT da placa) e 12 não metalizados. Brocas: 0,30, 0,40, 0,75, 0,762, 0,80, 0,90, 1,00, 1,016 mm (PTH) e 2,2 e 3,2 mm (NPTH); a menor, 0,3 mm, é o mínimo da JLCPCB.
- **Não** consegui olhar os gerbers num visualizador gráfico (nem `gerbv` nem o visualizador do KiCad estão disponíveis em modo texto, e o render do `gerbonara` ficou ilegível). A conferência visual foi feita na placa (render 3D do KiCad) e pelos números acima. **Abra o zip no visualizador de gerbers do KiCad ou da própria JLCPCB antes de pedir.**
- Anel mínimo de todos os pads THT ≥ 0,25 mm (o CLAUDE.md pede isso). O `MCP1700` no footprint `TO-92_Inline` tinha anel de 0,15 mm: troquei pelo footprint `TO-92` escalonado (pads de 1,3 mm, furo 0,75 mm, anel 0,275 mm), que aceita os mesmos pinos. Refiz a trilha local e o DRC.
- Ajustes da fase 5 repetidos aqui: 4 pads de GND com conexão sólida, ilhas de cobre sem GND ligadas por vias de costura (agora 530 vias no total, contra 336 do roteador), e vias duplicadas removidas.

### DRC final (placa fabricável)
`kicad-cli pcb drc --schematic-parity`: **0 erros, 0 ligações abertas**, 4 avisos `lib_footprint_mismatch` (furos de canto). Paridade só com diferenças cosméticas (campos Datasheet/Description, `PWR_FLAG` sem footprint, furos só na PCB).

### Riscos que sobram (para a conferência com as peças)
1. Medidas dos slots, do módulo Si5351 e do espaçamento mecânico (D17, D23, D25).
2. Direção da etiqueta (D27, D28).
3. Slot GBA SMD: pads de 1 mm; a máscara de solda do KiCad entre pads de 1,5 mm de passo funciona na JLCPCB, mas a solda é delicada.
4. A placa passa de 100 × 100 mm: o preço do lote é bem maior que o do lote pequeno.

## Fase 7 e 8 — estado (2026-11-02)

- **Fase 7:** `docs/montagem.md` escrito (ordem de solda, testes, primeira energização, solução de problemas, GBA SMD e regulador de 3,3 V). Falta a revisão do usuário.
- **Fase 8, feito e testado:** `docs/protocolo.md` (v1); `host/` em Python (`dumper.py detect|dump|save-read|save-write|info|ports`, `--simulate`), 36 testes `pytest` passando, incluindo o teste cruzado do cliente Python contra o código real do firmware compilado no PC; `firmware/oscr_serial` (protocolo + modo MOCK), 16 verificações C++ passando.
- **Fase 8, NÃO feito:** sketch do Mega e compilação AVR; cópia reduzida do `Cart_Reader` (o upstream usa `myFile` do SdFat ~280 vezes nos 4 sistemas; a ponte "sink" precisa ser feita com cuidado e validada com cartuchos reais; o upstream tem o modo `SERIAL_MONITOR` com menu em texto, mas ainda grava no SD); GUI Kotlin Multiplatform (`gui/`, pt-BR e en); `docs/` da GUI.
- Ferramentas já disponíveis na máquina: `arduino-cli` com `arduino:avr` instalado, Gradle 9.7 e Kotlin 2.4.

## Atualização (2026-11-02, depois da fase 8 parcial)

- **Codeberg:** repositório privado `legendaryredfox/oscr_minimal` criado pela API e enviado por HTTPS com o token em `~/.codeberg_token` (usado só no cabeçalho do `git push`; não fica gravado no remote). A chave SSH `legendaryredfox` não está cadastrada no Codeberg. GitHub e Codeberg recebem o mesmo `main`.
- **Silk (D33):** removido "(LADO DO USB)"; os textos de etiqueta de cada slot agora trazem o nome do console ("SNES: v v ETIQUETA v v", "NES: ...", "FAMICOM: ...", "MEGA DRIVE: ..."); o GBA já tinha "GBA: ETIQUETA P/ CIMA".
- **Furos do U1 (D34):** dois furos NPTH de 2,2 mm (M2), MH5 e MH6, a 20 mm um do outro (x = 131,5 mm; y = 30 e 50 mm no quadro da placa), na área reservada ao módulo Si5351, para espaçadores. Posição **estimada**: as medidas dos furos do módulo CJMCU-5351 não são conhecidas; conferir com o módulo e mover se preciso (os pontos foram escolhidos por não tocarem em trilhas, vias ou pads). Courtyard removido dos dois furos. DRC: 0 erros, 4 avisos dos furos de canto. Gerbers refeitos (915 furos metalizados, 14 não metalizados).
- **Licença (D35):** a mesma do OSCR: hardware CC BY 4.0, software GPL v3 ou posterior (`LICENSE.md`, `LICENSES/`, cabeçalhos SPDX).
- **Firmware (D36):** `firmware/arduino/oscr_dumper` (Arduino, compilado com `arduino-cli` para o Mega: 8.582 bytes de flash, 1.415 de RAM) e `firmware/platformio` (PlatformIO, `pio run` OK). Ambos usam a biblioteca `firmware/oscr_serial`, em modo MOCK. O `INFO_RESP` ganhou `max_payload` (AVR = 520).
- **GUI (D37):** `gui/` com Gradle 9.7 e Kotlin 2.4.0: `shared` (protocolo, cliente, textos pt-BR/en, testes) e `desktopApp` (Compose Desktop 1.9.3 + jSerialComm 2.11.4). Compila e os testes passam; a janela não foi executada.
- **Ainda falta:** cópia reduzida do `Cart_Reader` e a ponte da leitura real com o protocolo (`Backend` por sistema), e os testes com hardware.

## Fase 8 — firmware dos cartuchos, GUI em 4 idiomas, documentação de uso (2026-11-02)

### D38 — Firmware: leitores novos, em vez de copiar o Cart_Reader
O `Cart_Reader` do OSCR é um monolito: menus, LCD/OLED, SD (~280 usos de `myFile` nos 4 sistemas), banco de dados no SD e estado global espalhado entre os `.ino`. Adaptá-lo sem hardware seria um risco sem verificação possível. Em vez disso (e atendendo ao pedido de remover tela e outros consoles):
- `firmware/oscr_serial` ganhou `oscr_bus.h` (interfaces), `oscr_carts.{h,cpp}` (`CartBackend`) e `oscr_avr_buses.h` (HAL do ATmega2560, sequências de porta copiadas do OSCR).
- **Suportado:** SNES LoROM/HiROM (ROM até 4 MB; SRAM lida e gravada, com leitura de volta); NES e Famicom mapper 0 (cabeçalho iNES sintético, espelhamento "horizontal"); Mega Drive (ROM pelo tamanho do cabeçalho, até 4 MB); GBA (ROM, tamanho por espelhamento).
- **Não suportado ainda:** SA-1, ExHiROM e chips especiais do SNES; outros mappers do NES e saves do NES; mappers e SRAM do Mega Drive; saves do GBA; GB/GBC.
- **Testes:** 54 verificações em C++ com cartuchos simulados (dump byte a byte, cabeçalho inválido = sem cartucho, SRAM). Os dois projetos (Arduino e PlatformIO) compilam: real 12,9 KB de flash e 1,6 KB de RAM; modo de teste `-DOSCR_MOCK` 8,6 KB e 1,4 KB.
- **Não validado em hardware.** Os pontos mais prováveis de ajuste: tempos (`nop`s e `_delay_us`) e linhas de controle em `oscr_avr_buses.h`. Roteiro: `docs/uso.md`, seção 7.

### D39 — GUI: russo e chinês, ajuda embutida
`Lang` agora tem PT, EN, **RU** e **ZH** (chinês simplificado). Todos os textos continuam em `I18n.kt` (53 chaves × 4 idiomas), com teste de completude e de que RU/ZH não ficaram iguais ao inglês. A janela tem o botão **Ajuda** com casos de uso e problemas comuns nos 4 idiomas. 15 testes Kotlin passando. A janela não foi aberta (sem display aqui), então a renderização dos caracteres chineses e cirílicos não foi vista; o Compose usa as fontes do sistema.
Traduções feitas por mim (sem revisão de falante nativo): peça uma revisão.

### D40 — Documentação de uso
`docs/uso.md`: preparação, casos de uso (ler ROM e conferir CRC32, backup e restauração de save, conferir cartucho, teste sem cartucho, vários sistemas), tabela do que cada sistema suporta, solução de problemas, limites/segurança e o roteiro de primeira validação com hardware.

### D41 — NES/Famicom: mappers 1, 2, 3, 4 e 7
- O cartucho de NES não traz o mapper; o host informa `mapper`, `prg_kb` e `chr_kb` (opções opcionais de `DUMP_ROM`, `docs/protocolo.md`). Mapper 0 continua automático.
- Implementação em `oscr_carts.cpp`: MMC1 (modo PRG 3 e CHR em 4 KB, 5 escritas seriais; PRG até 256 KB), UxROM (2), CNROM (3), MMC3 (4: PRG em modo 0, CHR sem inversão) e AxROM (7). Mappers com conflito de barramento (2, 3, 7) escrevem os registradores num endereço da ROM cujo byte é igual ao valor. `NesBus` ganhou `prg_write` (HAL: `write_prg_byte` do OSCR).
- Testes: modelos independentes do hardware de cada mapper (com conflito de barramento) em `tests/test_carts.cpp`: 8 configurações de PRG/CHR, dump byte a byte igual ao original; opções inválidas (mapper desconhecido, PRG 0, CHR em mapper 2). 89 verificações no total. Host (40 testes) e Kotlin (16 testes) cobrem o transporte das opções; CLI `--mapper/--prg/--chr` e GUI (campos NES/Famicom).
- **Não validado em hardware.** Fora do escopo ainda: MMC1 de PRG > 256 KB (SUROM/SXROM), MMC3 com CHR-RAM, mappers 5, 9, 10, 11, 19, 24/26, 66, 69, 71 e outros; saves e PRG-RAM; espelhamento e bateria no cabeçalho iNES.

### D42 — GBA: leitura da SRAM de 32 KB
`GbaBus` ganhou `sram_read/sram_write` (HAL: `readByte_GBA`/`writeByte_GBA` do OSCR, com /CS2 em PH0; `begin()` agora também coloca PH0 como saída alta). `READ_SAVE` do GBA lê 32 KB assumindo SRAM; `DETECT` informa `tipo_save = 255` (desconhecido) para avisar. **Gravação não suportada** (`E_SEM_SAVE`): em cartuchos Flash, escritas na faixa da SRAM podem ser tratadas como comandos. Saber o tipo de save exigiria procurar as strings `SRAM_V`/`FLASH_V`/`EEPROM_V` na ROM inteira (minutos). 98 verificações de cartuchos simulados passando; firmware real compila (14,9 KB de flash). Não validado em hardware.

### D43 — Mega Drive: SRAM e mapper SSF2
- **SRAM:** lida do cabeçalho (`"RA"` em $1B0, tipo F820/F840/E020, início e fim), com a mesma lógica do OSCR para bytes ímpares, pares e ambos (incluindo as bases $300001 e $3C0001 e o conserto do Psy-o-blade); tamanho máximo aceito 64 KB. O registrador $A130F1 bit 0 liga a SRAM em $200000-$3FFFFF e é desligado ao terminar (a ROM não pode vazar com a SRAM ligada). A gravação usa `writeWord_MD` do OSCR e confere cada byte; no modo "ambos" a palavra é montada com dois bytes.
- **SSF2:** cabeçalho `"SEGA SSF"`; a janela 1 ($080000-$0FFFFF) varre os bancos de 512 KB pelo registrador $A130F3 (`writeSSF2Map` do OSCR, com /TIME). ROM de até 8 MB nesse modo; sem o mapper o tamanho é limitado a 4 MB.
- `MdBus` ganhou `write_word` e `map_write`. HAL com as sequências do OSCR (não validado em hardware).
- Testes: o simulador do Mega Drive modela SRAM nos 3 tipos (liga/desliga), registradores de banco e a máscara de bytes. 126 verificações de cartuchos simuladas passando. Firmware real: Arduino e PlatformIO compilam.
- **Fora do escopo:** EEPROM serial, Pier Solar, lock-on (Sonic & Knuckles), mappers piratas, saves de bateria de 16 bits fora dos endereços conhecidos.

### D44 — Mega Drive: tamanho da ROM e verificação do checksum; EEPROM fica de fora
- **Tamanho:** `prg_kb` do `DUMP_ROM` passa a ser o tamanho da ROM do Mega Drive (32 KB a 4 MB, 8 MB com SSF2). Sem ele, o firmware reduz o tamanho do cabeçalho à metade enquanto os dois lados batem em 4 pontos com conteúdo (ignora áreas só de 0xFF/0x00; não reduz ROMs SSF2). As opções valem por operação: `DETECT` as ignora e `close_read` as apaga.
- **Checksum do cabeçalho:** o host (Python, `oscr_host/verify.py`; Kotlin, `Verify.kt`) confere depois do dump: Mega Drive (soma de palavras de $200 ao fim vs $18E), SNES (soma dos bytes vs checksum, com espelhamento para tamanhos que não são potência de 2) e GBA (complemento em $BD). Aviso, não erro: há ROMs com checksum ruim de fábrica. GUI em 4 idiomas.
- **Testes:** 134 verificações de cartuchos simulados (inclui espelhamento, tamanho forçado, limites, isolamento das opções); host 45; Kotlin 20.
- **EEPROM serial do Mega Drive: não implementada.** O OSCR usa uma tabela de ~25 jogos por checksum e cinco famílias (Acclaim 1 e 2, Sega, EA, Codemasters) com ligações de SDA/SCL e tempos diferentes. Portar isso sem o hardware repetiria a minha leitura do código nos testes. Fica para quando houver os cartuchos para comparar. Também fora: Pier Solar, lock-on (Sonic & Knuckles) e mappers piratas.
