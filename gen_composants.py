#!/usr/bin/env python3
"""Construit le schema en feuilles hierarchiques : une feuille racine
(3 blocs (sheet ...)) + trois sous-feuilles (Alimentation, Flyback,
Isolation_Drivers). Sur demande de l'utilisateur (2026-09-28), en
remplacement de la premiere version a plat (un seul .kicad_sch, 41
composants en grille).

Connectivite inchangee : etiquettes globales uniquement, aucun fil --
meme convention que shield-c2000 (methode documentee dans
shield-c2000/doc/methode-kicad-claude.md). Une etiquette globale est
visible et se relie a travers TOUTE la hierarchie, pas seulement sur sa
propre feuille -- decouper en sous-feuilles ne change donc rien au
cablage, seulement l'organisation visuelle.

Decoupage retenu (frontieres fonctionnelles, proposees et validees avec
l'utilisateur) :
  Alimentation       -- connecteurs, Reg1/Reg2/Reg3 (LDO), PWR_FLAG
  Flyback            -- Cin, T1, Q1/Q2, clamp D1, bootstrap D2/C8, Cout
  Isolation_Drivers  -- UCC27517 x2, ISO7710 x2, DPC817

    python gen_composants.py [--force]
"""

import argparse
import json
import re
import uuid
from pathlib import Path

import kicad_gen as pg

PROJECT = "alim-flyback-filament"
ROOT = Path(__file__).parent
CUSTOM_LIB = ROOT / "lib" / "custom_parts.kicad_sym"

DEV = "Device"
R = "R"
C = "C"
CP = "C_Polarized"
FP_R = "Resistor_SMD:R_0805_2012Metric"
FP_C = "Capacitor_SMD:C_0805_2012Metric"

# Boitiers electrolytiques/polymere, aucun n'a de correspondance exacte
# dans Capacitor_SMD.pretty standard -- toutes approchees, a
# verifier/corriger a l'etape empreintes :
#   16SVPG330M   (D6.3xL10.4mm reel) -> 6.3x9.9  (0.5mm d'ecart)
#   A786MW...    (D10xL16.7mm reel)  -> 10x14.3  (2.4mm d'ecart -- le plus
#                                        proche standard, empreinte custom
#                                        a envisager si ca ne rentre pas)
FP_C_OUT = "Capacitor_SMD:CP_Elec_6.3x9.9"        # 16SVPG330M, approche (6.3x10.4 reel)
FP_C_IN = "A786:A786MW_VChip"                     # A786MW477M1VLAV010, custom (cotes confirmees utilisateur)

# --------------------------------------------------------------------------
# BOM, une liste par feuille. Chaque entree : (ref, lib_nick, lib_symbol,
# value, footprint, {numero_de_broche: nom_de_net}).
#
# Nets utilises (voir 00-intention-conception.md pour la justification
# electrique de chaque bloc) :
#   VIN, GND                                   entree, masse primaire
#   RAIL_8V25, RAIL_3V3_PRI                    auxiliaires primaires (§9)
#   SW_PRI, GATE_Q1                            noeud de commutation primaire
#   PWM_PRI_IN, PWM_PRI_OUT, EN_PRI_IN, EN_PRI_OUT   chaine de commande primaire
#   PWM_SEC_IN, PWM_SEC_OUT                    chaine de commande secondaire
#                                               (PWM_SEC_IN cote primaire,
#                                               PWM_SEC_OUT cote flottant)
#   VOUT_P, VOUT_N                             sortie / masse locale secondaire
#   SW_SEC, GATE_Q2, VBOOT, RAIL_3V3_SEC        secondaire flottant
#   HV_BIAS                                    entree biais externe 0-90V
#
# Toutes visibles depuis les trois feuilles (etiquettes globales).
# --------------------------------------------------------------------------

