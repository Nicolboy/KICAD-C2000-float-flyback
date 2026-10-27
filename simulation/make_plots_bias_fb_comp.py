"""Comparaison reponse en echelon sans/avec condensateur 10nF grille-masse
sur Q7 -- donnees reelles LTspice, deux echelles de temps (la version
compensee est ~1000x plus lente, meme echelle serait illisible)."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return rows

rows_nocomp = load("results/bias_fb_step_timedomain.csv")
rows_comp = load("results/bias_fb_step_10nF_long_downsampled.csv")

t1 = [float(r["time_s"]) * 1e6 for r in rows_nocomp]
vb1 = [float(r["hv_bias"]) for r in rows_nocomp]

t2 = [float(r["time_s"]) * 1e3 for r in rows_comp]  # en ms
vb2 = [float(r["hv_bias"]) for r in rows_comp]

fig, axs = plt.subplots(1, 2, figsize=(13, 5))

mask1 = [(tt, vv) for tt, vv in zip(t1, vb1) if 19.95 <= tt <= 20.5]
axs[0].plot([m[0] for m in mask1], [m[1] for m in mask1], color="C3", lw=1.5, marker=".", ms=3)
axs[0].axhline(65.945, color="gray", ls="--", lw=1)
axs[0].set_title("SANS compensation -- echelle microseconde\nstabilise en ~0,1us, mais depasse 80,9V puis 0V",
                  fontsize=10)
axs[0].set_xlabel("temps (us)")
axs[0].set_ylabel("HV_BIAS (V)")
axs[0].grid(alpha=0.3)

mask2 = [(tt, vv) for tt, vv in zip(t2, vb2) if 0.5 <= tt <= 6.0]
axs[1].plot([m[0] for m in mask2], [m[1] for m in mask2], color="C0", lw=1.5)
axs[1].axhline(65.945, color="gray", ls="--", lw=1, label="valeur etablie (65,9V)")
axs[1].set_title("AVEC 10nF grille-masse -- echelle MILLISECONDE\naucun depassement, mais ~5ms pour se stabiliser",
                  fontsize=10)
axs[1].set_xlabel("temps (ms)")
axs[1].set_ylabel("HV_BIAS (V)")
axs[1].legend(fontsize=8)
axs[1].grid(alpha=0.3)

fig.suptitle("Effet du condensateur 10nF (grille Q7 -> GND) sur la reponse en echelon -- "
             "note l'echelle de temps x1000 entre les deux panneaux", fontsize=11)
fig.tight_layout()
fig.savefig("plots/bias_fb_comp_tradeoff.png", dpi=140)
print("Ecrit plots/bias_fb_comp_tradeoff.png")
