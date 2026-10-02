#!/usr/bin/env python3
"""Genere lib/custom_parts.kicad_sym : UCC27517, ISO7710, MSD1514, UCC5304,
AMC0311S.

Aucun des cinq n'existe dans les bibliotheques KiCad standard (verifie :
Driver_FET.kicad_sym n'a que UCC27511/UCC27524 ; Isolator.kicad_sym n'a pas
ISO7710/UCC5304/AMC0311S ; Device.kicad_sym n'a pas de transformateur
couple 1:1 avec ce brochage). Convention de corps reprise des symboles
standard les plus proches (UCC27511, ISO7721D : simple rectangle IC, pas
de triangle op-amp — verifie avant construction, cf. conversation).

Brochages sources :
  UCC27517 : datasheets/ucc27517.pdf p.4 tbl Pin Functions - UCC27517
             1=VDD 2=GND 3=IN+ 4=IN- 5=OUT (SOT23-5, DBV)
  ISO7710  : datasheets/isolation/iso7710.pdf p.3 Figure 4-2, D Package
             1=VCC1 2=IN 3=VCC1 4=GND1 5=GND2 6=OUT 7=NC 8=VCC2 (SOIC-8)
  MSD1514  : datasheets/inductors/msd1514.pdf p.3 (page lue visuellement,
             pas seulement texte) : L1 sur pins 1(haut,point)-3(bas),
             L2 sur pins 2(haut)-4(bas), 1:1. Le point de polarite de L2
             (pin2 vs pin4) n'est pas explicitement marque dans le schema
             simplifie du datasheet -- pin2 retenu par symetrie avec pin1
             (meme position "haut" dans le dessin) ; A VERIFIER sur piece
             reelle avant de faire confiance a la polarite en simulation.
  UCC5304  : datasheets/isolation/ucc5304.pdf p.3 tbl "Pin Functions",
             DWV-8 (SOIC large corps) : 1=IN 2=VCCI 3=VCCI 4=GND (primaire)
             5=VSS 6=VSS 7=OUT 8=VDD (secondaire isole).
  AMC0311S : datasheets/isolation/amc0311s.pdf p.3 tbl 5-1, DWV-8 :
             1=VDD1 2=INP 3=SNSN 4=GND1 (cote field/haute-tension)
             5=GND2 6=REFIN 7=OUT 8=VDD2 (cote controleur/ADC).
"""

from pathlib import Path

OUT = Path(__file__).parent / "lib" / "custom_parts.kicad_sym"


def pin(num, name, x, y, angle, kind="input", length=2.54):
    return (
        '\t\t\t(pin %s line\n'
        '\t\t\t\t(at %.2f %.2f %d)\n'
        '\t\t\t\t(length %.2f)\n'
        '\t\t\t\t(name "%s" (effects (font (size 1.27 1.27))))\n'
        '\t\t\t\t(number "%s" (effects (font (size 1.27 1.27))))\n'
        '\t\t\t)\n'
    ) % (kind, x, y, angle, length, name, num)


def rect(x0, y0, x1, y1):
    return (
        '\t\t\t(rectangle\n'
        '\t\t\t\t(start %.2f %.2f) (end %.2f %.2f)\n'
        '\t\t\t\t(stroke (width 0.254) (type default))\n'
        '\t\t\t\t(fill (type background))\n'
        '\t\t\t)\n'
    ) % (x0, y0, x1, y1)


def header(name, ref, value, footprint, datasheet, descr, keywords):
    return (
        '\t(symbol "%s"\n'
        '\t\t(pin_names (offset 0.508))\n'
        '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)\n'
        '\t\t(property "Reference" "%s" (at 0 11.43 0) (effects (font (size 1.27 1.27))))\n'
        '\t\t(property "Value" "%s" (at 0 -11.43 0) (effects (font (size 1.27 1.27))))\n'
        '\t\t(property "Footprint" "%s" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
        '\t\t(property "Datasheet" "%s" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
        '\t\t(property "Description" "%s" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
        '\t\t(property "ki_keywords" "%s" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
    ) % (name, ref, value, footprint, datasheet, descr, keywords)


