#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D139: tira o bloco de troca de cartucho (desligar o 5V dos slots por software) de uma versão já roteada, mantendo o roteamento.
Sai: Q1 (chave de alta), Q2 (descarga), Q3 (sensor), LED verde, LED amarelo, os resistores deles e os pinos D19 (PWR_EN) e D53 (SENSE_MCU) do Mega.
Fica: F1, seletor 3,3 V/5 V (LDO, Q4, Q5, J1), resistores em série e TVS. O F1 passa a alimentar o +5V_CART direto (a rede +5V_F some).
No PCB o Q1 vira um jumper de cobre (duas vias e uma trilha de 0,8 mm entre os furos do dreno e da fonte): as trilhas que chegavam ao Q1 continuam valendo.

Uso (da raiz; python do sistema, com pcbnew):
  /usr/bin/python3 -I tools/troca/sem_bloco.py boards/<placa>/hardware-<versão>            # esquemático e PCB
  /usr/bin/python3 -I tools/troca/sem_bloco.py boards/<placa>/hardware-<versão> --so-sch   # só o esquemático
Depois: tools/troca/verifica.sh <placa> <versão> e python3 tools/check_netlist.py --board <placa> --sem-troca."""
import json, re, subprocess, sys, tempfile, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "sch"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sexp import parse, dump, val, find, S

HW = Path(sys.argv[1]).resolve()
SO_SCH = "--so-sch" in sys.argv
SO_REPARA = "--so-repara" in sys.argv      # só as correções finais (vias de troca de face e trilhas que o DRC aponta como soltas)
SCH = HW / "dumper.kicad_sch"
PCB = HW / "dumper.kicad_pcb"
TMP = Path(tempfile.mkdtemp())


def netlist():
    xml = TMP / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml), str(SCH)], check=True, capture_output=True)
    root = ET.parse(xml).getroot()
    comps = {c.get("ref"): (c.findtext("value") or "") for c in root.iter("comp")}
    nets = {n.get("name"): [(x.get("ref"), x.get("pin")) for x in n.iter("node")] for n in root.iter("net")}
    return comps, nets


def bloco_refs(comps, nets):
    """Peças do bloco, pela netlist: o que toca PWR_G, PWR_EN, SENSE ou SENSE_MCU, mais o que fica pendurado nelas só por redes internas
    (LED verde, resistor do LED, resistores de descarga) e o resistor de 100 k entre +5V_CART e GND (pull-down do Q3)."""
    sementes = [n for n in ("/PWR_G", "/PWR_EN", "/SENSE", "/SENSE_MCU") if n in nets]
    assert "/PWR_G" in nets and "/SENSE" in nets, "esta versão não tem o bloco de troca (PWR_G, SENSE)"
    ign = lambda r: r == "A1" or r.startswith(("FLG", "#"))
    rem = {r for n in sementes for r, _ in nets[n] if not ign(r)}
    rem |= {r for r, v in comps.items() if v.startswith(("LED verde", "LED amarelo"))}      # os LEDs do bloco (o status D1 tem outro valor)
    mudou = True
    while mudou:
        mudou = False
        for n, nodes in nets.items():
            if not n.startswith("Net-("):
                continue
            refs = {r for r, _ in nodes if not ign(r)}
            if refs & rem and not refs <= rem:
                rem |= refs; mudou = True
    for r, v in comps.items():          # pull-down de 100 k do gate do Q3: só liga +5V_CART e GND
        if r.startswith("R") and not r.startswith("RN") and v == "100k":
            ns = {n for n, nodes in nets.items() if any(x == r for x, _ in nodes)}
            if ns == {"+5V_CART", "GND"}:
                rem.add(r)
    return rem


def poda_drc():
    """Apaga as trilhas e vias que o próprio DRC do KiCad aponta como soltas (track_dangling, via_dangling), até não sobrar nenhuma."""
    import pcbnew
    total = 0
    for _ in range(30):
        js = TMP / "drc.json"
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "-o", str(js), str(PCB)], capture_output=True)
        d = json.loads(js.read_text())
        ids = {i["uuid"] for v in d.get("violations", []) if v["type"] in ("track_dangling", "via_dangling") for i in v["items"]}
        if not ids:
            break
        b = pcbnew.LoadBoard(str(PCB))
        mortos = [t for t in b.GetTracks() if t.m_Uuid.AsString() in ids]
        if not mortos:
            break
        for t in mortos:
            b.RemoveNative(t)
        total += len(mortos)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(str(PCB), b)
    return total


if SO_REPARA:
    print("trilhas e vias soltas (DRC) apagadas:", poda_drc())
    sys.exit(0)


comps, nets = netlist()
REM = bloco_refs(comps, nets)
print("peças do bloco:", ", ".join("%s(%s)" % (r, comps[r]) for r in sorted(REM)))
assert {r for r in REM if r.startswith("Q")} >= {"Q1", "Q2", "Q3"}, REM
Q1 = next(r for r in REM if r.startswith("Q") and comps[r] == "IRF9540N")
assert Q1 == "Q1"

# ------------------------------------------------------------------ esquemático
text = SCH.read_text()
tree = parse(text)
K = lambda x, y: (round(float(x), 2), round(float(y), 2))


def prop(c, name):
    for p in find(c, "property"):
        if val(p[1]) == name:
            return p
    return None


body = []
a1_nc = []
for c in tree[1:]:
    if isinstance(c, list) and c and val(c[0]) == "symbol" and find(c, "lib_id"):
        ref = val(prop(c, "Reference")[2])
        if ref in REM:
            continue
        if val(find(c, "lib_id")[0][1]) == "power:+5V":
            v = prop(c, "Value")
            if val(v[2]) == "+5V_F":
                v[2] = S("+5V_CART")
    if isinstance(c, list) and c and val(c[0]) == "label" and val(c[1]) in ("PWR_G", "PWR_EN", "SENSE", "SENSE_MCU"):
        continue
    body.append(c)
uu = iter(range(1, 1000))
nc_text = ""


def no_connect(x, y):
    return '\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)\n' % (x, y, "00000000-0000-4000-8000-%012d" % (0xD139000 + next(uu)))


def grava(body_):
    head = [c for c in body_]
    idx = next(i for i, c in enumerate(head) if isinstance(c, list) and c and val(c[0]) == "sheet_instances")
    out = "(kicad_sch\n"
    for c in head[:idx]:
        out += "\t" + dump(c, 1) + "\n"
    out += nc_text
    for c in head[idx:]:
        out += "\t" + dump(c, 1) + "\n"
    SCH.write_text(out + ")\n")


grava(body)


def erc():
    js = TMP / "erc.json"
    subprocess.run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all", "-o", str(js), str(SCH)], capture_output=True)
    d = json.loads(js.read_text())
    return [v for s in d.get("sheets", []) for v in s.get("violations", [])]


# fios, rótulos e símbolos de alimentação que ficaram soltos (o ERC aponta o fio e o rótulo pelo uuid, e o símbolo pela referência na descrição)
for it in range(40):
    viol = erc()
    kill, kill_ref, novos_nc = set(), set(), []      # kill_ref: (referência, x, y) do símbolo; as referências #PWR podem repetir (dois geradores), então a posição do pino decide
    for v in viol:
        t = v["type"]
        if t in ("unconnected_wire_endpoint", "label_dangling"):
            kill.add(v["items"][0]["uuid"])
        elif t == "pin_not_connected":
            d = v["items"][0].get("description", "")
            m = re.match(r"Symbol (\S+) Pin", d)
            if m and m.group(1).startswith(("#PWR", "FLG")):
                kill_ref.add((m.group(1), round(v["items"][0]["pos"]["x"], 2), round(v["items"][0]["pos"]["y"], 2)))
            elif m and m.group(1) == "A1":          # D19 (PWR_EN) e D53 (SENSE_MCU) do Mega ficam sem ligação
                pos = v["items"][0]["pos"]; novos_nc.append((pos["x"], pos["y"]))
        elif t == "pin_to_pin":      # dois PWR_FLAG na mesma rede (+5V_CART depois de juntar o +5V_F): fica o último
            refs = [(re.match(r"Symbol (\S+) Pin", i.get("description", "")), i) for i in v["items"]]
            refs = sorted((m.group(1), round(i["pos"]["x"], 2), round(i["pos"]["y"], 2)) for m, i in refs if m and m.group(1).startswith("FLG"))
            if len(refs) >= 2:
                kill_ref.update(refs[:-1])
    if not kill and not kill_ref and not novos_nc:
        break
    tree = parse(SCH.read_text())
    keep = []
    for c in tree[1:]:
        if isinstance(c, list) and c and val(c[0]) in ("wire", "label", "junction", "no_connect"):
            u = find(c, "uuid")
            if u and val(u[0][1]) in kill:
                continue
        if isinstance(c, list) and c and val(c[0]) == "symbol" and find(c, "lib_id"):
            pr = prop(c, "Reference")
            at = find(c, "at")[0]
            if pr is not None and (val(pr[2]), round(float(at[1]), 2), round(float(at[2]), 2)) in kill_ref:
                continue
        keep.append(c)
    nc_text = "".join(no_connect(x, y) for x, y in novos_nc)
    grava(keep)
    print("  passada %d: %d fios/rótulos, %d símbolos soltos removidos, %d pino(s) do Mega sem ligação" % (it + 1, len(kill), len(kill_ref), len(novos_nc)))
restam = [v for v in erc() if v["severity"] == "error"]
print("ERC depois da limpeza:", len(restam), "erro(s)")
for v in restam[:10]:
    print("  ", v["type"], v["description"][:100], [i.get("description", "")[:60] for i in v["items"]])
if SO_SCH:
    sys.exit(0)

# ------------------------------------------------------------------ PCB
import pcbnew
mm = pcbnew.FromMM; tomm = pcbnew.ToMM
b = pcbnew.LoadBoard(str(PCB))
nome = lambda n: b.FindNet(n)
f1_net, cart_net = nome("+5V_F"), nome("+5V_CART")
assert f1_net is not None and cart_net is not None, "nets +5V_F e +5V_CART não achadas"
q1 = b.FindFootprintByReference(Q1)
q1_pos = {p.GetNumber(): p.GetPosition() for p in q1.Pads()}
q1_pads = {p.GetNumber(): p for p in q1.Pads()}
def camadas_em(pos):
    ls = set()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            if t.GetPosition() == pos: ls |= {pcbnew.F_Cu, pcbnew.B_Cu}
        elif t.GetStart() == pos or t.GetEnd() == pos:
            ls.add(t.GetLayer())
    return ls
CAM_A, CAM_B = camadas_em(q1_pos["2"]), camadas_em(q1_pos["3"])
rem_pcb = [r for r in REM if b.FindFootprintByReference(r) is not None]
VIAR = []         # pads de furo passante que saem e serviam de troca de face para uma rede que continua: viram vias
TOL = mm(0.02)
perto = lambda p, q: abs(p.x - q.x) <= TOL and abs(p.y - q.y) <= TOL
for r in rem_pcb:
    fp = b.FindFootprintByReference(r)
    for pd in fp.Pads():
        if r == Q1 and pd.GetNumber() in ("2", "3"):
            continue
        cam = {t.GetLayer() for t in b.GetTracks() if t.GetClass() != "PCB_VIA" and t.GetNetCode() == pd.GetNetCode() and (perto(t.GetStart(), pd.GetPosition()) or perto(t.GetEnd(), pd.GetPosition()))}
        if len(cam) >= 2:
            VIAR.append((pd.GetPosition(), pd.GetNetname()))
HOT = []          # posições dos pads que saem: de lá começa a poda das trilhas que ficam com a ponta solta
for r in rem_pcb:
    fp = b.FindFootprintByReference(r)
    for pd in fp.Pads():
        if not (r == Q1 and pd.GetNumber() in ("2", "3")):
            HOT.append((pd.GetPosition().x, pd.GetPosition().y))
    b.RemoveNative(fp)
print("footprints removidos:", len(rem_pcb))

# +5V_F passa a +5V_CART (pads, trilhas, vias)
n_ren = 0
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetCode() == f1_net.GetNetCode():
            p.SetNet(cart_net); n_ren += 1
for t in b.GetTracks():
    if t.GetNetCode() == f1_net.GetNetCode():
        t.SetNet(cart_net); n_ren += 1
print("itens passados de +5V_F para +5V_CART:", n_ren)

# pinos D19 e D53 do Mega ficam sem ligação
a1 = b.FindFootprintByReference("A1")
for p in a1.Pads():
    if p.GetNumber() in ("D19", "D53"):
        nm = "unconnected-(A1-Pad%s)" % p.GetNumber()
        ni = b.FindNet(nm)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni)
        p.SetNet(ni)

# redes que ficaram sem nenhum pad: apaga as trilhas e vias delas
com_pad = set()
for f in b.GetFootprints():
    for p in f.Pads():
        com_pad.add(p.GetNetCode())
apagadas = 0
for t in list(b.GetTracks()):
    if t.GetNetCode() not in com_pad:
        b.RemoveNative(t); apagadas += 1
print("trilhas/vias de redes extintas apagadas:", apagadas)

for pos, nm in VIAR:
    ni = b.FindNet("+5V_CART" if nm == "+5V_F" else nm)
    if ni is not None and ni.GetNetCode() in com_pad:
        v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetNet(ni)
        v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4)); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
print("pads que trocavam de face viraram vias:", len(VIAR))

# o Q1 vira um jumper de cobre entre o dreno (pino 2) e a fonte (pino 3): na camada em que as duas trilhas chegam, ou em B.Cu com via onde faltar
pa, pb = q1_pos["2"], q1_pos["3"]
comum = CAM_A & CAM_B
camada = next(iter(comum)) if comum else pcbnew.B_Cu
PROT = []
for pos, cam in ((pa, CAM_A), (pb, CAM_B)):
    if camada not in cam or (cam - {camada}):      # o pad era a troca de face das trilhas desse lado: a via a refaz
        v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetNet(cart_net)
        v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4)); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); PROT.append(v)
j = pcbnew.PCB_TRACK(b); j.SetStart(pa); j.SetEnd(pb); j.SetLayer(camada); j.SetWidth(mm(0.8)); j.SetNet(cart_net); b.Add(j); PROT.append(j)
print("jumper do Q1 na camada", b.GetLayerName(camada), "com", len(PROT) - 1, "via(s)")

# pontas soltas que o bloco deixou: só a partir dos pads que saíram (a poda global do poda138.py apaga ligações em T no meio de outra trilha)
def poda_local(b, hot, ancoras, protegidos):
    import math
    TOL = mm(0.01)
    def perto(p, q): return abs(p[0] - q[0]) <= TOL and abs(p[1] - q[1]) <= TOL
    def dist_seg(p, a, c):
        ax, ay, cx, cy = a[0], a[1], c[0], c[1]
        dx, dy = cx - ax, cy - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))
    removidos = 0
    hot = list(hot)
    for _ in range(2000):
        pads = [(p.GetPosition().x, p.GetPosition().y, p.GetNetCode()) for f in b.GetFootprints() for p in f.Pads()]
        trs = [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
        vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
        gnd = b.FindNet("GND").GetNetCode()
        def ligado(pt, nc, ly, ignora):
            if any(perto(pt, (a.x, a.y)) for a in ancoras):
                return True
            if any(perto(pt, (x, y)) and n == nc for x, y, n in pads):
                return True
            if any(perto(pt, (v.GetPosition().x, v.GetPosition().y)) and v.GetNetCode() == nc and v is not ignora for v in vias):
                return True
            for t in trs:
                if t is ignora or t.GetNetCode() != nc or t.GetLayer() != ly:
                    continue
                if dist_seg(pt, (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)) <= t.GetWidth() / 2 + TOL:
                    return True
            return False
        mortos = []
        for t in trs:
            if any(t is q for q in protegidos):
                continue
            for e in (t.GetStart(), t.GetEnd()):
                pt = (e.x, e.y)
                if any(perto(pt, h) for h in hot) and not ligado(pt, t.GetNetCode(), t.GetLayer(), t):
                    mortos.append(t); break
        for v in vias:
            pt = (v.GetPosition().x, v.GetPosition().y)
            if v.GetNetCode() == gnd or any(v is q for q in protegidos) or not any(perto(pt, h) for h in hot):
                continue
            camadas = set()
            if any(perto(pt, (x, y)) and n == v.GetNetCode() for x, y, n in pads):
                camadas = {pcbnew.F_Cu, pcbnew.B_Cu}
            for t in trs:
                if t.GetNetCode() == v.GetNetCode() and (perto(pt, (t.GetStart().x, t.GetStart().y)) or perto(pt, (t.GetEnd().x, t.GetEnd().y))):
                    camadas.add(t.GetLayer())
            if len(camadas) < 2:
                mortos.append(v)
        if not mortos:
            break
        for t in mortos:
            if t.GetClass() == "PCB_VIA":
                hot.append((t.GetPosition().x, t.GetPosition().y))
            else:
                hot.extend([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)])
            b.RemoveNative(t); removidos += 1
    return removidos
print("trilhas e vias soltas podadas:", poda_local(b, HOT, [pa, pb], PROT))

# silkscreen: os rótulos dos LEDs saem; o aviso de troca passa a mandar desligar o USB
for d in list(b.GetDrawings()):
    if d.GetClass() == "PCB_TEXT":
        t = d.GetText()
        if t in ("SEGURO TROCAR", "5V LIGADO", "PTC 0,5 A"):
            b.RemoveNative(d)
        elif t == "SÓ TROQUE O CARTUCHO COM":
            d.SetText("TROQUE O CARTUCHO COM")
        elif t == "O LED AMARELO ACESO":
            d.SetText("O USB DESLIGADO")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(str(PCB), b)
print("trilhas e vias soltas (DRC) apagadas:", poda_drc())
print("ok", HW)
