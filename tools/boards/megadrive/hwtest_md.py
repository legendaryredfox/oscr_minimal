#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Suíte de bancada SOMENTE LEITURA para o Mega Drive (MD-10, docs/planos/melhorias-megadrive.md).

Modelo: md_rewriter/tools/hwtest/hwtest.py (repositório irmão). Esta suíte nunca grava nem apaga nada no cartucho: todo comando passa por `run_cli()`, que recusa
qualquer coisa fora de READ_ONLY_COMMANDS e os argumentos `--yes`, `--flash-id` e `-y` (a sondagem de ID da flash ESCREVE comandos no cartucho; num cartucho de máscara
isso não pode acontecer). rom-write, save-write, flash-*, firmware-flash e voltage não são alcançáveis daqui.

Fases
  host     sem hardware: guarda, análise de ROM e a CLI inteira contra o simulador (`--simulate -s mock`)
  nocart   placa ligada, slot VAZIO: conexão, 10 reconexões, `selftest`, `detect -s md` sem cartucho, duas leituras iguais
  cart     placa ligada, um cartucho no slot (nada é mudado nele): `detect`, duas leituras iguais, espelho, checksum do cabeçalho, blocos distintos

Uso, da raiz do repositório:
  python3 tools/boards/megadrive/hwtest_md.py host
  python3 tools/boards/megadrive/hwtest_md.py nocart [--port /dev/ttyACM0]
  python3 tools/boards/megadrive/hwtest_md.py cart   [--port /dev/ttyACM0] [--label "meu cartucho"]

Saída: tabela no stdout e relatório em test-results/<data>-<fase>/ (report.json, report.md e os dumps). Código de saída 0 só se nenhuma verificação falhou;
SKIP não é falha; INFO registra um valor. Só biblioteca padrão.

Regras do usuário (2026-11-13): cartucho original de máscara nunca é gravado; cada gravação só com o aval do usuário naquele momento (esta suíte não grava).
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DUMPER = ROOT / "host" / "dumper.py"
READ_ONLY_COMMANDS = {"info", "detect", "dump", "save-read", "selftest", "identify", "search"}
FORBIDDEN_ARGS = {"--yes", "-y", "--flash-id", "--ignore-cart-limit", "--allow-5v"}


class Guard(Exception):
    pass


def run_cli(args, timeout=600, simulate=False):
    """Roda a CLI com --json. Recusa o que poderia alterar um cartucho. Devolve o JSON (com _seconds e _rc)."""
    cmd = [a for a in args if not a.startswith("-")][:1]
    if not cmd or cmd[0] not in READ_ONLY_COMMANDS:
        raise Guard("comando fora da suíte somente leitura: %r" % (args,))
    if any(a in FORBIDDEN_ARGS for a in args):
        raise Guard("argumento proibido na suíte somente leitura: %r" % (args,))
    if not simulate:
        time.sleep(0.3)           # o firmware pode ignorar uma conexão logo depois de o processo anterior fechar a porta
    t0 = time.monotonic()
    argv = [sys.executable, str(DUMPER)] + (["--simulate"] if simulate else []) + ["--json"] + args
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    try:
        data = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        data = {"ok": False, "error": {"message": "a CLI não devolveu JSON"}, "stderr": p.stderr[-400:]}
    data["_seconds"] = round(time.monotonic() - t0, 2)
    data["_rc"] = p.returncode
    return data


