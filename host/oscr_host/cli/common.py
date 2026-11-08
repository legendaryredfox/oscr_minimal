# SPDX-License-Identifier: GPL-3.0-or-later
"""Coisas que todo comando usa: conexão (porta ou simulador), sistema, base de dados."""
from __future__ import annotations

from .. import database as DB
from .. import protocol as P
from ..client import Client, TimeoutError_
from ..transport import SerialTransport, Transport
from .messages import tr
from .errors import CliError, EXIT_ERROR, EXIT_NO_DEVICE, EXIT_USAGE


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
    """Abre a porta (ou o simulador), faz INFO e, em placa com a chave de 5V, liga o 5V dos slots (`--power auto`, o padrão).
    `need_cart=False` (info, power) nunca mexe no 5V. Com `--power keep` o 5V fica como está."""
    c, t, info = _open(args)
    if need_cart and info.get("power_switch") and getattr(args, "power", "auto") != "keep":
        try:
            if not c.power(P.POWER_STATUS)["on"]:
                c.power(P.POWER_ON)
        except BaseException:
            t.close()
            raise
    return c, t, info


def _open(args) -> tuple[Client, Transport, dict]:
    if args.simulate:
        import os

        from .. import sim

        # OSCR_SIM_POWER=1: o simulador finge uma placa com a chave de 5V (começa desligada)
        # OSCR_SIM_SENSE=1: finge também o sensor do rail e 3 tentativas do SA-1 (a placa com sensor tem a chave de 5V em software)
        sense = os.environ.get("OSCR_SIM_SENSE") == "1"
        dev = sim.MockDevice(power_switch=os.environ.get("OSCR_SIM_POWER") == "1", rail_sensor=sense, detect_attempts=3 if sense else 1)
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
        raise CliError("usage", f"sistema desconhecido: {name}. Use: {', '.join(P.SYSTEMS)}", EXIT_USAGE)
    return P.SYSTEMS[name][0]



def load_db(args, required: bool = False) -> DB.Database | None:
    """Base de dados do PC: a que vem no projeto (database/oscr/) mais as do usuário (--db, repetível, ou a variável OSCR_DB).
    None se não há nenhuma (--no-builtin-db e sem --db)."""
    paths = list(args.db or []) or DB.paths_from_env()
    builtin = not getattr(args, "no_builtin_db", False) and DB.BUILTIN_DIR.is_dir()
    if not paths and not builtin:
        if required:
            raise CliError("no_database", "nenhuma base de dados: use --db ARQUIVO_OU_PASTA (No-Intro .dat ou NES 2.0 XML) ou a variável OSCR_DB",
                           EXIT_USAGE)
        return None
    try:
        return DB.load_databases(paths, builtin=builtin)
    except (ValueError, OSError) as e:
        raise CliError("database", str(e), EXIT_ERROR, "confira o caminho e se o arquivo é um .dat (Logiqx) ou o nes20db.xml") from e


def game_options(db: DB.Database, query: str) -> DB.Entry:
    """Escolhe a entrada do NES 2.0 XML pelo nome (para preencher mapper, PRG e CHR)."""
    found = [e for e in db.search(query, 200) if e.nes_options()]
    exact = [e for e in found if e.name.lower() == query.lower()]
    found = exact or found
    uniq = {(e.mapper, e.prg_kb, e.chr_kb, e.ram_kb): e for e in found}
    if not uniq:
        raise CliError("game_not_found", f"nenhum jogo com mapper e tamanhos na base para: {query}", EXIT_USAGE,
                       "a base precisa ser o NES 2.0 XML (nes20db.xml); o No-Intro não traz o mapper. Use `dumper search` para procurar")
    if len(uniq) > 1:
        raise CliError("game_ambiguous", f"{len(found)} jogos combinam com '{query}' e têm configurações diferentes", EXIT_USAGE,
                       "seja mais específico. Exemplos: " + "; ".join(f"{e.name} (mapper {e.mapper}, PRG {e.prg_kb} KB, CHR {e.chr_kb} KB)" for e in list(uniq.values())[:5]))
    return next(iter(uniq.values()))

