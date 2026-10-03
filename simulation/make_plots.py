"""Figures de l'etape 4 a partir de results/envelope.csv (donnees reelles,
pas de valeurs inventees)."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/envelope.csv", encoding="utf-8")))
for r in rows:
    for k in r:
        if k not in ("label", "mode"):
            r[k] = float(r[k])

fig, axs = plt.subplots(1, 2, figsize=(12, 5))

for target, marker, color in [(6.0, "o", "C0"), (12.0, "s", "C1")]:
    pts = [r for r in rows if r["vout_target"] == target and r["rload"] != 36.0]
    pts.sort(key=lambda r: r["vin"])
    axs[0].plot([r["vin"] for r in pts], [r["eta_pct"] for r in pts],
                marker=marker, color=color, label=f"Vout cible={target:g}V")
    axs[1].plot([r["vin"] for r in pts], [r["vds_q2_max"] for r in pts],
                marker=marker, color=color, label=f"Vout cible={target:g}V")
    for r in pts:
        axs[0].annotate(r["mode"], (r["vin"], r["eta_pct"]), fontsize=8,
                         xytext=(4, 4), textcoords="offset points")

axs[0].set_xlabel("Vin (V)")
axs[0].set_ylabel("Rendement (%)")
axs[0].set_title("Rendement vs Vin (mode de conduction annote)")
axs[0].legend()
axs[0].grid(alpha=0.3)

axs[1].axhline(100, color="red", ls="--", lw=1.5, label="Vds max Q2 (100V, IPD050N10N5)")
axs[1].set_xlabel("Vin (V)")
axs[1].set_ylabel("Vds max Q2 pendant l'anneau (V)")
axs[1].set_title("Contrainte tension secondaire -- pas de clamp cote secondaire")
axs[1].legend()
axs[1].grid(alpha=0.3)

fig.tight_layout()
fig.savefig("plots/envelope_eta_vds.png", dpi=140)
print("Ecrit plots/envelope_eta_vds.png")
