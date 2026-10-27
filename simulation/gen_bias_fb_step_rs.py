"""Reponse en echelon du banc HV_BIAS composants reels (MMBF170 + MCP6001
parametre datasheet), topologie verifiee par netlist, avec :
  - Rs : resistance de degenerescence source de Q6/Q7 (meme principe que
    gen_bias_fb_ramp_real.py), seul remede confirme qui stabilise SANS
    ajouter de retard de phase dans la boucle.
  - miller_r/miller_c : reseau RC optionnel entre Drain (node_raw) et
    Grille (node_gate) de Q6 -- compensation Miller classique (contre-
    reaction LOCALE sur un etage inverseur : Q6 est monte en source
    commune, Drain et Grille varient en opposition de phase, donc ce
    reseau EST une vraie contre-reaction negative, contrairement au
    condensateur grille-masse seul teste precedemment qui ne faisait
    qu'ajouter un pole/retard dans le chemin direct sans ce couplage
    d'inversion -- et qui a d'ailleurs rendu l'oscillation BEAUCOUP plus
    violente, voir conversation)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402
from gen_bias_fb_ramp_real import place_mcp6001_real  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))

PIN = dict(_BASE_PIN)
PIN["opamp2"] = {
    "IN+": (-32, 16), "IN-": (-32, -16),
    "V+": (0, -32), "V-": (0, 32), "OUT": (32, 0),
}


def build(out_path, v_lo=0.5, v_hi=2.5, td=5e-3, tr=10e-9, tf=10e-9,
          pw=20e-3, tstop=50e-3, rs_val=330,
          miller_r=None, miller_c=None, maxstep=50e-9):
    s = Sheet()
    s.comment(40, 20,
              f"Echelon VAR_GATE {v_lo}<->{v_hi}V -- MMBF170 reel, Rs={rs_val}, "
              f"Miller Drain-Grille Q6 : R={miller_r} C={miller_c}")
    lib = os.path.join(_HERE, "models", "MMBF170.lib").replace("\\", "/")
    s.directive(40, 460, f'.lib "{lib}"')
    s.directive(40, 500, ".model DCLAMP_SMCJ100A D(BV=100 IBV=1m RS=1.0)")

    two_pin(s, "voltage", 80, 120, "Vvargate",
            f"PULSE({v_lo} {v_hi} {td*1e3:.4f}m {tr*1e9:.2f}n {tf*1e9:.2f}n "
            f"{pw*1e3:.4f}m {tstop*2e3:.4f}m)", "vargate", "0")
    two_pin(s, "voltage", 80, 340, "Vhv80in", "80", "hv80_in", "0")
    two_pin(s, "voltage", 80, 560, "Vrail", "3.3", "rail_3v3_pri", "0")
    two_pin(s, "res", 240, 120, "R47", "1000", "vargate", "node_a")
    two_pin(s, "res", 400, 220, "R48", "100000", "node_a", "0")
    two_pin(s, "res", 400, 460, "R53", "100000", "hv_bias", "node_sense")
    two_pin(s, "res", 400, 620, "R52", "3900", "node_sense", "0")
    two_pin(s, "res", 240, 700, "R36", "10000", "node_sense", "node_fb_sense")

    ox, oy = place_mcp6001_real(s, 600, 160, "U21")
    s.flag(ox + PIN["opamp2"]["IN-"][0], oy + PIN["opamp2"]["IN-"][1], "node_a")
    s.flag(ox + PIN["opamp2"]["IN+"][0], oy + PIN["opamp2"]["IN+"][1], "node_fb_sense")
    s.flag(ox + PIN["opamp2"]["V+"][0], oy + PIN["opamp2"]["V+"][1], "rail_3v3_pri")
    s.flag(ox + PIN["opamp2"]["V-"][0], oy + PIN["opamp2"]["V-"][1], "0")
    s.flag(ox + PIN["opamp2"]["OUT"][0], oy + PIN["opamp2"]["OUT"][1], "node_opout")

    two_pin(s, "cap", 760, 400, "C58", "100n", "rail_3v3_pri", "0")
    two_pin(s, "res", 840, 160, "R49", "1000", "node_opout", "node_gate")
    two_pin(s, "res", 1000, 80, "R50", "100000", "hv80_in", "node_raw")
    two_pin(s, "diode", 1140, 160, "D8", "DCLAMP_SMCJ100A", "0", "node_raw")

    mx, my = s.symbol("nmos", 1000, 280, rot="R0", inst="Q6", value="DI_MMBF170 L=100u W=100u", prefix="M")
    s.flag(mx + PIN["nmos"]["D"][0], my + PIN["nmos"]["D"][1], "node_raw")
    s.flag(mx + PIN["nmos"]["G"][0], my + PIN["nmos"]["G"][1], "node_gate")
    s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "q6_src")
    two_pin(s, "res", 1000, 420, "Rs6", f"{rs_val}", "q6_src", "0")

    qx, qy = s.symbol("nmos", 1280, 280, rot="R0", inst="Q7", value="DI_MMBF170 L=100u W=100u", prefix="M")
    s.flag(qx + PIN["nmos"]["D"][0], qy + PIN["nmos"]["D"][1], "hv80_in")
    s.flag(qx + PIN["nmos"]["G"][0], qy + PIN["nmos"]["G"][1], "node_raw")
    s.flag(qx + PIN["nmos"]["S"][0], qy + PIN["nmos"]["S"][1], "hv_bias")

    if miller_c:
        if miller_r:
            two_pin(s, "res", 1160, 220, "Rmiller", f"{miller_r}", "node_raw", "n_miller")
            two_pin(s, "cap", 1160, 340, "Cmiller", f"{miller_c}", "n_miller", "node_gate")
        else:
            two_pin(s, "cap", 1160, 220, "Cmiller", f"{miller_c}", "node_raw", "node_gate")

    s.directive(40, 620, f".tran 0 {tstop*1e3:.4f}m 0 {maxstep*1e9:.2f}n")
    s.write(out_path)
    print(f"Ecrit {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "step_rs.asc"
    build(out)
