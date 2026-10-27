"""Figure topologie avec Q7 (source-follower) -- donnees reelles LTspice."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/bias_fb_with_q7.csv", encoding="utf-8")))
vg = [float(r["vargate_v"]) for r in rows]
vb = [float(r["hv_bias_v"]) for r in rows]

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(vg, vb, color="C0", lw=2, label="V(HV_BIAS) simule (avec Q7)")
ax.plot([v for v in vg if v <= 3.0], [80 / 3 * v for v in vg if v <= 3.0],
        color="gray", ls="--", lw=1, label="Droite ideale 0->0V, 3V->80V")
ax.axvline(3.0, color="gray", ls=":", lw=1, alpha=0.6)
ax.set_xlabel("VAR_GATE (V)")
ax.set_ylabel("HV_BIAS (V)")
ax.set_title("Avec Q7 (source-follower) -- R47=1k R48=100k R52=33k R53=1M\n"
             "Plafond ameliore (78,9V) MAIS pente trop raide : jusqu'a +13,7% au milieu",
             fontsize=10)
ax.set_xlim(0, 3.3)
ax.set_ylim(-3, 85)
ax.grid(alpha=0.3)
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig("plots/bias_fb_q7_transfer.png", dpi=140)
print("Ecrit plots/bias_fb_q7_transfer.png")
