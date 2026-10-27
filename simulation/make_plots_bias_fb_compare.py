"""Comparaison tel-que-dessine vs polarite corrigee, memes valeurs R
(R47=1k R48=100k R52=33k R53=1M) -- donnees reelles LTspice."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return ([float(r["vargate_v"]) for r in rows],
            [float(r["hv_bias_v"]) for r in rows])

vg1, vb1 = load("results/bias_fb_asdrawn_full.csv")
vg2, vb2 = load("results/bias_fb_swapped_newvals_full.csv")

fig, axs = plt.subplots(1, 2, figsize=(13, 5.5))

axs[0].plot(vg1, vb1, color="C3", lw=2)
axs[0].set_title("Tel que dessine (IN+=commande, IN-=mesure)\n"
                  "-> bistable, PAS un regulateur lineaire", fontsize=10)
axs[0].set_xlabel("VAR_GATE (V)")
axs[0].set_ylabel("HV_BIAS (V)")
axs[0].set_xlim(0, 3.3)
axs[0].set_ylim(-3, 85)
axs[0].grid(alpha=0.3)

axs[1].plot(vg2, vb2, color="C0", lw=2)
ideal = [80 / 3 * v if v <= 3.0 else None for v in vg2]
axs[1].plot([v for v in vg2 if v <= 3.0], [80 / 3 * v for v in vg2 if v <= 3.0],
            color="gray", ls="--", lw=1, label="Droite ideale 0->0V, 3V->80V")
axs[1].set_title("Polarite corrigee (IN-=commande, IN+=mesure)\n"
                  "-> lineaire, plafonne a 72,9V (ceiling du pont)", fontsize=10)
axs[1].set_xlabel("VAR_GATE (V)")
axs[1].set_ylabel("HV_BIAS (V)")
axs[1].set_xlim(0, 3.3)
axs[1].set_ylim(-3, 85)
axs[1].legend(fontsize=8)
axs[1].grid(alpha=0.3)

fig.suptitle("R47=1k R48=100k R52=33k R53=1M -- memes valeurs, polarite differente",
             fontsize=11)
fig.tight_layout()
fig.savefig("plots/bias_fb_compare_polarity.png", dpi=140)
print("Ecrit plots/bias_fb_compare_polarity.png")
