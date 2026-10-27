"""Generateur de schema LTspice (.asc) pour le circuit de linearisation de
HV_BIAS (polarisation.kicad_sch, U20/Q5/R43-R46/R35/R26, revu 2026-10-27).

Premiere passe : modeles GENERIQUES/IDEAUX, pas encore constructeur (cf.
memoire methodologie -- modele simple d'abord, modele reel ensuite) :
  - U20 (MCP6001 reel) -> UniversalOpAmp2 ideal LTspice (Avol=1Meg,
    Rail=0 = sortie rail-to-rail ideale -- coherent avec le MCP6001 reel
    qui est rail-to-rail, mais PAS son modele SPICE Microchip reel).
  - Q5 (BSS127I reel) -> NMOS niveau 1 generique. VTO=1V choisi pour
    rester dans l'esprit "logic-level" du BSS127I (descriptif symbole :
    "logic-level, 4.5V rated") -- NON SOURCE, a readresser des que le
    modele Infineon reel est trouve/source.

Topologie reprise du schema fourni par l'utilisateur (capture d'ecran
polarisation.kicad_sch, 2026-10-27) :
  VAR_GATE --R43(1k)-- nodeA --R44(100k)-- GND ; nodeA -> IN+ U20
  HV80_IN --R26(100k)-- HV_BIAS
  HV_BIAS -- D3 (clamp SMCJ100A, meme modele zener/TVS 2-points que D1
    dans gen_asc.py) -- GND
  HV_BIAS = Drain Q5 ; Gate Q5 <- R46(1k) <- OUT U20 ; Source Q5 = node_fb
  node_fb --R45(1k)-- GND ; node_fb --R35(10k)-- IN- U20
  U20 alimente RAIL_3V3_PRI/GND (suppose 3.3V), decouplage C49 100n
    (sans effet en regime DC, inclus pour fidelite si une passe
    transitoire suit).

HV80_IN pris a 80V fixe (valeur nominale documentee -- "source 80V
externe fixe", 00-intention-conception.md section 16 -- PAS 90 ou 100V,
qui sont des niveaux de clamp/crete, pas la source nominale).

Convention de cablage : identique a gen_asc.py (FLAG par broche, pas de
WIRE explicite, garde-fou anti-collision de Sheet.flag()).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, snap, two_pin, PIN as _BASE_PIN  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))

PIN = dict(_BASE_PIN)
PIN["opamp2"] = {
    "IN+": (-32, 16),
    "IN-": (-32, -16),
    "V+": (0, -32),
    "V-": (0, 32),
    "OUT": (32, 0),
}


def build(vargate_start, vargate_stop, vargate_step, out_path,
          hv80in=80.0, rail_3v3=3.3,
          r43=1e3, r44=100e3, r45=1e3, r46=1e3, r35=10e3, r26=100e3,
          q5_vto=1.0, q5_kp=0.05, lib_dir=None, meas_points=None):
    s = Sheet()
    s.comment(40, 20,
              f"Linearisation HV_BIAS (U20/Q5) -- 1ere passe, modeles "
              f"generiques. HV80_IN={hv80in}V fixe, RAIL_3V3_PRI={rail_3v3}V, "
              f"VAR_GATE balaye {vargate_start}-{vargate_stop}V.")

    if lib_dir is None:
        lib_dir = os.path.join(_HERE, "models")

    # --- modeles generiques (NON sources, a readresser plus tard) ---
    s.directive(40, 500,
                f".model MBSS127_IDEAL NMOS(VTO={q5_vto} KP={q5_kp})")
    s.directive(40, 520, ".model DCLAMP_SMCJ100A D(BV=100 IBV=1m RS=1.0)")

    # --- sources ---
    two_pin(s, "voltage", 80, 120, "Vvargate",
            f"{vargate_start}", "vargate", "0")
    two_pin(s, "voltage", 80, 340, "Vhv80in", f"{hv80in}", "hv80_in", "0")
    two_pin(s, "voltage", 80, 560, "Vrail", f"{rail_3v3}", "rail_3v3_pri", "0")

    # --- entree : R43/R44, pont vers IN+ ---
    two_pin(s, "res", 240, 120, "R43", f"{r43:.0f}", "vargate", "node_a")
    two_pin(s, "res", 400, 220, "R44", f"{r44:.0f}", "node_a", "0")

    # --- U20 (ideal UniversalOpAmp2) ---
    ox, oy = s.symbol("UniversalOpAmp2", 600, 160, rot="R0", inst="U20")
    s.flag(ox + PIN["opamp2"]["IN+"][0], oy + PIN["opamp2"]["IN+"][1], "node_a")
    s.flag(ox + PIN["opamp2"]["IN-"][0], oy + PIN["opamp2"]["IN-"][1], "node_in_minus")
    s.flag(ox + PIN["opamp2"]["V+"][0], oy + PIN["opamp2"]["V+"][1], "rail_3v3_pri")
    s.flag(ox + PIN["opamp2"]["V-"][0], oy + PIN["opamp2"]["V-"][1], "0")
    s.flag(ox + PIN["opamp2"]["OUT"][0], oy + PIN["opamp2"]["OUT"][1], "node_opout")

    # --- decouplage RAIL_3V3_PRI (sans effet en DC, inclus pour fidelite) ---
    two_pin(s, "cap", 760, 400, "C49", "100n", "rail_3v3_pri", "0")

    # --- R46 : sortie opamp -> grille Q5 ---
    two_pin(s, "res", 840, 160, "R46", f"{r46:.0f}", "node_opout", "node_gate")

    # --- HV80_IN --R26-- HV_BIAS, clamp D3 ---
    two_pin(s, "res", 1000, 80, "R26", f"{r26:.0f}", "hv80_in", "hv_bias")
    two_pin(s, "diode", 1140, 160, "D3", "DCLAMP_SMCJ100A", "0", "hv_bias")

    # --- Q5 : Drain=HV_BIAS, Gate=node_gate, Source=node_fb ---
    mx, my = s.symbol("nmos", 1000, 280, rot="R0", inst="Q5",
                       value="MBSS127_IDEAL", prefix="M")
    s.flag(mx + PIN["nmos"]["D"][0], my + PIN["nmos"]["D"][1], "hv_bias")
    s.flag(mx + PIN["nmos"]["G"][0], my + PIN["nmos"]["G"][1], "node_gate")
    s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "node_fb")

    # --- R45 : source Q5 -> GND (capteur de courant) ---
    two_pin(s, "res", 1000, 460, "R45", f"{r45:.0f}", "node_fb", "0")

    # --- R35 : contre-reaction node_fb -> IN- ---
    two_pin(s, "res", 760, 560, "R35", f"{r35:.0f}", "node_fb", "node_in_minus")

    # --- balayage DC + mesures ponctuelles (reutilise le parsing .log
    # existant de run_point.py, pas de parsing .raw -- "simple d'abord") ---
    s.directive(40, 620,
                f".dc Vvargate {vargate_start} {vargate_stop} {vargate_step}")

    if meas_points is None:
        meas_points = [round(0.02 * i, 2) for i in range(51)]  # 0 -> 1.0V, pas 0.02V
        meas_points += [v for v in (1.5, 2.0, 2.5, 3.0) if v <= vargate_stop]
    # Les .meas sont place loin du circuit (hors du cadrage par defaut de
    # LTspice a l'ouverture) pour ne pas noyer le schema sous ~50 lignes de
    # texte -- purement cosmetique, aucun effet sur la simulation.
    meas_x, meas_lines_y = 2600, 40
    for i, v in enumerate(meas_points):
        s.directive(meas_x, meas_lines_y + i * 20,
                    f".meas DC Vbias_at_{v:.2f} FIND V(hv_bias) "
                    f"WHEN V(vargate)={v:.3f}")

    s.write(out_path)
    print(f"Ecrit {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "bias_lin.asc"
    build(0.0, 3.0, 0.01, out)
