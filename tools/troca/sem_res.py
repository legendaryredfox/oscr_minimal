#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D145: tira os resistores série R3 a R14 (0 ohm) das linhas de controle do slot Mega Drive da 16_bits, mantendo o roteamento; as duas redes de cada resistor viram uma só (a do lado do slot). Adaptado do sem_rn.py (D140), de onde vem o resto do texto abaixo.

Original (D140): tira de uma versão já roteada as redes de resistores RN (470 ohms em série com as linhas do slot Mega Drive) e as peças DNP (TVS D3 a D14, R15),
mantendo o roteamento. Foco: proteger o Arduino e o shield; a tensão que o cartucho aguenta fica por conta do usuário (avisos no silk e nos docs).

Esquemático: os rótulos <rede>_S dos pinos do slot voltam a <rede>; as redes RN e as peças DNP saem, e o ERC aponta o que sobrou solto (fios, rótulos, símbolos de alimentação).
PCB: cada par de pads da rede (pino i e pino 17-i) vira uma ponte de cobre (trilha de 0,3 mm entre os dois furos, com via onde o pad servia de troca de face);
as peças DNP saem e as trilhas que ficam com ponta solta são podadas.

Uso (da raiz; python do sistema, com pcbnew):
  /usr/bin/python3 -I tools/troca/sem_rn.py <pasta hardware-vX.Y>