BOM_ALIM = [
    ("J1", "Connector_Generic", "Conn_01x02", "VIN",
     "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     {"1": "VIN", "2": "GND"}),
    ("J3", "Connector_Generic", "Conn_01x02", "VOUT",
     "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     {"1": "VOUT_P", "2": "VOUT_N"}),
    ("J4", "Connector_Generic", "Conn_01x01", "HV_BIAS",
     "Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
     {"1": "HV_BIAS"}),
    ("R9", DEV, R, "100k", FP_R, {"1": "HV_BIAS", "2": "VOUT_P"}),
    ("R10", DEV, R, "100k", FP_R, {"1": "HV_BIAS", "2": "VOUT_N"}),
    ("J2", "Connector_Generic", "Conn_01x04", "CTRL",
     "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     {"1": "PWM_PRI_IN", "2": "EN_PRI_IN", "3": "PWM_SEC_IN", "4": "GND"}),

    # Reg1 (8,25V) puis Reg2 (3,3V) en cascade -- alim auxiliaire primaire (§9)
    ("Reg1", "Regulator_Linear", "LM317_SOT-223", "LM317M",
     "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
     {"1": "LM317_ADJ", "2": "RAIL_8V25", "3": "VIN"}),
    ("R1", DEV, R, "100", FP_R, {"1": "GND", "2": "LM317_ADJ"}),
    ("R2", DEV, R, "560", FP_R, {"1": "LM317_ADJ", "2": "RAIL_8V25"}),
    ("C9", DEV, C, "1u", FP_C, {"1": "VIN", "2": "GND"}),
    ("C10", DEV, C, "10u", FP_C, {"1": "RAIL_8V25", "2": "GND"}),
    ("Reg2", "Regulator_Linear", "MCP1703Ax-330xxTT", "MCP1703-3302",
     "Package_TO_SOT_SMD:SOT-23-3", {"1": "GND", "2": "RAIL_3V3_PRI", "3": "RAIL_8V25"}),
    ("C13", DEV, C, "1u", FP_C, {"1": "RAIL_8V25", "2": "GND"}),
    ("C14", DEV, C, "1u", FP_C, {"1": "RAIL_3V3_PRI", "2": "GND"}),

    # Reg3 (3,3V, bootstrap secondaire) -- meme role que Reg2, cote flottant
    ("Reg3", "Regulator_Linear", "MCP1703Ax-330xxTT", "MCP1703-3302",
     "Package_TO_SOT_SMD:SOT-23-3", {"1": "VOUT_N", "2": "RAIL_3V3_SEC", "3": "VBOOT"}),
    ("C11", DEV, C, "1u", FP_C, {"1": "VBOOT", "2": "VOUT_N"}),
    ("C12", DEV, C, "1u", FP_C, {"1": "RAIL_3V3_SEC", "2": "VOUT_N"}),
]

BOM_FLYBACK = [
    ("C1", DEV, CP, "470u", FP_C_IN, {"1": "VIN", "2": "GND"}),

    ("T1", "custom_parts", "MSD1514", "MSD1514-103ME", "MSD1514:MSD1514",
     {"1": "VIN", "3": "SW_PRI", "2": "SW_SEC", "4": "VOUT_P"}),

    ("Q1", "custom_parts", "MOSFET_3PIN_TAB2", "IPD050N10N5", "TO252:TO252-3_TabPin2",
     {"2": "SW_PRI", "1": "GATE_Q1", "3": "GND"}),
    ("D1", "Device", "D_TVS", "SMCJ43A", "Diode_SMD:D_SMC",
     {"1": "GND", "2": "SW_PRI"}),
    ("R7", DEV, R, "100k", FP_R, {"1": "GATE_Q1", "2": "GND"}),

    ("Q2", "custom_parts", "MOSFET_3PIN_TAB2", "IPD050N10N5", "TO252:TO252-3_TabPin2",
     {"2": "SW_SEC", "1": "GATE_Q2", "3": "VOUT_N"}),
    ("R8", DEV, R, "100k", FP_R, {"1": "GATE_Q2", "2": "VOUT_N"}),
    ("D2", "Device", "D", "BAT54", "Diode_SMD:D_SOD-123",
     {"1": "VOUT_P", "2": "VBOOT"}),
    ("C8", DEV, C, "4u7", FP_C, {"1": "VBOOT", "2": "VOUT_N"}),

    ("C3", DEV, CP, "330u", FP_C_OUT, {"1": "VOUT_P", "2": "VOUT_N"}),
    ("C4", DEV, CP, "330u", FP_C_OUT, {"1": "VOUT_P", "2": "VOUT_N"}),
]

BOM_ISO = [
    ("U1", "custom_parts", "UCC27517", "UCC27517", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "RAIL_8V25", "2": "GND", "3": "EN_PRI_OUT", "4": "PWM_PRI_OUT", "5": "GATE_Q1"}),
    ("U3", "custom_parts", "ISO7710", "ISO7710", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "RAIL_3V3_PRI", "2": "PWM_PRI_IN", "3": "RAIL_3V3_PRI", "4": "GND",
      "5": "GND", "6": "PWM_PRI_OUT", "8": "RAIL_3V3_PRI"}),
    ("U5", "Isolator", "PC817", "DPC817", "Package_DIP:DIP-4_W7.62mm",
     {"1": "EN_PRI_IN_R", "2": "GND", "3": "GND", "4": "EN_PRI_OUT"}),
    ("R3", DEV, R, "470", FP_R, {"1": "EN_PRI_IN", "2": "EN_PRI_IN_R"}),
    ("R4", DEV, R, "10k", FP_R, {"1": "RAIL_8V25", "2": "EN_PRI_OUT"}),
    ("R5", DEV, R, "100k", FP_R, {"1": "PWM_PRI_IN", "2": "GND"}),

    ("U4", "custom_parts", "ISO7710", "ISO7710", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "RAIL_3V3_PRI", "2": "PWM_SEC_IN", "3": "RAIL_3V3_PRI", "4": "GND",
      "5": "VOUT_N", "6": "PWM_SEC_OUT", "8": "RAIL_3V3_SEC"}),
    ("R6", DEV, R, "100k", FP_R, {"1": "PWM_SEC_IN", "2": "GND"}),

    ("U2", "custom_parts", "UCC27517", "UCC27517", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "VBOOT", "2": "VOUT_N", "3": "VBOOT", "4": "PWM_SEC_OUT", "5": "GATE_Q2"}),
]

