# SPDX-License-Identifier: GPL-3.0-or-later
import re, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from pcbgrid import *

SHEET = "7a60289e-82cc-4290-bd86-3bc08aff2373"

def sch_uuid(sch_text, ref):
    """uuid do simbolo `ref` no esquematico (para ligar o footprint ao simbolo)."""
    for m in re.finditer(r'\t\(symbol\n\t\t\(lib_id "[^"]*"\)(?:.*\n)*?\t\t\(uuid "([0-9a-f-]+)"\)\n(?:.*\n)*?\t\t\(property "Reference" "([^"]+)"', sch_text):
        if m.group(2) == ref: return m.group(1)
    raise KeyError(ref)

def add_fp(b, libdir, lib, name, ref, value, x, y, rot, pad_nets, uuid_sch, like=None):
    fp = pcbnew.FootprintLoad(libdir, name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref); fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I(int(x*MM), int(y*MM)))
    if rot: fp.SetOrientationDegrees(rot)
    b.Add(fp)
    for p in fp.Pads():
        n = pad_nets.get(p.GetNumber())
        if n: p.SetNet(b.FindNet(n))
    fp.SetPath(pcbnew.KIID_PATH("/%s/%s" % (SHEET, uuid_sch)))
    if like is not None:
        src = b.FindFootprintByReference(like)
        for a, bb in ((src.Reference(), fp.Reference()), (src.Value(), fp.Value())):
            bb.SetTextSize(a.GetTextSize()); bb.SetTextThickness(a.GetTextThickness()); bb.SetLayer(a.GetLayer()); bb.SetVisible(a.IsVisible())
            off = a.GetPosition() - src.GetPosition()
            bb.SetPosition(fp.GetPosition() + off)
    return fp

def add_path(b, g, net, path, width=TRK_W, p_start=None, p_end=None, snap_net_pads=True):
    """p_start/p_end = (x, y) em mm do centro das pads: a primeira e a ultima trilha terminam nelas."""
    segs, vias = simplify(path)
    netinfo = b.FindNet(net)
    def _tr(ax, ay, bx, by, l):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(int(round(ax*MM)), int(round(ay*MM)))); t.SetEnd(pcbnew.VECTOR2I(int(round(bx*MM)), int(round(by*MM))))
        t.SetWidth(int(width*MM)); t.SetLayer(g.layers[l]); t.SetNet(netinfo); b.Add(t)
    if p_start is not None:
        fx, fy = g.xy(path[0][0], path[0][1]); _tr(p_start[0], p_start[1], fx, fy, path[0][2])
    if p_end is None and snap_net_pads:
        lx, ly = g.xy(path[-1][0], path[-1][1])
        for f in b.GetFootprints():
            for pd in f.Pads():
                if pd.GetNetname() == net:
                    pc = pd.GetPosition()
                    if math.hypot(pc.x/MM-lx, pc.y/MM-ly) <= 1.6: p_end = (pc.x/MM, pc.y/MM)
    if p_end is not None:
        lx, ly = g.xy(path[-1][0], path[-1][1]); _tr(lx, ly, p_end[0], p_end[1], path[-1][2])
    for (x0, y0, x1, y1, l) in segs:
        t = pcbnew.PCB_TRACK(b)
        ax, ay = g.xy(x0, y0); bx, by = g.xy(x1, y1)
        t.SetStart(pcbnew.VECTOR2I(int(round(ax*MM)), int(round(ay*MM)))); t.SetEnd(pcbnew.VECTOR2I(int(round(bx*MM)), int(round(by*MM))))
        t.SetWidth(int(width*MM)); t.SetLayer(g.layers[l]); t.SetNet(netinfo)
        b.Add(t)
    for (x, y) in vias:
        v = pcbnew.PCB_VIA(b)
        ax, ay = g.xy(x, y)
        v.SetPosition(pcbnew.VECTOR2I(int(round(ax*MM)), int(round(ay*MM))))
        v.SetWidth(int(VIA_D*MM)); v.SetDrill(int(VIA_DRILL*MM)); v.SetNet(netinfo)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        b.Add(v)
    return len(segs), len(vias)
