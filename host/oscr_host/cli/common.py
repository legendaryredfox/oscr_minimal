# SPDX-License-Identifier: GPL-3.0-or-later
"""Coisas que todo comando usa: conexão (porta ou simulador), sistema, base de dados."""
from __future__ import annotations

import time
import os
import sys

from .. import database as DB
from .. import protocol as P
from ..client import Client, TimeoutError_
from ..transport import SerialTransport, Transport
from .messages import tr
from .errors import CliError, EXIT_ERROR, EXIT_NO_DEVICE, EXIT_REFUSED, EXIT_USAGE


BAUDS = P.BAUDS
BOOT_SETTLE = 2.5        # s sem enviar nada depois de abrir a porta
BOOT_WAIT = 2.0          # s que o Mega leva para subir depois de abrir a porta (reset por DTR)


def _sim_selftest_report() -> list:
    """OSCR_SIM_SELFTEST=1: o simulador acha um curto com GND (D30) e um par em curto (D22 e A3), para ver o texto do `selftest`."""
    return [(P.ST_GND, 30, 0), (P.ST_PAIR, 22, 57)] if os.environ.get("OSCR_SIM_SELFTEST") == "1" else []


def list_ports() -> list[str]:
    from serial.tools import list_ports as lp

    return [p.device for p in lp.comports()]


def auto_port() -> str:
    ports = [p for p in list_ports() if any(k in p for k in ("ttyUSB", "ttyACM", "cu.usb", "COM"))]
    if not ports:
        raise CliError("no_port", tr("err.no_port"), EXIT_NO_DEVICE, tr("err.no_port.hint"))
    return ports[0]


SIM_FLASHED = False        # --simulate --board: o "firmware antigo" simulado já foi trocado pelo novo (OSCR_SIM_OLD_FW=1 liga o antigo)


def connect(args, need_cart: bool = True) -> tuple[Client, Transport, dict]:
    """Abre a porta (ou o simulador), faz INFO e, em placa com o seletor 3,3 V/5 V (D138), ajusta a tensão antes de um comando de cartucho.
    O 5V dos slots fica sempre ligado (D139). A placa sobe em 3,3 V (estado seguro: abrir a porta reinicia o Mega); o padrão é 5 V; `--voltage 3v3`
    usa 3,3 V (cartucho marcado como 3,3 V); passar de 3,3 V (escolhido) para 5 V mostra o alerta e pede confirmação (ou `--allow-5v`).
    `need_cart=False` (info, voltage) nunca mexe na tensão. Falha de leitura nunca muda a tensão sozinha."""
    if getattr(args, "board", None):                           # D162: a placa escolhida decide se o firmware serve ou se precisa gravar
        from .cmd_board import ensure_board

        try:
            c, t, info = _open(args)
        except CliError as e:
            if e.kind != "no_response":
                raise
            c, t, info = ensure_board(args, None, None, None)
        else:
            c, t, info = ensure_board(args, c, t, info)
    else:
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
    c, t, info = _open_raw(args)
    from .output import stage_notifier
    c.on_stage = stage_notifier(getattr(args, "progress", "auto"))     # F-1: etapa avisada pelo firmware (apagando, gravando...)
    return c, t, info


