"""Banc de validation du proxy BSS127I.lib -- verifie que le modele
PARSE/CONVERGE et que l'algebre de derivation (voir commentaires du
.lib) est bien reproduite par le simulateur : ID=0 sous VTO, ID=10mA au
point de calibration gfs, ID~22,5mA a VGS=4V (coherent avec le coin
superieur droit du graphe 7 de la datasheet, ~25mA). Teste aussi la
diode de corps en direct (VSD a IF=16mA, cible 0,82V typ datasheet
p.3)."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402

LTSPICE = r"C:/Program Files/ADI/LTspice/LTspice.exe"
HERE = os.path.dirname(os.path.abspath(__file__))


def build_transfer(out_path):
    s = Sheet()
    s.comment(40, 20, "Validation BSS127I.lib -- ID=f(VGS) a VDS=10V fixe.")
    lib_path = os.path.join(HERE, "models", "BSS127I.lib").replace("\\", "/")
    s.directive(40, 500, f'.lib "{lib_path}"')

    two_pin(s, "voltage", 80, 120, "Vgs", "0", "vgs", "0")
    two_pin(s, "voltage", 80, 340, "Vds", "10", "vds", "0")

    mx, my = s.symbol("nmos", 400, 160, rot="R0", inst="Q1",
                       value="MBSS127I", prefix="X")
    s.flag(mx + _BASE_PIN["nmos"]["D"][0], my + _BASE_PIN["nmos"]["D"][1], "vds")
    s.flag(mx + _BASE_PIN["nmos"]["G"][0], my + _BASE_PIN["nmos"]["G"][1], "vgs")
    s.flag(mx + _BASE_PIN["nmos"]["S"][0], my + _BASE_PIN["nmos"]["S"][1], "0")

    s.directive(40, 560, ".dc Vgs 0 4.5 0.01")
    for vg in (2.0, 3.333, 4.0):
        s.directive(40, 580 + int(vg * 20),
                    f".meas DC Id_at_{vg:.3f} FIND I(Vds) AT {vg}")

    s.write(out_path)
    print(f"Ecrit {out_path}")


def build_diode(out_path):
    """Diode de corps en direct : VGS fortement negatif (canal bloque),
    VDS balaye en negatif -- le courant qui circule est alors uniquement
    celui de Dbody (S->D en direct). Cible : I(Vds) ~ -16mA quand
    V(vds) ~ -0,82V (VSD typ datasheet p.3)."""
    s = Sheet()
    s.comment(40, 20, "Validation diode de corps BSS127I.lib -- I=f(VDS<0), VGS=-5V (bloque).")
    lib_path = os.path.join(HERE, "models", "BSS127I.lib").replace("\\", "/")
    s.directive(40, 500, f'.lib "{lib_path}"')

    two_pin(s, "voltage", 80, 120, "Vgs", "-5", "vgs", "0")
    two_pin(s, "voltage", 80, 340, "Vds", "0", "vds", "0")

    mx, my = s.symbol("nmos", 400, 160, rot="R0", inst="Q1",
                       value="MBSS127I", prefix="X")
    s.flag(mx + _BASE_PIN["nmos"]["D"][0], my + _BASE_PIN["nmos"]["D"][1], "vds")
    s.flag(mx + _BASE_PIN["nmos"]["G"][0], my + _BASE_PIN["nmos"]["G"][1], "vgs")
    s.flag(mx + _BASE_PIN["nmos"]["S"][0], my + _BASE_PIN["nmos"]["S"][1], "0")

    s.directive(40, 560, ".dc Vds 0 -1.2 -0.001")
    s.directive(40, 580, ".meas DC I_at_m0p82 FIND I(Vds) AT -0.82")

    s.write(out_path)
    print(f"Ecrit {out_path}")


def run(out_path):
    proc = subprocess.run([LTSPICE, "-b", out_path], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True)
    log_path = out_path.replace(".asc", ".log")
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        return f.read()


if __name__ == "__main__":
    build_transfer("results/validate_bss127i_transfer.asc")
    print(run("results/validate_bss127i_transfer.asc"))
    build_diode("results/validate_bss127i_diode.asc")
    print(run("results/validate_bss127i_diode.asc"))
