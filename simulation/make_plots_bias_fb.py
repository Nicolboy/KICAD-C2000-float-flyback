"""Figure de la nouvelle architecture de linearisation HV_BIAS (mesure
par pont R52/R53, Q6 source directe au GND, polarite IN+/IN- corrigee)
a partir de results/bias_fb_final.csv (donnees reelles LTspice)."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/bias_fb_final.csv", encoding="utf-8")))
vg = [float(r["vargate_v"]) for r in rows]
vb = [float(r["hv_bias_v"]) for r in rows]
ideal = [80 / 3 * v if v <= 3.0 else None for v in vg]

fig, ax = plt.subplots(figsize=(9, 6))
ax.plot(vg, vb, color="C0", lw=2, label="V(HV_BIAS) simule (LTspice, modeles generiques)")
ax.plot([v for v in vg if v <= 3.0], [80 / 3 * v for v in vg if v <= 3.0],
        color="gray", ls="--", lw=1, label="Droite ideale 0V->0V, 3V->80V")
ax.axvline(3.0, color="gray", ls=":", lw=1, alpha=0.6)
ax.annotate("VAR_GATE=3,0V\nHV_BIAS=78,6V (-1,76%)",
            (3.0, 78.6), xytext=(1.6, 65), fontsize=9,
            arrowprops=dict(arrowstyle="->", alpha=0.6))
ax.set_xlabel("VAR_GATE (V)")
ax.set_ylabel("HV_BIAS (V)")
ax.set_title("Linearisation HV_BIAS -- mesure par pont R52/R53, Q6 source->GND directe\n"
             "R47=1k R48=100k R52=220k R53=5,6M -- IN-=commande, IN+=mesure",
             fontsize=11)
ax.set_xlim(0, 3.3)
ax.set_ylim(-3, 85)
ax.grid(alpha=0.3)
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig("plots/bias_fb_transfer.png", dpi=140)
print("Ecrit plots/bias_fb_transfer.png")
