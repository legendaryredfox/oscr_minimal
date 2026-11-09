# SPDX-License-Identifier: GPL-3.0-or-later
"""Coisas que todo comando usa: conexão (porta ou simulador), sistema, base de dados."""
from __future__ import annotations

import sys

from .. import database as DB
from .. import protocol as P
from ..client import Client, TimeoutError_
from ..transport import SerialTransport, Transport
from .messages import tr
from .errors import CliError, EXIT_ERROR, EXIT_NO_DEVICE, EXIT_REFUSED, EXIT_USAGE


BAUDS = (1_000_000, 115_200)


def list_ports() -> list[str]:
    from serial.tools import list_ports as lp

    return [p.device for p in lp.comports()]


def auto_port() -> str:
    ports = [p for p in list_ports() if any(k in p for k in ("ttyUSB", "ttyACM", "cu.usb", "COM"))]
    if not ports:
        raise CliError("no_port", tr("err.no_port"), EXIT_NO_DEVICE, tr("err.no_port.hint"))
    return ports[0]


def connect(args, need_cart: bool = True) -> tuple[Client, Transport, dict]:
    """Abre a porta (ou o simulador), faz INFO e, em placa com o seletor 3,3 V/5 V (D138), ajusta a tensão antes de um comando de cartucho.
    O 5V dos slots fica sempre ligado (D139). A placa sobe em 3,3 V (estado seguro: abrir a porta reinicia o Mega); o padrão é 5 V; `--voltage 3v3`
    usa 3,3 V (cartucho marcado como 3,3 V); passar de 3,3 V (escolhido) para 5 V mostra o alerta e pede confirmação (ou `--allow-5v`).
    `need_cart=False` (info, voltage) nunca mexe na tensão. Falha de leitura nunca muda a tensão sozinha."""
    c, t, info = _open(args)
    if need_cart:                                              # placa sem seletor: só recusa `--voltage 3v3`
        try:
            set_voltage(args, c, c.voltage(P.VOLT_STATUS))
        except BaseException:
            t.close()
            raise
    return c, t, info


def set_voltage(args, c: Client, st: dict) -> dict:
    """Aplica `--voltage`. `st` é o VOLT_STATUS atual. Devolve o estado depois."""
    mode = getattr(args, "voltage", "auto")
    sel = bool(st.get("voltage_select"))
    if mode == "3v3" and not sel:
        raise CliError("no_selector", tr("volt.no_selector"), EXIT_USAGE)           # pediu 3,3 V e a placa só dá 5 V: não segue calado
    if not sel:
        return st
    if mode == "3v3":
        return st if (st.get("voltage") == "3v3" and st.get("chosen")) else c.voltage(P.VOLT_3V3)
    if st.get("voltage") == "3v3":
        if mode == "5v" or not st.get("chosen"):                                      # padrão: 5 V. Só a escolha de 3,3 V do usuário pede confirmação
            if st.get("chosen"):
                confirm_5v(args)                                                      # slot marcado como 3,3 V: alerta e confirmação antes de subir
            return c.voltage(P.VOLT_5V)
    return st


def _warn_5v(args) -> None:
    """Alerta bem visível (no stderr) antes de passar o slot de 3,3 V para 5 V."""
    from . import ui
    lines = [tr("volt.warn_title"), "", tr("volt.warn_1"), "", tr("volt.warn_2"), "", tr("volt.warn_3")]
    bar = "#" * 78
    if ui.color_on(sys.stderr):
        out = [ui.paint(bar, "bold", "red", stream=sys.stderr), ui.paint(lines[0], "bold", "red", stream=sys.stderr)] + \
              [ui.paint(x, "bold", "yellow", stream=sys.stderr) if x else "" for x in lines[1:]] + [ui.paint(bar, "bold", "red", stream=sys.stderr)]
    else:
        out = [bar, lines[0]] + lines[1:] + [bar]
    print("\n".join(out), file=sys.stderr)


