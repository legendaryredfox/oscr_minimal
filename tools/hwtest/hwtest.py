#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Suíte de bancada SOMENTE LEITURA para todos os sistemas (P3, D160). Generaliza tools/boards/megadrive/hwtest_md.py; modelo: a matriz de validação do
n64cartreader (cartuchos "dourados" com hashes SHA-256 conhecidos). Nunca grava nem apaga nada no cartucho: todo comando passa pela guarda de hwtest_md.run_cli,
que recusa qualquer coisa fora de READ_ONLY_COMMANDS e os argumentos `--yes`, `--flash-id`, `--ignore-cart-limit` e `--allow-5v`.

Fases
  host      sem hardware: guarda, `golden.json` e a CLI inteira contra o simulador
  nocart    placa ligada, slots VAZIOS: conexão, 10 reconexões, autoteste e, para cada --system pedido, `detect` sem cartucho
  cart      placa ligada, UM cartucho do sistema --system: detect, duas leituras da ROM iguais, CRC32, SHA-256, (opcional) comparação com o cartucho dourado
            `--golden NOME` (golden.json), duas leituras do save iguais (`--save`, com `--mapper` onde o tipo de save é obrigatório, como no N64 sem base)

Uso, da raiz do repositório:
  python3 tools/hwtest/hwtest.py host
  python3 tools/hwtest/hwtest.py nocart --system snes --system n64 [--port /dev/ttyACM0]
  python3 tools/hwtest/hwtest.py cart --system gba --golden pokemon-esmeralda --save --mapper 5
O procedimento completo (o que fazer, em que ordem e o que conta como aprovado) está em docs/referencia/teste-de-bancada.md.

golden.json (tools/hwtest/golden.json): {"nome": {"system": "gba", "sha256": "...", "crc32": "...", "nota": "..."}}; o usuário preenche com os cartuchos que tem e que conhece.
Saída: tabela e test-results/<data>-<fase>/ (report.json, report.md, dumps). Código de saída 0 só se nenhuma verificação falhou; SKIP não é falha; INFO registra um valor.
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = Path(__file__).resolve().parent / "golden.json"
SYSTEMS = ("snes", "nes", "famicom", "md", "gba", "gb", "sms", "gg", "sg1000", "n64")


