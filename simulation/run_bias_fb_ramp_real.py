"""Lance la rampe quasi-statique composants reels (gen_bias_fb_ramp_real),
parse le .raw ASCII, ecrit un CSV temps + toutes les variables."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_bias_fb_ramp_real import build

LTSPICE = r"C:/Program Files/ADI/LTspice/LTspice.exe"


def parse_ascii_raw(raw_path):
    with open(raw_path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    nvars = npoints = None
    varnames = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("No. Variables:"):
            nvars = int(line.split(":")[1].strip())
        elif line.startswith("No. Points:"):
            npoints = int(line.split(":")[1].strip())
        elif line.startswith("Variables:"):
            i += 1
            for _ in range(nvars):
                parts = lines[i].split("\t")
                parts = [p for p in parts if p.strip() != ""]
                varnames.append(parts[1])
                i += 1
            continue
        elif line.startswith("Values:"):
            i += 1
            break
        i += 1

    data = {name: [] for name in varnames}
    for _ in range(npoints):
        first = lines[i].split("\t")
        first = [p for p in first if p.strip() != ""]
        data[varnames[0]].append(float(first[1]))
        i += 1
        for v in range(1, nvars):
            val = float(lines[i].strip())
            data[varnames[v]].append(val)
            i += 1
    return varnames, data


if __name__ == "__main__":
    import csv
    out = sys.argv[1] if len(sys.argv) > 1 else "results/bias_fb_ramp_real.asc"
    csv_out = sys.argv[2] if len(sys.argv) > 2 else "results/bias_fb_ramp_real_timedomain.csv"
    build(out)
    proc = subprocess.run([LTSPICE, "-b", "-ascii", out], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True)
    log_path = out.replace(".asc", ".log")
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        print(f.read())

    raw_path = out.replace(".asc", ".raw")
    varnames, data = parse_ascii_raw(raw_path)
    print("Variables:", varnames)
    wanted = [v for v in varnames if v.lower() in
              ("time", "v(vargate)", "v(hv_bias)", "v(node_raw)", "v(node_opout)")]
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time_s" if v.lower() == "time" else v for v in wanted])
        n = len(data[wanted[0]])
        for i in range(n):
            w.writerow([data[v][i] for v in wanted])
    print(f"Ecrit {csv_out} ({n} lignes)")
