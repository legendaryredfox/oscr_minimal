#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera boards/_lib/3dmodels/Fuseholder_Littelfuse_100_series_5x20mm.step: modelo 3D simples (só caixas, STEP AP214) do suporte de clipes para fusível 5x20 mm
(Littelfuse série 100), com as medidas do footprint `Fuse:Fuseholder_Littelfuse_100_series_5x20mm`: clipes em x = 0 a 4,6 mm e 15,9 a 20,5 mm (os pinos de furo
passante ficam nas pontas de cada clipe), largura de 5 mm, altura de 6,2 mm.
O modelo oficial desse footprint (Fuse.3dshapes/Fuseholder_Littelfuse_100_series_5x20mm.step) não vem no kicad-packages3d desta máquina (10.0.8). Este é aproximado:
chapas retas no lugar das dobras reais e pinos quadrados. Serve para ver tamanho e posição do suporte na placa, não para medida exata.
Sem dependências (escreve as faces planas direto). Uso: python3 tools/build_3d_fuseholder.py"""
from pathlib import Path

CLIP_X = (0.0, 15.9)           # x do primeiro pino de cada clipe
CL = 4.6                       # distância entre os dois pinos do clipe
W = 5.0                        # largura (y)
T = 0.5                        # espessura da chapa
H = 6.2                        # altura das paredes
Z0 = 0.3                       # folga do clipe à placa
COR = (0.78, 0.78, 0.80)       # metal

_n = [0]
linhas = []


def e(txt):
    _n[0] += 1
    linhas.append("#%d=%s;" % (_n[0], txt))
    return "#%d" % _n[0]


def num(v):
    return "%.6f" % v


def pt(p):
    return e("CARTESIAN_POINT('',(%s,%s,%s))" % tuple(num(c) for c in p))


def dire(d):
    return e("DIRECTION('',(%s,%s,%s))" % tuple(num(c) for c in d))


def caixa(x0, x1, y0, y1, z0, z1):
    """Sólido de 6 faces planas; devolve a referência do MANIFOLD_SOLID_BREP."""
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    pts = [pt(p) for p in V]
    vert = [e("VERTEX_POINT('',%s)" % p) for p in pts]
    # faces vistas de fora, no sentido anti-horário: (vértices, normal para fora, eixo x do plano)
    faces = [((0, 3, 2, 1), (0, 0, -1), (1, 0, 0)), ((4, 5, 6, 7), (0, 0, 1), (1, 0, 0)),
             ((0, 1, 5, 4), (0, -1, 0), (1, 0, 0)), ((2, 3, 7, 6), (0, 1, 0), (-1, 0, 0)),
             ((1, 2, 6, 5), (1, 0, 0), (0, 1, 0)), ((3, 0, 4, 7), (-1, 0, 0), (0, -1, 0))]
    arestas = {}

    def aresta(a, b):
        chave = (min(a, b), max(a, b))
        if chave not in arestas:
            p, q = V[chave[0]], V[chave[1]]
            d = [q[i] - p[i] for i in range(3)]
            L = sum(c * c for c in d) ** 0.5
            vec = e("VECTOR('',%s,%s)" % (dire([c / L for c in d]), num(L)))
            linha = e("LINE('',%s,%s)" % (pts[chave[0]], vec))
            arestas[chave] = e("EDGE_CURVE('',%s,%s,%s,.T.)" % (vert[chave[0]], vert[chave[1]], linha))
        return arestas[chave], (a, b) == chave
    fr = []
    for idx, n, ex in faces:
        orient = []
        for k in range(4):
            a, b = idx[k], idx[(k + 1) % 4]
            ed, sentido = aresta(a, b)
            orient.append(e("ORIENTED_EDGE('',*,*,%s,%s)" % (ed, ".T." if sentido else ".F.")))
        laco = e("EDGE_LOOP('',(%s))" % ",".join(orient))
        borda = e("FACE_OUTER_BOUND('',%s,.T.)" % laco)
        eixo = e("AXIS2_PLACEMENT_3D('',%s,%s,%s)" % (pts[idx[0]], dire(n), dire(ex)))
        plano = e("PLANE('',%s)" % eixo)
        fr.append(e("ADVANCED_FACE('',(%s),%s,.T.)" % (borda, plano)))
    casca = e("CLOSED_SHELL('',(%s))" % ",".join(fr))
    return e("MANIFOLD_SOLID_BREP('caixa',%s)" % casca)


solidos = []
for x0 in CLIP_X:
    x1 = x0 + CL
    xa, xb = x0 - 0.9, x1 + 0.9                                    # a chapa passa um pouco dos pinos
    solidos += [caixa(xa, xb, -W / 2, W / 2, Z0, Z0 + T),                                    # base
                caixa(xa + 0.9, xb - 0.9, -W / 2, -W / 2 + T, Z0, Z0 + H),                   # paredes
                caixa(xa + 0.9, xb - 0.9, W / 2 - T, W / 2, Z0, Z0 + H),
                caixa(xa + 0.9, xb - 0.9, -W / 2, -1.4, Z0 + H - T, Z0 + H),                 # bordas de cima (aproximadas)
                caixa(xa + 0.9, xb - 0.9, 1.4, W / 2, Z0 + H - T, Z0 + H)]
    for px in (x0, x1):                                                                      # pinos de furo passante
        solidos.append(caixa(px - 0.45, px + 0.45, -0.45, 0.45, -3.0, Z0 + T))

# contexto e produto
app = e("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
e("APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,%s)" % app)
pdc = e("PRODUCT_DEFINITION_CONTEXT('part definition',%s,'design')" % app)
prc = e("PRODUCT_CONTEXT('',%s,'mechanical')" % app)
prod = e("PRODUCT('Fuseholder_Littelfuse_100_series_5x20mm','Fuseholder_Littelfuse_100_series_5x20mm','',(%s))" % prc)
pdf = e("PRODUCT_DEFINITION_FORMATION('','',%s)" % prod)
pd = e("PRODUCT_DEFINITION('design','',%s,%s)" % (pdf, pdc))
pds = e("PRODUCT_DEFINITION_SHAPE('','',%s)" % pd)
u_len = e("(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.))")
u_ang = e("(NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.))")
u_sol = e("(NAMED_UNIT(*) SOLID_ANGLE_UNIT() SI_UNIT($,.STERADIAN.))")
tol = e("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-05),%s,'distance_accuracy_value','confusion accuracy')" % u_len)
ctx = e("(GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((%s)) GLOBAL_UNIT_ASSIGNED_CONTEXT((%s,%s,%s)) REPRESENTATION_CONTEXT('Context3D','3D Context with UNIT and UNCERTAINTY'))" % (tol, u_len, u_ang, u_sol))
origem = e("AXIS2_PLACEMENT_3D('',%s,%s,%s)" % (pt((0, 0, 0)), dire((0, 0, 1)), dire((1, 0, 0))))
rep = e("ADVANCED_BREP_SHAPE_REPRESENTATION('',(%s,%s),%s)" % (origem, ",".join(solidos), ctx))
e("SHAPE_DEFINITION_REPRESENTATION(%s,%s)" % (pds, rep))
# cor
cor = e("COLOUR_RGB('',%s,%s,%s)" % tuple(num(c) for c in COR))
fas = e("FILL_AREA_STYLE_COLOUR('',%s)" % cor)
fa = e("FILL_AREA_STYLE('',(%s))" % fas)
sfs = e("SURFACE_STYLE_FILL_AREA(%s)" % fa)
ssd = e("SURFACE_SIDE_STYLE('',(%s))" % sfs)
ssu = e("SURFACE_STYLE_USAGE(.BOTH.,%s)" % ssd)
psa = e("PRESENTATION_STYLE_ASSIGNMENT((%s))" % ssu)
est = [e("STYLED_ITEM('color',(%s),%s)" % (psa, s)) for s in solidos]
e("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',(%s),%s)" % (",".join(est), ctx))

cab = ("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Suporte de clipes para fusivel 5x20 mm (aproximado)'),'2;1');\n"
       "FILE_NAME('Fuseholder_Littelfuse_100_series_5x20mm.step','2026-11-09T00:00:00',(''),(''),'tools/build_3d_fuseholder.py','','');\n"
       "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\nDATA;\n")
saida = Path(__file__).resolve().parents[1] / "boards/_lib/3dmodels/Fuseholder_Littelfuse_100_series_5x20mm.step"
saida.write_text(cab + "\n".join(linhas) + "\nENDSEC;\nEND-ISO-10303-21;\n")
print("ok", saida, len(solidos), "caixas")
