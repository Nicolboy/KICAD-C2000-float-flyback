"""Comparaison des 4 scenarios de compensation -- donnees reelles LTspice."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path, tcol="time_s", tscale=1e6):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return ([float(r[tcol]) * tscale for r in rows],
            [float(r["hv_bias"]) for r in rows])

fig, axs = plt.subplots(2, 2, figsize=(12, 8))

t, vb = load("results/bias_fb_step_timedomain.csv", tscale=1e6)
m = [(tt, vv) for tt, vv in zip(t, vb) if 199.5 <= tt <= 205]
axs[0, 0].plot([x[0] - 200 for x in m], [x[1] for x in m], color="C3", lw=1.5)
axs[0, 0].axhline(65.945, color="gray", ls="--", lw=1)
axs[0, 0].set_title("SANS compensation\ndepasse 80,9V puis 0V, stabilise en ~0,1us", fontsize=10)
axs[0, 0].set_xlabel("temps depuis l'echelon (us)")
axs[0, 0].set_ylabel("HV_BIAS (V)")
axs[0, 0].grid(alpha=0.3)

t, vb = load("results/bias_fb_step_10nF_long_downsampled.csv", tscale=1e3)
m = [(tt, vv) for tt, vv in zip(t, vb) if 0.5 <= tt <= 6]
axs[0, 1].plot([x[0] - 0.5 for x in m], [x[1] for x in m], color="C1", lw=1.5)
axs[0, 1].axhline(65.945, color="gray", ls="--", lw=1)
axs[0, 1].set_title("10nF grille(Q7)-masse SEUL\naucun depassement, ~2ms pour se stabiliser", fontsize=10)
axs[0, 1].set_xlabel("temps depuis l'echelon (ms)")
axs[0, 1].set_ylabel("HV_BIAS (V)")
axs[0, 1].grid(alpha=0.3)

t, vb = load("results/bias_fb_step_cout_only_timedomain.csv", tscale=1e3)
m = [(tt, vv) for tt, vv in zip(t, vb) if 0.19 <= tt <= 20]
axs[1, 0].plot([x[0] - 0.2 for x in m], [x[1] for x in m], color="C0", lw=1.5)
axs[1, 0].axhline(65.945, color="gray", ls="--", lw=1, label="valeur etablie")
axs[1, 0].set_title("100nF en SORTIE (HV_BIAS) SEUL\naucun depassement, saut propre a 72V puis decroissance douce", fontsize=10)
axs[1, 0].set_xlabel("temps depuis l'echelon (ms)")
axs[1, 0].set_ylabel("HV_BIAS (V)")
axs[1, 0].legend(fontsize=8)
axs[1, 0].grid(alpha=0.3)

t, vb = load("results/bias_fb_step_both_timedomain.csv", tscale=1e3)
m = [(tt, vv) for tt, vv in zip(t, vb) if 0.19 <= tt <= 20]
axs[1, 1].plot([x[0] - 0.2 for x in m], [x[1] for x in m], color="C2", lw=1.5)
axs[1, 1].axhline(65.945, color="gray", ls="--", lw=1)
axs[1, 1].set_title("10nF grille + 100nF sortie ENSEMBLE\naucun depassement, leger ondulement avant stabilisation", fontsize=10)
axs[1, 1].set_xlabel("temps depuis l'echelon (ms)")
axs[1, 1].set_ylabel("HV_BIAS (V)")
axs[1, 1].grid(alpha=0.3)

fig.suptitle("Comparaison des options de compensation -- echelon VAR_GATE 0,5V->2,5V", fontsize=12)
fig.tight_layout()
fig.savefig("plots/bias_fb_comp_4ways.png", dpi=140)
print("Ecrit plots/bias_fb_comp_4ways.png")
