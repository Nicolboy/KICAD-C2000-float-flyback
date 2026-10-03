"""Genere un point de fonctionnement, le lance dans LTspice (mode batch),
affiche les resultats .meas. Usage :
    python run_point.py <Vin> <Vout_cible> <D> <Rload> [out.asc] [settle_periods]
"""
import subprocess
import sys

sys.path.insert(0, ".")
from gen_asc import build

LTSPICE = r"C:/Program Files/ADI/LTspice/LTspice.exe"
T = 1 / 200e3


def run(vin, vout_target, d, rload, out="point.asc", settle_periods=4000,
        measure_periods=100, pout=10.0):
    build("point", vin, vout_target, pout, d, 100e-9, T, out, rload=rload,
          settle_periods=settle_periods, measure_periods=measure_periods)
    subprocess.run([LTSPICE, "-b", out], stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
    log_path = out.replace(".asc", ".log")
    results = {}
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            # lignes .meas : "nom: EXPR=valeur [FROM x TO y | at t]"
            if ":" in line and "=" in line.split(":", 1)[1]:
                name, rest = line.split(":", 1)
                if not name.strip().replace("_", "").isalnum():
                    continue
                try:
                    val = float(rest.split("=")[-1].split()[0])
                    results[name.strip()] = val
                except (IndexError, ValueError):
                    pass
    return results


if __name__ == "__main__":
    vin = float(sys.argv[1])
    vout_t = float(sys.argv[2])
    d = float(sys.argv[3])
    rload = float(sys.argv[4])
    out = sys.argv[5] if len(sys.argv) > 5 else "point.asc"
    settle = int(sys.argv[6]) if len(sys.argv) > 6 else 4000
    r = run(vin, vout_t, d, rload, out, settle_periods=settle)
    for k, v in r.items():
        print(f"{k} = {v:.6g}")