def analyze_rom(data):
    """Fatos sobre um dump que separam defeito do cartucho de uma ROM normal. Função pura, sem dispositivo.

    declared: tamanho da ROM no cabeçalho (0x1A4), None se ausente ou implausível.
    cart: tamanho da imagem real. Uma leitura maior que o cartucho repete a imagem (linhas de endereço altas não decodificadas): isso é espelho, não defeito.
    checksum: palavra do cabeçalho em 0x18E contra a soma das palavras de 0x200 até o fim declarado. Divergência não prova leitura ruim (há jogos
    licenciados com valor errado): precisa de um dump de referência.
    """
    out = {"declared": None, "cart": len(data), "mirrored": False, "checksum": None, "run_blocks": {}}
    if len(data) >= 0x1A8 and data[0x100:0x103] == b"SEG":
        end = int.from_bytes(data[0x1A4:0x1A8], "big") + 1
        if 0x200 < end <= len(data) and end % 2 == 0:
            out["declared"] = end
            out["header_checksum"] = int.from_bytes(data[0x18E:0x190], "big")
            total = sum(int.from_bytes(data[i:i + 2], "big") for i in range(0x200, end, 2)) & 0xFFFF
            out["computed_checksum"] = total
            out["checksum"] = (total == out["header_checksum"])
    cart = len(data)
    uniform = len(data) > 0 and data.count(data[:1]) == len(data)      # cartucho vazio/apagado é um byte repetido: dividir ao meio não diz nada das linhas de endereço
    while not uniform and cart % 2 == 0 and cart > 0x80000 and data[:cart // 2] == data[cart // 2:cart]:
        cart //= 2
    out["cart"] = cart
    out["mirrored"] = cart < len(data)
    for name, byte in (("0x00", 0), ("0xFF", 0xFF)):
        out["run_blocks"][name] = sum(1 for i in range(0, cart, 0x8000) if data[i:i + 0x8000] == bytes([byte]) * len(data[i:i + 0x8000]))
    out["distinct_blocks"] = len({data[i:i + 0x8000] for i in range(0, cart, 0x8000)})
    out["blocks"] = (cart + 0x7FFF) // 0x8000
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Report:
    def __init__(self, phase, outdir):
        self.phase, self.outdir, self.rows = phase, outdir, []

    def add(self, status, name, detail=""):
        self.rows.append({"status": status, "name": name, "detail": detail})
        print("%-5s %-52s %s" % (status, name, detail))

    def check(self, cond, name, detail=""):
        self.add("PASS" if cond else "FAIL", name, detail)
        return cond

    def info(self, name, detail):
        self.add("INFO", name, str(detail))

    def skip(self, name, why):
        self.add("SKIP", name, why)

    @property
    def failed(self):
        return any(r["status"] == "FAIL" for r in self.rows)

    def save(self, extra):
        self.outdir.mkdir(parents=True, exist_ok=True)
        data = {"phase": self.phase, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "extra": extra, "rows": self.rows, "failed": self.failed}
        (self.outdir / "report.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
        lines = ["# Bancada do Mega Drive (somente leitura): %s" % self.phase, "", "Data: %s" % data["when"], ""]
        for k, v in extra.items():
            lines.append("- %s: %s" % (k, v))
        lines += ["", "| Estado | Verificação | Detalhe |", "|---|---|---|"]
        for r in self.rows:
            lines.append("| %s | %s | %s |" % (r["status"], r["name"], r["detail"].replace("|", "/")))
        (self.outdir / "report.md").write_text("\n".join(lines) + "\n")
        print("\nrelatório: %s" % self.outdir)


# ------------------------------------------------------------------ fases

def phase_host(rep, a):
    for bad in (["rom-write", "x.bin"], ["save-write", "x"], ["flash-write", "x"], ["firmware-flash"], ["voltage", "5v"],
                ["dump", "--yes"], ["info", "-y"], ["detect", "-s", "md", "--flash-id"], ["flash-id", "--bus", "md"]):
        try:
            run_cli(bad, simulate=True)
            rep.check(False, "a guarda recusa %s" % " ".join(bad))
        except Guard:
            rep.check(True, "a guarda recusa %s" % " ".join(bad))
    img = bytearray(b"\xff" * 0x100000)
    img[0x100:0x110] = b"SEGA MEGA DRIVE "
    img[0x1A4:0x1A8] = (0xFFFFF).to_bytes(4, "big")
    img[0x200:0x204] = b"\x12\x34\x56\x78"
    img[0x18E:0x190] = ((0x1234 + 0x5678 + 0xFFFF * ((0x100000 - 0x204) // 2)) & 0xFFFF).to_bytes(2, "big")
    an = analyze_rom(bytes(img) * 2)
    rep.check(an["mirrored"] and an["cart"] == 0x100000 and an["declared"] == 0x100000 and an["checksum"] is True,
              "analyze_rom: jogo de 1M lido como 2M (espelho), checksum certo")
    rep.check(not analyze_rom(b"\xff" * 0x200000)["mirrored"], "analyze_rom: imagem vazia de 2M não é espelho")
    img[0x18E] ^= 1
    an = analyze_rom(bytes(img))
    rep.check(an["checksum"] is False and not an["mirrored"], "analyze_rom: checksum errado é acusado, sem espelho")
    rep.check(analyze_rom(bytes(range(256)) * 4096)["distinct_blocks"] == 1, "analyze_rom: blocos iguais contam como um só (linha de endereço presa)")
    # a CLI inteira contra o simulador: duas leituras iguais, o mesmo caminho da fase `cart`
    rep.outdir.mkdir(parents=True, exist_ok=True)
    r = run_cli(["info"], simulate=True)
    rep.check(r.get("ok") and r.get("mock"), "info no simulador", "firmware %s" % r.get("firmware"))
    d = run_cli(["detect", "-s", "mock"], simulate=True)
    rep.check(d.get("ok") and d.get("status") == 0, "detect no simulador", d.get("name"))
    h = []
    for i in (1, 2):
        out = rep.outdir / ("sim_%d" % i)
        r = run_cli(["dump", "-s", "mock", "-o", str(out)], simulate=True)
        if not rep.check(r.get("ok"), "dump no simulador #%d" % i, "%s bytes" % r.get("bytes")):
            return
        h.append(sha256(r["file"]))
    rep.check(h[0] == h[1], "duas leituras do simulador são iguais", h[0][:16])
    r = run_cli(["selftest"], simulate=True)
    rep.check(r.get("ok") and r.get("findings") == [], "selftest no simulador")


def find_port(a):
    return ["--port", a.port] if a.port else []


def common_link(rep, a):
    pa = find_port(a)
    r = run_cli(["info"] + pa)
    ok = rep.check(r.get("ok"), "conexão e banner", r.get("firmware", (r.get("error") or {}).get("message", "")))
    if not ok:
        raise SystemExit("sem conexão com a placa: confira a porta e o grupo dialout")
    rep.info("versão do firmware", r.get("firmware"))
    rep.info("protocolo / carga máxima", "%s / %s" % (r.get("proto"), r.get("max_payload")))
    times, fails = [], 0
    for _ in range(10):
        x = run_cli(["info"] + pa)
        times.append(x["_seconds"])
        fails += 0 if x.get("ok") else 1
    rep.check(fails == 0, "10 reconexões seguidas", "máx. %.2fs, %d falhas" % (max(times), fails))
    return pa, r


def phase_nocart(rep, a):
    pa, _ = common_link(rep, a)
    r = run_cli(["selftest"] + pa, timeout=300)
    rep.check(r.get("ok"), "autoteste da placa (curtos, pull-up do D7, Si5351)", "%d achados, %.0fs" % (len(r.get("findings", [])), r["_seconds"]))
    for f in r.get("findings", []):
        rep.info("autoteste", f)
    d = run_cli(["detect", "-s", "md"] + pa)
    rep.check(d.get("status") == 2 or d.get("ok") is False, "detect -s md com o slot vazio não acha cartucho", d.get("status_text", d.get("status")))


def phase_cart(rep, a):
    pa, info = common_link(rep, a)
    d = run_cli(["detect", "-s", "md"] + pa)
    if not rep.check(d.get("ok"), "detect -s md", "%s, ROM %s bytes, save %s bytes" % (d.get("name"), d.get("rom_size"), d.get("save_size"))):
        return
    rep.outdir.mkdir(parents=True, exist_ok=True)
    hashes = []
    for i in (1, 2):
        out = rep.outdir / ("rom_%d" % i)
        r = run_cli(["dump", "-s", "md", "-o", str(out)] + pa, timeout=900)
        if not rep.check(r.get("ok"), "leitura da ROM #%d" % i, "%.1fs" % r["_seconds"]):
            return
        if i == 1:
            rep.info("velocidade", "%.0f KiB/s" % (r["bytes"] / 1024 / max(r["_seconds"], 0.01)))
            first = Path(r["file"])
            rep.info("CRC32 (compare com o No-Intro)", r.get("crc32"))
        hashes.append(sha256(r["file"]))
    rep.check(hashes[0] == hashes[1], "duas leituras da ROM são iguais", hashes[0][:16])
    rep.info("ROM sha256", hashes[0])
    data = first.read_bytes()
    rep.check(len(data) == d.get("rom_size"), "o dump tem o tamanho que o detect disse", "%d bytes" % len(data))
    rep.info("cabeçalho em 0x100", ("cabeçalho SEGA presente: " if data[0x100:0x103] == b"SEG" else "sem cabeçalho SEGA: ") + data[0x100:0x110].decode("latin1", "replace"))
    rep.info("nome no cabeçalho", data[0x120:0x150].decode("latin1", "replace").strip())
    an = analyze_rom(data)
    if an["declared"]:
        rep.info("tamanho da ROM no cabeçalho", "%d bytes (0x1A4)" % an["declared"])
        if an["checksum"] is True:
            rep.info("checksum do cabeçalho", "confere (0x%04X)" % an["header_checksum"])
        elif an["checksum"] is False:
            rep.info("checksum do cabeçalho", "DIVERGE: cabeçalho 0x%04X, calculado 0x%04X sobre 0x200..0x%X. Não prova leitura ruim: compare com um dump de referência"
                     % (an["header_checksum"], an["computed_checksum"], an["declared"]))
        if an["mirrored"]:
            rep.check(an["cart"] >= an["declared"], "o período do espelho cobre o tamanho do cabeçalho",
                      "lidos %d bytes, imagem do cartucho %d, cabeçalho %d" % (len(data), an["cart"], an["declared"]))
    if an["mirrored"]:
        rep.info("espelho", "a leitura de %d bytes repete uma imagem de %d bytes (linhas altas de endereço sem decodificar: normal em cartucho menor)" % (len(data), an["cart"]))
    rep.info("blocos de 32 KiB uniformes", "%d de 0x00, %d de 0xFF (preenchimento é normal; veja onde fica)" % (an["run_blocks"]["0x00"], an["run_blocks"]["0xFF"]))
    rep.info("blocos de 32 KiB distintos", "%d de %d na imagem de %d bytes (todos iguais = linha de endereço presa)" % (an["distinct_blocks"], an["blocks"], an["cart"]))
    if an["blocks"] > 1:
        rep.check(an["distinct_blocks"] > 1, "a imagem não é um bloco repetido", "%d blocos distintos" % an["distinct_blocks"])
    if d.get("save_size"):
        hs = []
        for i in (1, 2):
            r = run_cli(["save-read", "-s", "md", "-o", str(rep.outdir / ("save_%d" % i))] + pa)
            if not rep.check(r.get("ok"), "leitura do save #%d" % i, "%s bytes" % r.get("bytes")):
                break
            hs.append(sha256(r["file"]))
        if len(hs) == 2:
            rep.check(hs[0] == hs[1], "duas leituras do save são iguais", hs[0][:16])
    else:
        rep.skip("leituras do save", "o detect não informou save neste cartucho")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["host", "nocart", "cart"])
    ap.add_argument("--port")
    ap.add_argument("--label", default="")
    ap.add_argument("--out", help="pasta do resultado (padrão test-results/<hora>-<fase>)")
    a = ap.parse_args()
    outdir = Path(a.out) if a.out else ROOT / "test-results" / (time.strftime("%Y%m%d-%H%M%S") + "-md-" + a.phase)
    rep = Report(a.phase, outdir)
    print("Bancada do Mega Drive, fase %s (somente leitura)\n" % a.phase)
    try:
        {"host": phase_host, "nocart": phase_nocart, "cart": phase_cart}[a.phase](rep, a)
    except Guard as g:
        rep.add("FAIL", "guarda", str(g))
    except subprocess.TimeoutExpired as t:
        rep.add("FAIL", "tempo esgotado", str(t))
    rep.save({"rótulo": a.label, "CLI": str(DUMPER)})
    sys.exit(1 if rep.failed else 0)


if __name__ == "__main__":
    main()
