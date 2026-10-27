"""Meme topologie que gen_bias_fb.py (verifiee par kicad-cli netlist),
mais avec les VRAIS composants constructeur a la place des modeles
ideaux/generiques :
  - U21 : MCP6001 reel (macromodele PSpice officiel Microchip REV F,
    corrige pour LTspice -- voir simulation/models/MCP6001.lib).
  - Q6, Q7 : BSS127I reel (proxy construit sur les points typ de la
    datasheet Infineon BSS127 Rev 2.1 -- voir simulation/models/BSS127I.lib,
    LIMITE : pas de conduction sous le seuil, zone de fonctionnement
    reelle de Q6/Q7 ici proche du seuil -- voir commentaire du .lib).

R52=39k (valeur reellement appliquee sur la carte, cf. gen_bias_fb_step.py).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))

PIN = dict(_BASE_PIN)
# lib/sym/OpAmps/opamp2.asy -- symbole generique (Prefix=X, Value=nom du
# sous-circuit a instancier), PAS UniversalOpAmp2 (primitif comportemental
# a parametres fixes, incompatible avec un sous-circuit externe -- piege
# rencontre et documente dans validate_mcp6001.py).
PIN["opamp2_real"] = {
    "IN+": (-32, 80), "IN-": (-32, 48),
    "V+": (0, 32), "V-": (0, 96), "OUT": (32, 64),
}


def build(vargate_start, vargate_stop, vargate_step, out_path,
          hv80in=80.0, rail_3v3=3.3,
          r47=1e3, r48=100e3, r49=1e3, r50=100e3, r53=1e6, r52=39e3,
          r36=10e3, meas_points=None):
    s = Sheet()
    s.comment(40, 20,
              "Topologie verifiee par netlist -- COMPOSANTS REELS : "
              "U21=MCP6001, Q6/Q7=BSS127I (voir models/*.lib pour sources).")

    mcp_lib = os.path.join(_HERE, "models", "MCP6001.lib").replace("\\", "/")
    bss_lib = os.path.join(_HERE, "models", "BSS127I.lib").replace("\\", "/")
    s.directive(40, 480, f'.lib "{mcp_lib}"')
    s.directive(40, 500, f'.lib "{bss_lib}"')
    s.directive(40, 520, ".model DCLAMP_SMCJ100A D(BV=100 IBV=1m RS=1.0)")

    two_pin(s, "voltage", 80, 120, "Vvargate", f"{vargate_start}", "vargate", "0")
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

    s.directive(40, 640,
                f".dc Vvargate {vargate_start} {vargate_stop} {vargate_step}")

    if meas_points is None:
        meas_points = [round(0.1 * i, 2) for i in range(31)]
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
    out = sys.argv[1] if len(sys.argv) > 1 else "bias_fb_real.asc"
    build(0.0, 3.0, 0.01, out)