Depois: tools/troca/verifica.sh <placa> <versão>."""
import json, os, re, subprocess, sys, tempfile, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "sch"))
from sexp import parse, dump, val, find, S

HW = Path(sys.argv[1]).resolve()
SCH = HW / "dumper.kicad_sch"
PCB = HW / "dumper.kicad_pcb"
TMP = Path(tempfile.mkdtemp())


def prop(c, name):
    for p in find(c, "property"):
        if val(p[1]) == name:
            return p
    return None


def netlist():
    xml = TMP / "n.xml"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml), str(SCH)], check=True, capture_output=True)
    root = ET.parse(xml).getroot()
    return {n.get("name"): [(x.get("ref"), x.get("pin")) for x in n.iter("node")] for n in root.iter("net")}


def e_dnp(c):
    d = find(c, "dnp")
    return bool(d) and val(d[0][1]) == "yes"


text = SCH.read_text()
tree = parse(text)
nets = netlist()
REM, DNP = set(), set()
for c in tree[1:]:
    if isinstance(c, list) and c and val(c[0]) == "symbol" and find(c, "lib_id") and prop(c, "Reference") is not None:
        ref = val(prop(c, "Reference")[2])
        if re.fullmatch(r"R([3-9]|1[0-4])", ref):
            REM.add(ref)
assert REM, "nada a retirar nesta versão"
S_NETS = set()
S_LABELS = {n.lstrip("/") for n in S_NETS}
print("retirados:", ", ".join(sorted(REM)), "| DNP:", ", ".join(sorted(DNP)) or "-", "| redes _S:", len(S_NETS))

# ------------------------------------------------------------------ esquemático
body, nren = [], 0
for c in tree[1:]:
    if isinstance(c, list) and c and val(c[0]) == "symbol" and find(c, "lib_id"):
        pr = prop(c, "Reference")
        if pr is not None and val(pr[2]) in REM:
            at = find(c, "at")[0]; ax, ay, ar = float(at[1]), float(at[2]), float(at[3])
            dx, dy = (3.81, 0) if round(ar) % 180 == 90 else (0, 3.81)
            body.append(parse('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))' % (round(ax - dx, 2), round(ay - dy, 2), round(ax + dx, 2), round(ay + dy, 2), __import__("uuid").uuid4())))
            continue
    if isinstance(c, list) and c and val(c[0]) == "label" and val(c[1]) in S_LABELS:
        c[1] = S(val(c[1])[:-2]); nren += 1
    body.append(c)
print("rótulos _S renomeados:", nren)


def grava(body_):
    idx = next(i for i, c in enumerate(body_) if isinstance(c, list) and c and val(c[0]) == "sheet_instances")
    out = "(kicad_sch\n"
    for c in body_[:idx]:
        out += "\t" + dump(c, 1) + "\n"
    for c in body_[idx:]:
        out += "\t" + dump(c, 1) + "\n"
    SCH.write_text(out + ")\n")


grava(body)


def erc():
    js = TMP / "erc.json"
    subprocess.run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all", "-o", str(js), str(SCH)], capture_output=True)
    d = json.loads(js.read_text())
    return [v for s in d.get("sheets", []) for v in s.get("violations", [])]


for it in range(80):
    kill, kill_ref = set(), set()
    for v in erc():
        t = v["type"]
        if t in ("unconnected_wire_endpoint", "label_dangling", "no_connect_dangling"):
            kill.add(v["items"][0]["uuid"])
        elif t == "pin_not_connected":
            d = v["items"][0].get("description", "")
            m = re.match(r"Symbol (\S+) Pin", d)
            if m and m.group(1).startswith(("#PWR", "FLG")):
                kill_ref.add((m.group(1), round(v["items"][0]["pos"]["x"], 2), round(v["items"][0]["pos"]["y"], 2)))
    if not kill and not kill_ref:
        break
    tree = parse(SCH.read_text())
    keep = []
    for c in tree[1:]:
        if isinstance(c, list) and c and val(c[0]) in ("wire", "label", "junction", "no_connect"):
            u = find(c, "uuid")
            if u and val(u[0][1]) in kill:
                continue
        if isinstance(c, list) and c and val(c[0]) == "symbol" and find(c, "lib_id"):
            pr = prop(c, "Reference"); at = find(c, "at")[0]
            if pr is not None and (val(pr[2]), round(float(at[1]), 2), round(float(at[2]), 2)) in kill_ref:
                continue
        keep.append(c)
    grava(keep)
restam = [v for v in erc() if v["severity"] == "error"]
print("ERC depois da limpeza:", len(restam), "erro(s)")
for v in restam[:10]:
    print("  ", v["type"], v["description"][:100], [i.get("description", "")[:60] for i in v["items"]])

# ------------------------------------------------------------------ PCB
import math
import pcbnew
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(str(PCB))
TOL = mm(0.02)
perto = lambda p, q: abs(p.x - q.x) <= TOL and abs(p.y - q.y) <= TOL


def camadas_em(pos, nc):
    ls = set()
    for t in b.GetTracks():
        if t.GetNetCode() != nc:
            continue
        if t.GetClass() == "PCB_VIA":
            if perto(t.GetPosition(), pos):
                ls |= {pcbnew.F_Cu, pcbnew.B_Cu}
        elif perto(t.GetStart(), pos) or perto(t.GetEnd(), pos):
            ls.add(t.GetLayer())
    return ls


pontes = []       # (pos_base, camadas_base, pos_slot, camadas_slot, rede_slot, rede_mega)
SURV = {}
for r in sorted(REM):
    fp = b.FindFootprintByReference(r)
    pads = {p.GetNumber(): p for p in fp.Pads()}
    pa, pb_ = pads["1"], pads["2"]      # 1: lado do Mega (Net-(A1-PadD..)), 2: lado do slot (/D..)
    assert not pb_.GetNetname().startswith("Net-("), (r, pa.GetNetname(), pb_.GetNetname())
    pontes.append((pa.GetPosition(), camadas_em(pa.GetPosition(), pa.GetNetCode()), pb_.GetPosition(), camadas_em(pb_.GetPosition(), pb_.GetNetCode()), pb_.GetNetCode(), pa.GetNetCode()))
    SURV[pa.GetNetCode()] = pb_.GetNetname()

# pads DNP que servem de troca de face para uma rede que continua
VIAR, HOT = [], []
for r in sorted(DNP):
    fp = b.FindFootprintByReference(r)
    if fp is None:
        continue
    for pd in fp.Pads():
        if len(camadas_em(pd.GetPosition(), pd.GetNetCode())) >= 2 and pd.GetNetname() != "GND":
            VIAR.append((pd.GetPosition(), pd.GetNetCode()))
        HOT.append((pd.GetPosition().x, pd.GetPosition().y))
for r in sorted(REM):
    fp = b.FindFootprintByReference(r)
    if fp is not None:
        b.RemoveNative(fp)

base = {ns: nb for _, _, _, _, nb, ns in pontes}
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetCode() in base:
            p.SetNet(b.FindNet(SURV[p.GetNetCode()]))
for t in b.GetTracks():
    if t.GetNetCode() in base:
        t.SetNet(b.FindNet(SURV[t.GetNetCode()]))
print("pontes dos resistores:", len(pontes))

PROT = []
CLEAR = mm(0.2) + mm(0.08)


def seg_seg(a, b, c, d):
    """Distância entre dois segmentos (pontos como tuplas)."""
    def ps(p, u, v):
        dx, dy = v[0] - u[0], v[1] - u[1]
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((p[0] - u[0]) * dx + (p[1] - u[1]) * dy) / L2))
        return math.hypot(p[0] - (u[0] + t * dx), p[1] - (u[1] + t * dy))
    def cruza(p1, p2, p3, p4):
        def o(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0
    if cruza(a, b, c, d):
        return 0
    return min(ps(a, c, d), ps(b, c, d), ps(c, a, b), ps(d, a, b))


def livre(camada, pa, pb_, w, nc, extra_vias):
    A, B = (pa.x, pa.y), (pb_.x, pb_.y)
    for t in b.GetTracks():
        if t.GetNetCode() == nc:
            continue
        if t.GetClass() == "PCB_VIA":
            if seg_seg(A, B, (t.GetPosition().x, t.GetPosition().y), (t.GetPosition().x, t.GetPosition().y)) < w / 2 + mm(0.6) / 2 + CLEAR:
                return False
        elif t.GetLayer() == camada:
            if seg_seg(A, B, (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)) < w / 2 + t.GetWidth() / 2 + CLEAR:
                return False
    for ex, ey, enc in ENDS:
        if enc != nc and seg_seg(A, B, (ex, ey), (ex, ey)) < w / 2 + mm(0.3) + CLEAR:
            return False
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() == nc or not p.IsOnLayer(camada):
                continue
            r = max(p.GetSizeX(), p.GetSizeY()) / 2
            q = (p.GetPosition().x, p.GetPosition().y)
            if seg_seg(A, B, q, q) < w / 2 + r + CLEAR:
                return False
    return True


import heapq

G = mm(0.1)                      # passo da grade do roteador das pontes
BW = mm(0.3)                     # largura das trilhas das pontes
RT, RV = BW / 2 + CLEAR, mm(0.3) + CLEAR       # raio de folga de uma trilha e de uma via de 0,6 mm


def modo(g, bw, clear):
    """Muda o passo da grade, a largura da trilha e a folga do roteador (as pontes difíceis tentam de novo com grade fina e trilha de 0,2 mm)."""
    global G, BW, RT, RV, CLEAR
    G, BW, CLEAR = mm(g), mm(bw), mm(clear)
    RT, RV = BW / 2 + CLEAR, mm(0.3) + CLEAR


def obstaculos(nc, x0, y0, x1, y1):
    """Itens de outras redes perto da janela: (camada ou None para as duas, ponto ou segmento, raio de cobre)."""
    its = []
    for t in b.GetTracks():
        if t.GetNetCode() == nc:
            continue
        if t.GetClass() == "PCB_VIA":
            q = (t.GetPosition().x, t.GetPosition().y); its.append((None, q, q, t.GetWidth(pcbnew.F_Cu) / 2))
        else:
            a_, c_ = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            f_ = mm(2)      # a folga do cobre invade a janela mesmo com a trilha fora dela
            if max(a_[0], c_[0]) < x0 - f_ or min(a_[0], c_[0]) > x1 + f_ or max(a_[1], c_[1]) < y0 - f_ or min(a_[1], c_[1]) > y1 + f_:
                continue
            its.append((t.GetLayer(), a_, c_, t.GetWidth() / 2))
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() == nc:
                continue
            q = (p.GetPosition().x, p.GetPosition().y)
            r = max(p.GetSizeX(), p.GetSizeY()) / 2
            if q[0] + r < x0 - mm(2) or q[0] - r > x1 + mm(2) or q[1] + r < y0 - mm(2) or q[1] - r > y1 + mm(2):
                continue
            for l in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(l):
                    its.append((l, q, q, r))
    for ex, ey, enc in ENDS:
        if enc != nc and x0 - mm(2) <= ex <= x1 + mm(2) and y0 - mm(2) <= ey <= y1 + mm(2):
            its.append((None, (ex, ey), (ex, ey), mm(0.3)))
    return its


def roteia(pa, ca, pb_, cb, nc, margem=6):
    """A* na grade de 0,1 mm, duas camadas, com via; devolve a lista [(camada, x, y)] ou None."""
    m = mm(margem)
    x0, y0 = min(pa.x, pb_.x) - m, min(pa.y, pb_.y) - m
    x1, y1 = max(pa.x, pb_.x) + m, max(pa.y, pb_.y) + m
    W, H = int((x1 - x0) / G) + 1, int((y1 - y0) / G) + 1
    its = obstaculos(nc, x0, y0, x1, y1)
    LY = (pcbnew.F_Cu, pcbnew.B_Cu)
    bloq = {l: bytearray(W * H) for l in LY}
    blqv = bytearray(W * H)
    for ly, a_, c_, r in its:
        for l in (LY if ly is None else (ly,)):
            R = r + RT; Rv = r + RV
            xa, xb = int((min(a_[0], c_[0]) - Rv - x0) / G) - 1, int((max(a_[0], c_[0]) + Rv - x0) / G) + 1      # a janela cobre o raio da via, que é o maior
            ya, yb = int((min(a_[1], c_[1]) - Rv - y0) / G) - 1, int((max(a_[1], c_[1]) + Rv - y0) / G) + 1
            for gx in range(max(0, xa), min(W, xb + 1)):
                for gy in range(max(0, ya), min(H, yb + 1)):
                    q = (x0 + gx * G, y0 + gy * G)
                    d = seg_seg(q, q, a_, c_)
                    if d < R:
                        bloq[l][gy * W + gx] = 1
                    if d < Rv:
                        blqv[gy * W + gx] = 1
    eb = b.GetBoardEdgesBoundingBox()      # a borda da placa (contorno retangular): cobre a 0,5 mm dela, no mínimo
    for gx in range(W):
        for gy in range(H):
            qx, qy = x0 + gx * G, y0 + gy * G
            d = min(qx - eb.GetLeft(), eb.GetRight() - qx, qy - eb.GetTop(), eb.GetBottom() - qy)
            if d < mm(0.5) + BW / 2 + mm(0.1):
                for l in LY:
                    bloq[l][gy * W + gx] = 1
            if d < mm(0.5) + mm(0.3) + mm(0.1):
                blqv[gy * W + gx] = 1
    for t in b.GetTracks():          # vias da mesma rede: outra via a menos de 0,6 mm (furo contra furo) não pode
        if t.GetClass() == "PCB_VIA" and t.GetNetCode() == nc:
            q = (t.GetPosition().x, t.GetPosition().y)
            for gx in range(max(0, int((q[0] - mm(0.7) - x0) / G)), min(W, int((q[0] + mm(0.7) - x0) / G) + 2)):
                for gy in range(max(0, int((q[1] - mm(0.7) - y0) / G)), min(H, int((q[1] + mm(0.7) - y0) / G) + 2)):
                    if math.hypot(x0 + gx * G - q[0], y0 + gy * G - q[1]) < mm(0.6):
                        blqv[gy * W + gx] = 1
    cell = lambda p: (int(round((p.x - x0) / G)), int(round((p.y - y0) / G)))
    s, g = cell(pa), cell(pb_)
    ini = [(s[0], s[1], LY.index(l)) for l in (ca if ca else LY)]
    fim = {(g[0], g[1], LY.index(l)) for l in (cb if cb else LY)}
    for n in ini:                    # os pads de partida e chegada são da própria rede: a folga deles não vale
        for l in range(2):
            bloq[LY[l]][n[1] * W + n[0]] = 0
    dist, pai, pq = {}, {}, []
    for n in ini:
        dist[n] = 0; heapq.heappush(pq, (0, n))
    mv = [(1, 0, 10), (-1, 0, 10), (0, 1, 10), (0, -1, 10), (1, 1, 14), (1, -1, 14), (-1, 1, 14), (-1, -1, 14)]
    fin = None
    while pq:
        c, n = heapq.heappop(pq)
        if c > dist.get(n, 1e18):
            continue
        if n in fim:
            fin = n; break
        x, y, l = n
        for dx, dy, k in mv:
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and not bloq[LY[l]][ny * W + nx]:
                if dx and dy and (bloq[LY[l]][y * W + nx] or bloq[LY[l]][ny * W + x]):
                    continue
                m_ = (nx, ny, l); nc_ = c + k
                if nc_ < dist.get(m_, 1e18):
                    dist[m_] = nc_; pai[m_] = n; heapq.heappush(pq, (nc_, m_))
        if not blqv[y * W + x] or (x, y) == s or (x, y) == g:
            m_ = (x, y, 1 - l); nc_ = c + 60
            if nc_ < dist.get(m_, 1e18):
                dist[m_] = nc_; pai[m_] = n; heapq.heappush(pq, (nc_, m_))
    if fin is None:
        xs = [n[0] for n in dist]; ys = [n[1] for n in dist]
        print('   sem caminho: %d nós alcançados, x %.1f..%.1f y %.1f..%.1f; início %s camadas %s, fim %s camadas %s' % (len(dist), (x0 + min(xs) * G) / 1e6, (x0 + max(xs) * G) / 1e6, (y0 + min(ys) * G) / 1e6, (y0 + max(ys) * G) / 1e6, (pa.x / 1e6, pa.y / 1e6), [b.GetLayerName(l) for l in ca], (pb_.x / 1e6, pb_.y / 1e6), [b.GetLayerName(l) for l in cb]))
        return None
    cam = [fin]
    while cam[-1] in pai:
        cam.append(pai[cam[-1]])
    cam.reverse()
    return [(LY[l], x0 + x * G, y0 + y * G) for x, y, l in cam]


ENDS = [(p_.x, p_.y, nb_) for pa_, ca_, pb2, cb_, nb_, ns_ in pontes for p_ in (pa_, pb2)]
def ponte(pa, ca, pb_, cb, nb, ns):
    modo(0.1, 0.3, 0.28)
    netname = None
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() == nb:
                netname = p.GetNetname(); break
        if netname: break
    if os.environ.get('SEMRN_ONLY') and netname != os.environ['SEMRN_ONLY']:
        return None
    ni = b.FindNet(netname)
    ordem = list(ca & cb) + [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if l not in (ca & cb)]
    camada = next((l for l in ordem if livre(l, pa, pb_, mm(0.3), nb, None)), None)
    if camada is not None:          # ponte reta
        for pos, cam in ((pa, ca), (pb_, cb)):
            if camada not in cam or (cam - {camada}):
                v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetNet(ni)
                v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); PROT.append(v)
        j = pcbnew.PCB_TRACK(b); j.SetStart(pa); j.SetEnd(pb_); j.SetLayer(camada); j.SetWidth(mm(0.3)); j.SetNet(ni); b.Add(j); PROT.append(j)
        return None
    cam = roteia(pa, ca, pb_, cb, nb) or roteia(pa, ca, pb_, cb, nb, 16)
    if cam is None:                  # grade fina, trilha de 0,2 mm e folga justa
        modo(0.05, 0.2, 0.22)
        cam = roteia(pa, ca, pb_, cb, nb, 8)
        if cam is None:
            cam = roteia(pa, ca, pb_, cb, nb, 16)
        if cam is not None:
            print("   ponte", netname, "roteada com trilha de 0,2 mm")
        else:
            modo(0.1, 0.3, 0.28)
    if os.environ.get('SEMRN_ONLY'):
        print('caminho', netname, [(b.GetLayerName(l), round(x / 1e6, 2), round(y / 1e6, 2)) for l, x, y in (cam or [])])
    if cam is None:
        return netname
    # o caminho vira trilhas (um segmento por trecho reto) e vias nas trocas de camada; vias também nas pontas se o pad trocava de face
    def seg(l, p, q):
        j = pcbnew.PCB_TRACK(b); j.SetStart(pcbnew.VECTOR2I(int(p[0]), int(p[1]))); j.SetEnd(pcbnew.VECTOR2I(int(q[0]), int(q[1])))
        j.SetLayer(l); j.SetWidth(BW); j.SetNet(ni); b.Add(j); PROT.append(j)
    def via(p):
        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(p[0]), int(p[1]))); v.SetNet(ni)
        v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); PROT.append(v)
    ini_l, fim_l = cam[0][0], cam[-1][0]
    # pontos exatos nos pads (a grade pode errar por até meio passo)
    cam = [(cam[0][0], pa.x, pa.y)] + cam[1:-1] + [(cam[-1][0], pb_.x, pb_.y)]
    i = 0
    run = [cam[0]]
    for k in range(1, len(cam)):
        if cam[k][0] != cam[k - 1][0]:
            via((cam[k][1], cam[k][2]))
            run_pts = run
            # compacta trechos retos
            pts = [run_pts[0]]
            for q in run_pts[1:]:
                if len(pts) >= 2 and ((pts[-1][1] - pts[-2][1]) * (q[2] - pts[-1][2]) == (pts[-1][2] - pts[-2][2]) * (q[1] - pts[-1][1])):
                    pts[-1] = q
                else:
                    pts.append(q)
            for u, v_ in zip(pts, pts[1:]):
                seg(u[0], (u[1], u[2]), (v_[1], v_[2]))
            run = [cam[k]]
        else:
            run.append(cam[k])
    pts = [run[0]]
    for q in run[1:]:
        if len(pts) >= 2 and ((pts[-1][1] - pts[-2][1]) * (q[2] - pts[-1][2]) == (pts[-1][2] - pts[-2][2]) * (q[1] - pts[-1][1])):
            pts[-1] = q
        else:
            pts.append(q)
    for u, v_ in zip(pts, pts[1:]):
        seg(u[0], (u[1], u[2]), (v_[1], v_[2]))
    for pos, cam_l, l in ((pa, ca, ini_l), (pb_, cb, fim_l)):      # o pad servia às duas faces e a ponta do caminho está em uma só
        if cam_l and (cam_l - {l}):
            via((pos.x, pos.y))
    return None


N_PROT0 = len(PROT)
ordem_p = list(range(len(pontes)))
for rodada in range(3):
    falhas = []
    for i in ordem_p:
        r_ = ponte(*pontes[i])
        if r_:
            falhas.append((i, r_))
    if not falhas or rodada == 2:
        falhas = [n for _, n in falhas]
        break
    print("rodada", rodada + 1, ": sem caminho em", ", ".join(n for _, n in falhas), "; refaz com elas primeiro")
    for q in PROT[N_PROT0:]:
        b.RemoveNative(q)
    del PROT[N_PROT0:]
    ordem_p = [i for i, _ in falhas] + [i for i in ordem_p if i not in {j for j, _ in falhas}]
if falhas:
    print("pontes sem caminho (fechar à mão):", ", ".join(falhas))

com_pad = {p.GetNetCode() for f in b.GetFootprints() for p in f.Pads()}
for pos, nc in VIAR:
    if nc in com_pad:
        v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetNet(next(p for f in b.GetFootprints() for p in f.Pads() if p.GetNetCode() == nc).GetNet())
        v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); PROT.append(v)
apagadas = 0
for t in list(b.GetTracks()):
    if t.GetNetCode() not in com_pad:
        b.RemoveNative(t); apagadas += 1
print("trilhas/vias de redes extintas apagadas:", apagadas)

# poda das pontas soltas que as peças DNP deixaram (só a partir dos pads que saíram)
ANC = [p for t in PROT if t.GetClass() != "PCB_VIA" for p in (t.GetStart(), t.GetEnd())]


def dist_seg(p, a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


PROT_IDS = {q.m_Uuid.AsString() for q in PROT}


def poda_local(hot):
    pc = lambda p, q: abs(p[0] - q[0]) <= mm(0.01) and abs(p[1] - q[1]) <= mm(0.01)
    removidos = 0
    hot = list(hot)
    gnd = b.FindNet("GND").GetNetCode()
    for _ in range(2000):
        pads = [(p.GetPosition().x, p.GetPosition().y, p.GetNetCode()) for f in b.GetFootprints() for p in f.Pads()]
        trs = [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
        vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]

        def ligado(pt, nc, ly, ign):
            if any(pc(pt, (a.x, a.y)) for a in ANC):
                return True
            if any(pc(pt, (x, y)) and n == nc for x, y, n in pads):
                return True
            if any(pc(pt, (v.GetPosition().x, v.GetPosition().y)) and v.GetNetCode() == nc and v is not ign for v in vias):
                return True
            for t in trs:
                if t is ign or t.GetNetCode() != nc or t.GetLayer() != ly:
                    continue
                if dist_seg(pt, (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)) <= t.GetWidth() / 2 + mm(0.01):
                    return True
            return False
        mortos = []
        for t in trs:
            if t.m_Uuid.AsString() in PROT_IDS:
                continue
            for e in (t.GetStart(), t.GetEnd()):
                pt = (e.x, e.y)
                if any(pc(pt, h) for h in hot) and not ligado(pt, t.GetNetCode(), t.GetLayer(), t):
                    mortos.append(t); break
        for v in vias:
            pt = (v.GetPosition().x, v.GetPosition().y)
            if v.GetNetCode() == gnd or v.m_Uuid.AsString() in PROT_IDS or not any(pc(pt, h) for h in hot):
                continue
            cam = set()
            if any(pc(pt, (x, y)) and n == v.GetNetCode() for x, y, n in pads):
                cam = {pcbnew.F_Cu, pcbnew.B_Cu}
            for t in trs:
                if t.GetNetCode() == v.GetNetCode() and (pc(pt, (t.GetStart().x, t.GetStart().y)) or pc(pt, (t.GetEnd().x, t.GetEnd().y))):
                    cam.add(t.GetLayer())
            if len(cam) < 2:
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


print("trilhas e vias soltas podadas:", poda_local(HOT))

# silkscreen: o aviso dos TVS sai
for d in list(b.GetDrawings()):
    if d.GetClass() == "PCB_TEXT" and d.GetText().startswith("TVS 5V"):
        b.RemoveNative(d)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(str(PCB), b)


def poda_drc():
    total = 0
    for _ in range(30):
        js = TMP / "drc.json"
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "-o", str(js), str(PCB)], capture_output=True)
        d = json.loads(js.read_text())
        ids = {i["uuid"] for v in d.get("violations", []) if v["type"] in ("track_dangling", "via_dangling") for i in v["items"]}
        if not ids:
            break
        bb = pcbnew.LoadBoard(str(PCB))
        mortos = [t for t in bb.GetTracks() if t.m_Uuid.AsString() in ids]
        if not mortos:
            break
        for t in mortos:
            bb.RemoveNative(t)
        total += len(mortos)
        pcbnew.ZONE_FILLER(bb).Fill(bb.Zones()); pcbnew.SaveBoard(str(PCB), bb)
    return total


if "--sem-poda-drc" not in sys.argv and not falhas:
    print("trilhas e vias soltas (DRC) apagadas:", poda_drc())
elif falhas:
    print("poda final do DRC pulada: as pontes abertas deixaram pontas que ela apagaria")
print("ok", HW)
