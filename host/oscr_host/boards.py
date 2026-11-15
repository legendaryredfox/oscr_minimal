# SPDX-License-Identifier: GPL-3.0-or-later
"""Perfis das placas e a decisão "o firmware gravado serve a esta placa?" (D162).

O usuário escolhe a placa (`--board 16_bits` ou `--board 16_bits@v1.3`); o programa compara o que ela precisa com o que o firmware gravado diz no
`INFO` e decide, sem tocar em nada, o que fazer (`plan`):

  none          o firmware serve e o perfil já está guardado
  set_profile   o firmware serve, falta só dizer a ele que placa é (BOARD, grava na EEPROM; é barato e reversível, não pede confirmação)
  flash         falta suporte (um sistema ou o BOARD): grava a menor imagem que cobre a placa (pede confirmação, quem chama)
  unsupported   nenhuma imagem conhecida cobre a placa, ou não há imagem para gravar

Regra do usuário (2026-11-14): uma imagem só sempre que couber; variantes só se for impossível. Hoje existe uma imagem (`completa`), então `flash`
significa gravar essa. Os dados vêm de boards/perfis.json (gerado por tools/gen_perfis.py) e de firmware/images/manifest.json (tools/build_images.py).
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from . import protocol as P

REPO = Path(__file__).resolve().parents[2]
PROFILES_FILE = Path(__file__).with_name("perfis.json")
MANIFEST_NAME = "manifest.json"


class BoardError(Exception):
    """Placa ou versão desconhecida (mensagem em português, para o usuário)."""


@dataclass(frozen=True)
class Profile:
    board: str
    version: str
    slots: tuple[str, ...]
    systems: frozenset[int]
    voltage_select: bool

    @property
    def label(self) -> str:
        return f"{self.board} {self.version}"


@dataclass(frozen=True)
class Image:
    id: str
    hex: Path
    firmware: tuple[int, int, int]
    systems: frozenset[int]
    sha256: str

    @property
    def firmware_str(self) -> str:
        return ".".join(map(str, self.firmware))


@dataclass
class Plan:
    action: str                       # none | set_profile | flash | unsupported
    reasons: list[str] = field(default_factory=list)
    image: Image | None = None
    profile_flags: int = 0            # flags a gravar no BOARD (set_profile, e depois do flash)


def load_profiles(path: Path | None = None) -> dict:
    return json.loads((path or PROFILES_FILE).read_text(encoding="utf-8"))


def board_names(path: Path | None = None) -> list[str]:
    return sorted(load_profiles(path))


def versions_of(board: str, path: Path | None = None) -> list[str]:
    return list(load_profiles(path)[board]["versoes"])


def resolve(spec: str, path: Path | None = None) -> Profile:
    """`16_bits` (versão atual da placa) ou `16_bits@v1.3`."""
    profiles = load_profiles(path)
    name, _, ver = spec.partition("@")
    if name not in profiles:
        raise BoardError(f"placa desconhecida: {name}. Placas: {', '.join(sorted(profiles))}")
    d = profiles[name]
    ver = ver or d["atual"]
    if not ver.startswith("v"):
        ver = "v" + ver
    if ver not in d["versoes"]:
        raise BoardError(f"versão desconhecida: {name} {ver}. Versões: {', '.join(d['versoes'])}")
    return Profile(name, ver, tuple(d["slots"]), frozenset(d["sistemas"]), bool(d["versoes"][ver]["seletor"]))


def profile_flags(p: Profile) -> int:
    return P.BOARD_VOLT_SELECT if p.voltage_select else 0


# ---- imagens de firmware

def image_dirs(explicit: str | None = None) -> list[Path]:
    out = []
    for c in (explicit, os.environ.get("OSCR_FIRMWARE_DIR")):
        if c:
            out.append(Path(c).expanduser())
    out.append(REPO / "firmware" / "images")
    return out


def load_images(explicit: str | None = None) -> list[Image]:
    """Lê o manifest.json do primeiro diretório que o tiver. Imagem sem o .hex ao lado ou com SHA-256 que não bate é ignorada."""
    for d in image_dirs(explicit):
        mf = d / MANIFEST_NAME
        if not mf.is_file():
            continue
        data = json.loads(mf.read_text(encoding="utf-8"))
        imgs = []
        for e in data.get("images", []):
            hexp = d / e["hex"]
            if not hexp.is_file():
                continue
            if hashlib.sha256(hexp.read_bytes()).hexdigest() != e["sha256"]:
                continue
            fw = tuple(int(x) for x in e["firmware"].split("."))
            imgs.append(Image(e["id"], hexp, fw, frozenset(e["sistemas"]), e["sha256"]))
        return imgs
    return []


def best_image(images: list[Image], needed: frozenset[int]) -> Image | None:
    """A menor imagem que cobre o que a placa precisa (menos sistemas), a mais nova no empate."""
    ok = [i for i in images if needed <= i.systems]
    return min(ok, key=lambda i: (len(i.systems), tuple(-x for x in i.firmware)), default=None)


def info_system_ids(info: dict) -> frozenset[int]:
    return frozenset(info.get("system_ids", []))


def plan(profile: Profile, info: dict | None, board_state: dict | None, images: list[Image]) -> Plan:
    """Decide o que fazer. `info` é o INFO do firmware gravado (None = não respondeu); `board_state` é o BOARD_RESP (None se o firmware não tem BOARD)."""
    need = profile.systems
    flags = profile_flags(profile)
    if info is None:
        img = best_image(images, need)
        if img is None:
            return Plan("unsupported", ["o firmware não respondeu e não há imagem de firmware conhecida para gravar"], None, flags)
        return Plan("flash", ["o Arduino não respondeu (sem firmware, ou firmware que não é deste projeto)"], img, flags)

    reasons = []
    missing = sorted(need - info_system_ids(info))
    if missing:
        reasons.append("o firmware não tem os sistemas " + ", ".join(P.system_name(i) for i in missing))
    has_board = bool(info.get("board_profile"))
    selector_ok = bool(info.get("voltage_select")) == profile.voltage_select
    if not has_board and not selector_ok:
        reasons.append("o firmware não aceita o perfil da placa (BOARD) e o seletor de tensão dele não bate com a placa")
    if reasons:
        img = best_image(images, need)
        if img is None:
            return Plan("unsupported", reasons + ["nenhuma imagem de firmware conhecida cobre esta placa"], None, flags)
        if img.firmware <= _fw(info) and not missing and has_board:
            return Plan("unsupported", reasons + ["a imagem conhecida não é mais nova que o firmware gravado"], None, flags)
        return Plan("flash", reasons, img, flags)

    stored = bool(board_state and board_state.get("stored"))
    if has_board and (not stored or not selector_ok):
        return Plan("set_profile", ["gravar o perfil da placa no firmware"], None, flags)
    return Plan("none", [], None, flags)


def _fw(info: dict) -> tuple[int, int, int]:
    try:
        a, b, c = info["firmware"].split(".")
        return int(a), int(b), int(c)
    except Exception:
        return (0, 0, 0)
