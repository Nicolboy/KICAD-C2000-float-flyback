"""Generateur LTspice pour l'architecture de linearisation HV_BIAS,
reconstruite depuis le VRAI netlist exporte par kicad-cli (pas une
lecture d'image -- cf. le piege des croisements de fils sans point de
connexion) sur KICAD-HT.kicad_sch au 2026-10-27.

Modeles GENERIQUES/IDEAUX (meme esprit que gen_bias_lin.py) : U21 ->
UniversalOpAmp2 ideal, Q6/Q7 -> NMOS niveau 1 generique.

Topologie confirmee par `kicad-cli sch export netlist` :
  VAR_GATE --R47(1k)-- node_a --R48(100k)-- GND ; node_a -> IN- U21 (commande)
  HV80_IN --R50(100k)-- node_raw (Drain Q6 / cathode D8 / Grille Q7)
  node_raw -- D8 (clamp SMCJ100A) -- GND
  Q6 : Drain=node_raw, Source=GND (DIRECT, pas de resistance de source),
       Grille <- R49(1k) <- OUT U21
  Q7 (source-follower, AJOUTE depuis la derniere revue) : Grille=node_raw,
       Drain=HV80_IN, Source=HV_BIAS -- decouple node_raw (regulation) de
       HV_BIAS (sortie chargee par R53 et le reste du projet, R9/R10 etc.)
  HV_BIAS --R53(1M)-- node_sense --R52(33k)-- GND
  node_sense --R36(10k)-- IN+ U21 (mesure, contre-reaction)
  U21 alimente RAIL_3V3_PRI/GND, decouplage C58 100n
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402

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
          r47=1e3, r48=100e3, r49=1e3, r50=100e3, r53=1e6, r52=33e3,
          r36=10e3, q_vto=1.0, q_kp=0.05,
          meas_points=None):
    """Topologie verifiee par netlist kicad-cli (2026-10-27) :
    IN- = commande (R47/R48, VAR_GATE), IN+ = mesure (R36, via R53/R52
    sur HV_BIAS post-Q7). Q7 (source-follower) decouple le noeud de
    regulation (node_raw = Drain Q6 / cathode D8 / R50) du noeud
    HV_BIAS reellement charge (R53 ici, R9/R10 etc. ailleurs sur le
    projet)."""
    s = Sheet()
    s.comment(40, 20,
              "Topologie verifiee par netlist (pas une lecture d'image) : "
              "Q7 source-follower ajoute entre node_raw et HV_BIAS. "
              "1ere passe, modeles generiques.")

    s.directive(40, 500, f".model MQ_IDEAL NMOS(VTO={q_vto} KP={q_kp})")
    s.directive(40, 520, ".model DCLAMP_SMCJ100A D(BV=100 IBV=1m RS=1.0)")

    two_pin(s, "voltage", 80, 120, "Vvargate", f"{vargate_start}", "vargate", "0")
    two_pin(s, "voltage", 80, 340, "Vhv80in", f"{hv80in}", "hv80_in", "0")
    two_pin(s, "voltage", 80, 560, "Vrail", f"{rail_3v3}", "rail_3v3_pri", "0")

    two_pin(s, "res", 240, 120, "R47", f"{r47:.0f}", "vargate", "node_a")
    two_pin(s, "res", 400, 220, "R48", f"{r48:.0f}", "node_a", "0")

    two_pin(s, "res", 400, 460, "R53", f"{r53:.0f}", "hv_bias", "node_sense")
    two_pin(s, "res", 400, 620, "R52", f"{r52:.0f}", "node_sense", "0")
    two_pin(s, "res", 240, 700, "R36", f"{r36:.0f}", "node_sense", "node_fb_sense")

    # IN- = commande (node_a), IN+ = mesure (node_fb_sense) -- verifie netlist
    ox, oy = s.symbol("UniversalOpAmp2", 600, 160, rot="R0", inst="U21")
    s.flag(ox + PIN["opamp2"]["IN-"][0], oy + PIN["opamp2"]["IN-"][1], "node_a")
    s.flag(ox + PIN["opamp2"]["IN+"][0], oy + PIN["opamp2"]["IN+"][1], "node_fb_sense")
    s.flag(ox + PIN["opamp2"]["V+"][0], oy + PIN["opamp2"]["V+"][1], "rail_3v3_pri")
    s.flag(ox + PIN["opamp2"]["V-"][0], oy + PIN["opamp2"]["V-"][1], "0")
    s.flag(ox + PIN["opamp2"]["OUT"][0], oy + PIN["opamp2"]["OUT"][1], "node_opout")

    two_pin(s, "cap", 760, 400, "C58", "100n", "rail_3v3_pri", "0")

    two_pin(s, "res", 840, 160, "R49", f"{r49:.0f}", "node_opout", "node_gate")

    two_pin(s, "res", 1000, 80, "R50", f"{r50:.0f}", "hv80_in", "node_raw")
    two_pin(s, "diode", 1140, 160, "D8", "DCLAMP_SMCJ100A", "0", "node_raw")

    mx, my = s.symbol("nmos", 1000, 280, rot="R0", inst="Q6",
                       value="MQ_IDEAL", prefix="M")
    s.flag(mx + PIN["nmos"]["D"][0], my + PIN["nmos"]["D"][1], "node_raw")
    s.flag(mx + PIN["nmos"]["G"][0], my + PIN["nmos"]["G"][1], "node_gate")
    s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "0")  # Source=GND direct

    # Q7 : source-follower -- Grille=node_raw, Drain=hv80_in, Source=hv_bias
    qx, qy = s.symbol("nmos", 1280, 280, rot="R0", inst="Q7",
                       value="MQ_IDEAL", prefix="M")
    s.flag(qx + PIN["nmos"]["D"][0], qy + PIN["nmos"]["D"][1], "hv80_in")
    s.flag(qx + PIN["nmos"]["G"][0], qy + PIN["nmos"]["G"][1], "node_raw")
    s.flag(qx + PIN["nmos"]["S"][0], qy + PIN["nmos"]["S"][1], "hv_bias")

    s.directive(40, 620,
                f".dc Vvargate {vargate_start} {vargate_stop} {vargate_step}")

    if meas_points is None:
        meas_points = [round(0.1 * i, 2) for i in range(31)]  # 0 -> 3.0V, pas 0.1V
    meas_x, meas_lines_y = 2600, 40
    for i, v in enumerate(meas_points):
        s.directive(meas_x, meas_lines_y + i * 20,
                    f".meas DC Vbias_at_{v:.2f} FIND V(hv_bias) "
                    f"WHEN V(vargate)={v:.3f}")
        s.directive(meas_x, meas_lines_y + i * 20 + 10,
                    f".meas DC Vopout_at_{v:.2f} FIND V(node_opout) "
                    f"WHEN V(vargate)={v:.3f}")

    s.write(out_path)
    print(f"Ecrit {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "bias_fb.asc"
    build(0.0, 3.0, 0.01, out)
