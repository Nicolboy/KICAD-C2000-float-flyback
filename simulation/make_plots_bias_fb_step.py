"""Reponse en echelon de la boucle HV_BIAS, montee et descente --
donnees reelles LTspice (transitoire, modeles generiques)."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/bias_fb_step_timedomain.csv", encoding="utf-8")))
t = [float(r["time_s"]) * 1e6 for r in rows]  # en us
vg = [float(r["vargate"]) for r in rows]
vb = [float(r["hv_bias"]) for r in rows]

fig, axs = plt.subplots(2, 2, figsize=(12, 8))

# --- Vue d'ensemble ---
axs[0, 0].plot(t, vg, color="C1", lw=1.2)
axs[0, 0].set_title("VAR_GATE (echelon)")
axs[0, 0].set_xlabel("temps (us)")
axs[0, 0].set_ylabel("VAR_GATE (V)")
axs[0, 0].grid(alpha=0.3)

axs[0, 1].plot(t, vb, color="C0", lw=1.2)
axs[0, 1].set_title("HV_BIAS -- vue d'ensemble")
axs[0, 1].set_xlabel("temps (us)")
axs[0, 1].set_ylabel("HV_BIAS (V)")
axs[0, 1].grid(alpha=0.3)

# --- Zoom montee (0.5V->2.5V a t=20us) ---
mask = [(tt, vv) for tt, vv in zip(t, vb) if 19.95 <= tt <= 20.5]
axs[1, 0].plot([m[0] for m in mask], [m[1] for m in mask], color="C0", lw=1.5, marker=".", ms=3)
axs[1, 0].axhline(65.945, color="gray", ls="--", lw=1, label="valeur etablie (65,9V)")
axs[1, 0].set_title("Montee 0,5V->2,5V : depassement ~80,9V, sous-oscillation\navant stabilisation (~10us)")
axs[1, 0].set_xlabel("temps (us)")
axs[1, 0].set_ylabel("HV_BIAS (V)")
axs[1, 0].legend(fontsize=8)
axs[1, 0].grid(alpha=0.3)

# --- Zoom descente (2.5V->0.5V a t=170us) ---
mask2 = [(tt, vv) for tt, vv in zip(t, vb) if 169.98 <= tt <= 170.5]
axs[1, 1].plot([m[0] for m in mask2], [m[1] for m in mask2], color="C3", lw=1.5, marker=".", ms=3)
axs[1, 1].axhline(13.18, color="gray", ls="--", lw=1, label="valeur etablie (13,2V)")
axs[1, 1].set_title("Descente 2,5V->0,5V : meme comportement,\namplitude plus faible")
axs[1, 1].set_xlabel("temps (us)")
axs[1, 1].set_ylabel("HV_BIAS (V)")
axs[1, 1].legend(fontsize=8)
axs[1, 1].grid(alpha=0.3)

fig.suptitle("Reponse en echelon, boucle complete (Q6+Q7+U21), modeles generiques -- "
             "oscillation amortie, PAS soutenue", fontsize=11)
fig.tight_layout()
fig.savefig("plots/bias_fb_step_response.png", dpi=140)
print("Ecrit plots/bias_fb_step_response.png")