def confirm_5v(args) -> None:
    """Escolheu 5 V num cartucho marcado como 3,3 V (D138): mostra o alerta de risco e só segue se o usuário digitar 5V ou se `--allow-5v` foi dado
    (scripts). Sem terminal e sem `--allow-5v`, recusa. Levanta CliError (EXIT_REFUSED) se não confirmar."""
    _warn_5v(args)
    if getattr(args, "allow_5v", False):
        print(tr("volt.now_5v"), file=sys.stderr)
        return
    if getattr(args, "json", False) or not sys.stdin.isatty():
        raise CliError("refused", tr("volt.need_flag"), EXIT_REFUSED)
    if input(tr("volt.prompt")).strip().lower() != "5v":
        raise CliError("refused", tr("volt.cancelled"), EXIT_REFUSED)
    print(tr("volt.now_5v"), file=sys.stderr)


def _open(args) -> tuple[Client, Transport, dict]:
    if args.simulate:
        import os

        from .. import sim

        # OSCR_SIM_VOLT=1: o simulador finge o seletor 3,3 V/5 V (sobe em 3,3 V); OSCR_SIM_5V_CART=1: o cartucho só é lido a 5 V
        dev = sim.MockDevice(volt_select=os.environ.get("OSCR_SIM_VOLT") == "1", cart_needs_5v=os.environ.get("OSCR_SIM_5V_CART") == "1")        # seletor 3,3 V/5 V e cartucho que só lê a 5 V (D138)
        t, _dev, _stop, _th = sim.start(dev)
        c = Client(t, timeout=0.5, long_timeout=5.0)
        return c, t, c.info()
    port = args.port or auto_port()
    bauds = (args.baud,) if args.baud else BAUDS
    last: Exception | None = None
    for b in bauds:
        try:
            t = SerialTransport(port, b)
        except OSError as e:                              # porta ocupada, sem permissão (grupo dialout), cabo solto
            raise CliError("open_port", tr("err.open_port", port=port, error=e), EXIT_NO_DEVICE, tr("err.open_port.hint")) from e
        c = Client(t, timeout=0.5)
        try:
            return c, t, c.info()
        except TimeoutError_ as e:
            last = e
            t.close()
    raise CliError("no_response", tr("err.no_response", port=port, bauds=", ".join(map(str, bauds)), error=last), EXIT_NO_DEVICE, tr("err.no_response.hint"))


def system_id(name: str) -> int:
    if name not in P.SYSTEMS:
        raise CliError("usage", tr("sys.unknown", name=name, systems=", ".join(P.SYSTEMS)), EXIT_USAGE)
    return P.SYSTEMS[name][0]



def load_db(args, required: bool = False) -> DB.Database | None:
    """Base de dados do PC: a que vem no projeto (database/oscr/) mais as do usuário (--db, repetível, ou a variável OSCR_DB).
    None se não há nenhuma (--no-builtin-db e sem --db)."""
    paths = list(args.db or []) or DB.paths_from_env()
    builtin = not getattr(args, "no_builtin_db", False) and DB.BUILTIN_DIR.is_dir()
    if not paths and not builtin:
        if required:
            raise CliError("no_database", tr("db.none"), EXIT_USAGE)
        return None
    try:
        return DB.load_databases(paths, builtin=builtin)
    except (ValueError, OSError) as e:
        raise CliError("database", str(e), EXIT_ERROR, tr("db.load_hint")) from e


def game_options(db: DB.Database, query: str) -> DB.Entry:
    """Escolhe a entrada do NES 2.0 XML pelo nome (para preencher mapper, PRG e CHR)."""
    found = [e for e in db.search(query, 200) if e.nes_options()]
    exact = [e for e in found if e.name.lower() == query.lower()]
    found = exact or found
    uniq = {(e.mapper, e.prg_kb, e.chr_kb, e.ram_kb): e for e in found}
    if not uniq:
        raise CliError("game_not_found", tr("game.not_found", query=query), EXIT_USAGE, tr("game.not_found.hint"))
    if len(uniq) > 1:
        raise CliError("game_ambiguous", tr("game.ambiguous", n=len(found), query=query), EXIT_USAGE,
                       tr("game.ambiguous.hint", examples="; ".join(tr("game.example", name=e.name, mapper=e.mapper, prg=e.prg_kb, chr=e.chr_kb) for e in list(uniq.values())[:5])))
    return next(iter(uniq.values()))

