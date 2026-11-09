# boards/_lib — símbolos e footprints do dumper

Gerado por `tools/build_lib.py` (não edite à mão).

| Item | Origem |
|---|---|
| `SNES_Slot`, `NES_Slot`, `FC_Slot`, `MD_Slot` (símbolo + footprint) | Copiados do OSCR (`sanni/cartreader`, `hardware/`), **CC BY 4.0**, de sanni e comunidade. Alterações: footprint ganhou courtyard, contorno Fab, rótulo e marca do pino 1; símbolo aponta para `dumper:<nome>`. |
| `SMS_Slot` (símbolo + footprint) | Copiado do OSCR (`mastersystem_adapter`, CC BY 4.0): 50 pads a 2,54 mm em 2 fileiras a 5,08 mm. Acrescentado à mão ao `dumper.kicad_sym` e ao `.pretty` (a regeneração completa por `build_lib.py` refaz os outros arquivos em formato antigo; só o `SMS_Slot` foi tirado dela). |
| `GBA_Slot` (símbolo + footprint) | Footprint do OSCR (SMD, 32 pads 5 × 1 mm a 1,5 mm, 2 pads de blindagem, 2 furos de 2,2 mm), CC BY 4.0. O símbolo é próprio, com os pads de blindagem nomeados `SHIELD_3`/`SHIELD_4`. **3,3 V apenas.** |
| `Mega2560_R3_Shield` (símbolo + footprint) | Gerado a partir das cotas oficiais do Arduino Mega 2560 R3 (docs.arduino.cc/hardware/mega-2560). 85 pads de header + 6 furos de 3,2 mm. |
| `Mega2560_R3_Shield_4MH` (só footprint) | Cópia do anterior **sem os 6 furos do Mega** (85 pads), igual ao que está dentro do PCB da `16_bits`, `snes` e `megadrive` (só os 4 M3 de canto, D25/D34). Feito à mão a partir do arquivo anterior (D107); use este na v. 1.3 se continuar sem os furos. As placas existentes ainda apontam para `Mega2560_R3_Shield`, por isso o DRC mostra `lib_footprint_mismatch` no A1. |
| `Si5351_Module` (símbolo) | Próprio. Header 1x7 do módulo: VIN, GND, SDA, SCL, CLK2, CLK1, CLK0. Usa o footprint padrão `PinSocket_1x07_P2.54mm_Vertical`. |

Atribuição: "Based on Open Source Cartridge Reader by sanni — CC BY 4.0".

O corpo dos slots é ESTIMADO (12 mm de largura, vão dos pads + 8 mm, ~16 mm de altura; ver `docs/decisoes.md` D17). Medir os slots comprados e ajustar `BODY_W`/`BODY_END` em `tools/build_lib.py`.

- `3dmodels/Fuseholder_Littelfuse_100_series_5x20mm.step`: modelo 3D aproximado do suporte de fusível 5x20 mm (F1), gerado por `tools/build_3d_fuseholder.py` porque o modelo oficial não vem no kicad-packages3d desta máquina (D140). Os PCBs apontam para ele com `${KIPRJMOD}/../../_lib/3dmodels/...`.