def _load_base():
    spec = importlib.util.spec_from_file_location("hwtest_md", ROOT / "tools" / "boards" / "megadrive" / "hwtest_md.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B = _load_base()
Guard, Report, run_cli, sha256 = B.Guard, B.Report, B.run_cli, B.sha256


def load_golden(path=GOLDEN):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def system_args(a, system):
    """Opções do sistema que a CLI exige ou aceita: --mapper (adaptador do SMS, tipo de save do GBA e do N64) e --prg (tamanho do N64 em MB, do SMS em KB)."""
    out = ["-s", system]
    if a.mapper:
        out += ["--mapper", str(a.mapper)]
    if a.prg:
        out += ["--prg", str(a.prg)]
    return out


def phase_host(rep, a):
    for bad in (["rom-write", "x.bin"], ["save-write", "x"], ["flash-write", "x"], ["firmware-flash"], ["voltage", "5v"],
                ["dump", "--yes"], ["info", "-y"], ["detect", "-s", "md", "--flash-id"]):
        try:
            run_cli(bad, simulate=True)
            rep.check(False, "a guarda recusa %s" % " ".join(bad))
        except Guard:
            rep.check(True, "a guarda recusa %s" % " ".join(bad))
    g = {k: v for k, v in load_golden().items() if not k.startswith("_")}
    rep.check(isinstance(g, dict), "golden.json é um objeto", "%d cartuchos" % len(g))
    for nome, v in g.items():
        rep.check(v.get("system") in SYSTEMS and (v.get("sha256") or v.get("crc32")), "golden %s: sistema conhecido e um hash" % nome)
    rep.outdir.mkdir(parents=True, exist_ok=True)
    r = run_cli(["info"], simulate=True)
    rep.check(r.get("ok") and r.get("mock"), "info no simulador", "firmware %s" % r.get("firmware"))
    hashes = []
    for i in (1, 2):
        r = run_cli(["dump", "-s", "mock", "-o", str(rep.outdir / ("sim_%d" % i))], simulate=True)
        rep.check(r.get("ok") and r.get("sha1") and r.get("md5"), "dump no simulador #%d (CRC32, MD5 e SHA-1)" % i, "%s bytes" % r.get("bytes"))
        hashes.append(sha256(r["file"]))
    rep.check(hashes[0] == hashes[1], "duas leituras do simulador são iguais", hashes[0][:16])


def common_link(rep, a):
    pa = ["--port", a.port] if a.port else []
    r = run_cli(["info"] + pa)
    if not rep.check(r.get("ok"), "conexão e banner", r.get("firmware", (r.get("error") or {}).get("message", ""))):
        raise SystemExit("sem conexão com a placa: confira a porta e o grupo dialout")
    rep.info("versão do firmware", r.get("firmware"))
    rep.info("sistemas que o firmware informa", ", ".join(r.get("systems", [])))
    times, fails = [], 0
    for _ in range(10):
        x = run_cli(["info"] + pa)
        times.append(x["_seconds"])
        fails += 0 if x.get("ok") else 1
    rep.check(fails == 0, "10 reconexões seguidas", "máx. %.2fs, %d falhas" % (max(times), fails))
    return pa, r


def phase_nocart(rep, a):
    pa, info = common_link(rep, a)
    r = run_cli(["selftest"] + pa, timeout=300)
    rep.check(r.get("ok"), "autoteste da placa (curtos, pull-up do D7, Si5351)", "%d achados, %.0fs" % (len(r.get("findings", [])), r["_seconds"]))
    for f in r.get("findings", []):
        rep.info("autoteste", f)
    for system in a.system or ["md"]:
        if system not in (info.get("systems") or [system]):
            rep.skip("detect -s %s sem cartucho" % system, "o firmware não informa este sistema")
            continue
        d = run_cli(["detect", "-s", system] + pa)
        rep.check(d.get("status") in (1, 2) or d.get("ok") is False, "detect -s %s com o slot vazio não acha cartucho" % system, d.get("status_text", d.get("status")))


def phase_cart(rep, a):
    pa, info = common_link(rep, a)
    system = a.system[0] if a.system else None
    if system not in SYSTEMS:
        raise SystemExit("--system é obrigatório na fase cart: " + ", ".join(SYSTEMS))
    sa = system_args(a, system)
    d = run_cli(["detect"] + sa + pa)
    if not rep.check(d.get("ok"), "detect -s %s" % system, "%s, ROM %s bytes, save %s bytes" % (d.get("name"), d.get("rom_size"), d.get("save_size"))):
        return
    if d.get("n64"):
        rep.info("N64 pelo CRC1", d["n64"])
    rep.outdir.mkdir(parents=True, exist_ok=True)
    hashes, last = [], None
    for i in (1, 2):
        r = run_cli(["dump"] + sa + ["-o", str(rep.outdir / ("rom_%d" % i))] + pa, timeout=1800)
        if not rep.check(r.get("ok"), "leitura da ROM #%d" % i, "%.1fs, %s bytes" % (r["_seconds"], r.get("bytes"))):
            return
        if i == 1:
            rep.info("velocidade", "%.0f KiB/s" % (r["bytes"] / 1024 / max(r["_seconds"], 0.01)))
            rep.info("CRC32 (compare com o No-Intro)", r.get("crc32"))
            rep.info("SHA-1 (o No-Intro e o Redump catalogam por SHA-1)", r.get("sha1"))
            rep.info("checksum do cabeçalho", r.get("checksum"))
            last = r
        hashes.append(sha256(r["file"]))
    rep.check(hashes[0] == hashes[1], "duas leituras da ROM são iguais", hashes[0][:16])
    rep.info("ROM sha256", hashes[0])
    if last and last.get("game"):
        rep.info("jogo achado na base", last["game"].get("name"))
    if a.golden:
        g = {k: v for k, v in load_golden().items() if not k.startswith("_")}.get(a.golden)
        if not g:
            rep.add("FAIL", "cartucho dourado %s" % a.golden, "não está em golden.json")
        else:
            rep.check(g.get("system") == system, "o dourado %s é de %s" % (a.golden, system))
            if g.get("sha256"):
                rep.check(g["sha256"].lower() == hashes[0].lower(), "SHA-256 igual ao do cartucho dourado %s" % a.golden, hashes[0][:16])
            if g.get("crc32"):
                rep.check(g["crc32"].upper() == (last or {}).get("crc32", "").upper(), "CRC32 igual ao do cartucho dourado %s" % a.golden, g["crc32"])
    else:
        rep.skip("comparação com cartucho dourado", "passe --golden NOME (golden.json) para um cartucho de hashes conhecidos")
    if a.save:
        hs = []
        for i in (1, 2):
            r = run_cli(["save-read"] + sa + ["-o", str(rep.outdir / ("save_%d" % i))] + pa)
            if not rep.check(r.get("ok"), "leitura do save #%d" % i, "%s bytes" % r.get("bytes")):
                break
            hs.append(sha256(r["file"]))
        if len(hs) == 2:
            rep.check(hs[0] == hs[1], "duas leituras do save são iguais", hs[0][:16])
    else:
        rep.skip("leituras do save", "passe --save (e --mapper onde o tipo de save é obrigatório)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["host", "nocart", "cart"])
    ap.add_argument("--port")
    ap.add_argument("--system", action="append", choices=SYSTEMS, help="sistema(s); na fase cart, um só")
    ap.add_argument("--mapper", type=int, default=0)
    ap.add_argument("--prg", type=int, default=0)
    ap.add_argument("--golden", help="nome do cartucho dourado em golden.json")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--label", default="")
    ap.add_argument("--out")
    a = ap.parse_args()
    outdir = Path(a.out) if a.out else ROOT / "test-results" / (time.strftime("%Y%m%d-%H%M%S") + "-" + a.phase + ("-" + a.system[0] if a.system else ""))
    rep = Report(a.phase, outdir)
    print("Bancada (somente leitura), fase %s\n" % a.phase)
    try:
        {"host": phase_host, "nocart": phase_nocart, "cart": phase_cart}[a.phase](rep, a)
    except Guard as g:
        rep.add("FAIL", "guarda", str(g))
    except B.subprocess.TimeoutExpired as t:
        rep.add("FAIL", "tempo esgotado", str(t))
    rep.save({"rótulo": a.label, "sistema": ",".join(a.system or []), "CLI": str(B.DUMPER)})
    sys.exit(1 if rep.failed else 0)


if __name__ == "__main__":
    main()
