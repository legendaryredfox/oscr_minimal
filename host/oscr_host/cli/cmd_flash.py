# SPDX-License-Identifier: GPL-3.0-or-later
"""Comandos flash-* (programador de flash genérico, sistema 7)."""
from __future__ import annotations

import sys
from pathlib import Path

from .. import protocol as P
from .. import romimage as RI
from . import common
from .messages import tr
from .errors import CliError, EXIT_ERROR, EXIT_NO_CART, EXIT_OK, EXIT_REFUSED, EXIT_USAGE
from .output import emit, progress, save_result


# ---------------------------------------------------------------- programador de flash genérico (sistema 7; docs/referencia/funcoes-oscr.md)
def _fp_job(args, need_type: bool = False, detect: bool = False):
    try:
        return RI.flashprog_params(args.bus, args.flash_kb, args.flash_type, args.sector_kb, args.buffer, need_type, detect)
    except ValueError as e:
        raise CliError("usage", str(e), EXIT_USAGE) from e


def _fp_sid(args) -> int:
    return 255 if args.system == "mock" else 7              # o simulador só entende o sistema MOCK


def _fp_need(c, info: dict) -> None:
    if not info.get("flash_prog"):
        raise CliError("unsupported_firmware", "este firmware não tem o programador de flash genérico", EXIT_ERROR, "atualize o firmware (docs/referencia/funcoes-oscr.md)")


def _fp_read(args, c, job) -> bytes:
    return c.dump_rom(_fp_sid(args), getattr(args, "block", 0), progress("flash-read", args.progress), job.chip, job.prg_kb, job.chr_word).data


def cmd_flash_id(args) -> int:
    """Lê o ID do chip. Sem --flash-type, no flash de 8 bits mostra o ID pelas quatro rotinas do OSCR (Intel 28F, AMD 29F032, AMD 29F1610, SST 39SF040).
    Com --bus md identifica o flash do cartucho de Mega Drive pela tabela do firmware (nome e capacidade)."""
    job = _fp_job(args, detect=True)
    c, t, info = common.connect(args)
    try:
        _fp_need(c, info)
        r = c.detect(_fp_sid(args), job.chip, job.prg_kb, job.chr_word)
    finally:
        t.close()
    if args.bus == "md":
        known = r["status"] == 0
        label = RI.FLASHPROG_LABEL["md"]
        if known:
            emit(args, {"ok": True, "known": True, "ids": r["name"], "chip": r["name"].rsplit(" ", 1)[0], "size": r["rom_size"], "status": 0},
                 [f"{label}: {r['name']}  ({r['rom_size'] // 1024} KB)"])
            return EXIT_OK
        cfi = r["name"].startswith("CFI ")
        emit(args, {"ok": False, "known": False, "ids": r["name"], "chip": None, "size": r["rom_size"] if cfi else 0, "cfi": cfi, "status": r["status"]},
             [f"{label}: chip fora da tabela ou sem resposta ({r['name']}): sem flash (ROM de máscara), cartucho mal encaixado, ou um chip que o firmware ainda não conhece. "
              + (f"O chip respondeu à consulta CFI e diz ter {r['rom_size'] // 1024} KB, mas só chips da tabela são gravados. " if cfi else "") + "Nada foi gravado."])
        return EXIT_ERROR
    legend = " (I = Intel 28F, A = AMD 29F032, B = AMD 29F1610, S = SST 39SF040; ID 0000 ou FFFF = o chip não respondeu a essa rotina)" if "=" in r["name"] else ""
    ok = r["status"] == 0
    emit(args, {"ok": ok, "ids": r["name"], "size": r["rom_size"], "status": r["status"]},
         [f"{RI.FLASHPROG_LABEL[args.bus]}: {r['name']}{legend}" if ok else f"{RI.FLASHPROG_LABEL[args.bus]}: nenhum chip respondeu (ID 0000 ou FFFF)"])
    return EXIT_OK if ok else EXIT_NO_CART


def cmd_flash_read(args) -> int:
    job = _fp_job(args)
    c, t, info = common.connect(args)
    try:
        _fp_need(c, info)
        data = _fp_read(args, c, job)
    finally:
        t.close()
    return save_result(args, type("R", (), {"data": data, "crc32": P.crc32(data)})(), ".bin", "flash.bin")


