#!/usr/bin/env python3
"""Genere la nouvelle feuille hierarchique limitation-courant.kicad_sch
(limitation de courant cycle-par-cycle locale au primaire + retour isole
nTRIP, voir 00-intention-conception.md S19) et ajoute son bloc (sheet ...)
a la feuille racine KICAD-HT.kicad_sch.

Reprend telles quelles les briques de gen_composants.py (place(),
global_label(), load_symbol(), sheet_block()) -- meme convention
etiquettes globales uniquement, aucun fil pose par script.

Ne touche a AUCUNE feuille deja reprise a la main (isolation, flyback,
alim, polarisation) : ce script n'ecrit que le nouveau fichier et
n'ajoute qu'un bloc (sheet ...) en fin de KICAD-HT.kicad_sch (insertion
chirurgicale faite separement, pas par ce script -- la racine a deja ete
retouchee a la main pour ajouter Polarisation, donc plus question de la
regenerer non plus).

    python gen_limitation_courant.py
"""

import uuid
from pathlib import Path

import kicad_gen as pg
import gen_composants as gc

ROOT = Path(__file__).parent
PROJECT = "KICAD-HT"
DEV = "Device"
R = "R"
C = "C"
FP_R = "Resistor_SMD:R_0805_2012Metric"
FP_C = "Capacitor_SMD:C_0805_2012Metric"

# Sheet uuid dans la feuille racine (c8449ac7-...) -- repris identique aux
# 4 sheet_path existants dans KICAD-HT.kicad_sch.
ROOT_UUID = "c8449ac7-87b3-4a93-889f-06dd686c5aff"
SHEET_UUID = "b1e6f2a4-3c9d-4e5a-8f21-6a7d9c4e2b10"
SHEET_PATH = "/%s/%s" % (ROOT_UUID, SHEET_UUID)
PAGE_NUM = "6"
SHEET_FILENAME = "limitation-courant.kicad_sch"

# --------------------------------------------------------------------------
# BOM -- voir 00-intention-conception.md S19 pour la justification de
# chaque valeur (citations datasheet page par page).
#
# Nets utilises :
#   ISNS_KP/ISNS_KN     Kelvin brut (pastilles S1/S2 de R19, flyback.kicad_sch)
#   ISNS_AMP_P          entree TSV791 IN+, apres filtre/protection
#   ISNS_AMP_FB         entree TSV791 IN- (jonction Rg/Rf)
#   ISNS_AMP            sortie TSV791 (x10.09), entree LMV7219 +IN
#   V_REF25             sortie ATL431 (2.5V, mode 2 broches REF=CATHODE)
#   V_TH                seuil comparateur (pont R31/R32 depuis V_REF25)
#   COMP                sortie LMV7219
#   PWM_LEB             PWM_PRI_OUT retarde (R33/C52), entree A du NAND
#   nPRE                sortie NAND (74LVC1G132), /PRE du verrou
#   Q_TRIP / nQ_TRIP     sorties du verrou (74LVC1G74)
#   RAIL_3V3_PRI, GND    alimentation/masse primaire locale (existants)
#   PWM_PRI_OUT          PWM primaire (existant, sortie U3)
#   GND_CTRL, 3V3_ISO    domaine controle isole (existants, cote C2000)
#   I_Shunt_ht_comp      retour isole vers J2 pin17 (broche deja reservee,
#                        pas de modif connecteur -- voir S18)
# --------------------------------------------------------------------------

