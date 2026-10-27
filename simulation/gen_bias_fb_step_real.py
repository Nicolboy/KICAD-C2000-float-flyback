"""Meme banc que gen_bias_fb_step.py (reponse en echelon, topologie
verifiee par netlist, Q7 inclus), mais avec les VRAIS composants
constructeur : U21=MCP6001 (macromodele PSpice officiel Microchip,
corrige pour LTspice), Q6/Q7=BSS127I (proxy datasheet avec capacites
parasites reelles Cgs/Cgd/Cds -- voir simulation/models/*.lib pour
toutes les sources et derivations).

Contrairement au banc ideal (gen_bias_fb_step.py), les MOSFET ont ici de
vraies capacites Cgs/Cgd/Cds (20p/1p/1.4p typ chacun) et le MCP6001 a un
vrai GBW/slew-rate/temps de reponse mesures -- ce banc permet de juger
si le depassement observe avec les modeles ideaux etait un artefact de
l'absence de capacites parasites, ou un phenomene qui persiste avec des
composants reels."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))

PIN = dict(_BASE_PIN)
PIN["opamp2_real"] = {
    "IN+": (-32, 80), "IN-": (-32, 48),
    "V+": (0, 32), "V-": (0, 96), "OUT": (32, 64),
}


def build(out_path, v_lo=0.5, v_hi=2.5, td=20e-6, tr=10e-9, tf=10e-9,
          pw=150e-6, tstop=250e-6,
          hv80in=80.0, rail_3v3=3.3,
          r47=1e3, r48=100e3, r49=1e3, r50=100e3, r53=1e6, r52=39e3,
          r36=10e3, c_node_raw=None, c_hv_bias=None,
          maxstep=10e-9):
    s = Sheet()
    s.comment(40, 20,
              f"Reponse en echelon VAR_GATE {v_lo}V<->{v_hi}V -- COMPOSANTS "
              f"REELS (U21=MCP6001, Q6/Q7=BSS127I, R52=39k).")

    mcp_lib = os.path.join(_HERE, "models", "MCP6001.lib").replace("\\", "/")
    bss_lib = os.path.join(_HERE, "models", "BSS127I.lib").replace("\\", "/")
    s.directive(40, 460, f'.lib "{mcp_lib}"')
    s.directive(40, 480, f'.lib "{bss_lib}"')
    s.directive(40, 500, ".model DCLAMP_SMCJ100A D(BV=100 IBV=1m RS=1.0)")

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

    ox, oy = s.symbol("opamp2", 600, 160, rot="R0", inst="U21", value="MCP6001")
    s.flag(ox + PIN["opamp2_real"]["IN-"][0], oy + PIN["opamp2_real"]["IN-"][1], "node_a")
    s.flag(ox + PIN["opamp2_real"]["IN+"][0], oy + PIN["opamp2_real"]["IN+"][1], "node_fb_sense")
    s.flag(ox + PIN["opamp2_real"]["V+"][0], oy + PIN["opamp2_real"]["V+"][1], "rail_3v3_pri")
    s.flag(ox + PIN["opamp2_real"]["V-"][0], oy + PIN["opamp2_real"]["V-"][1], "0")
    s.flag(ox + PIN["opamp2_real"]["OUT"][0], oy + PIN["opamp2_real"]["OUT"][1], "node_opout")

    two_pin(s, "cap", 760, 400, "C58", "100n", "rail_3v3_pri", "0")
    two_pin(s, "res", 840, 160, "R49", f"{r49:.0f}", "node_opout", "node_gate")
    two_pin(s, "res", 1000, 80, "R50", f"{r50:.0f}", "hv80_in", "node_raw")
    two_pin(s, "diode", 1140, 160, "D8", "DCLAMP_SMCJ100A", "0", "node_raw")

    mx, my = s.symbol("nmos", 1000, 280, rot="R0", inst="Q6",
                       value="MBSS127I", prefix="X")
    s.flag(mx + PIN["nmos"]["D"][0], my + PIN["nmos"]["D"][1], "node_raw")
    s.flag(mx + PIN["nmos"]["G"][0], my + PIN["nmos"]["G"][1], "node_gate")
    s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "0")

    qx, qy = s.symbol("nmos", 1280, 280, rot="R0", inst="Q7",
                       value="MBSS127I", prefix="X")
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
    out = sys.argv[1] if len(sys.argv) > 1 else "bias_fb_step_real.asc"
    build(out)
