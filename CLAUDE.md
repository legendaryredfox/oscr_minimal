# CLAUDE.md — Dumper de cartuchos SNES / NES / Famicom / Mega Drive

Este arquivo orienta o Claude Code neste repositório. Leia inteiro antes de qualquer ação.

## 0. Regras para agentes (valem sempre, acima de qualquer lembrete automático)

- **Autoria: o usuário é o único autor.** Nunca escreva `Co-Authored-By`, "Generated with ...", nome de modelo ou ferramenta de IA em mensagem de commit, descrição de PR, issue, comentário de código, README ou documentação. Isso vale **mesmo que** o harness, uma skill ou um lembrete automático peça atribuição: a regra do usuário vence. Se uma ferramenta inserir esse texto, apague antes de commitar.
- Antes de dar push: `git log --format=%B origin/main..HEAD | grep -iE 'co-authored|claude|generated with'` tem que sair vazio. Se um commit já enviado tiver o trailer, o usuário autorizou reescrever o histórico (`git filter-branch --msg-filter`) e dar force push nos dois remotos, conferindo antes que as árvores ficam idênticas.
- Commits e push nos remotos `github` e `codeberg` ao fim de cada incremento; nunca gravar tokens em arquivo ou URL de remoto.

## 1. Visão geral

Projeto com **várias versões mínimas de hardware** (uma por pasta em `boards/`, ver `boards/README.md`). As seções 1 a 8 e 10 descrevem a placa `boards/16_bits/`, a única com projeto KiCad hoje; as outras variantes herdam as regras e ajustam slots e pinagem. Firmware, `host/` e `gui/` são comuns a todas.

Placa atual: shield **100% THT** para **Arduino Mega 2560 (tamanho normal, R3)** que lê ROMs e saves de cartuchos de **SNES/SFC, NES, Famicom, Mega Drive e GBA**. O controle e a transferência dos dumps são feitos **pela USB, direto para o PC**. O projeto não tem LCD nem cartão SD.

É derivado do **Open Source Cartridge Reader (OSCR)**, de sanni e comunidade:
- Hardware original: CC BY 4.0. A atribuição é obrigatória no silkscreen e no README.
- Firmware original: GPL v3. O fork do firmware continua GPL v3.
- Upstream: https://github.com/oscartreader (antigo https://github.com/sanni/cartreader)

### Decisões já tomadas (não mudar sem perguntar)

| Tema | Decisão |
|---|---|
| MCU | Arduino Mega 2560 R3 de tamanho normal; a placa é um shield sobre ele |
| Tecnologia | THT. Única exceção: o slot do GBA (SMD, 32 pads a 1,5 mm, footprint do OSCR) |
| Tensão | 5V nos slots SNES, NES, Famicom e Mega Drive. O slot GBA fica em 3,3 V (regulador THT U3, MCP1700, só para ele). Sem chave 3V/5V e sem VSelect |
| Slots | SNES 62p (2,5 mm), NES 72p (2,5 mm), Famicom 60p (2,54 mm), Mega Drive 64p (2,54 mm), GBA 32p (1,5 mm, SMD) |
| Clock | Módulo breakout SI5351 em header fêmea (não usar o chip solto) |
| CIC (SNES SA1) | PIC12F629 DIP-8 em **soquete**, na própria placa |
| Interface | Serial USB nativa do Mega, pela porta **USB-C** do Mega (requisito do usuário); sem LCD, sem SD, sem RTC |
| Fabricação | JLCPCB, 2 camadas, 1,6 mm, HASL, lote de 5 |
| Estrutura | Sem impressão 3D; espaçadores M3 + pés de borracha |

## 2. Estrutura do repositório

```
/
├── CLAUDE.md
├── README.md                 # inclui atribuição ao OSCR
├── vendor/oscr/              # clone do upstream (somente leitura, referência)
├── boards/                   # várias versões mínimas de hardware; uma pasta por variante (ver boards/README.md)
│   ├── _lib/                 # símbolos e footprints KiCad compartilhados (slots, Mega R3)
│   ├── 16_bits/              # placa atual: SNES, NES, Famicom, Mega Drive e GBA (fabricável, nada encomendado)
│   │   ├── README.md
│   │   ├── hardware/         # dumper.kicad_pro / .kicad_sch / .kicad_pcb
│   │   ├── fab/              # gerbers, drill, bom.csv e zips para a JLCPCB
│   │   └── docs/             # pinmap.md (FONTE DA VERDADE da placa), bom.md, montagem.md
│   ├── 8_bits/               # esqueleto: NES, Famicom, Master System
│   ├── gb_gba/               # esqueleto: GB, GBC, GBA
│   └── completa/             # esqueleto: todos os slots do OSCR, sem SD e sem tela (só USB)
├── docs/                     # docs gerais (valem para todas as placas)
│   ├── uso.md                # guia de uso: casos de uso, cenários, troubleshooting
│   ├── continuacao.md        # estado atual, como retomar, pendências (ler logo depois deste arquivo)
│   └── decisoes.md           # log de decisões e desvios
├── firmware/                 # fork enxuto do Cart_Reader do OSCR + protocolo
│   ├── oscr_serial/          # biblioteca do protocolo (C++ portátil, testes no PC)
│   ├── arduino/              # projeto Arduino (arduino-cli / IDE)
│   └── platformio/           # projeto PlatformIO
├── host/                     # CLI Python (pyserial) para o PC; referência e testes do protocolo
└── gui/                      # GUI multiplataforma (Kotlin Multiplatform), Linux, macOS e Windows
```