# Nets racine dont l'alimentation vient de broches "passive" (connecteur,
# enroulement de transformateur) que l'ERC ne reconnait pas comme une
# source de puissance. Meme situation que shield-c2000
# (doc/methode-kicad-claude.md, "power_pin_not_driven ... voir le
# PWR_FLAG") : un PWR_FLAG par net racine, pose sur la feuille Alimentation
# (une etiquette globale se relie a travers toute la hierarchie, peu importe
# la feuille ou le flag est physiquement pose).
PWR_FLAG_NETS = ["VIN", "GND", "VOUT_N", "VBOOT"]

SHEETS = [
    # (nom, fichier, BOM, pose_les_pwr_flags_ici)
    ("Alimentation", "alim.kicad_sch", BOM_ALIM, True),
    ("Flyback", "flyback.kicad_sch", BOM_FLYBACK, False),
    ("Isolation_Drivers", "isolation.kicad_sch", BOM_ISO, False),
]

# Espacement genereux et etiquettes Reference/Value a gauche/droite du
# corps (pas au-dessus/en-dessous) -- consigne de l'utilisateur
# (2026-09-29) apres qu'un placement en grille serree ait fait se
# recouvrir composants et etiquettes globales sur les trois feuilles.
# Note : une fois une feuille retravaillee a la main par l'utilisateur,
# elle devient un fichier de travail (voir methode-kicad-claude.md de
# shield-c2000) -- ne plus la regenerer. Ces valeurs ne comptent donc que
# pour une feuille encore jamais placee a la main.
ORIGIN = (25.4, 25.4)
STEP_X = 38.1
STEP_Y = 33.02
PER_ROW = 5
LABEL_OFFSET = 8.89

LABEL_DIR = {0: (180, "right"), 180: (0, "left"),
             90: (270, "right"), 270: (90, "left")}


def uid():
    return str(uuid.uuid4())


def global_label(name, x, y, angle):
    rot, just = LABEL_DIR[angle]
    return (
        '\t(global_label "%s" (shape bidirectional) (at %.2f %.2f %d)\n'
        '\t\t(fields_autoplaced yes)\n'
        '\t\t(effects (font (size 1.27 1.27)) (justify %s))\n'
        '\t\t(uuid "%s")\n'
        '\t)\n'
    ) % (name, x, y, rot, just, uid())


def load_symbol(nick, name):
    """Renvoie (bloc_lib_symbols, [(num,nom,x,y,angle)]) pour un symbole."""
    if nick == "custom_parts":
        block = pg.extract_from(CUSTOM_LIB, name, new_nick=nick)
    else:
        libfile = pg.KILIB / (nick + ".kicad_sym")
        block = pg.extract_from(libfile, name, new_nick=nick)
    pins = []
    for sub in re.finditer(r'\(symbol "[^"]*_\d+_1"', block):
        sub_block = pg.sexp_block(block, sub.start())
        pins.extend(pg.parse_pins(sub_block))
    return block, pins


