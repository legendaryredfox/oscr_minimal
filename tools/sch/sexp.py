# SPDX-License-Identifier: GPL-3.0-or-later
"""Leitor e escritor mínimo de S-expressions do KiCad (mesmo formato de tools/megadrive/strip_sch.py)."""
def parse(s):
    i = 0
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
            while s[j] != '"': j += 2 if s[j] == "\\" else 1
            t = s[i:j + 1]; i = j + 1; return ("S", t)
        j = i
        while s[j] not in " \t\r\n()": j += 1
        t = s[i:j]; i = j; return t
    return node()

def dump(x, ind=0):
    if isinstance(x, tuple): return x[1]
    if isinstance(x, str): return x
    if not x: return "()"
    if all(not isinstance(c, list) for c in x):
        return "(" + " ".join(dump(c) for c in x) + ")"
    out = "(" + dump(x[0])
    for c in x[1:]:
        if isinstance(c, list): out += "\n" + "\t" * (ind + 1) + dump(c, ind + 1)
        else: out += " " + dump(c)
    return out + "\n" + "\t" * ind + ")"

def val(x): return x[1].strip('"') if isinstance(x, tuple) else x
def find(x, name): return [c for c in x if isinstance(c, list) and c and val(c[0]) == name]
def S(t): return ("S", '"%s"' % t)