def cmd_flash_blank(args) -> int:
    """Confere se o chip está em branco (tudo 0xFF): lê o chip e olha no PC (o OSCR olhava no próprio aparelho)."""
    job = _fp_job(args)
    c, t, info = common.connect(args)
    try:
        _fp_need(c, info)
        data = _fp_read(args, c, job)
    finally:
        t.close()
    first = next((i for i, b in enumerate(data) if b != 0xFF), None)
    emit(args, {"ok": first is None, "blank": first is None, "bytes": len(data), "first_non_blank": first},
         ["em branco" if first is None else f"NÃO está em branco (primeiro byte diferente de FF no offset {first})"])
    return EXIT_OK if first is None else EXIT_ERROR


def cmd_flash_erase(args) -> int:
    """Apaga o chip inteiro. EPROM não se apaga. Sempre confirma."""
    if args.bus == "eprom":
        raise CliError("usage", "EPROM não se apaga (a 27C322 só apaga com luz ultravioleta); use flash-blank para conferir se está em branco", EXIT_USAGE)
    job = _fp_job(args, need_type=args.bus in ("8", "plcc32"))
    if not args.yes:
        if not sys.stdin.isatty():
            raise CliError("refused", tr("refused.erase"), EXIT_REFUSED, tr("refused.repeat"))
        ans = input(f"Apagar {RI.FLASHPROG_LABEL[args.bus]} de {job.prg_kb} KB? Isso PERDE o conteúdo. Continuar? [s/N] ")
        if ans.strip().lower() not in ("s", "sim", "y", "yes", "да", "д", "是", "是的"):
            print(tr("cancelled"))
            return 1
    c, t, info = common.connect(args)
    try:
        _fp_need(c, info)
        c.erase(_fp_sid(args), job.chip, job.prg_kb, job.chr_word, args.begin_timeout)
    finally:
        t.close()
    emit(args, {"erased": True, "bus": args.bus, "flash_kb": job.prg_kb}, ["chip apagado"])
    return EXIT_OK


def cmd_flash_write(args) -> int:
    """Apaga e grava o arquivo no chip (flash de 8 e 16 bits) ou grava a EPROM (precisa estar em branco). Confere lendo de volta."""
    try:
        job = RI.split_flashprog(Path(args.input).read_bytes(), args.bus, args.flash_kb, args.flash_type, args.sector_kb, args.buffer)
    except ValueError as e:
        raise CliError("bad_rom", str(e), EXIT_USAGE) from e
    what = f"{RI.FLASHPROG_LABEL[args.bus]}: {len(job.rom)} bytes em um chip de {job.prg_kb} KB"
    if not args.yes:
        if not sys.stdin.isatty():
            raise CliError("refused", tr("refused.write"), EXIT_REFUSED, tr("refused.repeat"))
        ans = input(f"Gravar {what}? Isso APAGA o conteúdo atual do chip. Continuar? [s/N] ")
        if ans.strip().lower() not in ("s", "sim", "y", "yes", "да", "д", "是", "是的"):
            print(tr("cancelled"))
            return 1
    c, t, info = common.connect(args)
    try:
        _fp_need(c, info)
        crc = c.write_rom(_fp_sid(args), job.body, job.chip, job.prg_kb, job.chr_word, args.block or P.DEFAULT_BLOCK,
                          progress("flash-write", args.progress), args.begin_timeout)
    finally:
        t.close()
    out = {"bus": args.bus, "flash_kb": job.prg_kb, "bytes": len(job.body), "crc32": f"{crc:08X}"}
    lines = [f"gravado: {what}  CRC32 {crc:08X}"]
    if args.no_verify or args.system == "mock":
        out["verify"] = "skipped"
        lines.append("conferência depois de gravar: pulada")
    else:
        c2, t2, _ = common.connect(args)
        try:
            back = _fp_read(args, c2, job)
        finally:
            t2.close()
        n = len(job.rom)
        diff = next((i for i in range(min(len(back), n)) if back[i] != job.rom[i]), None if len(back) >= n else len(back))
        out["verify"] = {"ok": diff is None, "read_bytes": len(back), "first_diff": diff}
        if diff is not None:
            raise CliError("verify_failed", f"o chip lido de volta NÃO confere com o arquivo (primeiro byte diferente no offset {diff})", EXIT_ERROR,
                           "confira o tipo do flash, limpe os contatos e grave de novo; o chip pode estar apagado ou pela metade", written=out, first_diff=diff)
        lines.append(f"conferência depois de gravar: OK (leu {len(back)} bytes do chip)")
    emit(args, out, lines)
    return EXIT_OK

