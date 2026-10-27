"""Reponse en echelon (transitoire) de la boucle HV_BIAS complete, meme
topologie verifiee par netlist que gen_bias_fb.py (Q7 source-follower
inclus), R52=39k applique.

ATTENTION -- limite de cette 1ere passe : les modeles NMOS generiques
utilises ici (niveau 1, pas de Cgs/Cgd/Cds explicites) n'ont quasiment
pas de capacite parasite. Un ampli-op ideal (UniversalOpAmp2, GBW=10MHz)
+ des MOSFET sans capacite donnent une boucle numeriquement tres rapide
et bien comportee -- ca ne prouve PAS la marge de stabilite reelle.
Le risque de bruit/Miller qui a motive la question (cap Drain-Grille
sur Q7) vient justement des capacites parasites reelles, absentes ici.
A revalider avec les modeles constructeur (BSS127I, MCP6001) avant de
conclure quoi que ce soit sur la stabilite reelle.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402

PIN = dict(_BASE_PIN)
PIN["opamp2"] = {
    "IN+": (-32, 16), "IN-": (-32, -16),
    "V+": (0, -32), "V-": (0, 32), "OUT": (32, 0),
}


def build(out_path, v_lo=0.5, v_hi=2.5, td=20e-6, tr=10e-9, tf=10e-9,
          pw=150e-6, tstop=250e-6,
          hv80in=80.0, rail_3v3=3.3,
          r47=1e3, r48=100e3, r49=1e3, r50=100e3, r53=1e6, r52=39e3,
          r36=10e3, q_vto=1.0, q_kp=0.05, c_node_raw=None, c_hv_bias=None,
          maxstep=10e-9):
    s = Sheet()
    s.comment(40, 20,
              f"Reponse en echelon VAR_GATE {v_lo}V<->{v_hi}V -- topologie "
              f"verifiee par netlist (Q7 source-follower, R52=39k). "
              f"Modeles generiques -- voir limite en tete de script.")

    s.directive(40, 500, f".model MQ_IDEAL NMOS(VTO={q_vto} KP={q_kp})")
    s.directive(40, 520, ".model DCLAMP_SMCJ100A D(BV=100 IBV=1m RS=1.0)")

    two_pin(s, "voltage", 80, 120, "Vvargate",
            f"PULSE({v_lo} {v_hi} {td*1e6:.4f}u {tr*1e9:.2f}n {tf*1e9:.2f}n "
            f"{pw*1e6:.4f}u {tstop*2e6:.4f}u)", "vargate", "0")
    two_pin(s, "voltage", 80, 340, "Vhv80in", f"{hv80in}", "hv80_in", "0")
    two_pin(s, "voltage", 80, 560, "Vrail", f"{rail_3v3}", "rail_3v3_pri", "0")

    two_pin(s, "res", 240, 120, "R47", f"{r47:.0f}", "vargate", "node_a")
    two_pin(s, "res", 400, 220, "R48", f"{r48:.0f}", "node_a", "0")

    two_pin(s, "res", 400, 460, "R53", f"{r53:.0f}", "hv_bias", "node_sense")
    two_pin(s, "res", 400, 620, "R52", f"{r52:.0f}", "node_sense", "0")
    two_pin(s, "res", 240, 700, "R36", f"{r36:.0f}", "node_sense", "node_fb_sense")

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
    s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "0")

    qx, qy = s.symbol("nmos", 1280, 280, rot="R0", inst="Q7",
                       value="MQ_IDEAL", prefix="M")
    s.flag(qx + PIN["nmos"]["D"][0], qy + PIN["nmos"]["D"][1], "hv80_in")
    s.flag(qx + PIN["nmos"]["G"][0], qy + PIN["nmos"]["G"][1], "node_raw")
    s.flag(qx + PIN["nmos"]["S"][0], qy + PIN["nmos"]["S"][1], "hv_bias")

    if c_node_raw:
        two_pin(s, "cap", 1420, 460, "Ccomp", f"{c_node_raw}", "node_raw", "0")
    if c_hv_bias:
        two_pin(s, "cap", 1420, 620, "Cout", f"{c_hv_bias}", "hv_bias", "0")

    s.directive(40, 620, f".tran 0 {tstop*1e6:.4f}u 0 {maxstep*1e9:.4f}n")

    s.write(out_path)
    print(f"Ecrit {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "bias_fb_step.asc"
    build(out)
