# SPDX-License-Identifier: GPL-3.0-or-later
"""Cores, barra de progresso, banner e arte ASCII da CLI.

Só aparecem num terminal (ou com `--color always`). Com `--json`, saída redirecionada, `NO_COLOR` ou `--color never`
a CLI continua em texto puro, como os scripts e os agentes esperam (docs/referencia/cli.md)."""
from __future__ import annotations

import os
import re
import sys
import time

_mode = "auto"          # auto | always | never (--color)

RESET = "\x1b[0m"
CODES = {"bold": "1", "dim": "2", "red": "31", "green": "32", "yellow": "33", "blue": "34", "magenta": "35", "cyan": "36", "gray": "90"}


def set_mode(mode: str) -> None:
    global _mode
    _mode = mode


def _tty(stream) -> bool:
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def color_on(stream=None) -> bool:
    """Cor ANSI: --color always liga, never desliga; no auto vale NO_COLOR, FORCE_COLOR e o terminal."""
    stream = stream or sys.stdout
    if _mode == "always":
        return True
    if _mode == "never" or os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return _tty(stream) and os.environ.get("TERM") != "dumb"


def fancy(stream=None) -> bool:
    """Enfeites (arte ASCII, quadros): onde a cor é permitida."""
    return color_on(stream)


def unicode_on(stream=None) -> bool:
    enc = (getattr(stream or sys.stdout, "encoding", "") or "").lower()
    return enc.startswith("utf")


def paint(text: str, *styles: str, stream=None) -> str:
    if not styles or not color_on(stream):
        return text
    return "\x1b[" + ";".join(CODES[s] for s in styles) + "m" + text + RESET


def c256(text: str, n: int, stream=None) -> str:
    return f"\x1b[38;5;{n}m{text}{RESET}" if color_on(stream) else text


# ---------------------------------------------------------------- ícones e barra
def icon(kind: str, stream=None) -> str:
    uni = unicode_on(stream)
    table = {"ok": ("✔", "[OK]", "green"), "err": ("✘", "[ERRO]", "red"), "warn": ("⚠", "[!]", "yellow"), "info": ("ℹ", "[i]", "cyan")}
    sym, plain, col = table[kind]
    return paint(sym if uni else plain, col, "bold", stream=stream)


GRADIENT = (196, 202, 208, 214, 220, 226, 190, 154, 118, 82, 46)      # vermelho -> amarelo -> verde