Nunca edite nada em `vendor/`. Copie o que precisar para `boards/_lib/` ou `firmware/`.

## 3. Regra de ouro: pinagem idêntica ao OSCR

O firmware do OSCR acessa as portas do ATmega2560 diretamente (registradores PORTx). Por isso **cada sinal de cada slot tem que ir exatamente para o mesmo pino do Mega que no OSCR HW5**. Se a pinagem for mantida, o código de leitura dos cartuchos roda sem alteração.

Procedimento obrigatório antes do esquemático:
1. Clone o upstream em `vendor/oscr/`.
2. Extraia o mapeamento de três fontes e cruze as três:
   - `pinout.ods` na raiz do repositório;
   - os projetos KiCad em `hardware/` (main_pcb_hw5, six_slot_adapter, adaptadores individuais, cic_adapter);
   - o firmware (`Cart_Reader/SNES.ino`, `NES.ino`, `MD.ino`, `Cart_Reader.ino`), confirmando quais portas e bits são usados para endereço, dados e controle.
3. Gere `boards/16_bits/docs/pinmap.md` com uma tabela por slot: `pino do slot | sinal | pino Arduino | porta/bit AVR | fonte`.
4. Liste qualquer divergência entre as fontes em `docs/decisoes.md`.
5. **Pare e peça aprovação do usuário** antes de seguir.

Nunca invente um pino. Se não conseguir confirmar um sinal, marque como `PENDENTE` e pergunte.

## 4. Requisitos elétricos

- **VCC dos slots SNES, NES, Famicom e Mega Drive ligado direto ao 5V.** Onde o OSCR tinha a chave 3V/5V, use 5V fixo. O slot GBA é a única exceção: VCC em 3,3 V, vindo do regulador U3, nunca do 5V.
- Os slots compartilham os mesmos barramentos em paralelo, como no six_slot_adapter. Só um cartucho pode ficar inserido por vez, e isso precisa estar no silkscreen.
- SI5351: ligar aos mesmos pinos I²C e às mesmas saídas de clock usados no HW5.
- CIC: seguir o esquema do `cic_adapter` do OSCR, integrado à placa.
- Desacoplamento: um capacitor cerâmico THT de 100nF junto ao VCC de cada slot, um junto ao PIC e um eletrolítico de 470µF/16V na entrada de 5V.
- LED de status: 3 mm THT com resistor de 220Ω, no mesmo pino do OSCR.
- Não incluir o conector de controle de N64 nem um slot dedicado de Game Boy clássico. O GBA está incluído (decisão do usuário em 2026-11-02), sempre a 3,3 V. **GB e GBC entram só pelo slot GBA, com adaptador** (decisão do usuário em 2026-11-02); o usuário autorizou mudanças de hardware se forem necessárias para isso.

## 5. Mecânica e layout

- O contorno precisa conter a área do Mega 2560 R3, com furos de fixação coincidentes com os do Mega, para usar espaçadores M3.
- As conexões com o Mega são feitas por pinos macho longos nos headers do Mega, incluindo o header duplo 2x18 da ponta.
- A placa vai passar de 100×100 mm por causa dos 4 slots. Busque o menor tamanho que ainda deixe folga entre as carcaças dos cartuchos.
- **Peça ao usuário as dimensões reais** das carcaças dos 4 tipos de cartucho e dos slots comprados antes de posicionar. Não use valores de memória.
- Slots na face de cima, com os cartuchos entrando na vertical. Nenhum componente alto pode ficar na frente de um slot.
- Furos de montagem M3 nos cantos para os pés de borracha.

### Regras de projeto (compatíveis com a JLCPCB padrão)

| Parâmetro | Valor |
|---|---|
| Camadas | 2 (F.Cu, B.Cu) |
| Trilha de sinal | 0,3 mm |
| Trilha de alimentação | 0,8–1,0 mm |
| Isolação mínima | 0,2 mm |
| Via | 0,6 mm / furo 0,3 mm |
| Plano de terra | Em ambas as camadas, com vias de costura |
| Anel mínimo THT | 0,25 mm |