def place(ref, nick, symname, value, footprint, net_map, pos, lib_symbols_seen, sheet_path):
    x0, y0 = pos
    lib_id = "%s:%s" % (nick, symname)
    if lib_id not in lib_symbols_seen:
        block, pins = load_symbol(nick, symname)
        lib_symbols_seen[lib_id] = (block, pins)
    _, pins = lib_symbols_seen[lib_id]
    pin_by_num = {num: (name, x, y, ang) for num, name, x, y, ang in pins}

    out = []
    out.append(
        '\t(symbol\n'
        '\t\t(lib_id "%s")\n'
        '\t\t(at %.2f %.2f 0)\n'
        '\t\t(unit 1)\n'
        '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
        '\t\t(uuid "%s")\n'
        '\t\t(property "Reference" "%s" (at %.2f %.2f 0) (effects (font (size 1.27 1.27))))\n'
        '\t\t(property "Value" "%s" (at %.2f %.2f 0) (effects (font (size 1.27 1.27))))\n'
        '\t\t(property "Footprint" "%s" (at %.2f %.2f 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
        % (lib_id, x0, y0, uid(), ref, x0 - LABEL_OFFSET, y0, value, x0 + LABEL_OFFSET, y0,
           footprint or "", x0, y0)
    )
    for num in pin_by_num:
        out.append('\t\t(pin "%s" (uuid "%s"))\n' % (num, uid()))
    out.append(
        '\t\t(instances\n'
        '\t\t\t(project "%s"\n'
        '\t\t\t\t(path "%s" (reference "%s") (unit 1))\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t)\n' % (PROJECT, sheet_path, ref)
    )
    symbol_block = "".join(out)

    labels = []
    for num, net in net_map.items():
        if num not in pin_by_num:
            raise SystemExit("%s : broche %s absente du symbole %s (broches : %s)"
                              % (ref, num, lib_id, sorted(pin_by_num)))
        _, px, py, ang = pin_by_num[num]
        lx, ly = pg.snap(x0 + px), pg.snap(y0 - py)
        labels.append(global_label(net, lx, ly, ang))
    return symbol_block, "".join(labels)


def place_pwr_flag(net, x, y, sheet_path):
    """PWR_FLAG n'a qu'une unite ('_0_0' pour la broche, '_0_1' pour le
    dessin) -- hors du motif '_N_1' que load_symbol() sait lire, traite a
    part."""
    return (
        '\t(symbol\n'
        '\t\t(lib_id "power:PWR_FLAG")\n'
        '\t\t(at %.2f %.2f 0)\n'
        '\t\t(unit 1)\n'
        '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n'
        '\t\t(uuid "%s")\n'
        '\t\t(property "Reference" "#FLG" (at %.2f %.2f 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
        '\t\t(property "Value" "PWR_FLAG" (at %.2f %.2f 0) (effects (font (size 1.27 1.27))))\n'
        '\t\t(pin "1" (uuid "%s"))\n'
        '\t\t(instances\n'
        '\t\t\t(project "%s"\n'
        '\t\t\t\t(path "%s" (reference "#FLG%s") (unit 1))\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t)\n'
    ) % (x, y, uid(), x, y + 1.905, x, y + 3.81, uid(), PROJECT, sheet_path, net) \
      + global_label(net, x, y, 90)


POWER_LIB = pg.KILIB / "power.kicad_sym"
PWR_FLAG_LIB_BLOCK = pg.extract_from(POWER_LIB, "PWR_FLAG", new_nick="power")


