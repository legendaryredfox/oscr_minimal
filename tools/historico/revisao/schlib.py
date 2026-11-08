# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilitarios de texto para o esquematico do dumper (sem wires: cada pino leva um label na ponta)."""
import re, uuid


def block_at(s, start):
    """(texto, fim) do bloco S-expression que abre em s[start] == '('."""
    d = 0
    j = start
    while True:
        c = s[j]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                return s[start:j + 1], j + 1
        j += 1


def lib_symbols(s):
    """nome -> bloco de texto de cada simbolo em (lib_symbols ...)."""
    i = s.index('\t(lib_symbols')
    blk, end = block_at(s, i + 1)
    out = {}
    for m in re.finditer(r'\n\t\t\(symbol "([^"]+)"', blk):
        t, _ = block_at(blk, m.start() + 3)
        out[m.group(1)] = t
    return out


def pins_of(libtxt):
    """numero do pino -> (x, y) na ponta (coordenadas do simbolo, y para cima)."""
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-0-9.]+) ([-0-9.]+) (\d+)\)\s*\(length ([0-9.]+)\)(?:.|\n)*?\(number "([^"]*)"', libtxt):
        pins[m.group(5)] = (float(m.group(1)), float(m.group(2)))
    return pins


def placed(s):
    """lista de dicts com lib_id, x, y, rot, ref, uuid, bloco."""
    out = []
    for m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "([^"]*)"\)\n\t\t\(at ([-0-9.]+) ([-0-9.]+) (\d+)\)', s):
        blk, _ = block_at(s, m.start() + 1)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        u = re.search(r'\n\t\t\(uuid "([0-9a-f-]+)"\)', blk).group(1)
        out.append(dict(lib=m.group(1), x=float(m.group(2)), y=float(m.group(3)), rot=int(m.group(4)), ref=ref, uuid=u, blk=blk, start=m.start() + 1))
    return out


def pin_xy(sym, pin, libs):
    px, py = pins_of(libs[sym['lib']])[pin]
    assert sym['rot'] == 0, "so simbolos sem rotacao"
    return (round(sym['x'] + px, 3), round(sym['y'] - py, 3))


def labels(s):
    """lista de (texto, x, y, ang, inicio, fim)."""
    out = []
    for m in re.finditer(r'\n\t\(label "([^"]*)"\n\t\t\(at ([-0-9.]+) ([-0-9.]+) (\d+)\)', s):
        blk, end = block_at(s, m.start() + 1)
        out.append((m.group(1), float(m.group(2)), float(m.group(3)), int(m.group(4)), m.start() + 1, end))
    return out


def label_text(name, x, y, ang, just='left bottom'):
    return ('\t(label "%s"\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'
            % (name, ('%.3f' % x).rstrip('0').rstrip('.'), ('%.3f' % y).rstrip('0').rstrip('.'), ang, just, uuid.uuid4()))