def _open_raw(args) -> tuple[Client, Transport, dict]:
    if args.simulate:
        import os

        from .. import sim

        # OSCR_SIM_VOLT=1: o simulador finge o seletor 3,3 V/5 V (sobe em 3,3 V); OSCR_SIM_5V_CART=1: o cartucho só é lido a 5 V
        # OSCR_SIM_OLD_FW=1: o simulador finge um firmware 0.1.0 sem BOARD e sem os sistemas novos, até um `--board` mandar gravar (D162)
        old = os.environ.get("OSCR_SIM_OLD_FW") == "1" and not SIM_FLASHED
        dev = sim.MockDevice(volt_select=os.environ.get("OSCR_SIM_VOLT") == "1", cart_needs_5v=os.environ.get("OSCR_SIM_5V_CART") == "1",
                             selftest_report=_sim_selftest_report(),         # seletor 3,3 V/5 V e cartucho que só lê a 5 V (D138)
                             board_profile=not old, firmware=(0, 1, 0) if old else (0, 2, 0), stages=not old, clock=not old,
                             systems=0 if old else (os.environ.get("OSCR_SIM_SYSTEMS") and int(os.environ["OSCR_SIM_SYSTEMS"])) or sum(1 << i for i in range(1, 12)))
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
        # Abrir a porta reinicia o Mega (DTR do CH340 e do 16U2): bootloader + setup() levam ~2 s e o INFO que sai antes se perde.
        # Insiste na mesma abertura até BOOT_WAIT s em vez de desistir em 0,5 s (e reabrir, o que reinicia de novo).
        ser = getattr(t, "ser", None)                     # só a porta real reinicia o Mega; as falsas dos testes não têm `ser`
        if ser is not None:
            time.sleep(BOOT_SETTLE)                       # nada de enviar durante o boot: bytes que chegam antes de ~0,9 s (bootloader) fazem o Mega não subir o firmware (D196)
            ser.reset_input_buffer()
        deadline = time.monotonic() + (BOOT_WAIT if ser is not None else 0)
        while True:
            try:
                return c, t, c.info()
            except TimeoutError_ as e:
                last = e
                if time.monotonic() >= deadline:
                    break
        t.close()
    raise CliError("no_response", tr("err.no_response", port=port, bauds=", ".join(map(str, bauds)), error=last), EXIT_NO_DEVICE, tr("err.no_response.hint"))


def set_size_hint(c: Client, args, sid: int, kind: str, mapper: int = 0, size_kb: int = 0, third: int = 0) -> None:
    c.size_hint = size_estimate(c, args, sid, kind, mapper, size_kb, third)


def size_estimate(c: Client, args, sid: int, kind: str, mapper: int = 0, size_kb: int = 0, third: int = 0) -> int:
    """Tamanho esperado (bytes) para a barra de progresso quando o firmware só diz o tamanho no END (núcleos do OSCR; D199). `kind`: "rom" ou "save".
    Vem do DETECT (mesmos parâmetros do dump); N64 sem tamanho no DETECT usa --prg (MB). Qualquer falha ou `--progress none` devolve 0 (sem progresso, como antes)."""
    if getattr(args, "progress", "auto") == "none":
        return 0
    try:
        d = c.detect(sid, mapper, size_kb, third)
    except (P.DeviceError, P.ProtocolError, TimeoutError_):
        return 0
    except AttributeError:                                # cliente falso dos testes, sem DETECT
        return 0
    n = d.get("rom_size" if kind == "rom" else "save_size", 0) if d.get("status") == 0 else 0
    if not n and sid == 11 and kind == "rom" and getattr(args, "prg", 0):
        n = args.prg * 1024 * 1024
    return n


def snes_type_code(args) -> int:
    """`--type` do SNES (F-2, D164) como código do protocolo; 0 = pelo cabeçalho. Em outro sistema é erro de uso."""
    t = getattr(args, "type", None)
    acc = getattr(args, "accessory", None)
    if not t and not acc:
        return 0
    if args.system != "snes":
        raise CliError("usage", tr("snes_type.only_snes" if t else "snes_acc.only_snes"), EXIT_USAGE)
    if t and acc:
        raise CliError("usage", tr("snes_acc.with_type"), EXIT_USAGE)
    if acc:                                                # F-10: Sufami Turbo (ROM) e GPC (save); o comando confere se o acessório serve a ele
        is_save = acc in P.SNES_SAVE_ACCESSORIES               # GPC e SRAM do BS-X são RAM; os outros, ROM
        cmd = getattr(args, "cmd", "")
        if (is_save and cmd in ("dump", "detect")) or (not is_save and cmd in ("save-read", "save-write")):
            raise CliError("usage", tr("snes_acc.gpc_is_save" if is_save else "snes_acc.sufami_is_rom"), EXIT_USAGE)
        return P.SNES_ACCESSORIES[acc]
    return P.SNES_TYPES[t]


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

