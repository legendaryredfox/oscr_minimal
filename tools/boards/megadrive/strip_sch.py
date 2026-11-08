#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tira do esquemático da 16_bits o que a placa só-Mega-Drive não usa.
Remove os símbolos (REMOVE), os rótulos e no_connects que estavam nos pinos deles
e as definições de símbolo sem uso. Uso: strip_sch.py entrada.kicad_sch saida.kicad_sch [REF,REF,...]  (padrão: o que a placa megadrive não usa)"""
import math, re, sys

REMOVE = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else {"SNES1", "U1", "U2", "R2", "C2", "C4"}

def parse(s):
    i, n = 0, len(s)
    def node():
        nonlocal i
        while s[i] in " \t\r\n": i += 1
        if s[i] == "(":
            i += 1; items = []
            while True:
                while s[i] in " \t\r\n": i += 1
                if s[i] == ")": i += 1; return items
                items.append(node())
        if s[i] == '"':
            j = i + 1
            while s[j] != '"':
                j += 2 if s[j] == "\\" else 1
            t = s[i:j + 1]; i = j + 1; return ("S", t)
        j = i
        while s[j] not in " \t\r\n()": j += 1
        t = s[i:j]; i = j; return t
    return node()

def dump(x, ind=0):
    if isinstance(x, tuple): return x[1]
    if isinstance(x, str): return x
    if not x: return "()"
    head = x[0]
    if all(not isinstance(c, list) for c in x):
        return "(" + " ".join(dump(c) for c in x) + ")"
    out = "(" + dump(head)
    for c in x[1:]:
        if isinstance(c, list):
            out += "\n" + "\t" * (ind + 1) + dump(c, ind + 1)
        else:
            out += " " + dump(c)
    return out + "\n" + "\t" * ind + ")"

def val(x): return x[1].strip('"') if isinstance(x, tuple) else x
def find(x, name): return [c for c in x if isinstance(c, list) and c and val(c[0]) == name]

tree = parse(open(sys.argv[1]).read())
libs = find(tree, "lib_symbols")[0]
libdef = {val(c[1]): c for c in libs[1:] if isinstance(c, list)}
removed_pts, keep, used = [], [], set()
for c in tree:
    if isinstance(c, list) and c and val(c[0]) == "symbol":
        ref = [val(p[2]) for p in find(c, "property") if val(p[1]) == "Reference"][0]
        lib = val(find(c, "lib_id")[0][1])
        if ref in REMOVE:
            at = find(c, "at")[0]
            X, Y, R = float(at[1]), float(at[2]), float(at[3])
            sub = libdef[lib]
            pins = []
            def walk(n):
                for k in n:
                    if isinstance(k, list) and k:
                        if val(k[0]) == "pin": pins.append(k)
                        else: walk(k)
            walk(sub)
            for p in pins:
                a = find(p, "at")[0]
                px, py = float(a[1]), float(a[2])
                r = math.radians(R)
                x2 = px * math.cos(r) - py * math.sin(r)
                y2 = px * math.sin(r) + py * math.cos(r)
                removed_pts.append((X + x2, Y - y2))
            continue
        used.add(lib)
    keep.append(c)

def near(at):
    x, y = float(at[1]), float(at[2])
    return any(abs(x - a) < 0.02 and abs(y - b) < 0.02 for a, b in removed_pts)

# pontos ocupados por pinos de símbolos que ficam (não apagar rótulo ali)
final, dropped = [], 0
for c in keep:
    if isinstance(c, list) and c and val(c[0]) in ("label", "no_connect"):
        if near(find(c, "at")[0]): dropped += 1; continue
    final.append(c)
# rótulo que ficou sozinho (pino do Mega sem par) vira no_connect
import collections, uuid
cnt = collections.Counter(val(c[1]) for c in final if isinstance(c, list) and c and val(c[0]) == "label")
alone = 0
for k, c in enumerate(final):
    if isinstance(c, list) and c and val(c[0]) == "label" and cnt[val(c[1])] == 1:
        a = find(c, "at")[0]
        final[k] = [("S", "no_connect") if False else "no_connect", ["at", a[1], a[2]], ["uuid", ("S", '"%s"' % uuid.uuid4())]]
        alone += 1
print("rotulos sozinhos viraram no_connect", alone, file=sys.stderr)
for c in list(libs):
    if isinstance(c, list) and c and val(c[0]) == "symbol" and val(c[1]) not in used:
        libs.remove(c)
open(sys.argv[2], "w").write(dump(final) + "\n")
print("pinos removidos", len(removed_pts), "rotulos/nc apagados", dropped, file=sys.stderr)