def ucc27517():
    body = rect(-7.62, 5.08, 7.62, -5.08)
    pins = "".join([
        pin("1", "VDD", 0, 7.62, 270, "power_in"),
        pin("2", "GND", 0, -7.62, 90, "power_in"),
        pin("3", "IN+", -10.16, 2.54, 0, "input"),
        pin("4", "IN-", -10.16, -2.54, 0, "input"),
        pin("5", "OUT", 10.16, 0, 180, "output"),
    ])
    return (
        header(
            "UCC27517", "U", "UCC27517",
            "Package_TO_SOT_SMD:SOT-23-5",
            "${KIPRJMOD}/../composants-datasheets/datasheets/ucc27517.pdf",
            "Single-channel high-speed low-side gate driver, inverting/non-inverting dual input, SOT23-5",
            "gate driver UCC27517",
        )
        + '\t\t(symbol "UCC27517_0_1"\n' + body + '\t\t)\n'
        + '\t\t(symbol "UCC27517_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def iso7710():
    body = rect(-7.62, 6.35, 7.62, -6.35)
    # Petit repere de barriere au centre du corps (esthetique, pas
    # electrique) -- convention deja vue sur ISO7721D standard.
    barrier = (
        '\t\t\t(polyline\n'
        '\t\t\t\t(pts (xy 0 6.35) (xy 0 -6.35))\n'
        '\t\t\t\t(stroke (width 0.127) (type dash))\n'
        '\t\t\t\t(fill (type none))\n'
        '\t\t\t)\n'
    )
    pins = "".join([
        pin("1", "VCC1", -10.16, 3.81, 0, "power_in"),
        pin("2", "IN", -10.16, 1.27, 0, "input"),
        pin("3", "VCC1", -10.16, -1.27, 0, "power_in"),
        pin("4", "GND1", -10.16, -3.81, 0, "power_in"),
        pin("5", "GND2", 10.16, -3.81, 180, "power_in"),
        pin("6", "OUT", 10.16, -1.27, 180, "output"),
        pin("7", "NC", 10.16, 1.27, 180, "no_connect"),
        pin("8", "VCC2", 10.16, 3.81, 180, "power_in"),
    ])
    return (
        header(
            "ISO7710", "U", "ISO7710",
            "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "${KIPRJMOD}/../composants-datasheets/datasheets/isolation/iso7710.pdf",
            "High speed reinforced single-channel digital isolator, 100Mbps, SOIC-8 (D package)",
            "digital isolator ISO7710",
        )
        + '\t\t(symbol "ISO7710_0_1"\n' + body + barrier + '\t\t)\n'
        + '\t\t(symbol "ISO7710_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def ucc5304():
    body = rect(-7.62, 6.35, 7.62, -6.35)
    barrier = (
        '\t\t\t(polyline\n'
        '\t\t\t\t(pts (xy 0 6.35) (xy 0 -6.35))\n'
        '\t\t\t\t(stroke (width 0.127) (type dash))\n'
        '\t\t\t\t(fill (type none))\n'
        '\t\t\t)\n'
    )
    pins = "".join([
        pin("1", "IN", -10.16, 3.81, 0, "input"),
        pin("2", "VCCI", -10.16, 1.27, 0, "power_in"),
        pin("3", "VCCI", -10.16, -1.27, 0, "power_in"),
        pin("4", "GND", -10.16, -3.81, 0, "power_in"),
        pin("8", "VDD", 10.16, 3.81, 180, "power_in"),
        pin("7", "OUT", 10.16, 1.27, 180, "output"),
        pin("6", "VSS", 10.16, -1.27, 180, "power_in"),
        pin("5", "VSS", 10.16, -3.81, 180, "power_in"),
    ])
    return (
        header(
            "UCC5304", "U", "UCC5304",
            "Package_SO:SOIC-8_7.5x5.85mm_P1.27mm",
            "${KIPRJMOD}/../composants-datasheets/datasheets/isolation/ucc5304.pdf",
            "4-A source/6-A sink single-channel reinforced isolated gate driver, DWV-8 (wide SOIC)",
            "gate driver isolated UCC5304",
        )
        + '\t\t(symbol "UCC5304_0_1"\n' + body + barrier + '\t\t)\n'
        + '\t\t(symbol "UCC5304_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def amc0311r():
    body = rect(-7.62, 6.35, 7.62, -6.35)
    barrier = (
        '\t\t\t(polyline\n'
        '\t\t\t\t(pts (xy 0 6.35) (xy 0 -6.35))\n'
        '\t\t\t\t(stroke (width 0.127) (type dash))\n'
        '\t\t\t\t(fill (type none))\n'
        '\t\t\t)\n'
    )
    pins = "".join([
        pin("1", "VDD1", -10.16, 3.81, 0, "power_in"),
        pin("2", "INP", -10.16, 1.27, 0, "input"),
        pin("3", "SNSN", -10.16, -1.27, 0, "input"),
        pin("4", "GND1", -10.16, -3.81, 0, "power_in"),
        pin("8", "VDD2", 10.16, 3.81, 180, "power_in"),
        pin("7", "OUT", 10.16, 1.27, 180, "output"),
        pin("6", "REFIN", 10.16, -1.27, 180, "input"),
        pin("5", "GND2", 10.16, -3.81, 180, "power_in"),
    ])
    return (
        header(
            "AMC0311R", "U", "AMC0311R",
            "SOIC_DWV:SOIC-8_DWV_5.85x11.5mm_P1.27mm",
            "${KIPRJMOD}/../composants-datasheets/datasheets/isolation/amc0311r.pdf",
            "Precision reinforced isolated amplifier, ratiometric single-ended output, 77mV-2.25V linear input, DWV-8",
            "isolated amplifier isoamp AMC0311R",
        )
        + '\t\t(symbol "AMC0311R_0_1"\n' + body + barrier + '\t\t)\n'
        + '\t\t(symbol "AMC0311R_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def amc0302r():
    body = rect(-7.62, 6.35, 7.62, -6.35)
    barrier = (
        '\t\t\t(polyline\n'
        '\t\t\t\t(pts (xy 0 6.35) (xy 0 -6.35))\n'
        '\t\t\t\t(stroke (width 0.127) (type dash))\n'
        '\t\t\t\t(fill (type none))\n'
        '\t\t\t)\n'
    )
    pins = "".join([
        pin("1", "VDD1", -10.16, 3.81, 0, "power_in"),
        pin("2", "INP", -10.16, 1.27, 0, "input"),
        pin("3", "INN", -10.16, -1.27, 0, "input"),
        pin("4", "GND1", -10.16, -3.81, 0, "power_in"),
        pin("8", "VDD2", 10.16, 3.81, 180, "power_in"),
        pin("7", "OUT", 10.16, 1.27, 180, "output"),
        pin("6", "REFIN", 10.16, -1.27, 180, "input"),
        pin("5", "GND2", 10.16, -3.81, 180, "power_in"),
    ])
    return (
        header(
            "AMC0302R", "U", "AMC0302R",
            "SOIC_DWV:SOIC-8_DWV_5.85x11.5mm_P1.27mm",
            "${KIPRJMOD}/../composants-datasheets/datasheets/isolation/amc0302r.pdf",
            "Precision reinforced isolated amplifier, ratiometric single-ended output, +-50mV input optimise shunt direct, DWV-8",
            "isolated amplifier isoamp current shunt AMC0302R",
        )
        + '\t\t(symbol "AMC0302R_0_1"\n' + body + barrier + '\t\t)\n'
        + '\t\t(symbol "AMC0302R_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def bss127i():
    # Corps simple (comme iso7710/amc0311r) ; brochage et coordonnees de
    # pin IDENTIQUES a Q_NMOS_GSD standard KiCad (Transistor_FET.kicad_sym)
    # -- G=1 (-5.08,0), S=2 (2.54,-5.08), D=3 (2.54,5.08) -- pour rester
    # compatible avec tout schema qui calculerait les positions de pin a
    # partir de cette table standard. Datasheet/footprint pointent sur la
    # piece Infineon reellement sourcee (datasheets/transistors/
    # infineon-bss127i-datasheet-en.pdf), pas la reference Diodes Inc. du
    # symbole generique KiCad "BSS127S".
    body = rect(-2.54, 7.62, 2.54, -7.62)
    pins = "".join([
        pin("1", "G", -5.08, 0, 0, "input", length=2.54),
        pin("2", "S", 2.54, -5.08, 90, "passive", length=2.54),
        pin("3", "D", 2.54, 5.08, 270, "passive", length=2.54),
    ])
    return (
        header(
            "BSS127I", "Q", "BSS127I",
            "Package_TO_SOT_SMD:SOT-23",
            "${KIPRJMOD}/../composants-datasheets/datasheets/transistors/infineon-bss127i-datasheet-en.pdf",
            "600V N-Channel enhancement MOSFET, small-signal (21mA), logic-level (4.5V rated), SOT-23",
            "MOSFET small-signal high-voltage BSS127",
        )
        + '\t\t(symbol "BSS127I_0_1"\n' + body + '\t\t)\n'
        + '\t\t(symbol "BSS127I_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def mmbt2222():
    # Brochage et coordonnees IDENTIQUES a Q_NPN_BEC standard KiCad
    # (Transistor_BJT.kicad_sym) -- B=1 (-5.08,0), E=2 (2.54,-5.08),
    # C=3 (2.54,5.08).
    body = rect(-2.54, 7.62, 2.54, -7.62)
    pins = "".join([
        pin("1", "B", -5.08, 0, 0, "input", length=2.54),
        pin("2", "E", 2.54, -5.08, 90, "passive", length=2.54),
        pin("3", "C", 2.54, 5.08, 270, "passive", length=2.54),
    ])
    return (
        header(
            "MMBT2222", "Q", "MMBT2222",
            "Package_TO_SOT_SMD:SOT-23",
            "https://assets.nexperia.com/documents/data-sheet/MMBT2222A.pdf",
            "NPN small-signal switching transistor, SOT-23",
            "NPN transistor MMBT2222",
        )
        + '\t\t(symbol "MMBT2222_0_1"\n' + body + '\t\t)\n'
        + '\t\t(symbol "MMBT2222_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def msd1514():
    # Geometrie reprise de Device:Transformer_1P_1S (meme arcs, memes
    # positions de broches), seuls les NUMEROS de broches changent pour
    # correspondre au brochage reel MSD1514 (1/3 = L1, 2/4 = L2).
    arcs_left = "".join(
        '\t\t\t(arc (start %.3f %.3f) (mid %.3f %.3f) (end %.3f %.3f)\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type none))\n\t\t\t)\n'
        % pts for pts in [
            (-1.27, 3.81, -1.656, 2.9336, -2.54, 2.5654),
            (-1.27, 1.27, -1.656, 0.3936, -2.54, 0.0254),
            (-1.27, -1.27, -1.656, -2.1464, -2.54, -2.5146),
            (-1.27, -3.81, -1.656, -4.6864, -2.54, -5.0546),
            (-2.54, 5.08, -1.642, 4.708, -1.27, 3.81),
            (-2.54, 2.54, -1.642, 2.168, -1.27, 1.27),
            (-2.54, 0, -1.642, -0.372, -1.27, -1.27),
            (-2.54, -2.54, -1.642, -2.912, -1.27, -3.81),
        ]
    )
    arcs_right = "".join(
        '\t\t\t(arc (start %.3f %.3f) (mid %.3f %.3f) (end %.3f %.3f)\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type none))\n\t\t\t)\n'
        % (-x0, y0, -x1, y1, -x2, y2)
        for (x0, y0, x1, y1, x2, y2) in [
            (-1.27, 3.81, -1.656, 2.9336, -2.54, 2.5654),
            (-1.27, 1.27, -1.656, 0.3936, -2.54, 0.0254),
            (-1.27, -1.27, -1.656, -2.1464, -2.54, -2.5146),
            (-1.27, -3.81, -1.656, -4.6864, -2.54, -5.0546),
            (-2.54, 5.08, -1.642, 4.708, -1.27, 3.81),
            (-2.54, 2.54, -1.642, 2.168, -1.27, 1.27),
            (-2.54, 0, -1.642, -0.372, -1.27, -1.27),
            (-2.54, -2.54, -1.642, -2.912, -1.27, -3.81),
        ]
    )
    # Repere de polarite (point) cote L1 pin1 et L2 pin2 -- meme convention
    # que le "Dot indicates pin1" du datasheet.
    dots = "".join([
        '\t\t\t(circle (center -3.302 5.08) (radius 0.254)\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type outline))\n\t\t\t)\n',
        '\t\t\t(circle (center 3.302 5.08) (radius 0.254)\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type outline))\n\t\t\t)\n',
    ])
    ratio_text = (
        '\t\t\t(text "1:1"\n'
        '\t\t\t\t(at 0 -6.985 0)\n'
        '\t\t\t\t(effects (font (size 1.27 1.27)))\n'
        '\t\t\t)\n'
    )
    pins = "".join([
        pin("1", "L1.1", -10.16, 5.08, 0, "passive", length=7.62),
        pin("3", "L1.2", -10.16, -5.08, 0, "passive", length=7.62),
        pin("2", "L2.1", 10.16, 5.08, 180, "passive", length=7.62),
        pin("4", "L2.2", 10.16, -5.08, 180, "passive", length=7.62),
    ])
    return (
        header(
            "MSD1514", "T1", "MSD1514-103ME",
            "${KIPRJMOD}/lib_fp/MSD1514.pretty:MSD1514",
            "${KIPRJMOD}/../composants-datasheets/datasheets/inductors/msd1514.pdf",
            "Coupled inductor 1:1, k=0.99, 10uH each winding -- pins 1/3=L1(primary), 2/4=L2(secondary)",
            "coupled inductor transformer flyback MSD1514",
        )
        + '\t\t(symbol "MSD1514_0_1"\n' + arcs_left + arcs_right + dots + ratio_text + '\t\t)\n'
        + '\t\t(symbol "MSD1514_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def mosfet_d2pak():
    # Corps repris tel quel de Device:Q_NMOS (meme dessin), broches
    # renumerotees 1/2/3 pour correspondre aux pastilles reelles de
    # Package_TO_SOT_SMD:TO-263-3_TabPin2 (verifie : pastilles nommees
    # "1","2","3" + languette non nommee liee a "2"). Device:Q_NMOS numerote
    # ses broches "D"/"G"/"S" (des lettres, pas des chiffres) : F8 ne peut
    # pas les associer aux pastilles numeriques de l'empreinte reelle
    # -> symbole dedie plutot que renumerotage a la volee.
    #
    # Correspondance G=1, D=2(languette), S=3 : convention JEDEC standard
    # pour un MOSFET de puissance en D2PAK/TO-263 a 3 broches (Infineon,
    # Vishay, onsemi, IXYS...), pas verifiee par capture photo -- IRF540S et
    # IPB020N10N5 n'ont pas de table de brochage textuelle dans leur
    # datasheet (juste un petit croquis), donc pas de citation page precise
    # possible ici. A confirmer sur piece reelle avant premier reflow, meme
    # reserve que pour le brochage physique du MSD1514.
    body = (
        '\t\t\t(polyline (pts (xy 0.254 1.905) (xy 0.254 -1.905))\n'
        '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 0.254 0) (xy -2.54 0))\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 0.762 2.286) (xy 0.762 1.27))\n'
        '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 0.762 0.508) (xy 0.762 -0.508))\n'
        '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 0.762 -1.27) (xy 0.762 -2.286))\n'
        '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 0.762 -1.778) (xy 3.302 -1.778) (xy 3.302 1.778) (xy 0.762 1.778))\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 1.016 0) (xy 2.032 0.381) (xy 2.032 -0.381) (xy 1.016 0))\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type outline)))\n'
        '\t\t\t(circle (center 1.651 0) (radius 2.794)\n'
        '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 2.54 2.54) (xy 2.54 1.778))\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))\n'
        '\t\t\t(circle (center 2.54 1.778) (radius 0.254)\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type outline)))\n'
        '\t\t\t(circle (center 2.54 -1.778) (radius 0.254)\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type outline)))\n'
        '\t\t\t(polyline (pts (xy 2.54 -2.54) (xy 2.54 0) (xy 0.762 0))\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 2.921 0.381) (xy 3.683 0.381))\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))\n'
        '\t\t\t(polyline (pts (xy 3.302 0.381) (xy 2.921 -0.254) (xy 3.683 -0.254) (xy 3.302 0.381))\n'
        '\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))\n'
    )
    pins = "".join([
        pin("2", "D", 2.54, 5.08, 270, "passive"),
        pin("1", "G", -5.08, 0, 0, "input"),
        pin("3", "S", 2.54, -5.08, 90, "passive"),
    ])
    return (
        header(
            "MOSFET_3PIN_TAB2", "Q", "MOSFET_3PIN_TAB2",
            "Package_TO_SOT_SMD:TO-263-3_TabPin2",
            "",
            "N-channel power MOSFET, D2PAK/TO-263 3 broches -- 1=G, 2=D(languette), 3=S (convention JEDEC standard, pas verifiee sur piece reelle)",
            "mosfet nmos D2PAK TO-263",
        )
        + '\t\t(symbol "MOSFET_3PIN_TAB2_0_1"\n' + body + '\t\t)\n'
        + '\t\t(symbol "MOSFET_3PIN_TAB2_1_1"\n' + pins + '\t\t)\n'
        + '\t)\n'
    )


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = (ucc27517() + iso7710() + msd1514() + mosfet_d2pak() + ucc5304() + amc0311r()
            + amc0302r() + bss127i() + mmbt2222())
    text = (
        '(kicad_symbol_lib\n'
        '\t(version 20241209)\n'
        '\t(generator "gen_symboles")\n'
        '\t(generator_version "1.0")\n'
        + body
        + ')\n'
    )
    OUT.write_text(text, encoding="utf-8")
    print("Ecrit :", OUT)


if __name__ == "__main__":
    main()
