# SPDX-License-Identifier: GPL-3.0-or-later
"""Comando firmware-flash: grava o firmware do fork (`firmware/oscr`) no Arduino Mega pela USB, com o avrdude (D131).

Sem PlatformIO: basta o `.hex` e o `avrdude`. O `.hex` vem de --hex, da variável OSCR_FIRMWARE_HEX ou da compilação do projeto
(`firmware/oscr/.pio/build/<--env>/firmware.hex`). O avrdude vem de --avrdude, da variável AVRDUDE, do PATH ou do PlatformIO."""
from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import common
from .errors import CliError, EXIT_ERROR, EXIT_NO_DEVICE, EXIT_OK, EXIT_REFUSED, EXIT_USAGE
from .output import emit, progress

REPO = Path(__file__).resolve().parents[3]
DEFAULT_ENV = "SerialASCII"
ENV_HELP = ("SerialASCII (padrão), SerialASCII_Power (placa com a chave de 5V sem sensor) ou SerialASCII_PowerSense "
            "(placas v1.1 e 16_bits v1.3, com o bloco de troca)")
BOOTLOADER_BAUD = 115_200                                     # bootloader do Mega 2560 (wiring/STK500v2)
_PCT = re.compile(r"(Writing|Reading)\s*\|[# ]*\|\s*(\d+)%")


def find_hex(args) -> Path:
    cand = args.hex or os.environ.get("OSCR_FIRMWARE_HEX") or str(REPO / "firmware" / "oscr" / ".pio" / "build" / args.env / "firmware.hex")
    p = Path(cand).expanduser()
    if not p.is_file():
        raise CliError("no_hex", f"arquivo de firmware não encontrado: {p}", EXIT_USAGE,
                       "use --hex ARQUIVO.hex, ou compile antes: `cd firmware/oscr && pio run -e " + args.env + "`")
    return p


def find_avrdude(args) -> str:
    cand = args.avrdude or os.environ.get("AVRDUDE")
    if cand:
        if not (shutil.which(cand) or Path(cand).is_file()):
            raise CliError("no_avrdude", f"avrdude não encontrado: {cand}", EXIT_USAGE, "confira o caminho de --avrdude")
        return cand
    found = shutil.which("avrdude")
    if found:
        return found
    pio = sorted(glob.glob(str(Path.home() / ".platformio" / "packages" / "tool-avrdude*" / "avrdude*")))
    pio = [x for x in pio if Path(x).is_file() and not x.endswith((".conf", ".txt"))]
    if pio:
        return pio[0]
    raise CliError("no_avrdude", "avrdude não encontrado", EXIT_USAGE,
                   "instale o avrdude (Linux: `sudo apt install avrdude`; macOS: `brew install avrdude`; Windows: winget ou o pacote do Arduino) ou use --avrdude CAMINHO")


def avrdude_cmd(exe: str, port: str, hex_path: Path, verify: bool) -> list[str]:
    cmd = [exe, "-p", "atmega2560", "-c", "wiring", "-P", port, "-b", str(BOOTLOADER_BAUD), "-D"]
    if not verify:
        cmd.append("-V")
    return cmd + ["-U", f"flash:w:{hex_path}:i"]


def run_avrdude(cmd: list[str], cb_for) -> tuple[int, str]:
    """Roda o avrdude e traduz as barras dele ("Writing | ### | 45%") em progresso. Devolve (código, texto de erro)."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
    tail, buf, cbs = [], b"", {}
    assert proc.stderr is not None
    while True:
        ch = proc.stderr.read(1)
        if not ch:
            break
        if ch in (b"\r", b"\n"):
            line = buf.decode("utf-8", "replace"); buf = b""
            m = _PCT.search(line)
            if m:
                label = "gravando" if m.group(1) == "Writing" else "conferindo"
                cbs.setdefault(label, cb_for(label))(int(m.group(2)), 100)
            elif line.strip():
                tail.append(line.strip())
                tail = tail[-8:]
        else:
            buf += ch
    proc.wait()
    return proc.returncode, " | ".join(tail)


def _info_after(args, timeout: float = 12.0) -> dict | None:
    """O Mega reinicia ao fim da gravação e a porta some por um instante: tenta o INFO por alguns segundos."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            c, t, info = common._open(args)
            t.close()
            return info
        except Exception:
            time.sleep(1.0)
    return None


def cmd_firmware_flash(args) -> int:
    hex_path = find_hex(args)
    simulate = args.simulate
    exe = "avrdude (simulado)" if simulate else find_avrdude(args)
    port = args.port or ("simulador" if simulate else common.auto_port())
    before = None
    try:                                                      # a versão de antes só se o firmware atual responder; placa nova responde nada
        c, t, before = common._open(args)
        t.close()
    except Exception:
        before = None
    what = f"gravar {hex_path.name} ({hex_path.stat().st_size} bytes de HEX) em {port} com o avrdude"
    if args.dry_run:
        cmd = avrdude_cmd(exe, port, hex_path, not args.no_verify)
        emit(args, {"dry_run": True, "port": port, "hex": str(hex_path), "avrdude": exe, "command": cmd,
                    "firmware_before": before["firmware"] if before else None},
             ["não gravou nada (--dry-run). Comando: " + " ".join(cmd)])
        return EXIT_OK
    if not args.yes:
        if not sys.stdin.isatty():
            raise CliError("refused", "recusado: gravar o firmware troca o programa do Arduino. Em modo não interativo confirme com --yes.",
                           EXIT_REFUSED, "repita o comando com --yes")
        ans = input(f"{what.capitalize()}. O firmware atual será substituído. Continuar? [s/N] ")
        if ans.strip().lower() not in ("s", "sim", "y", "yes"):
            print("cancelado")
            return EXIT_ERROR
    if simulate:
        after = before
        out = {"simulated": True, "port": port, "hex": str(hex_path), "firmware_before": before["firmware"] if before else None,
               "firmware_after": after["firmware"] if after else None}
        emit(args, out, [f"simulado: {what}"])
        return EXIT_OK
    cmd = avrdude_cmd(exe, port, hex_path, not args.no_verify)
    mode = getattr(args, "progress", "auto")
    code, err = run_avrdude(cmd, lambda label: progress(label, mode))
    if code != 0:
        raise CliError("avrdude", f"o avrdude falhou (código {code}): {err or 'sem mensagem'}", EXIT_NO_DEVICE if code in (1, 127) else EXIT_ERROR,
                       "confira a porta e o cabo, feche outros programas que usam a porta (monitor serial, GUI) e repita; no Linux, grupo dialout")
    after = _info_after(args, args.wait)
    out = {"port": port, "hex": str(hex_path), "verified": not args.no_verify, "firmware_before": before["firmware"] if before else None,
           "firmware_after": after["firmware"] if after else None, "responds": after is not None}
    lines = [f"firmware gravado em {port}" + ("" if args.no_verify else " e conferido pelo avrdude")]
    if after:
        lines.append(f"o dispositivo respondeu ao INFO: firmware {after['firmware']}, protocolo {after['proto']}"
                     + (f" (antes: {before['firmware']})" if before else ""))
    else:
        lines.append("o dispositivo ainda não respondeu ao INFO (a porta pode ter mudado de nome): rode `dumper info` em alguns segundos")
    emit(args, out, lines)
    return EXIT_OK
