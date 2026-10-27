"""Configuration FINALE validee pour la boucle HV_BIAS (composants reels) :
  - Q6/Q7 = MMBF170 (NPN... non, NMOS reel, Diodes Inc., voir models/MMBF170.lib)
  - U21 = MCP6001 PARAMETRE (datasheet, pas macromodele -- voir
    gen_bias_fb_ramp_real.py pour pourquoi)
  - Rs = 330 ohm sur la source de Q6/Q7 (degenerescence locale -- supprime
    l'oscillation du proxy/MOSFET pres du seuil, cf. conversation)
  - Cint = 1nF entre la sortie de l'ampli-op (node_opout) et son entree
    inverseuse (node_a) -- compensation "integrateur" classique, autour de
    l'ampli-op uniquement. Confirme : supprime COMPLETEMENT le depassement
    en echelon, meme au pire cas (front de commande 10ns), sans toucher a
    Rs (donc sans degrader l'acces a HV_BIAS=0V).
  - R53=100k / R52=3,9k (valeurs reelles appliquees sur la carte).

NE PAS ajouter de condensateur de sortie (HV_BIAS) sans re-balayer sa valeur
AVEC Cint deja en place : le 100nF qui semblait interessant seul recree un
depassement et une oscillation lente une fois combine a Cint (teste,
confirme mauvais -- deux poles qui interagissent).

Coordonnees x3 par rapport aux scripts precedents (gen_bias_fb_step_rs.py
etc.) uniquement pour la lisibilite visuelle dans LTspice -- aucun effet
electrique, c'est juste de l'espacement."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402
from gen_bias_fb_ramp_real import place_mcp6001_real  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
SCALE = 3

PIN = dict(_BASE_PIN)
PIN["opamp2"] = {
    "IN+": (-32, 16), "IN-": (-32, -16),
    "V+": (0, -32), "V-": (0, 32), "OUT": (32, 0),
}


def build(out_path, v_lo=0.5, v_hi=2.5, td=5e-3, tr=10e-9, tf=10e-9,
          pw=20e-3, tstop=50e-3, rs_val=330, c_int="1n", maxstep=20e-9):
    s = Sheet(width=1400 * SCALE, height=900 * SCALE)
    s.comment(40 * SCALE, 20 * SCALE,
              f"CONFIGURATION FINALE -- Rs={rs_val}, Cint={c_int} (opout->node_a), "
              f"MMBF170 reel, MCP6001 parametre, R53=100k/R52=3,9k. "
              f"Echelon VAR_GATE {v_lo}<->{v_hi}V, front {tr*1e9:.0f}ns.")

    lib = os.path.join(_HERE, "models", "MMBF170.lib").replace("\\", "/")
    s.directive(40 * SCALE, 460 * SCALE, f'.lib "{lib}"')
    s.directive(40 * SCALE, 500 * SCALE, ".model DCLAMP_SMCJ100A D(BV=100 IBV=1m RS=1.0)")

    two_pin(s, "voltage", 80 * SCALE, 120 * SCALE, "Vvargate",
            f"PULSE({v_lo} {v_hi} {td*1e3:.4f}m {tr*1e9:.2f}n {tf*1e9:.2f}n "
            f"{pw*1e3:.4f}m {tstop*2e3:.4f}m)", "vargate", "0")
    two_pin(s, "voltage", 80 * SCALE, 340 * SCALE, "Vhv80in", "80", "hv80_in", "0")
    two_pin(s, "voltage", 80 * SCALE, 560 * SCALE, "Vrail", "3.3", "rail_3v3_pri", "0")
    two_pin(s, "res", 240 * SCALE, 120 * SCALE, "R47", "1000", "vargate", "node_a")
    two_pin(s, "res", 400 * SCALE, 220 * SCALE, "R48", "100000", "node_a", "0")
    two_pin(s, "res", 400 * SCALE, 460 * SCALE, "R53", "100000", "hv_bias", "node_sense")
    two_pin(s, "res", 400 * SCALE, 620 * SCALE, "R52", "3900", "node_sense", "0")
    two_pin(s, "res", 240 * SCALE, 700 * SCALE, "R36", "10000", "node_sense", "node_fb_sense")

    ox, oy = place_mcp6001_real(s, 600 * SCALE, 160 * SCALE, "U21")
    s.flag(ox + PIN["opamp2"]["IN-"][0], oy + PIN["opamp2"]["IN-"][1], "node_a")
    s.flag(ox + PIN["opamp2"]["IN+"][0], oy + PIN["opamp2"]["IN+"][1], "node_fb_sense")
    s.flag(ox + PIN["opamp2"]["V+"][0], oy + PIN["opamp2"]["V+"][1], "rail_3v3_pri")
    s.flag(ox + PIN["opamp2"]["V-"][0], oy + PIN["opamp2"]["V-"][1], "0")
    s.flag(ox + PIN["opamp2"]["OUT"][0], oy + PIN["opamp2"]["OUT"][1], "node_opout")

    if c_int:
        two_pin(s, "cap", 700 * SCALE, 60 * SCALE, "Cint", f"{c_int}", "node_opout", "node_a")

    two_pin(s, "cap", 760 * SCALE, 400 * SCALE, "C58", "100n", "rail_3v3_pri", "0")
    two_pin(s, "res", 840 * SCALE, 160 * SCALE, "R49", "1000", "node_opout", "node_gate")
    two_pin(s, "res", 1000 * SCALE, 80 * SCALE, "R50", "100000", "hv80_in", "node_raw")
    two_pin(s, "diode", 1140 * SCALE, 160 * SCALE, "D8", "DCLAMP_SMCJ100A", "0", "node_raw")

    mx, my = s.symbol("nmos", 1000 * SCALE, 280 * SCALE, rot="R0", inst="Q6",
                       value="DI_MMBF170 L=100u W=100u", prefix="M")
    s.flag(mx + PIN["nmos"]["D"][0], my + PIN["nmos"]["D"][1], "node_raw")
    s.flag(mx + PIN["nmos"]["G"][0], my + PIN["nmos"]["G"][1], "node_gate")
    s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "q6_src")
    two_pin(s, "res", 1000 * SCALE, 420 * SCALE, "Rs6", f"{rs_val}", "q6_src", "0")

    qx, qy = s.symbol("nmos", 1280 * SCALE, 280 * SCALE, rot="R0", inst="Q7",
                       value="DI_MMBF170 L=100u W=100u", prefix="M")
    s.flag(qx + PIN["nmos"]["D"][0], qy + PIN["nmos"]["D"][1], "hv80_in")
    s.flag(qx + PIN["nmos"]["G"][0], qy + PIN["nmos"]["G"][1], "node_raw")
    s.flag(qx + PIN["nmos"]["S"][0], qy + PIN["nmos"]["S"][1], "hv_bias")

    s.directive(40 * SCALE, 620 * SCALE, f".tran 0 {tstop*1e3:.4f}m 0 {maxstep*1e9:.2f}n")
    s.write(out_path)
    print(f"Ecrit {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "step_final.asc"
    build(out)