def bar(fraction: float, width: int = 28, stream=None) -> str:
    """Barra de progresso com degradê; sem Unicode usa # e -."""
    fraction = max(0.0, min(1.0, fraction))
    full, empty = ("█", "░") if unicode_on(stream) else ("#", "-")
    n = int(round(fraction * width))
    if not color_on(stream):
        return "[" + full * n + empty * (width - n) + "]"
    cells = "".join(c256(full, GRADIENT[min(len(GRADIENT) - 1, i * len(GRADIENT) // width)], stream) for i in range(n))
    return "[" + cells + paint(empty * (width - n), "gray", stream=stream) + "]"


SPIN_U, SPIN_A = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", "|/-\\"


def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


class ProgressLine:
    """Linha de progresso em stderr: giro, rótulo, barra, porcentagem, velocidade e tempo restante."""

    def __init__(self, label: str, stream=None):
        self.label, self.stream = label, stream or sys.stderr
        self.start = time.monotonic()
        self.frame = 0

    def render(self, done: int, total: int) -> str:
        s = self.stream
        frac = done / total if total else 0.0
        el = max(time.monotonic() - self.start, 1e-6)
        rate = done / el
        eta = f"  ETA {int((total - done) / rate)}s" if rate > 0 and done < total and el > 1.0 else ""
        spin = (SPIN_U if unicode_on(s) else SPIN_A)
        self.frame += 1
        sp = paint(spin[self.frame % len(spin)], "cyan", stream=s) if done < total else icon("ok", s)
        return (f"\r{sp} {paint(self.label, 'bold', stream=s):<14} {bar(frac, 28, s)} {int(frac * 100):3d}%  "
                f"{human_bytes(done)}/{human_bytes(total)}  {paint(human_bytes(rate) + '/s', 'dim', stream=s)}{eta}\x1b[K")


# ---------------------------------------------------------------- texto dos comandos
_RULES = [
    (re.compile(r"\b(CRC32 )([0-9A-Fa-f]{8})\b"), lambda m: m.group(1) + paint(m.group(2), "cyan", "bold")),
    (re.compile(r"\b(OK)\b"), lambda m: paint(m.group(1), "green", "bold")),
    (re.compile(r"(NÃO confere|NAO confere|NOT match|does NOT match)"), lambda m: paint(m.group(1), "red", "bold")),
    (re.compile(r"(\d[\d.,]*)( bytes| KB| MB)"), lambda m: paint(m.group(1), "bold") + m.group(2)),
]


def decorate(line: str, stream=None) -> str:
    """Realça uma linha de saída humana (ícone no começo, CRC32 em ciano, OK em verde, avisos em amarelo)."""
    if not color_on(stream):
        return line
    low = line.lstrip().lower()
    prefix = ""
    if low.startswith(("aviso", "warning")):
        return icon("warn", stream) + " " + paint(line, "yellow", stream=stream)
    if low.startswith(("rom gravada", "save gravado", "rom written", "save written")) or ("confer" in low and re.search(r"\bOK\b", line)):
        prefix = icon("ok", stream) + " "
    for rx, fn in _RULES:
        line = rx.sub(fn, line)
    return prefix + line


def error_line(message: str, hint: str | None, stream=None) -> str:
    s = icon("err", stream) + " " + paint("erro:", "red", "bold", stream=stream) + " " + message
    if hint:
        s += "\n  " + icon("info", stream) + " " + paint("dica: " + hint, "yellow", stream=stream)
    return s


# ---------------------------------------------------------------- arte ASCII
_GLYPHS = {
    "O": ["  ___  ", " / _ \\ ", "| | | |", "| |_| |", " \\___/ "],
    "S": [" ____  ", "/ ___| ", "\\___ \\ ", " ___) |", "|____/ "],
    "C": ["  ____ ", " / ___|", "| |    ", "| |___ ", " \\____|"],
    "R": [" ____  ", "|  _ \\ ", "| |_) |", "|  _ < ", "|_| \\_\\"],
}
BANNER_COLORS = (51, 45, 39, 33, 99)        # ciano -> azul -> violeta


def logo() -> list[str]:
    return ["".join(_GLYPHS[ch][r] for ch in "OSCR") for r in range(5)]


def banner(version: str, stream=None) -> str:
    """Logo OSCR em ASCII com degradê e a lista dos sistemas."""
    rows = []
    for i, line in enumerate(logo()):
        rows.append("  " + c256(line, BANNER_COLORS[i], stream))
    rows.append("  " + paint("minimal", "bold", "magenta", stream=stream) + paint(f"  v{version}", "dim", stream=stream)
                + paint("  -  dumper de cartuchos pela USB", "dim", stream=stream))
    systems = ["SNES", "NES", "Famicom", "Mega Drive", "GB", "GBC", "GBA"]
    cols = (196, 208, 220, 82, 45, 99, 171)
    rows.append("  " + paint(" · " if unicode_on(stream) else " | ", "gray", stream=stream).join(c256(n, c, stream) for n, c in zip(systems, cols)))
    return "\n".join(rows)


# Cartuchos: o rótulo ({label}) é centralizado numa área de largura fixa, então todas as linhas têm o mesmo tamanho.
_ART = {
    1: ["  .--------------------.  ", "  | .----------------. |  ", "  | |{label}| |  ", "  | '----------------' |  ", "  '--.              .--'  ",
        "     |::::::::::::::|     ", "     '--------------'     "],
    2: ["   .------------------.   ", "   |  ______________  |   ", "   | |{label}| |   ", "   | |______________| |   ", "   |  o            o  |   ",
        "   '--.----------.----'   ", "      ||||||||||||||      "],
    3: ["   .------------------.   ", "   | .--------------. |   ", "   | |{label}| |   ", "   | '--------------' |   ", "   |  o            o  |   ",
        "   '--.----------.----'   ", "      ||||||||||||||      "],
    4: [" .----------------------. ", " |" + " " + "//  " * 5 + " " + "| ", " | ==================== | ", " | |{label}| | ", " | ==================== | ",
        " '--.              .----' ", "     ||||||||||||||||     "],
    5: ["    _________________    ", "   /  _____________  \\   ", "  |  |{label}|  |  ", "  |  |_____________|  |  ", "  |___.           .___|  ",
        "      ||||||||||||       "],
    6: ["   ________________   ", "  |  ____________  \\  ", "  | |{label}|  | ", "  | |____________|  | ", "  |   o   o   o     | ", "  |__________________|",
        "     ||||||||||||     "],
}
_ART_WIDTH = {1: 16, 2: 14, 3: 14, 4: 18, 5: 13, 6: 12}
_ART_LABEL = {1: "S N E S", 2: "N E S", 3: "FAMICOM", 4: "MEGA DRIVE", 5: "G B A", 6: "GAME BOY"}
_ART_COLOR = {1: 141, 2: 203, 3: 215, 4: 75, 5: 134, 6: 108}


def cartridge(system: int, stream=None) -> list[str]:
    """Desenho do cartucho do sistema (1 SNES, 2 NES, 3 Famicom, 4 Mega Drive, 5 GBA, 6 GB/GBC); outro valor usa o do SNES."""
    kind = system if system in _ART else 1
    label = _ART_LABEL[kind].center(_ART_WIDTH[kind])
    rows = [row.replace("{label}", label) for row in _ART[kind]]
    width = max(len(r) for r in rows)
    return [c256(r.ljust(width), _ART_COLOR[kind], stream) for r in rows]


def side_by_side(left: list[str], right: list[str], gap: int = 2) -> list[str]:
    """Junta duas colunas; a da esquerda é medida sem os códigos de cor."""
    strip = re.compile(r"\x1b\[[0-9;]*m")
    width = max((len(strip.sub("", l)) for l in left), default=0)
    out = []
    for i in range(max(len(left), len(right))):
        l = left[i] if i < len(left) else ""
        r = right[i] if i < len(right) else ""
        out.append(l + " " * (width - len(strip.sub("", l)) + gap) + r)
    return out


def detect_card(system: int, status_text: str, ok: bool, fields: list[tuple[str, str]], stream=None) -> list[str]:
    """Cartucho ao lado dos dados do `detect`."""
    right = [(icon("ok", stream) if ok else icon("err", stream)) + " " + paint(status_text, "bold", stream=stream)]
    for k, v in fields:
        right.append(f"  {paint(k + ':', 'gray', stream=stream)} {paint(v, 'bold', stream=stream)}")
    return side_by_side(cartridge(system, stream), right)
