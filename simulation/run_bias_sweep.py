"""Genere le banc de linearisation HV_BIAS, le lance dans LTspice (mode
batch), affiche la courbe de transfert VAR_GATE -> HV_BIAS extraite des
.meas DC FIND...WHEN du .log (meme methode de parsing que run_point.py,
pas de lecture de .raw -- "simple d'abord")."""
import subprocess
import sys

sys.path.insert(0, ".")
from gen_bias_lin import build

LTSPICE = r"C:/Program Files/ADI/LTspice/LTspice.exe"


def run(out="bias_lin.asc", **kwargs):
    build(0.0, 3.0, 0.01, out, **kwargs)
    proc = subprocess.run([LTSPICE, "-b", out], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True)
    log_path = out.replace(".asc", ".log")
    results = {}
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        log_text = f.read()
    for line in log_text.splitlines():
        if ":" in line and "=" in line.split(":", 1)[1]:
            name, rest = line.split(":", 1)
            if not name.strip().replace("_", "").replace(".", "").isalnum():
                continue
            try:
                val = float(rest.split("=")[-1].split()[0])
                results[name.strip()] = val
            except (IndexError, ValueError):
                pass
    return results, log_text


if __name__ == "__main__":
    import csv
    out = sys.argv[1] if len(sys.argv) > 1 else "bias_lin.asc"
    csv_out = sys.argv[2] if len(sys.argv) > 2 else "results/bias_lin.csv"
    results, log_text = run(out)
    points = sorted(
        ((float(k.split("_at_")[1]), v) for k, v in results.items()
         if k.lower().startswith("vbias_at_")),
        key=lambda t: t[0])
    if not points:
        print("Aucun point Vbias_at_* trouve -- log LTspice complet :")
        print(log_text)
    else:
        print(f"{'VAR_GATE (V)':>14} {'HV_BIAS (V)':>14}")
        for vg, vb in points:
            print(f"{vg:14.2f} {vb:14.3f}")
        with open(csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["vargate_v", "hv_bias_v"])
            for vg, vb in points:
                w.writerow([f"{vg:.3f}", f"{vb:.6f}"])
        print(f"Ecrit {csv_out}")
