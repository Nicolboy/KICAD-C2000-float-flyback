"""Comparaison modele diode de corps (reel, lent) vs Schottky generique
(simplifie, rapide) -- rendement et perte dans le clamp D1."""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

real = {r["label"]: r for r in csv.DictReader(open("results/envelope.csv", encoding="utf-8"))}
sch = {r["label"]: r for r in csv.DictReader(open("results/envelope_schottky.csv", encoding="utf-8"))}

labels = ["11V_6V", "11V_12V", "20V_6V", "20V_12V", "25V_6V", "25V_12V", "20V_6V_light"]
vins = [float(real[l]["vin"]) for l in labels]

fig, axs = plt.subplots(1, 2, figsize=(13, 5))

eta_real = [float(real[l]["eta_pct"]) for l in labels]
eta_sch = [float(sch[l]["eta_pct"]) for l in labels]
x = range(len(labels))
axs[0].bar([i - 0.2 for i in x], eta_real, width=0.4, label="Diode de corps (reel, lent)", color="C0")
axs[0].bar([i + 0.2 for i in x], eta_sch, width=0.4, label="Schottky generique (simplifie, rapide)", color="C1")
axs[0].set_xticks(list(x))
axs[0].set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
axs[0].set_ylabel("Rendement (%)")
axs[0].set_title("Rendement : modele reel vs simplifie")
axs[0].legend(fontsize=9)
axs[0].grid(alpha=0.3, axis="y")

d1_loss = [float(sch[l]["ploss_d1"]) * 1000 for l in labels]
axs[1].bar(x, d1_loss, color="C3")
axs[1].set_xticks(list(x))
axs[1].set_xticklabels(labels, rotation=40, ha="right", fontsize=8)
axs[1].set_ylabel("Perte dans D1 (clamp) [mW]")
axs[1].set_title("Perte clamp D1 (SMCJ43A reel) -- P_av datasheet = 5W")
axs[1].grid(alpha=0.3, axis="y")

fig.tight_layout()
fig.savefig("plots/compare_real_vs_schottky.png", dpi=140)
print("Ecrit plots/compare_real_vs_schottky.png")
