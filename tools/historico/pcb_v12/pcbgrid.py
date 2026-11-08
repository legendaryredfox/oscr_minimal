# SPDX-License-Identifier: GPL-3.0-or-later
# Mapa de obstaculos em grade e roteador A* de 2 camadas para a placa 16_bits (pcbnew do venv do KiCad MCP).
import pcbnew, numpy as np, heapq, math
from scipy import ndimage

RES = 0.1                      # mm por celula
MM = 1e6
CLR = 0.2                      # folga minima da placa (JLCPCB 2 camadas)
TRK_W = 0.3
VIA_D, VIA_DRILL = 0.6, 0.3
TRK_MARGIN = 0.12

class Grid:
    def __init__(self, path):
        self.b = pcbnew.LoadBoard(path) if isinstance(path, str) else path
        bb = self.b.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = bb.GetLeft()/MM, bb.GetTop()/MM
        self.x1, self.y1 = bb.GetRight()/MM, bb.GetBottom()/MM
        self.nx = int((self.x1-self.x0)/RES)+1
        self.ny = int((self.y1-self.y0)/RES)+1
        self.layers = [pcbnew.F_Cu, pcbnew.B_Cu]
        xs = self.x0 + np.arange(self.nx)*RES
        ys = self.y0 + np.arange(self.ny)*RES
        self.X, self.Y = np.meshgrid(xs, ys)           # [iy, ix]
    def cell(self, x, y):
        return int(round((x-self.x0)/RES)), int(round((y-self.y0)/RES))
    def xy(self, ix, iy):
        return self.x0+ix*RES, self.y0+iy*RES

    def _seg(self, m, ax, ay, bx, by, hw):
        x0 = min(ax, bx)-hw; x1 = max(ax, bx)+hw; y0 = min(ay, by)-hw; y1 = max(ay, by)+hw
        i0, j0 = self.cell(x0, y0); i1, j1 = self.cell(x1, y1)
        i0 = max(i0-1, 0); j0 = max(j0-1, 0); i1 = min(i1+1, self.nx-1); j1 = min(j1+1, self.ny-1)
        X = self.X[j0:j1+1, i0:i1+1]; Y = self.Y[j0:j1+1, i0:i1+1]
        dx, dy = bx-ax, by-ay
        L2 = dx*dx+dy*dy
        t = np.zeros_like(X) if L2 == 0 else np.clip(((X-ax)*dx+(Y-ay)*dy)/L2, 0, 1)
        d = np.hypot(X-(ax+t*dx), Y-(ay+t*dy))
        m[j0:j1+1, i0:i1+1] |= d <= hw

    def _box(self, m, x0, y0, x1, y1):
        i0, j0 = self.cell(x0, y0); i1, j1 = self.cell(x1, y1)
        m[max(j0,0):j1+2, max(i0,0):i1+2] = True

    def foreign(self, net, layer):
        """Mascara do cobre que NAO e da rede `net` (nome) na camada."""
        m = np.zeros((self.ny, self.nx), bool)
        for t in self.b.GetTracks():
            if t.GetNetname() == net: continue
            if t.Type() == pcbnew.PCB_VIA_T:
                p = t.GetPosition(); r = t.GetWidth(pcbnew.F_Cu)/2/MM
                self._seg(m, p.x/MM, p.y/MM, p.x/MM, p.y/MM, r)
            elif t.GetLayer() == layer:
                a, b2 = t.GetStart(), t.GetEnd()
                self._seg(m, a.x/MM, a.y/MM, b2.x/MM, b2.y/MM, t.GetWidth()/2/MM)
        for f in self.b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() == net and net != "": continue
                if not p.IsOnLayer(layer) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH: continue
                bb = p.GetBoundingBox()
                self._box(m, bb.GetLeft()/MM, bb.GetTop()/MM, bb.GetRight()/MM, bb.GetBottom()/MM)
        return m

    def free_maps(self, net, edge=1.0, extra=None):
        """(livre para trilha F, B, livre para via, mapas de distancia)."""
        fm = [self.foreign(net, l) for l in self.layers]
        dist = [ndimage.distance_transform_edt(~m)*RES for m in fm]
        both = ndimage.distance_transform_edt(~(fm[0] | fm[1]))*RES
        # borda da placa
        border = np.ones((self.ny, self.nx), bool)
        e = int(edge/RES)
        border[e:-e, e:-e] = False
        trk = [(d >= TRK_W/2+CLR+TRK_MARGIN) & ~border for d in dist]
        via = (both >= VIA_D/2+CLR+TRK_MARGIN) & ~border
        return trk, via, dist, both