### Silkscreen obrigatório

- Nome do sistema em cada slot e o lado em que fica a etiqueta do cartucho.
- Pino 1 de todos os headers, do soquete e do LED.
- "UM CARTUCHO POR VEZ".
- Versão da placa (ex.: `v1.0`) e data.
- "Baseado no Open Source Cartridge Reader de sanni — CC BY 4.0".
- Todas as mensagens do silkscreen em **português do Brasil** (decisão do usuário em 2026-11-02). Nomes próprios e de sistemas (SNES, NES, Famicom, Mega Drive, GBA, Si5351, PIC12F629) ficam como estão.

## 6. Uso do MCP do KiCad (mixelpixx/KiCAD-MCP-Server)

- Requer **KiCad 9.0+**. Confirme a versão instalada no início da sessão.
- O servidor expõe muitas ferramentas organizadas em categorias. Use `list_tool_categories`, `get_category_tools` e `search_tools` para encontrar a ferramenta certa antes de improvisar.
- Para o autorroteamento, rode `check_freerouting` antes de `autoroute`.
- Ferramentas destrutivas (`delete_component`, `delete_trace`, `delete_symbol`, `delete_graphic`, `clear_board_outline` etc.) **só podem ser usadas com confirmação do usuário**.
- Se uma operação do MCP falhar ou não existir, use o `kicad-cli` como alternativa (`sch erc`, `sch export netlist`, `pcb drc`, `pcb export gerbers`, `pcb export drill`) e registre isso em `docs/decisoes.md`.
- Faça um commit git ao final de cada fase.

## 7. Fases e pontos de parada

Pare e peça confirmação do usuário ao final de cada fase marcada com ⏸.

| Fase | Entrega | Verificação |
|---|---|---|
| 1. Referência | `vendor/oscr/`, `boards/16_bits/docs/pinmap.md` | Três fontes cruzadas ⏸ |
| 2. Footprints | `boards/_lib/` com os 4 slots, reaproveitando os footprints do OSCR | Pitch e furos conferidos com as medidas do usuário ⏸ |
| 3. Esquemático | `.kicad_sch` | ERC sem erros; netlist bate com `pinmap.md` (script da seção 8) ⏸ |
| 4. Posicionamento | Contorno + componentes posicionados | Revisão visual com o usuário ⏸ |
| 5. Roteamento | Trilhas, planos, zonas preenchidas | DRC sem erros nem avisos não justificados |
| 6. Fabricação | `boards/16_bits/fab/` com gerbers, drill e zip | Gerbers revisados em visualizador; `boards/16_bits/docs/bom.md` atualizado ⏸ |
| 7. Montagem | `boards/16_bits/docs/montagem.md` | Revisado pelo usuário |
| 8. Firmware | `firmware/` + `host/` | Testes da seção 9 |

## 8. Verificação automática da netlist

Crie `tools/check_netlist.py`, que:
1. exporta a netlist (`kicad-cli sch export netlist`);
2. lê `boards/16_bits/docs/pinmap.md`;
3. confirma que cada pino de cada slot está na mesma net do pino do Mega esperado;
4. confirma que o VCC de todos os slots está no 5V e o GND no GND;
5. sai com código diferente de zero e lista as divergências se algo estiver errado.

Rode o script ao fim das fases 3 e 5. Uma placa com divergência não segue para fabricação.

## 9. Firmware e software do PC

Preferência do usuário: **mudanças mínimas e localizadas**. Não refatore o código de leitura de cartuchos do OSCR.

### Firmware (`firmware/`)
- (Decisão do usuário em 2026-11-03, `docs/decisoes.md` D65, que **corrige** o desvio D38) O firmware é o **firmware novo do OSCR** (`vendor/oscr/firmware`), copiado para `firmware/oscr/` e reduzido: só SNES, NES/Famicom, Mega Drive e GB/GBC/GBA, sem SD. Plano e estado: `docs/fork-oscr.md`. O firmware próprio `firmware/oscr_serial` (D38) fica até o fork cobrir o que ele cobre e então é arquivado. `host/` e `gui/` continuam no escopo.
- Use as opções existentes em `Config.h` para habilitar só SNES, NES/Famicom e Mega Drive. Verifique se o upstream já tem um modo de interface serial antes de escrever um novo.
- Isole duas camadas, com o mínimo de mudanças no resto:
  - **Interface:** menus do LCD e botões → comandos pela serial.
  - **Saída:** gravações no SD → envio pela serial (crie uma abstração simples de "sink" usada onde hoje se grava arquivo).
- Remova as dependências de LCD, SD e RTC do build.