def render_sheet_body(bom, sheet_path, with_pwr_flags):
    """Pose tous les composants d'une feuille. Renvoie (lib_symbols_text,
    bodies_text, labels_text)."""
    lib_symbols_seen = {}
    bodies = []
    labels = []

    for i, (ref, nick, symname, value, footprint, net_map) in enumerate(bom):
        col, row = i % PER_ROW, i // PER_ROW
        x = pg.snap(ORIGIN[0] + col * STEP_X)
        y = pg.snap(ORIGIN[1] + row * STEP_Y)
        body, lbl = place(ref, nick, symname, value, footprint, net_map,
                           (x, y), lib_symbols_seen, sheet_path)
        bodies.append(body)
        labels.append(lbl)

    if with_pwr_flags:
        flag_row = pg.snap(ORIGIN[1] + (len(bom) // PER_ROW + 1) * STEP_Y)
        for i, net in enumerate(PWR_FLAG_NETS):
            x = pg.snap(ORIGIN[0] + i * 12.7)
            bodies.append(place_pwr_flag(net, x, flag_row, sheet_path))

    lib_symbols_text = "\n".join(block for block, _ in lib_symbols_seen.values())
    if with_pwr_flags:
        lib_symbols_text += "\n" + PWR_FLAG_LIB_BLOCK
    return lib_symbols_text, "".join(bodies), "".join(labels)


def write_subsheet(path, own_uuid, sheet_path, page_num, lib_symbols_text, bodies_text, labels_text):
    sch = (
        '(kicad_sch\n'
        '\t(version 20260306)\n'
        '\t(generator "gen_composants")\n'
        '\t(generator_version "1.0")\n'
        '\t(uuid "%s")\n'
        '\t(paper "A4")\n'
        '\t(lib_symbols\n%s\n\t)\n'
        '%s'
        '%s'
        '\t(sheet_instances\n'
        '\t\t(path "%s" (page "%s"))\n'
        '\t)\n'
        ')\n'
    ) % (own_uuid, lib_symbols_text, bodies_text, labels_text, sheet_path, page_num)
    path.write_text(sch, encoding="utf-8")


def sheet_block(name, filename, sheet_uuid, pos, size, page_num):
    x, y = pos
    w, h = size
    return (
        '\t(sheet\n'
        '\t\t(at %.2f %.2f)\n'
        '\t\t(size %.2f %.2f)\n'
        '\t\t(fields_autoplaced yes)\n'
        '\t\t(stroke (width 0.1524) (type solid))\n'
        '\t\t(fill (color 0 0 0 0.0000))\n'
        '\t\t(uuid "%s")\n'
        '\t\t(property "Sheetname" "%s"\n'
        '\t\t\t(at %.2f %.2f 0)\n'
        '\t\t\t(effects (font (size 1.27 1.27)) (justify left bottom))\n'
        '\t\t)\n'
        '\t\t(property "Sheetfile" "%s"\n'
        '\t\t\t(at %.2f %.2f 0)\n'
        '\t\t\t(effects (font (size 1.27 1.27)) (justify left top))\n'
        '\t\t)\n'
        '\t\t(instances\n'
        '\t\t\t(project "%s"\n'
        '\t\t\t\t(path "/" (page "%s"))\n'
        '\t\t\t)\n'
        '\t\t)\n'
        '\t)\n'
    ) % (x, y, w, h, sheet_uuid, name, x, y - 0.5, filename, x, y + h + 0.5,
         PROJECT, page_num)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    pg.refuser_si_kicad_ouvert(ROOT)

    root_path = ROOT / (PROJECT + ".kicad_sch")
    if root_path.exists() and not args.force:
        raise SystemExit("%s existe deja -- utiliser --force" % root_path)

    root_uuid = uid()
    sheet_positions = [(20.0, 20.0), (110.0, 20.0), (200.0, 20.0)]
    sheet_size = (70.0, 50.0)

    sheet_blocks = []
    total = 0
    for (name, filename, bom, with_flags), pos, page in zip(
            SHEETS, sheet_positions, ("2", "3", "4")):
        sheet_uuid = uid()
        sheet_path = "/%s" % sheet_uuid
        lib_symbols_text, bodies_text, labels_text = render_sheet_body(
            bom, sheet_path, with_flags)
        own_uuid = uid()
        write_subsheet(ROOT / filename, own_uuid, sheet_path, page,
                        lib_symbols_text, bodies_text, labels_text)
        sheet_blocks.append(sheet_block(name, filename, sheet_uuid, pos, sheet_size, page))
        print("Ecrit :", ROOT / filename, "(%d composants)" % len(bom))
        total += len(bom)

    root_sch = (
        '(kicad_sch\n'
        '\t(version 20260306)\n'
        '\t(generator "gen_composants")\n'
        '\t(generator_version "1.0")\n'
        '\t(uuid "%s")\n'
        '\t(paper "A4")\n'
        '\t(lib_symbols\n\t)\n'
        '%s'
        '\t(sheet_instances\n'
        '\t\t(path "/" (page "1"))\n'
        '\t)\n'
        ')\n'
    ) % (root_uuid, "".join(sheet_blocks))
    root_path.write_text(root_sch, encoding="utf-8")
    print("Ecrit :", root_path, "(feuille racine, 3 sous-feuilles, %d composants au total)" % total)

    # sym-lib-table : necessaire pour que KiCad resolve custom_parts:* a
    # l'ouverture (le cache lib_symbols suffit pour kicad-cli/ERC mais pas
    # pour une edition ulterieure dans l'IHM).
    table = ROOT / "sym-lib-table"
    table.write_text(
        '(sym_lib_table\n'
        '  (version 7)\n'
        '  (lib (name "custom_parts")(type "KiCad")(uri "${KIPRJMOD}/lib/custom_parts.kicad_sym")(options "")(descr "Symboles custom alim-flyback"))\n'
        ')\n',
        encoding="utf-8",
    )

    (ROOT / (PROJECT + ".kicad_pcb")).write_text(pg.gen_pcb(), encoding="utf-8")
    pro = pg.gen_pro(PROJECT)
    (ROOT / (PROJECT + ".kicad_pro")).write_text(json.dumps(pro, indent=2), encoding="utf-8")
    print("Ecrit :", PROJECT + ".kicad_pcb / .kicad_pro")


if __name__ == "__main__":
    main()
