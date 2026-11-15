#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verifica todas as placas e versões de uma vez (K-1, docs/planos/pendencias-sem-placa-spec.md).

Para cada boards/<placa>/hardware-<versão>/:
  - ERC e DRC (com paridade esquemático x PCB) pelo kicad-cli, em JSON;
  - falha se houver ligação aberta, curto, folga, trilhas cruzadas, via solta, furo, borda ou peça faltando;
  - silk obrigatório (CLAUDE.md seção 5): atribuição CC BY 4.0, versão da placa, lado da etiqueta do slot.
Para a versão atual de cada placa (boards/versoes.json):
  - tools/check_netlist.py --board <placa> (netlist x pinmap.md);
  - existência de README.md, renders, gerbers, BOM e zip da fab;
  - SHA-256 do zip contra o PEDIDO.md (aviso se a linha da versão atual não bate).

Uso: python3 tools/check_all_boards.py [--board <placa>] [--no-drc] [--json] [-j N]
Sai com 1 se achar algum ERRO (avisos não mudam o código de saída).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOARDS = ROOT / "boards"

# Classes de DRC que são defeito de verdade (as mesmas de tools/troca/verifica.sh).
DRC_ERRORS = {"unconnected_items", "shorting_items", "clearance", "tracks_crossing", "via_dangling",
              "copper_edge_clearance", "hole_clearance", "courtyards_overlap", "missing_footprint"}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def versoes():
    return json.loads((BOARDS / "versoes.json").read_text())


def board_dirs(only):
    out = []
    for p in sorted(BOARDS.iterdir()):
        if p.name.startswith("_") or not p.is_dir() or (only and p.name != only):
            continue
        vs = sorted(d.name[len("hardware-"):] for d in p.glob("hardware-v*") if d.is_dir())
        if vs:
            out.append((p.name, vs))
    return out


def drc(hw, tmp):
    out = tmp / "drc.json"
    r = run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "--schematic-parity",
             "-o", str(out), str(hw / "dumper.kicad_pcb")])
    if not out.exists():
        return None, r.stderr.strip()[-200:]
    d = json.loads(out.read_text())
    cnt = {}
    errs = []
    items = list(d.get("violations", [])) + [dict(x, type="unconnected_items") for x in d.get("unconnected_items", [])] \
        + list(d.get("schematic_parity", []))
    for v in items:
        t = v["type"]
        txt = " ".join(i.get("description", "") for i in v.get("items", []))
        tudo = f"{v.get('description', '')} {txt}"
        if t in DRC_ERRORS and not re.search(r"\bFLG\d+\b \(PWR_FLAG\)", tudo):
            errs.append(f"{t}: {tudo}"[:200])
        cnt[t] = cnt.get(t, 0) + 1
    return {"classes": cnt, "errors": errs}, None


def erc(hw, tmp):
    out = tmp / "erc.json"
    run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all", "-o", str(out), str(hw / "dumper.kicad_sch")])
    if not out.exists():
        return None, "ERC não gerou saída"
    d = json.loads(out.read_text())
    cnt = {}
    errs = []
    for s in d.get("sheets", []):
        for v in s.get("violations", []):
            cnt[v["type"]] = cnt.get(v["type"], 0) + 1
            if v.get("severity") == "error":
                errs.append(f"{v['type']}: {v.get('description', '')}"[:200])
    return {"classes": cnt, "errors": errs}, None


def silk(hw, ver):
    txt = (hw / "dumper.kicad_pcb").read_text(errors="replace")
    texts = re.findall(r'\(gr_text "([^"]*)"', txt)
    joined = "\n".join(texts)
    errs = []
    if "CC BY 4.0" not in joined:
        errs.append("silk sem a atribuição ao OSCR (CC BY 4.0)")
    if not re.search(r"v\.? ?" + re.escape(ver[1:]) + r"\b", joined):
        errs.append(f"silk sem a versão {ver}")
    slots = re.findall(r'\(footprint "[^"]*(?:Slot|SLOT)[^"]*"', txt)
    if len(slots) > 1 and "UM CARTUCHO POR VEZ" not in joined.upper():
        errs.append('placa com mais de um slot sem "UM CARTUCHO POR VEZ"')
    if slots and "ETIQUETA" not in joined.upper():
        errs.append("silk sem o lado da etiqueta do cartucho")
    # mensagens do silk em pt-BR: palavras inglesas comuns que não são nomes próprios
    for w in ("CARTRIDGE ONLY", "DO NOT", "ONE CART", "LABEL SIDE", "INSERT"):
        if w in joined.upper().replace("OPEN SOURCE CARTRIDGE READER", ""):
            errs.append(f"silk em inglês: {w}")
    return errs


