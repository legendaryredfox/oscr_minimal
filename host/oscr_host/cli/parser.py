# SPDX-License-Identifier: GPL-3.0-or-later
"""Definição dos argumentos (argparse)."""
from __future__ import annotations

import argparse
import json
import sys

from .. import protocol as P
from .. import romimage as RI
from .. import __version__
from .cmd_db import cmd_identify, cmd_search
from .cmd_detect import cmd_detect
from .cmd_dump import cmd_dump
from .cmd_firmware import ENV_HELP, DEFAULT_ENV, cmd_firmware_flash
from .cmd_flash import cmd_flash_blank, cmd_flash_erase, cmd_flash_id, cmd_flash_read, cmd_flash_write
from .cmd_info import cmd_errors, cmd_info, cmd_ports, cmd_systems
from .cmd_power import cmd_power
from .cmd_rom import cmd_rom_write
from .cmd_save import cmd_save_read, cmd_save_write
from .errors import EXIT_USAGE


class _Parser(argparse.ArgumentParser):
    """Erro de uso vira saída 64 (e JSON com --json), não o 2 do argparse, que é 'nenhum cartucho'."""

    json_mode = False

    def error(self, message):
        if _Parser.json_mode:
            print(json.dumps({"ok": False, "error": {"kind": "usage", "message": message}}, ensure_ascii=False))
        else:
            self.print_usage(sys.stderr)
            print(f"{self.prog}: erro: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def _add_common(p: argparse.ArgumentParser, top: bool) -> None:
    """Opções globais. Valem antes e depois do subcomando (nos subcomandos o padrão é SUPPRESS para não sobrescrever)."""
    d = (lambda v: v) if top else (lambda v: argparse.SUPPRESS)
    p.add_argument("-p", "--port", default=d(None), help="porta serial (padrão: primeira ttyUSB/ttyACM/COM)")
    p.add_argument("-b", "--baud", type=int, default=d(None), help="baud (padrão: 1000000, depois 115200)")
    p.add_argument("--db", action="append", default=d(None), metavar="CAMINHO",
                   help="base de dados extra para identificar o jogo: arquivo ou pasta de .dat (No-Intro) ou nes20db.xml; pode repetir; também lê a variável OSCR_DB. A base do projeto (database/oscr/) já vem carregada")
    p.add_argument("--no-builtin-db", action="store_true", default=d(False),
                   help="não carrega a base de jogos que vem no projeto (database/oscr/); fica só o que vier de --db e OSCR_DB")
    p.add_argument("--simulate", action="store_true", default=d(False), help="usa o simulador em memória (sem hardware)")
    p.add_argument("--json", action="store_true", default=d(False),
                   help='saída em JSON (uma linha em stdout, sempre com "ok"; erros: {"ok":false,"error":{kind,message,hint}})')
    p.add_argument("--color", choices=("auto", "always", "never"), default=d("auto"),
                   help="cores e arte ASCII: auto (só em terminal; respeita NO_COLOR), always, never. Com --json nunca há enfeite")
    p.add_argument("--power", choices=("auto", "keep"), default=d("auto"),
                   help="placa com chave de 5V: auto (padrão) liga o 5V dos slots antes do comando e o mantém ligado; keep não mexe no 5V")
    p.add_argument("--progress", choices=("auto", "none", "jsonl"), default=d("auto"),
                   help="progresso em stderr: auto (barra se for terminal), none, jsonl (uma linha JSON por 1%%)")


EPILOG = """códigos de saída: 0 ok | 1 erro | 2 nenhum cartucho | 3 sem porta/dispositivo | 4 recusado (falta --yes) | 64 uso | 130 Ctrl+C
exemplos:
  dumper --json detect -s snes
  dumper dump -s snes -o jogo --json --progress jsonl
  dumper save-write -s snes -i jogo.sav --yes --json
  dumper power off            # antes de trocar o cartucho (placa com chave de 5V); depois: dumper power on
  dumper --simulate --json systems
Guia completo para agentes: docs/referencia/cli.md"""


def build_parser() -> argparse.ArgumentParser:
    ap = _Parser(prog="dumper", description="Dumper de cartuchos oscr_minimal", epilog=EPILOG,
                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"dumper {__version__} (protocolo {P.PROTO_VERSION})")
    _add_common(ap, True)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_, system=True, out=False, inp=False):
        sp = sub.add_parser(name, help=help_, description=help_, epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
        sp.set_defaults(fn=fn)
        _add_common(sp, False)
        if system:
            sp.add_argument("-s", "--system", default="mock", choices=sorted(P.SYSTEMS), help="sistema (padrão: mock)")
        if out:
            sp.add_argument("-o", "--output", help="arquivo de saída (a extensão certa é acrescentada; sobrescreve se existir)")
        if inp:
            sp.add_argument("-i", "--input", required=True, help="arquivo para gravar (save, ou ROM no rom-write)")
        if out or inp:
            sp.add_argument("--block", type=int, default=0, help="tamanho do bloco (padrão 512)")
        return sp

    add("ports", cmd_ports, "lista as portas seriais", system=False)
    add("systems", cmd_systems, "lista os sistemas, extensões e opções de cada um (não abre a porta)", system=False)
    add("errors", cmd_errors, "lista os códigos de erro do dispositivo e os códigos de saída da CLI (não abre a porta)", system=False)
    add("info", cmd_info, "versão do firmware e sistemas suportados", system=False)
    pwp = add("power", cmd_power, "liga, desliga ou consulta o 5V dos slots (placa com chave de 5V; para trocar o cartucho)", system=False)
    pwp.add_argument("action", choices=("on", "off", "status"), help="on liga; off solta os pinos, corta o 5V e espera a descarga; status só consulta")
    fw = add("firmware-flash", cmd_firmware_flash, "grava o firmware do fork no Arduino Mega pela USB (usa o avrdude; troca o programa da placa)", system=False)
    fw.add_argument("--hex", help="arquivo .hex do firmware (padrão: a compilação do projeto, firmware/oscr/.pio/build/<env>/firmware.hex, ou a variável OSCR_FIRMWARE_HEX)")
    fw.add_argument("--env", default=DEFAULT_ENV, help="ambiente do PlatformIO de onde vem o .hex quando --hex não é dado: " + ENV_HELP)
    fw.add_argument("--avrdude", help="caminho do avrdude (padrão: a variável AVRDUDE, o PATH ou o que o PlatformIO instalou)")
    fw.add_argument("--yes", action="store_true", help="não pergunta antes de gravar (obrigatório fora de um terminal)")
    fw.add_argument("--no-verify", action="store_true", help="não pede ao avrdude para ler o firmware de volta (padrão: confere)")
    fw.add_argument("--wait", type=float, default=12.0, help="segundos esperando o dispositivo voltar a responder ao INFO depois da gravação (padrão 12; 0 não espera)")
    fw.add_argument("--dry-run", action="store_true", help="só mostra o comando do avrdude e a versão atual do firmware; não grava")
    dtp = add("detect", cmd_detect, "detecta o cartucho")
    dtp.add_argument("--flash-id", action="store_true", help="Mega Drive: identifica também o chip de flash do cartucho (a sondagem escreve comandos de ID no cartucho; ROM de máscara os ignora)")
    ip = add("identify", cmd_identify, "identifica arquivos já salvos pelo CRC32 na base de dados (--db), sem abrir a porta")
    ip.add_argument("files", nargs="+", help="ROMs a identificar")
    sp_ = add("search", cmd_search, "procura jogos pelo nome na base de dados (--db), sem abrir a porta", system=False)
    sp_.add_argument("query", help="palavras do nome (todas precisam aparecer)")
    sp_.add_argument("--limit", type=int, default=20, help="máximo de resultados (padrão 20)")
    dp = add("dump", cmd_dump, "lê a ROM", out=True)
    dp.add_argument("--mapper", type=int, default=0, help="NES/Famicom: número do mapper (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 30, 33, 34, 48, 66, 67, 68, 69, 70, 71, 72, 73, 75, 78, 79, 86, 87, 92, 93, 94, 118, 140, 152, 180, 184, 206)")
    dp.add_argument("--prg", type=int, default=0, help="NES/Famicom: tamanho da PRG em KB (múltiplo de 16); Mega Drive e SNES (todos os tipos): tamanho da ROM em KB (0 = pelo cabeçalho)")
    dp.add_argument("--chr", type=int, default=0, help="NES/Famicom: tamanho da CHR em KB (múltiplo de 8; 0 = CHR-RAM)")
    dp.add_argument("--raw", action="store_true", help="NES/Famicom: grava PRG e CHR em arquivos separados (.prg e .chr), sem cabeçalho iNES (leitura raw do OSCR)")
    dp.add_argument("--twice", action="store_true", help="lê a ROM duas vezes e compara; se diferirem, grava as duas leituras (NOME.leitura1 e NOME.leitura2) e sai com erro (kind mismatch)")
    dp.add_argument("--game", help="NES/Famicom: nome do jogo na base NES 2.0 XML (--db); preenche --mapper, --prg e --chr que ficaram em 0")
    for sp in (add("save-read", cmd_save_read, "lê o save", out=True), add("save-write", cmd_save_write, "grava o save", inp=True)):
        sp.add_argument("--mapper", type=int, default=0, help="NES/Famicom: mapper do cartucho (1, 4, 5 ou 69 têm save com bateria)")
        sp.add_argument("--ram", type=int, default=0, help="NES/Famicom: RAM do save em KB (8, 16 ou 32; 16 e 32 só nos mappers 1 e 5; 0 = 8)")
        if sp.prog.endswith("save-write"):
            sp.add_argument("--yes", action="store_true", help="não pergunta antes de gravar (obrigatório fora de um terminal)")
            sp.add_argument("--no-backup", action="store_true", help="não lê o save atual antes de gravar")
            sp.add_argument("--no-verify", action="store_true", help="não lê o save de volta para conferir depois de gravar (padrão: confere)")
            sp.add_argument("--backup-dir", default="~/oscr_backups", help="pasta do backup (padrão ~/oscr_backups)")
    rp = add("rom-write", cmd_rom_write, "grava a ROM em um cartucho de flash (apaga o chip)", inp=True)
    rp.set_defaults(system="nes")
    rp.add_argument("--chip", choices=sorted(RI.CHIPS), help="chip de flash (NES: padrão pelo mapper do cabeçalho, 30 = nesmaker, 0 = a29040b; SNES: snes-lorom ou snes-hirom (flash CFI), snes-lorom-p0, snes-hirom-p0, snes-exlorom-p1 ou snes-exhirom-p1; obrigatório; MD: md-flash; GBA: gba-flash; GB: gb-diy-mbc3, gb-diy-mbc5, gb-hdr-mbc30, gb-cam-first, gb-cam-second, gb-orange-fm, gb-39sf-mbc5, gb-cfi)")
    rp.add_argument("--capacity", type=int, choices=RI.SNES_CAPACITIES_KB, help="SNES CFI, disposição 1x: capacidade do flash em KB (padrão: a menor em que a ROM cabe)")
    rp.add_argument("--layout", choices=list(RI.SNES_LAYOUTS), default="1x",
                    help="SNES CFI: chips do cartucho: 1x (1 chip de 2 ou 4 MB, padrão), 2x2mb, 2x4mb, 4x2mb ou 1x8mb (as três últimas: ROM de 6 a 8 MB, como no OSCR)")
    rp.add_argument("--block369", type=int, default=0, help="GBA 369-in-1: bloco de 4 MB (0 a 63) onde começa a gravação (\"Write Offset\" do OSCR); 0 = do começo (\"Write 256MB\")")
    rp.add_argument("--flash-type", choices=list(RI.FLASH_TYPES), help="SNES P0/P1: tipo do flash de 8 bits (nomes do FlashType do OSCR)")
    rp.add_argument("--flash-mb", type=int, help="SNES P0/P1: tamanho do chip em MB (1 a 8)")
    rp.add_argument("--sector-kb", type=int, help="SNES P0/P1, tipos 29gl, lh28f0xx e e28fxxxj3a: tamanho do setor em KB (potência de 2)")
    rp.add_argument("--buffer", type=int, help="SNES P0/P1, tipos 29gl, lh28f0xx e e28fxxxj3a: buffer de escrita em bytes (potência de 2, 2 a 128)")
    rp.add_argument("--yes", action="store_true", help="não pergunta antes de gravar (obrigatório fora de um terminal)")
    rp.add_argument("--no-verify", action="store_true", help="não lê a ROM de volta para conferir depois de gravar (padrão: confere)")
    rp.add_argument("--begin-timeout", type=float, default=90.0, help="segundos de espera pelo apagamento antes dos dados (padrão 90)")
    # programador de flash genérico (sistema 7)
    def flash_cmd(name, fn, help_, out=False, inp=False, write=False):
        sp = add(name, fn, help_, system=False, out=out, inp=inp)
        sp.add_argument("-s", "--system", default="flash", choices=["flash", "mock"], help="sistema (padrão: flash; mock só no simulador)")
        sp.add_argument("--bus", required=True, choices=list(RI.FLASHPROG_BUS), help="chip: 8 (flash de 8 bits no adaptador de flash), plcc32 (8 bits PLCC32 no adaptador de SNES), 16 (flash de 16 bits), eprom (27C322) ou md (flash de um cartucho de Mega Drive; só em flash-id)")
        sp.add_argument("--flash-kb", type=int, help="tamanho do chip em KB (1 a 8192; a EPROM é sempre 4096)")
        sp.add_argument("--flash-type", choices=list(RI.FLASH_TYPES), help="flash de 8 bits: tipo (nomes do FlashType do OSCR); obrigatório para apagar e gravar")
        sp.add_argument("--sector-kb", type=int, help="tipos 29gl, lh28f0xx e e28fxxxj3a: tamanho do setor em KB (potência de 2)")
        sp.add_argument("--buffer", type=int, help="tipos 29gl, lh28f0xx e e28fxxxj3a: buffer de escrita em bytes (potência de 2, 2 a 128)")
        if write or fn is cmd_flash_erase:
            sp.add_argument("--yes", action="store_true", help="não pergunta antes de apagar ou gravar (obrigatório fora de um terminal)")
            sp.add_argument("--begin-timeout", type=float, default=90.0, help="segundos de espera pelo apagamento (padrão 90)")
        if write:
            sp.add_argument("--no-verify", action="store_true", help="não lê o chip de volta para conferir depois de gravar")
        return sp

    flash_cmd("flash-id", cmd_flash_id, "programador de flash: lê o ID do chip")
    flash_cmd("flash-read", cmd_flash_read, "programador de flash: lê o chip inteiro para um arquivo", out=True)
    flash_cmd("flash-blank", cmd_flash_blank, "programador de flash: confere se o chip está em branco (lê o chip e olha no PC)")
    flash_cmd("flash-erase", cmd_flash_erase, "programador de flash: apaga o chip inteiro")
    flash_cmd("flash-write", cmd_flash_write, "programador de flash: apaga e grava o arquivo no chip (a EPROM precisa estar em branco)", inp=True, write=True)
    return ap

