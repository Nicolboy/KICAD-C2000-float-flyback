"""Figures 18,9W (doc/sim-vs-mesure.md Sec.7) a partir de
results/envelope_18w9_schottky.csv et envelope_18w9_sync.csv -- donnees
reelles, pas de valeurs inventees. Meme style que make_plots.py (etape 4,
10W), pour comparaison directe."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sch = {r["label"]: r for r in csv.DictReader(open("results/envelope_18w9_schottky.csv", encoding="utf-8"))}
sync = {r["label"]: r for r in csv.DictReader(open("results/envelope_18w9_sync.csv", encoding="utf-8"))}

labels_63 = ["11V_6V3", "20V_6V3", "25V_6V3"]
labels_126 = ["11V_12V6", "20V_12V6", "25V_12V6"]

fig, axs = plt.subplots(1, 2, figsize=(12, 5))

for labels, marker, color, name in [(labels_63, "o", "C0", "6,3V"), (labels_126, "s", "C1", "12,6V")]:
    vins = [float(sync[l]["vin"]) for l in labels]
    eta_sch = [float(sch[l]["eta_pct"]) for l in labels]
    eta_sync = [float(sync[l]["eta_pct"]) for l in labels]
    vds_sch = [float(sch[l]["vds_q2_max"]) for l in labels]
    vds_sync = [float(sync[l]["vds_q2_max"]) for l in labels]
    axs[0].plot(vins, eta_sch, marker=marker, color=color, ls="--", alpha=0.5,
                label=f"Vout={name}, Schottky ideal")
    axs[0].plot(vins, eta_sync, marker=marker, color=color,
                label=f"Vout={name}, reel+synchrone")
    axs[1].plot(vins, vds_sch, marker=marker, color=color, ls="--", alpha=0.5,
                label=f"Vout={name}, Schottky ideal")
    axs[1].plot(vins, vds_sync, marker=marker, color=color,
                label=f"Vout={name}, reel+synchrone")

axs[0].set_xlabel("Vin (V)")
axs[0].set_ylabel("Rendement (%)")
axs[0].set_title("Rendement vs Vin -- 18,9W, Schottky vs reel+synchrone (UCC24612)")
axs[0].legend(fontsize=8)
axs[0].grid(alpha=0.3)

axs[1].axhline(100, color="red", ls="-", lw=1.5, label="Vds max Q2 (100V, IPD050N10N5)")
axs[1].set_xlabel("Vin (V)")
axs[1].set_ylabel("Vds max Q2 pendant la résonance (V)")
axs[1].set_title("Contrainte tension secondaire -- 18,9W, sans clamp")
axs[1].legend(fontsize=8)
axs[1].grid(alpha=0.3)

fig.tight_layout()
fig.savefig("plots/envelope_eta_vds_18w9.png", dpi=140)
print("Ecrit plots/envelope_eta_vds_18w9.png")
