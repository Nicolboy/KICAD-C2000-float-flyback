"""Lance le banc HV_BIAS a composants reels (MCP6001 + BSS127I) en mode
batch LTspice, parse les .meas DC Vbias_at_*/Vopout_at_* du .log, ecrit
le CSV -- meme methode que run_bias_sweep.py."""
import subprocess
import sys

sys.path.insert(0, ".")
from gen_bias_fb_real import build

LTSPICE = r"C:/Program Files/ADI/LTspice/LTspice.exe"


def run(out="results/bias_fb_real.asc", **kwargs):
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
    out = sys.argv[1] if len(sys.argv) > 1 else "results/bias_fb_real.asc"
    csv_out = sys.argv[2] if len(sys.argv) > 2 else "results/bias_fb_real.csv"
    results, log_text = run(out)
    bias_pts = sorted(
        ((float(k.split("_at_")[1]), v) for k, v in results.items()
         if k.lower().startswith("vbias_at_")), key=lambda t: t[0])
    opout_pts = dict(
        (round(float(k.split("_at_")[1]), 2), v) for k, v in results.items()
        if k.lower().startswith("vopout_at_"))
    if not bias_pts:
        print("Aucun point Vbias_at_* trouve -- log LTspice complet :")
        print(log_text)
    else:
        print(f"{'VAR_GATE (V)':>14} {'HV_BIAS (V)':>14} {'OPOUT (V)':>12}")
        for vg, vb in bias_pts:
            print(f"{vg:14.2f} {vb:14.3f} {opout_pts.get(round(vg,2), float('nan')):12.3f}")
        with open(csv_out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["vargate_v", "hv_bias_v", "opout_v"])
            for vg, vb in bias_pts:
                w.writerow([f"{vg:.3f}", f"{vb:.6f}",
                            f"{opout_pts.get(round(vg,2), float('nan')):.6f}"])
        print(f"Ecrit {csv_out}")