def route(g, net, start, goal, trk, via, via_cost=8.0, extra_block=None, allow_via=True):
    """A* 2 camadas. start/goal = (x, y, camada_idx) em mm; devolve lista de (ix, iy, l)."""
    sx, sy = g.cell(start[0], start[1]); gx, gy = g.cell(goal[0], goal[1])
    sl, gl = start[2], goal[2]
    # as celulas de partida/chegada ficam livres (estao dentro das proprias pads)
    free = [t.copy() for t in trk]
    for (cx, cy, l) in ((sx, sy, None), (gx, gy, None)):
        for L in range(2):
            free[L][cy-6:cy+7, cx-6:cx+7] |= False
    if extra_block is not None:
        for L in range(2): free[L] &= ~extra_block[L]
    nbr = [(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.4142),(1,-1,1.4142),(-1,1,1.4142),(-1,-1,1.4142)]
    def h(x, y): return RES*max(abs(x-gx), abs(y-gy)) + 0.4142*RES*min(abs(x-gx), abs(y-gy))
    openq = [(h(sx, sy), 0.0, sx, sy, sl, None)]
    best = {}
    parent = {}
    seen_goal = None
    import itertools
    cnt = itertools.count()
    heap = [(h(sx, sy), next(cnt), 0.0, sx, sy, sl)]
    best[(sx, sy, sl)] = 0.0
    parent[(sx, sy, sl)] = None
    while heap:
        f, _, gc, x, y, l = heapq.heappop(heap)
        if gc > best.get((x, y, l), 1e18): continue
        if (x, y) == (gx, gy) and l == gl:
            seen_goal = (x, y, l); break
        for dx, dy, c in nbr:
            nx_, ny_ = x+dx, y+dy
            if not (0 <= nx_ < g.nx and 0 <= ny_ < g.ny): continue
            if not free[l][ny_, nx_] and (nx_, ny_) != (gx, gy) : continue
            if dx and dy and not (free[l][y, nx_] and free[l][ny_, x]): continue
            ng = gc + c*RES
            k = (nx_, ny_, l)
            if ng < best.get(k, 1e18):
                best[k] = ng; parent[k] = (x, y, l)
                heapq.heappush(heap, (ng+h(nx_, ny_), next(cnt), ng, nx_, ny_, l))
        if allow_via and via[y, x]:
            l2 = 1-l
            if free[l2][y, x]:
                ng = gc + via_cost
                k = (x, y, l2)
                if ng < best.get(k, 1e18):
                    best[k] = ng; parent[k] = (x, y, l)
                    heapq.heappush(heap, (ng+h(x, y), next(cnt), ng, x, y, l2))
    if seen_goal is None: return None
    path = []; k = seen_goal
    while k is not None:
        path.append(k); k = parent[k]
    return path[::-1]

def simplify(path):
    """Junta celulas colineares em segmentos; devolve [(x0,y0,x1,y1,l)] em celulas e vias [(x,y)]."""
    segs = []; vias = []
    i = 0
    while i < len(path)-1:
        x, y, l = path[i]; x2, y2, l2 = path[i+1]
        if l != l2:
            vias.append((x, y)); i += 1; continue
        d = (x2-x, y2-y)
        j = i+1
        while j < len(path)-1 and path[j+1][2] == l and (path[j+1][0]-path[j][0], path[j+1][1]-path[j][1]) == d:
            j += 1
        segs.append((x, y, path[j][0], path[j][1], l)); i = j
    return segs, vias

def courtyard_mask(g, margin=0.3, skip=()):
    """Mascara dos patios (F.CrtYd) de todos os footprints: onde o corpo da peca ocupa espaco."""
    m = np.zeros((g.ny, g.nx), bool)
    for f in g.b.GetFootprints():
        if f.GetReference() in skip: continue
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() == 0:
            bb = f.GetBoundingBox(False)
        else:
            bb = cy.BBox()
        g._box(m, bb.GetLeft()/MM-margin, bb.GetTop()/MM-margin, bb.GetRight()/MM+margin, bb.GetBottom()/MM+margin)
    return m

def net_mask(g, net):
    """Cobre da rede `net` por camada (para usar como destino do roteador)."""
    ms = [np.zeros((g.ny, g.nx), bool) for _ in g.layers]
    for t in g.b.GetTracks():
        if t.GetNetname() != net: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition(); r = t.GetWidth(pcbnew.F_Cu)/2/MM
            for m in ms: g._seg(m, p.x/MM, p.y/MM, p.x/MM, p.y/MM, r)
        else:
            L = g.layers.index(t.GetLayer()) if t.GetLayer() in g.layers else None
            if L is None: continue
            a, b = t.GetStart(), t.GetEnd()
            g._seg(ms[L], a.x/MM, a.y/MM, b.x/MM, b.y/MM, t.GetWidth()/2/MM)
    for f in g.b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net: continue
            bb = p.GetBoundingBox()
            for L, lay in enumerate(g.layers):
                if p.IsOnLayer(lay): g._box(ms[L], bb.GetLeft()/MM, bb.GetTop()/MM, bb.GetRight()/MM, bb.GetBottom()/MM)
    return ms