def fab(board, ver):
    """Arquivos de fabricação da versão e SHA-256 contra o PEDIDO.md."""
    f = BOARDS / board / "fab"
    errs, warns = [], []
    for need in (f / f"gerbers-{ver}", f / f"bom-{ver}.csv", f / f"dumper-{ver}-jlcpcb.zip"):
        if not need.exists():
            errs.append(f"falta {need.relative_to(ROOT)}")
    z = f / f"dumper-{ver}-jlcpcb.zip"
    ped = f / "PEDIDO.md"
    if z.exists() and ped.exists():
        sha = hashlib.sha256(z.read_bytes()).hexdigest()
        linhas = [ln for ln in ped.read_text().splitlines() if f"dumper-{ver}-jlcpcb.zip" in ln and re.search(r"[0-9a-f]{64}", ln)]
        if not linhas:
            warns.append(f"PEDIDO.md sem SHA-256 do zip da {ver}")
        elif not any(sha in ln for ln in linhas):
            warns.append(f"SHA-256 do PEDIDO.md não bate com o zip da {ver} (real {sha[:12]}...)")
    return errs, warns


def netlist(board):
    r = run([sys.executable, str(ROOT / "tools/check_netlist.py"), "--board", board])
    if r.returncode != 0:
        return [l for l in (r.stdout + r.stderr).splitlines() if l.strip()][-6:]
    return []


def one(args):
    board, ver, atual, do_drc = args
    hw = BOARDS / board / f"hardware-{ver}"
    res = {"board": board, "ver": ver, "atual": atual, "errors": [], "warnings": [], "drc": None, "erc": None}
    for need in ("dumper.kicad_pcb", "dumper.kicad_sch"):
        if not (hw / need).exists():
            res["errors"].append(f"falta {need}")
            return res
    res["errors"] += silk(hw, ver)
    if do_drc:
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            d, e = drc(hw, tmp)
            if d is None:
                res["errors"].append(f"DRC falhou: {e}")
            else:
                res["drc"] = d["classes"]
                res["errors"] += [f"DRC {x}" for x in d["errors"]]
            d, e = erc(hw, tmp)
            if d is None:
                res["errors"].append(e)
            else:
                res["erc"] = d["classes"]
                res["errors"] += [f"ERC {x}" for x in d["errors"]]
    if atual:
        for need in ("README.md", "render-cima.png", "render-baixo.png"):
            if not (hw / need).exists():
                res["errors"].append(f"falta {need} na versão atual")
        fe, fw = fab(board, ver)
        res["errors"] += fe
        res["warnings"] += fw
        res["errors"] += [f"netlist: {l}" for l in netlist(board)]
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board")
    ap.add_argument("--no-drc", action="store_true", help="pula ERC e DRC (rápido)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-j", type=int, default=3, help="placas em paralelo (cada DRC já usa vários núcleos)")
    a = ap.parse_args()
    if run(["kicad-cli", "--version"]).returncode != 0:
        print("kicad-cli não encontrado", file=sys.stderr)
        return 2
    ver_atual = versoes()
    jobs = []
    for board, vs in board_dirs(a.board):
        atual = ver_atual.get(board, {}).get("atual")
        if atual is None:
            print(f"AVISO: {board} fora de boards/versoes.json", file=sys.stderr)
        elif atual not in vs:
            print(f"ERRO: boards/versoes.json diz {board} {atual}, mas hardware-{atual}/ não existe", file=sys.stderr)
            return 1
        jobs += [(board, v, v == atual, not a.no_drc) for v in vs]
    with ThreadPoolExecutor(max_workers=a.j) as ex:
        results = list(ex.map(one, jobs))
    if a.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            tag = "atual" if r["atual"] else "     "
            mark = "ERRO" if r["errors"] else ("aviso" if r["warnings"] else "ok")
            drc_s = ""
            if r["drc"] is not None:
                drc_s = f"  DRC {sum(r['drc'].values())} itens, ERC {sum((r['erc'] or {}).values())} itens"
            print(f"{mark:5} {r['board']:15} {r['ver']:5} {tag}{drc_s}")
            for e in r["errors"]:
                print(f"        ERRO  {e}")
            for w in r["warnings"]:
                print(f"        aviso {w}")
    n_err = sum(1 for r in results if r["errors"])
    print(f"\n{len(results)} versões, {n_err} com erro, {sum(1 for r in results if r['warnings'])} com aviso")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
