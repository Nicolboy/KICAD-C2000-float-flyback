"""Banc de validation minimal du modele MCP6001.lib corrige (voir
header de ce fichier pour le detail des corrections de syntaxe) --
suiveur unity-gain, alimentation unique 0-3,3V (RRIO), entree en
echelon 0,3V->2,8V. Objectif : verifier que le modele PARSE et
CONVERGE dans LTspice (pas d'erreur "time step too small" / singularite
-- probleme connu du fichier vendeur brut, cf. commentaires
MCP6001.lib), et que la sortie suit l'entree en gain unitaire avant
d'integrer le modele dans le banc HV_BIAS complet."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402

LTSPICE = r"C:/Program Files/ADI/LTspice/LTspice.exe"
HERE = os.path.dirname(os.path.abspath(__file__))

PIN = dict(_BASE_PIN)
# Symbole generique LTspice lib/sym/OpAmps/opamp2.asy (Prefix=X, Value a
# renseigner = nom du sous-circuit a instancier -- PAS UniversalOpAmp2,
# qui est un primitif comportemental LTspice a parametres fixes
# [Avol/GBW/Slew/...], incompatible avec la substitution d'un sous-circuit
# externe comme MCP6001). Offsets de pattes lus directement dans ce .asy.
PIN["opamp2"] = {
    "IN+": (-32, 80), "IN-": (-32, 48),
    "V+": (0, 32), "V-": (0, 96), "OUT": (32, 64),
}


def build(out_path):
    s = Sheet()
    s.comment(40, 20,
              "Validation MCP6001.lib (corrige) -- suiveur unity-gain, "
              "rail unique 0-3,3V, echelon 0,3V->2,8V.")
    lib_path = os.path.join(HERE, "models", "MCP6001.lib").replace("\\", "/")
    s.directive(40, 500, f'.lib "{lib_path}"')

    two_pin(s, "voltage", 80, 120, "Vin", "PULSE(0.3 2.8 10u 1u 1u 200u 400u)",
            "vin", "0")
    two_pin(s, "voltage", 80, 340, "Vdd", "3.3", "rail_3v3", "0")

    ox, oy = s.symbol("opamp2", 400, 160, rot="R0", inst="U1", value="MCP6001")
    s.flag(ox + PIN["opamp2"]["IN+"][0], oy + PIN["opamp2"]["IN+"][1], "vin")
    s.flag(ox + PIN["opamp2"]["IN-"][0], oy + PIN["opamp2"]["IN-"][1], "vout")
    s.flag(ox + PIN["opamp2"]["V+"][0], oy + PIN["opamp2"]["V+"][1], "rail_3v3")
    s.flag(ox + PIN["opamp2"]["V-"][0], oy + PIN["opamp2"]["V-"][1], "0")
    s.flag(ox + PIN["opamp2"]["OUT"][0], oy + PIN["opamp2"]["OUT"][1], "vout")

    two_pin(s, "res", 600, 300, "Rload", "10k", "vout", "0")

    s.directive(40, 560, ".tran 0 400u 0 50n")
    s.directive(40, 600, ".meas TRAN Vout_at_300u FIND V(vout) AT 300u")
    s.directive(40, 620, ".meas TRAN Vin_at_300u FIND V(vin) AT 300u")
    s.directive(40, 640, ".meas TRAN Vout_at_100u FIND V(vout) AT 100u")
    s.directive(40, 660, ".meas TRAN Vin_at_100u FIND V(vin) AT 100u")
    s.directive(40, 680, ".meas TRAN Vout_at_50u FIND V(vout) AT 50u")
    s.directive(40, 700, ".meas TRAN Vout_max MAX V(vout) FROM 0 TO 400u")
    s.directive(40, 720, ".meas TRAN Vout_min MIN V(vout) FROM 0 TO 400u")

    s.write(out_path)
    print(f"Ecrit {out_path}")


if __name__ == "__main__":
    out = "results/validate_mcp6001.asc"
    build(out)
    proc = subprocess.run([LTSPICE, "-b", out], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True)
    log_path = out.replace(".asc", ".log")
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        log_text = f.read()
    print(log_text)
    bad = [kw for kw in ("time step too small", "singular", "did not converge",
                          "Simulation interrupted")
           if kw.lower() in log_text.lower()]
    print("PROBLEMES DETECTES:" if bad else "Aucune erreur de convergence detectee.", bad)
