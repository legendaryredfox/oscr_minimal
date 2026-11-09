# megadrive_sms — Mega Drive e Master System

![Render 3D da placa megadrive_sms (KiCad, vista de cima)](render.png)

**README por versão** (renders de cima e de baixo, peças, diferenças): [v1.0](hardware-v1.0/README.md).

Versão mínima de dois slots em shield para Arduino Mega 2560 R3, 100% THT, só USB, **5 V** fixo: **Mega Drive** (64p, 2,54 mm) e **Master System / Mark III** (50p, 2,54 mm). Um cartucho por vez. Pinagem idêntica ao OSCR HW5 (`docs/pinmap.md`; o SMS vem do `mastersystem_adapter` do OSCR).

**Estado:** v1.0, 107,1 × 83,1 mm, 5V direto nos slots (nenhuma versão corta o 5V por software, D139: desligue o USB para trocar o cartucho). ERC 0 violações; DRC sem erros nem ligações abertas; netlist confere com `docs/pinmap.md` (`tools/check_netlist.py --board megadrive_sms --sem-troca`); gerbers em `fab/`. Roteada pelo Freerouting e costurada com vias de GND: **revisar o layout no KiCad antes de encomendar**. Nada encomendado, montado nem testado.

## Decisões (2026-11-08, D136)

- Pino 47 (Clock) do SMS sem ligação; sem Si5351.
- Slot SMS de 50p a 2,54 mm (2 × 25), o mesmo tipo de item de AliExpress do slot Mega Drive (wiki de peças do OSCR). Footprint `SMS_Slot` em `boards/_lib/` (e no repositório `romulofer/kicad_libraries_romulo`). Medir o slot recebido.
- Game Gear e SG-1000 por adaptador de terceiros (Retrode, Retron, Raphnet), fora da placa.
- v1.0 sem seletor de tensão; a v1.1 acrescenta o seletor 3,3 V/5 V (D138). Nenhuma versão tem o bloco de troca de cartucho (D139).

## Diferenças em relação à `megadrive` v1.0

| Item | megadrive | megadrive_sms |
|---|---|---|
| Slots | Mega Drive | Mega Drive e Master System (50p) |
| Capacitores de 100 nF | C2, C3, C4 | C2, C3, C4 e C5 (junto ao 5V do slot SMS) |
| Placa | 107,1 × 65,1 mm | 107,1 × 83,1 mm (slot SMS abaixo da fileira de baixo do Mega) |
| Furos M3 | 4 | 6 |

## Adaptadores de referência

O slot Mega Drive recebe os adaptadores de **Game Gear** (Retron 3in1, Retrode) e de **SG-1000** (Raphnet) que o núcleo `SMS.cpp` do OSCR conhece; **só os comerciais, sem arquivos abertos**. Lista de repositórios e links (`sanni/cartreader`, `oscartreader`, Raphnet, Retrode, RetroSix, smspower.org): [`README.md`](../../README.md#adaptadores-e-repositórios-de-referência). Modos de adaptador no protocolo: `docs/referencia/protocolo.md`.

## Pendências

1. **Direção da etiqueta do cartucho SMS** no silk (não confirmada; o do Mega Drive está).
2. Medidas dos dois slots comprados e folga entre eles (cerca de 40 mm entre os centros).
3. **Firmware (D137):** o núcleo `SMS.cpp` do OSCR está ligado no fork (Master System, Game Gear e SG-1000; sistemas 8, 9 e 10 do protocolo); compila e a lógica pura tem teste no PC, **mas nada rodou em hardware**. O slot SMS desta placa é o `--mapper 0` (fiação do `mastersystem_adapter`).
4. Revisar o layout no KiCad (roteamento por autoroteador).

## Como foi feita

Scripts em `tools/boards/megadrive_sms/` (da raiz do repositório):

1. `gen_pinmap_sms.py` gera a seção Master System do `docs/pinmap.md` (netlist do `mastersystem_adapter` do OSCR, `pinout.ods`, `SMS.cpp`).
2. `add_sms_sch.py` copia o esquemático da `megadrive` v1.0 e acrescenta SMS1 (rótulos de net, `+5V`, GND, não conexões) e C5.
3. `place_sms.py` (python do sistema, com `pcbnew`) copia o PCB da `megadrive` v1.0, tira trilhas e zonas, estende a placa, põe SMS1, C5 e os furos novos.
4. Roteamento: DSN por `pcbnew`, Freerouting (`java -jar ~/.kicad-mcp/freerouting.jar -de ... -mp 30`, 0 não roteados), SES importado; depois `tools/boards/megadrive/` `tp_header.py`, `add_zones.py`, `stitch.py` e `frag_vias.py`.

Verificação:

```
python3 tools/check_netlist.py --board megadrive_sms boards/megadrive_sms/hardware-v1.0/dumper.kicad_sch
kicad-cli sch erc boards/megadrive_sms/hardware-v1.0/dumper.kicad_sch
kicad-cli pcb drc boards/megadrive_sms/hardware-v1.0/dumper.kicad_pcb
tools/export_fab.sh megadrive_sms v1.0
```

Peças opcionais: [`docs/componentes-opcionais.md`](docs/componentes-opcionais.md). BOM: [`docs/bom.md`](docs/bom.md). Montagem: [`docs/montagem.md`](docs/montagem.md).

Atribuição: baseado no Open Source Cartridge Reader de sanni (CC BY 4.0).
