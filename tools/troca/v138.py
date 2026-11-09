#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D138: F1, J1 e seletor 3,3 V/5 V em uma placa. ATENÇÃO (D139): o modo `bloco` gerava o bloco de troca de cartucho, retirado de todas as placas (veja `sem_bloco.py`); não o use. Só `fusivel:<versão>` e `existente` ainda fazem sentido. Refaz a versão a partir do git (HEAD), roda o gerador e o roteamento.
Uso (da raiz):
  python3 tools/troca/v138.py <placa> prep  bloco|fusivel:<versão> [--ext mm]    esquemático + posicionamento
  python3 tools/troca/v138.py <placa> rota  bloco|fusivel:<versão>               Freerouting + acabamento
Parâmetros por placa em tools/troca/boards.json (anchor, region, version, fonte, sel_slots, sel_caps, moves, hide)."""
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
PY = os.environ.get("PY", str(Path.home() / "development/llms/KiCAD-MCP-Server/.venv/bin/python"))
B, ETAPA, ALVO = sys.argv[1:4]
EXT = float(sys.argv[sys.argv.index("--ext") + 1]) if "--ext" in sys.argv else None
cfg = json.loads((ROOT / "tools/troca/boards.json").read_text())[B]
fus = ALVO.startswith("fusivel:")
VER = ALVO.split(":")[1] if fus else cfg["version"]
MODO_BLOCO = cfg.get("modo", "bloco")      # "existente": a fonte já tem o bloco de troca (16_bits v1.3)
FONTE = VER if (fus or MODO_BLOCO == "existente") else cfg.get("fonte", "v1.0")
sel = None if fus else cfg.get("sel")
HW = ROOT / f"boards/{B}/hardware-{VER}"
def run(cmd, env=None, check=True):
    e = dict(os.environ, **(env or {}))
    r = subprocess.run(cmd, cwd=ROOT, env=e, text=True, capture_output=True)
    out = (r.stdout or "") + (r.stderr or "")
    out = "\n".join(l for l in out.splitlines() if "FakeAssoc" not in l and "Debug:" not in l)
    if check and r.returncode:
        sys.exit("FALHA: %s\n%s" % (" ".join(cmd), out[-1500:]))
    return out, r.returncode
if ETAPA == "manifesto":      # refaz só o esquemático numa pasta temporária e guarda d138.json (peças do D138) ao lado do projeto
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as td:
        src = subprocess.run(["git", "show", f"HEAD:boards/{B}/hardware-{FONTE}/dumper.kicad_sch"], cwd=ROOT, capture_output=True, check=True).stdout
        (Path(td) / "dumper.kicad_sch").write_bytes(src)
        env = {"TROCA_MODO": "fusivel" if fus else MODO_BLOCO, "TROCA_FUSE": "1"}
        if sel:
            env.update(TROCA_SELETOR="1", TROCA_SLOTS=",".join(sel["slots"]), TROCA_SEL_CAPS=",".join(sel["caps"]))
        run(["python3", "tools/troca/sch_block.py", str(Path(td) / "dumper.kicad_sch"), VER], env)
        shutil.copy(Path(td) / "d138.json", HW / "d138.json")
    print("manifesto de", B, VER, ":", (HW / "d138.json").read_text().replace("\n", " "))
    sys.exit(0)
if ETAPA == "prep":
    for ext in ("kicad_sch", "kicad_pcb"):
        src = subprocess.run(["git", "show", f"HEAD:boards/{B}/hardware-{FONTE}/dumper.{ext}"], cwd=ROOT, capture_output=True, check=True).stdout
        (HW / f"dumper.{ext}").write_bytes(src)
    env = {"TROCA_MODO": "fusivel" if fus else MODO_BLOCO, "TROCA_FUSE": "1"}
    src_cfg = cfg.get("fusivel", cfg) if fus else cfg
    region = src_cfg["region"]; anchor = src_cfg["anchor"]
    if sel:
        env.update(TROCA_SELETOR="1", TROCA_SLOTS=",".join(sel["slots"]), TROCA_SEL_CAPS=",".join(sel["caps"]))
    out, _ = run(["python3", "tools/troca/sch_block.py", str(HW / "dumper.kicad_sch"), VER], env)
    print("\n".join(l for l in out.splitlines() if l.startswith(("símbolos", "resistores", "  SEM", "ok"))))
    last = ""
    for ext in ([EXT] if EXT is not None else ([20, 25, 30, 35, 40, 45, 50, 60] if sel else [0, 5, 10, 15, 20, 25, 30, 40])):
        if ext:   # volta o PCB ao estado do git e estende o contorno para baixo: todo o bloco vai para a faixa nova
            src = subprocess.run(["git", "show", f"HEAD:boards/{B}/hardware-{FONTE}/dumper.kicad_pcb"], cwd=ROOT, capture_output=True, check=True).stdout
            (HW / "dumper.kicad_pcb").write_bytes(src)
            o, _ = run(["/usr/bin/python3", "-I", "tools/troca/estende.py", str(HW), str(ext)])
            y0, y1, bx0, bx1 = [float(v) for v in o.split()[-4:]]
            region = [bx0 + 3, y0 + 0.5, bx1 - 3, y1 - 1.5]
            anchor = [(bx0 + bx1) / 2, (y0 + y1) / 2]
        o, rc = run([PY, "tools/troca/pcb_block.py", str(HW), VER, str(anchor[0]), str(anchor[1])] + [str(v) for v in region], check=False)
        last = o
        if rc == 0:
            Path("/tmp/claude-1000/route").mkdir(parents=True, exist_ok=True)
            Path("/tmp/claude-1000/route/ext-%s-%s" % (B, VER)).write_text(str(ext))      # a etapa "rota" não move textos de uma placa estendida
            print("PCB posicionado" + (" com extensão de %d mm" % ext if ext else "")); print("\n".join(o.splitlines()[-4:])); break
        print("  extensão de", ext, "mm: ", [l for l in o.splitlines() if "sem lugar" in l][:1])
    else:
        sys.exit("sem lugar mesmo com a maior extensão\n" + last[-800:])
else:
    out, _ = run([PY, "tools/troca/route.py", str(HW), os.environ.get("PASSES", "40")])
    print(out[-300:])
    cmd = [PY, "tools/troca/finish.py", str(HW), "--date", "2026-11-08"]
    if fus: cmd.append("--fusivel")
    else:
        mark = Path("/tmp/claude-1000/route/ext-%s-%s" % (B, VER))
        if not (mark.exists() and float(mark.read_text() or 0) > 0):      # placa estendida: os textos antigos ficam onde estão
            for m in cfg.get("moves", []): cmd += ["--move", m]
            for h in cfg.get("hide", []): cmd += ["--hide", h]
    out, _ = run(cmd)
    print(out[-400:])
