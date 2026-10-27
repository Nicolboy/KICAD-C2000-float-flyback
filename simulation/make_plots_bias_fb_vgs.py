"""Vgs(Q7) = V(node_raw, grille) - V(hv_bias, source) pendant la reponse
en echelon -- donnees reelles LTspice deja extraites (meme run que
make_plots_bias_fb_step.py)."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/bias_fb_step_timedomain.csv", encoding="utf-8")))
t = [float(r["time_s"]) * 1e6 for r in rows]
node_raw = [float(r["node_raw"]) for r in rows]
hv_bias = [float(r["hv_bias"]) for r in rows]
vgs = [a - b for a, b in zip(node_raw, hv_bias)]

fig, axs = plt.subplots(1, 3, figsize=(15, 4.5))

axs[0].plot(t, vgs, color="C2", lw=1)
axs[0].axhline(1.0, color="gray", ls=":", lw=1, label="Vth du modele (1,0V)")
axs[0].set_title("Vgs(Q7) -- vue d'ensemble")
axs[0].set_xlabel("temps (us)")
axs[0].set_ylabel("Vgs Q7 (V)")
axs[0].legend(fontsize=8)
axs[0].grid(alpha=0.3)

mask = [(tt, vv, nr, hb) for tt, vv, nr, hb in zip(t, vgs, node_raw, hv_bias) if 19.95 <= tt <= 20.5]
axs[1].plot([m[0] for m in mask], [m[1] for m in mask], color="C2", lw=1.5, marker=".", ms=3, label="Vgs = node_raw - hv_bias")
axs[1].axhline(1.0, color="gray", ls=":", lw=1, label="Vth (1,0V)")
axs[1].set_title("Montee -- Vgs(Q7)\n(negatif = Q7 bloque, follower decroche)")
axs[1].set_xlabel("temps (us)")
axs[1].set_ylabel("Vgs Q7 (V)")
axs[1].legend(fontsize=8)
axs[1].grid(alpha=0.3)

mask2 = [(tt, vv) for tt, vv in zip(t, vgs) if 169.98 <= tt <= 170.5]
axs[2].plot([m[0] for m in mask2], [m[1] for m in mask2], color="C3", lw=1.5, marker=".", ms=3)
axs[2].axhline(1.0, color="gray", ls=":", lw=1, label="Vth (1,0V)")
axs[2].set_title("Descente -- Vgs(Q7)")
axs[2].set_xlabel("temps (us)")
axs[2].set_ylabel("Vgs Q7 (V)")
axs[2].legend(fontsize=8)
axs[2].grid(alpha=0.3)

fig.suptitle("Vgs(Q7) = V(node_raw) - V(HV_BIAS) pendant l'echelon", fontsize=11)
fig.tight_layout()
fig.savefig("plots/bias_fb_q7_vgs.png", dpi=140)
print("Ecrit plots/bias_fb_q7_vgs.png")

# quelques chiffres cles
import math
peak = max(vgs)
trough = min(vgs)
print(f"Vgs max = {peak:.3f} V, Vgs min = {trough:.3f} V")
