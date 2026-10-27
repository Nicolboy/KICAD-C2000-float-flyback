"""Figure topologie avec Q7 + R52 corrige (39k) -- donnees reelles LTspice."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/bias_fb_with_q7_r52_39k.csv", encoding="utf-8")))
vg = [float(r["vargate_v"]) for r in rows]
vb = [float(r["hv_bias_v"]) for r in rows]

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(vg, vb, color="C0", lw=2, label="V(HV_BIAS) simule (Q7 + R52=39k)")
ax.plot([v for v in vg if v <= 3.0], [80 / 3 * v for v in vg if v <= 3.0],
        color="gray", ls="--", lw=1, label="Droite ideale 0->0V, 3V->80V")
ax.axvline(3.0, color="gray", ls=":", lw=1, alpha=0.6)
ax.annotate("3,0V -> 78,9V (-1,32%)", (3.0, 78.9), xytext=(1.7, 68),
            fontsize=9, arrowprops=dict(arrowstyle="->", alpha=0.6))
ax.set_xlabel("VAR_GATE (V)")
ax.set_ylabel("HV_BIAS (V)")
ax.set_title("Q7 (source-follower) + R52=39k (E12, etait 33k) -- R47=1k R48=100k R53=1M\n"
             "Lineaire sur toute la plage, ecart < 1,4% partout", fontsize=10)
ax.set_xlim(0, 3.3)
ax.set_ylim(-3, 85)
ax.grid(alpha=0.3)
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig("plots/bias_fb_q7_fixed_transfer.png", dpi=140)
print("Ecrit plots/bias_fb_q7_fixed_transfer.png")
