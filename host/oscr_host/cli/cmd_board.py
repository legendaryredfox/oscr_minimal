# SPDX-License-Identifier: GPL-3.0-or-later
"""Placa escolhida pelo usuário (`--board`): confere o firmware do Arduino, grava o perfil da placa e, se faltar suporte, grava o firmware certo (D162).

Regra do usuário (2026-11-14): uma imagem de firmware só sempre que couber; se o firmware gravado não serve à placa, o programa grava sozinho a imagem que
serve, **depois de pedir confirmação** (ela apaga o firmware atual e reinicia o Mega; `--auto-flash` confirma de antemão, para scripts). A decisão é de
`oscr_host.boards.plan`, que não toca em nada; aqui só se executa."""
from __future__ import annotations

import sys

from .. import boards as B
from .. import protocol as P
from ..client import Client
from ..protocol import DeviceError
from ..transport import Transport
from . import common
from .errors import CliError, EXIT_ERROR, EXIT_NO_DEVICE, EXIT_OK, EXIT_REFUSED, EXIT_USAGE
from .messages import tr
from .output import emit

YES = ("s", "sim", "y", "yes", "да", "д", "是", "是的")


def _reasons(reasons) -> str:
    return "; ".join(tr(f"board.reason.{r.code}", **r.params) for r in reasons)


def resolve(args) -> B.Profile:
    try:
        return B.resolve(args.board)
    except B.BoardError as e:
        raise CliError("unknown_board", tr(f"board.{e.kind}", **e.params), EXIT_USAGE, tr("board.unknown.hint")) from e


def _sel(profile: B.Profile) -> str:
    return tr("board.yes" if profile.voltage_select else "board.no")


def _confirm(args, profile: B.Profile, what: str) -> None:
    if getattr(args, "auto_flash", False):
        return
    if getattr(args, "json", False) or not sys.stdin.isatty():
        raise CliError("refused", tr("board.refused", board=profile.label), EXIT_REFUSED, tr("board.refused.hint"))
    if input(tr("board.ask", what=what[:1].upper() + what[1:])).strip().lower() not in YES:
        raise CliError("refused", tr("board.cancelled"), EXIT_REFUSED)


def _flash(args, profile: B.Profile, pl: B.Plan, port: str) -> None:
    from . import cmd_firmware

    img = pl.image
    assert img is not None
    what = tr("board.flash_what", fw=img.firmware_str, image=img.hex.name, port=port)
    print(tr("board.need_flash", board=profile.label, reasons=_reasons(pl.reasons)), file=sys.stderr)
    _confirm(args, profile, what)
    print(tr("board.flashing", fw=img.firmware_str, port=port), file=sys.stderr)
    if args.simulate:
        common.SIM_FLASHED = True                                   # o simulador passa a ser o firmware novo
        return
    after = cmd_firmware.write_firmware(args, img.hex, port)
    if after is None:
        raise CliError("flash_no_answer", tr("board.flash_no_answer"), EXIT_NO_DEVICE, tr("board.flash_no_answer.hint"))


def ensure_board(args, c: Client | None, t: Transport | None, info: dict | None) -> tuple[Client, Transport, dict]:
    """Garante que o Arduino serve à placa `--board`. `c`, `t` e `info` são None se o Arduino não respondeu. Devolve a conexão pronta (nova, se gravou)."""
    profile = resolve(args)
    images = B.load_images(getattr(args, "firmware_dir", None))
    state = None
    if c is not None and info and info.get("board_profile"):
        try:
            state = c.board()
        except DeviceError:
            state = None
    pl = B.plan(profile, info, state, images)
    args.board_result = {"board": profile.board, "version": profile.version, "action": pl.action}

    if pl.action == "unsupported":
        if t is not None:
            t.close()
        raise CliError("board_unsupported", tr("board.unsupported", board=profile.label, reasons=_reasons(pl.reasons)), EXIT_ERROR, tr("board.unsupported.hint"))

    if pl.action == "flash":
        port = args.port or (tr("fw.simulator") if args.simulate else common.auto_port())
        if t is not None:
            t.close()                                               # solta a porta para o avrdude
        _flash(args, profile, pl, port)
        c, t, info = common._open(args)
        state = c.board() if info.get("board_profile") else None
        again = B.plan(profile, info, state, images)
        if again.action == "flash" or again.action == "unsupported":
            t.close()
            raise CliError("flash_still_missing", tr("board.flash_still_missing", board=profile.label, reasons=_reasons(again.reasons)), EXIT_ERROR)
        pl = again
        args.board_result.update(action="flash", firmware=info["firmware"])

    if pl.action == "set_profile":
        assert c is not None and t is not None
        c.board(P.BOARD_SET, pl.profile_flags)
        info = c.info()
        print(tr("board.profile_set", board=profile.label, selector=_sel(profile)), file=sys.stderr)
        if args.board_result["action"] != "flash":
            args.board_result["action"] = "set_profile"
    assert c is not None and t is not None and info is not None
    args.board_result.setdefault("firmware", info["firmware"])
    return c, t, info


def cmd_boards(args) -> int:
    rows = []
    lines = [tr("board.list_head")]
    for name in B.board_names():
        d = B.load_profiles()[name]
        cur = d["versoes"][d["atual"]]["seletor"]
        rows.append({"board": name, "current": d["atual"], "slots": d["slots"], "systems": d["sistemas"], "versions": {v: x["seletor"] for v, x in d["versoes"].items()}})
        lines.append(tr("board.list_line", board=name, current=d["atual"], slots=", ".join(d["slots"]), selector=tr("board.yes" if cur else "board.no")))
    emit(args, {"boards": rows}, lines)
    return EXIT_OK


def cmd_board(args) -> int:
    if not getattr(args, "board", None):
        raise CliError("usage", tr("board.need_arg"), EXIT_USAGE)
    c, t, info = common.connect(args, need_cart=False)
    try:
        r = dict(args.board_result, systems=info.get("system_ids", []), voltage_select=info.get("voltage_select", False))
    finally:
        t.close()
    profile = resolve(args)
    emit(args, r, [tr("board.ok", board=profile.label, fw=r["firmware"])])
    return EXIT_OK