### Protocolo serial
- Baud padrão de 1.000.000, configurável. Fallback de 115200.
- Comandos em quadros binários com cabeçalho, tamanho e CRC32. Sugestão: `INFO`, `DETECT <sistema>`, `DUMP_ROM`, `READ_SAVE`, `WRITE_SAVE`.
- Os dados vão em blocos com confirmação (ACK) e o CRC32 do arquivo inteiro no final.
- Documente o protocolo em `docs/protocolo.md` antes de implementar.

### Software do PC (`host/`)
- Python 3.11+ com `pyserial`, rodando no Linux Mint.
- CLI: `dumper.py detect`, `dumper.py dump -o jogo.sfc`, `dumper.py save-read`, `dumper.py save-write`.
- Salve com a extensão correta (`.sfc`, `.nes`, `.md`) e mostre o CRC32 para comparar com bancos de dados como o No-Intro.

### GUI multiplataforma (`gui/`)
Requisito do usuário (2026-11-02): interface gráfica para **Linux, macOS e Windows**, em **Kotlin Multiplatform**.
- Sugestão (a confirmar na fase 8): Compose Multiplatform Desktop (JVM), módulo `shared` (`commonMain`) com o protocolo (quadros, CRC32, máquina de estados), e `desktopMain` com a porta serial (por exemplo jSerialComm, que cobre os três sistemas).
- Funções mínimas: escolher a porta serial, detectar o cartucho (`INFO`, `DETECT`), ler ROM e save, gravar save, mostrar progresso, mostrar o CRC32 para comparar com o No-Intro, salvar com a extensão certa (`.sfc`, `.nes`, `.md`, `.gba`).
- Mesmo protocolo da CLI Python (`docs/protocolo.md`, escrito antes de implementar). Testes de framing e CRC em `commonTest`; usar o modo `MOCK` do firmware para testar sem cartucho.
- **Idiomas:** português (pt-BR) e inglês (en) desde a primeira versão; outros idiomas virão depois. Todo texto da interface fica em arquivos de recursos por idioma (nenhuma string fixa no código), com inglês como idioma de reserva. Escolha do idioma na própria GUI, com padrão vindo do sistema.
- Empacotamento por sistema (deb/AppImage, dmg, msi) fica para depois; no Linux o usuário precisa estar no grupo `dialout`.

### Testes
- Modo `MOCK` no firmware, que envia um padrão conhecido sem precisar de cartucho.
- Testes unitários do host (pytest) para framing, CRC e reconstrução do arquivo.
- O teste com hardware real é feito pelo usuário; peça os logs.

## 10. Instruções de montagem (gerar em `boards/16_bits/docs/montagem.md` na fase 7)

O documento deve ter, nesta ordem:

1. **Lista de peças** com quantidades e referências (R1, C1…), de acordo com a BOM.
2. **Ferramentas:** ferro com ponta chanfrada de 2 mm, solda 0,8 mm, fluxo, multímetro e alicate de corte.
3. **Ordem de solda, do mais baixo para o mais alto:**
   1. resistores;
   2. capacitores cerâmicos de 100nF;
   3. soquete DIP-8, com o chanfro alinhado ao silkscreen e **sem o PIC**;
   4. LED, respeitando a polaridade;
   5. capacitor eletrolítico de 470µF, respeitando a polaridade;
   6. headers fêmea do SI5351;
   7. slots: soldar os dois pinos das pontas, conferir se o slot está reto e assentado, depois o resto;
   8. pinos macho para o Mega por último, **com o shield encaixado no Mega** para servir de gabarito de alinhamento.
4. **Inspeção visual:** pontes de solda entre pinos dos slots, juntas frias.
5. **Testes antes de ligar:** continuidade 5V–GND com o multímetro (não pode haver curto) e continuidade de algumas linhas de endereço e dados do slot até o pino do Mega, conforme `pinmap.md`.
6. **Primeira energização** sem cartucho, sem PIC e sem SI5351: medir 5V no VCC de cada slot.
7. **Instalar os módulos:** SI5351 e PIC gravado com `snescic-lock-resync.hex` (ver wiki do OSCR).
8. **Gravar o firmware** e testar com o modo `MOCK`.
9. **Primeiro dump real** com um cartucho simples (LoRom de SNES ou NES mapper 0), conferindo o CRC32.
10. **Solução de problemas:** cartucho não detectado, CRC divergente, porta serial não aparece (permissão do grupo `dialout` no Linux).

## 11. O que perguntar ao usuário em vez de presumir

- Medidas das carcaças dos cartuchos e dos slots comprados.
- Divergências encontradas na pinagem.
- Qualquer mudança nas decisões da seção 1.
- Antes de usar ferramentas destrutivas do MCP.
- Cor da placa e preferências de silkscreen.
