"""Suite du §7 (doc/sim-vs-mesure.md) : chiffre la dissipation d'un clamp
secondaire candidat sur Q2, modele reel IPD050N10N5 + grille synchrone
ideale (proxy UCC24612), memes 6 points/D que l'enveloppe 18,9W.

Deux candidats compares :
  - SMCJ43A (Vbr_min=47,8V) : meme reference que D1 cote primaire,
    proposition de reutiliser le meme composant (deja au BOM).
  - SMCJ54A (Vbr_min=60V, Vc=87,1V@17,3A, Bourns SMCJ series,
    bourns-smcj-series.pdf p.2) : candidat alternatif choisi pour
    degager de la marge au-dessus de l'excursion normale (hors
    resonance) de Vds_Q2, tout en gardant une marge raisonnable sous les
    100V du MOSFET (Vc=87,1V, ~13% de marge).

Modele clamp = meme construction que D1 (BV + IBV=1mA + RS=1 Ohm), pas
une valeur sourcee au-dela des 2 points datasheet -- exploratoire, pour
eclairer un choix, pas pour qualifier un composant final.
"""
import csv
import sys

sys.path.insert(0, ".")
from run_point import run

POINTS = [
    ("11V_6V3", 11.0, 6.3, 0.4006, 2.1),
    ("11V_12V6", 11.0, 12.6, 0.5502, 8.4),
    ("20V_6V3", 20.0, 6.3, 0.2602, 2.1),
    ("20V_12V6", 20.0, 12.6, 0.4006, 8.4),
    ("25V_6V3", 25.0, 6.3, 0.2194, 2.1),
    ("25V_12V6", 25.0, 12.6, 0.3462, 8.4),
]
POUT_T = 18.9

CANDIDATES = [
    ("smcj43a", 47.8),
    ("smcj54a", 60.0),
]

FIELDS = ["candidate", "bv", "label", "vin", "vout_target", "vout_avg",
          "pout_avg", "eta_pct", "vds_q2_max", "ploss_d2sec", "ipk_pri"]


def main():
    rows = []
    for cand_name, bv in CANDIDATES:
        for label, vin, vout_t, d, rload in POINTS:
            print(f"=== {cand_name} (BV={bv}V) {label} ===")
            out = f"results/point18w9_clamp_{cand_name}_{label}.asc"
            r = run(vin, vout_t, d, rload, out=out, settle_periods=4000,
                    measure_periods=100, pout=POUT_T, rectifier="sync_ideal",
                    sec_clamp_bv=bv)
            if "vout_avg" not in r:
                print(f"  ECHEC pour {cand_name}/{label}, retente une fois...")
                r = run(vin, vout_t, d, rload, out=out, settle_periods=4000,
                        measure_periods=100, pout=POUT_T, rectifier="sync_ideal",
                        sec_clamp_bv=bv)
            if "vout_avg" not in r:
                print(f"  ECHEC definitif pour {cand_name}/{label} : {r}")
                continue
            row = {
                "candidate": cand_name, "bv": bv, "label": label,
                "vin": vin, "vout_target": vout_t,
                "vout_avg": round(r["vout_avg"], 4),
                "pout_avg": round(r["pout_avg"], 4),
                "eta_pct": round(100 * r["pout_avg"] / r["pin_avg"], 2),
                "vds_q2_max": round(r.get("vds_q2_max", 0.0), 3),
                "ploss_d2sec": round(r.get("ploss_d2sec", 0.0), 4),
                "ipk_pri": round(r.get("ipk_pri", 0.0), 4),
            }
            rows.append(row)
            print(f"  Vout={row['vout_avg']}V Vds_Q2_max={row['vds_q2_max']}V "
                  f"Ploss_D2sec={row['ploss_d2sec']}W")

    with open("results/sec_clamp_candidates.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nEcrit results/sec_clamp_candidates.csv ({len(rows)} points)")


if __name__ == "__main__":
    main()
