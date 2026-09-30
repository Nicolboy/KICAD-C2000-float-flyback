#!/usr/bin/env python3
"""Briques communes au generateur de ce projet KiCad.

Repris du meme motif que shield-c2000/kicad_gen.py (methode documentee dans
shield-c2000/doc/methode-kicad-claude.md) : primitives s-expression, garde-fou
de verrou KiCad, gabarits .kicad_pcb / .kicad_pro.
"""

import re
import sys
import uuid
from pathlib import Path

KILIB = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")
KIFP = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")

# Contour de carte, contraintes fab 2 couches (meme ordre de grandeur que le
# reste du workspace).
BOARD_W = 70.0
BOARD_H = 55.0
BOARD_X = 100.0
BOARD_Y = 80.0

TRACK_MIN = 0.25
VIA_DIA = 0.6
VIA_DRILL = 0.3
CLEARANCE = 0.2

GRID = 1.27


def uid():
    return str(uuid.uuid4())


def snap(v):
    return round(round(v / GRID) * GRID, 2)


NUM = r'-?[\d.]+(?:[eE][-+]?\d+)?'

PIN_RE = re.compile(
    r'\(pin\s+\S+\s+\S+\s+\(at\s+(' + NUM + r')\s+(' + NUM + r')\s+(\d+)\)'
    r'.*?\(name\s+"([^"]*)"'
    r'.*?\(number\s+"([^"]+)"',
    re.S,
)


def parse_pins(block):
    """[(numero, nom, x, y, angle)] en coordonnees symbole."""
    out = []
    for m in PIN_RE.finditer(block):
        x, y, ang, name, num = m.groups()
        out.append((num, name, round(float(x), 3), round(float(y), 3), int(ang)))
    return out


def sexp_block(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("bloc non termine")


def extract_from(path, name, new_nick=None):
    """Extrait un bloc symbole top-level d'une librairie, reprefixe."""
    text = Path(path).read_text(encoding="utf-8")
    pat = re.compile(r'^\t\(symbol "%s"' % re.escape(name), re.M)
    m = pat.search(text)
    if not m:
        raise SystemExit("symbole introuvable : %s dans %s" % (name, path))
    block = sexp_block(text, m.start())
    if new_nick:
        block = block.replace('(symbol "%s"' % name,
                               '(symbol "%s:%s"' % (new_nick, name), 1)
    return block


def refuser_si_kicad_ouvert(project_dir):
    lock = Path(project_dir) / ("~%s.kicad_pro.lck" % Path(project_dir).name)
    for p in Path(project_dir).glob("~*.lck"):
        sys.exit("KiCad a l'air ouvert sur ce projet (%s) — le fermer avant "
                  "de regenerer le schema." % p.name)


def gen_pcb():
    x0, y0 = BOARD_X, BOARD_Y
    x1, y1 = BOARD_X + BOARD_W, BOARD_Y + BOARD_H
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    edges = []
    for i in range(4):
        sx, sy = corners[i]
        ex, ey = corners[(i + 1) % 4]
        edges.append(
            '\t(gr_line (start %.3f %.3f) (end %.3f %.3f)\n'
            '\t\t(stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "%s")\n\t)'
            % (sx, sy, ex, ey, uid())
        )
    return """(kicad_pcb
\t(version 20241229)
\t(generator "kicad_gen")
\t(generator_version "1.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t)
\t(net 0 "")
%s
)
""" % ("\n".join(edges))


def gen_pro(name):
    return {
        "board": {
            "design_settings": {
                "defaults": {
                    "board_outline_line_width": 0.1,
                    "copper_line_width": TRACK_MIN,
                    "silk_line_width": 0.15,
                    "silk_text_size_h": 1.0,
                    "silk_text_size_v": 1.0,
                },
                "rules": {
                    "min_clearance": CLEARANCE,
                    "min_track_width": TRACK_MIN,
                    "min_through_hole_diameter": VIA_DRILL,
                    "min_via_annular_width": (VIA_DIA - VIA_DRILL) / 2,
                    "min_via_diameter": VIA_DIA,
                },
                "track_widths": [0.0, TRACK_MIN, 0.5, 1.0],
                "via_dimensions": [
                    {"diameter": 0.0, "drill": 0.0},
                    {"diameter": VIA_DIA, "drill": VIA_DRILL},
                ],
            }
        },
        "meta": {"filename": name + ".kicad_pro", "version": 3},
        "net_settings": {
            "classes": [
                {
                    "clearance": CLEARANCE,
                    "name": "Default",
                    "track_width": TRACK_MIN,
                    "via_diameter": VIA_DIA,
                    "via_drill": VIA_DRILL,
                }
            ]
        },
        "sheets": [],
        "text_variables": {},
    }