BOM = [
    # -- protection d'entree + ampli x10.09 --
    ("R27", DEV, R, "100", FP_R, {"1": "ISNS_KP", "2": "ISNS_AMP_P"}),
    ("C47", DEV, C, "22p", FP_C, {"1": "ISNS_AMP_P", "2": "GND"}),
    ("D5", "custom_parts", "BAT54S", "BAT54S", "Package_TO_SOT_SMD:SOT-23",
     {"1": "GND", "2": "RAIL_3V3_PRI", "3": "ISNS_AMP_P"}),
    ("U14", "custom_parts", "TSV791", "TSV791", "Package_TO_SOT_SMD:SOT-23-5",
     {"3": "ISNS_AMP_P", "4": "ISNS_AMP_FB", "1": "ISNS_AMP", "5": "RAIL_3V3_PRI", "2": "GND"}),
    ("C48", DEV, C, "100n", FP_C, {"1": "RAIL_3V3_PRI", "2": "GND"}),
    ("R28", DEV, R, "1.00k", FP_R, {"1": "ISNS_AMP_FB", "2": "ISNS_KN"}),
    ("R29", DEV, R, "9.09k", FP_R, {"1": "ISNS_AMP_FB", "2": "ISNS_AMP"}),

    # -- reference de seuil ATL431 2.5V + pont diviseur --
    # Symbole stock "Reference_Voltage:TL431DBZ" (pas custom_parts:ATL431) :
    # meme brochage (1=K/2=REF/3=A) et meme footprint SOT-23, substitue a
    # la main dans le schema (plus adapte que le symbole custom dessine a
    # la main) -- la piece reellement sourcee/montee reste l'ATL431, Value
    # et Datasheet de l'instance le confirment explicitement.
    ("U15", "Reference_Voltage", "TL431DBZ", "ATL431", "Package_TO_SOT_SMD:SOT-23",
     {"1": "V_REF25", "2": "V_REF25", "3": "GND"}),
    ("R30", DEV, R, "2.67k", FP_R, {"1": "RAIL_3V3_PRI", "2": "V_REF25"}),
    ("C49", DEV, C, "100n", FP_C, {"1": "V_REF25", "2": "GND"}),
    ("R31", DEV, R, "16.5k", FP_R, {"1": "V_REF25", "2": "V_TH"}),
    ("R32", DEV, R, "8.45k", FP_R, {"1": "V_TH", "2": "GND"}),
    ("C50", DEV, C, "10n", FP_C, {"1": "V_TH", "2": "GND"}),

    # -- comparateur --
    ("U16", "custom_parts", "LMV7219", "LMV7219", "Package_TO_SOT_SMD:SOT-23-5",
     {"3": "ISNS_AMP", "4": "V_TH", "1": "COMP", "5": "RAIL_3V3_PRI", "2": "GND"}),
    ("C51", DEV, C, "100n", FP_C, {"1": "RAIL_3V3_PRI", "2": "GND"}),

    # -- blanking (LEB) --
    ("R33", DEV, R, "1.5k", FP_R, {"1": "PWM_PRI_OUT", "2": "PWM_LEB"}),
    ("C52", DEV, C, "100p", FP_C, {"1": "PWM_LEB", "2": "GND"}),
    ("U17", "custom_parts", "SN74LVC1G132", "SN74LVC1G132", "Package_TO_SOT_SMD:SOT-23-5",
     {"1": "PWM_LEB", "2": "COMP", "3": "GND", "4": "nPRE", "5": "RAIL_3V3_PRI"}),
    ("C53", DEV, C, "100n", FP_C, {"1": "RAIL_3V3_PRI", "2": "GND"}),

    # -- verrou --
    ("U18", "custom_parts", "SN74LVC1G74", "SN74LVC1G74", "Package_SO:VSSOP-8_3x3mm_P0.65mm",
     {"1": "GND", "2": "GND", "6": "PWM_PRI_OUT", "7": "nPRE",
      "3": "Q_TRIP", "5": "nQ_TRIP", "8": "RAIL_3V3_PRI", "4": "GND"}),
    ("C54", DEV, C, "100n", FP_C, {"1": "RAIL_3V3_PRI", "2": "GND"}),

    # -- retour isole nTRIP (ISO7710F, sens primaire -> controle, inverse de U3) --
    ("U19", "custom_parts", "ISO7710", "ISO7710F", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "RAIL_3V3_PRI", "3": "RAIL_3V3_PRI", "2": "nQ_TRIP", "4": "GND",
      "5": "GND_CTRL", "6": "I_Shunt_ht_comp", "8": "3V3_ISO"}),
    ("C55", DEV, C, "100n", FP_C, {"1": "RAIL_3V3_PRI", "2": "GND"}),
    ("C56", DEV, C, "100n", FP_C, {"1": "3V3_ISO", "2": "GND_CTRL"}),
]

ORIGIN = (25.4, 25.4)
STEP_X = 38.1
STEP_Y = 33.02
PER_ROW = 6


def main():
    pg.refuser_si_kicad_ouvert(ROOT)

    lib_symbols_seen = {}
    bodies = []
    labels = []
    for i, (ref, nick, symname, value, footprint, net_map) in enumerate(BOM):
        col, row = i % PER_ROW, i // PER_ROW
        x = pg.snap(ORIGIN[0] + col * STEP_X)
        y = pg.snap(ORIGIN[1] + row * STEP_Y)
        body, lbl = gc.place(ref, nick, symname, value, footprint, net_map,
                              (x, y), lib_symbols_seen, SHEET_PATH)
        bodies.append(body)
        labels.append(lbl)

    lib_symbols_text = "\n".join(block for block, _ in lib_symbols_seen.values())
    bodies_text = "".join(bodies)
    labels_text = "".join(labels)

    sheet_file_uuid = str(uuid.uuid4())
    gc.write_subsheet(ROOT / SHEET_FILENAME, sheet_file_uuid, SHEET_PATH, PAGE_NUM,
                       lib_symbols_text, bodies_text, labels_text)
    print("Ecrit :", ROOT / SHEET_FILENAME, "(%d composants)" % len(BOM))

    sb = gc.sheet_block("Limitation_Courant", SHEET_FILENAME, SHEET_UUID,
                         (110.0, 90.0), (70.0, 50.0), PAGE_NUM)
    (ROOT / "limitation_courant_sheet_block.txt").write_text(sb, encoding="utf-8")
    print("Bloc (sheet ...) ecrit dans limitation_courant_sheet_block.txt",
          "-- a inserer a la main dans KICAD-HT.kicad_sch (deja retouche a la main, pas regenere)")


if __name__ == "__main__":
    main()