def route_mask(g, start, goal_mask, trk, via, via_cost=8.0, allow_via=True, maxexp=3_000_000):
    """Dijkstra/A* 2 camadas ate qualquer celula de goal_mask[l]. start=(x,y,l). Devolve caminho de (ix,iy,l)."""
    sx, sy = g.cell(start[0], start[1]); sl = start[2]
    free = [t.copy() for t in trk]
    for L in range(2):
        free[L][sy-8:sy+9, sx-8:sx+9] = trk[L][sy-8:sy+9, sx-8:sx+9] | free[L][sy-8:sy+9, sx-8:sx+9]
    import itertools
    cnt = itertools.count()
    nbr = [(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.4142),(1,-1,1.4142),(-1,1,1.4142),(-1,-1,1.4142)]
    heap = [(0.0, next(cnt), sx, sy, sl)]
    best = {(sx, sy, sl): 0.0}; parent = {(sx, sy, sl): None}
    n = 0
    while heap:
        gc, _, x, y, l = heapq.heappop(heap)
        if gc > best.get((x, y, l), 1e18): continue
        n += 1
        if n > maxexp: return None
        if goal_mask[l][y, x] and (x, y, l) != (sx, sy, sl):
            path = []; k = (x, y, l)
            while k is not None: path.append(k); k = parent[k]
            return path[::-1]
        for dx, dy, c in nbr:
            nx_, ny_ = x+dx, y+dy
            if not (0 <= nx_ < g.nx and 0 <= ny_ < g.ny): continue
            if not (free[l][ny_, nx_] or goal_mask[l][ny_, nx_]): continue
            if dx and dy and not ((free[l][y, nx_] or goal_mask[l][y, nx_]) and (free[l][ny_, x] or goal_mask[l][ny_, x])): continue
            ng = gc + c*RES
            k = (nx_, ny_, l)
            if ng < best.get(k, 1e18):
                best[k] = ng; parent[k] = (x, y, l)
                heapq.heappush(heap, (ng, next(cnt), nx_, ny_, l))
        if allow_via and via[y, x]:
            l2 = 1-l
            if free[l2][y, x] or goal_mask[l2][y, x]:
                ng = gc + via_cost; k = (x, y, l2)
                if ng < best.get(k, 1e18):
                    best[k] = ng; parent[k] = (x, y, l)
                    heapq.heappush(heap, (ng, next(cnt), x, y, l2))
    return None

def dijkstra_from(g, sources, trk, via, via_cost=8.0, maxd=40.0):
    """Distancia de roteamento de cada celula livre ate o cobre `sources` (lista por camada). Devolve (dist[2], parent dict)."""
    import itertools
    cnt = itertools.count()
    INF = 1e18
    dist = [np.full((g.ny, g.nx), INF) for _ in range(2)]
    parent = {}
    heap = []
    for L in range(2):
        ys, xs = np.nonzero(sources[L])
        for y, x in zip(ys, xs):
            dist[L][y, x] = 0.0; parent[(x, y, L)] = None
            heap.append((0.0, next(cnt), x, y, L))
    heapq.heapify(heap)
    nbr = [(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.4142),(1,-1,1.4142),(-1,1,1.4142),(-1,-1,1.4142)]
    while heap:
        gc, _, x, y, l = heapq.heappop(heap)
        if gc > dist[l][y, x]: continue
        if gc > maxd: break
        for dx, dy, c in nbr:
            nx_, ny_ = x+dx, y+dy
            if not (0 <= nx_ < g.nx and 0 <= ny_ < g.ny): continue
            if not trk[l][ny_, nx_]: continue
            if dx and dy and not (trk[l][y, nx_] and trk[l][ny_, x]): continue
            ng = gc + c*RES
            if ng < dist[l][ny_, nx_]:
                dist[l][ny_, nx_] = ng; parent[(nx_, ny_, l)] = (x, y, l)
                heapq.heappush(heap, (ng, next(cnt), nx_, ny_, l))
        if via[y, x] and trk[1-l][y, x]:
            ng = gc + via_cost; l2 = 1-l
            if ng < dist[l2][y, x]:
                dist[l2][y, x] = ng; parent[(x, y, l2)] = (x, y, l)
                heapq.heappush(heap, (ng, next(cnt), x, y, l2))
    return dist, parent

def path_from(parent, cell):
    out = []; k = cell
    while k is not None: out.append(k); k = parent[k]
    return out
