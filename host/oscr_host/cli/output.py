# SPDX-License-Identifier: GPL-3.0-or-later
"""Saída dos comandos: JSON ou texto, barra de progresso, nome e gravação do arquivo."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .. import protocol as P
from . import ui


def progress(label: str, mode: str = "auto"):
    """mode: auto (barra se stderr for terminal), none, jsonl (uma linha JSON por 1% em stderr)."""
    state = {"last": -1}
    line = ui.ProgressLine(label)

    def cb(done: int, total: int) -> None:
        if mode == "none" or total == 0:
            return
        if mode == "jsonl":
            pct = done * 100 // total
            if pct != state["last"]:
                state["last"] = pct
                print(json.dumps({"event": "progress", "label": label, "done": done, "total": total, "percent": pct}),
                      file=sys.stderr, flush=True)
            return
        if not sys.stderr.isatty():
            return
        pct = done * 100 // total
        if pct != state["last"]:
            state["last"] = pct
            if ui.color_on(sys.stderr):                          # barra com degradê, velocidade e tempo restante
                print(line.render(done, total), end="", file=sys.stderr, flush=True)
            else:
                print(f"\r{label}: {pct:3d}%  ({done}/{total} bytes)", end="", file=sys.stderr, flush=True)
            if done >= total:
                print(file=sys.stderr)

    return cb



def out_path(args, ext: str, default: str) -> Path:
    p = Path(args.output) if args.output else Path(default)
    if p.suffix == "":
        p = p.with_suffix(ext)
    return p



def emit(args, obj: dict, lines: list[str]) -> None:
    """Saída do comando: uma linha de JSON com --json (sempre com "ok"), senão o texto para humanos."""
    if args.json:
        print(json.dumps({"ok": True, **obj} if "ok" not in obj else obj, ensure_ascii=False))
    else:
        for l in lines:
            print(ui.decorate(l))


def safe_name(title: str, default: str) -> str:
    n = re.sub(r"[^A-Za-z0-9._ -]+", "_", title or "").strip(" ._")
    return n or default



def save_result(args, res: P.Frame | object, ext: str, default: str, extra: dict | None = None, notes: list[str] | None = None) -> int:
    path = out_path(args, ext, default)
    path.write_bytes(res.data)
    obj = {"file": str(path), "bytes": len(res.data), "crc32": f"{res.crc32:08X}"}
    obj.update(extra or {})
    emit(args, obj, [f"{path}  {len(res.data)} bytes  CRC32 {res.crc32:08X}"] + (notes or []))
    return 0



def diff_summary(a: bytes, b: bytes) -> tuple[int, int]:
    """(bytes diferentes, deslocamento do primeiro). Tamanhos diferentes contam o excesso; sem diferença nos bytes comuns, o primeiro é o fim do menor. Iguais: (0, -1)."""
    n = min(len(a), len(b))
    idx = [i for i in range(n) if a[i] != b[i]]
    return len(idx) + abs(len(a) - len(b)), (idx[0] if idx else (n if len(a) != len(b) else -1))
