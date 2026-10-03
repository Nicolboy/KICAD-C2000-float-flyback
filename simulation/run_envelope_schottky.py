import csv, sys
sys.path.insert(0, ".")
from run_point import run

POINTS = [
    ("11V_6V", 11.0, 6.0, 0.3828, 3.6, 10.0),
    ("11V_12V", 11.0, 12.0, 0.5359, 14.4, 10.0),
    ("20V_6V", 20.0, 6.0, 0.2500, 3.6, 10.0),
    ("20V_12V", 20.0, 12.0, 0.3016, 14.4, 10.0),
    ("25V_6V", 25.0, 6.0, 0.2109, 3.6, 10.0),
    ("25V_12V", 25.0, 12.0, 0.2625, 14.4, 10.0),
    ("20V_6V_light", 20.0, 6.0, 0.1134, 36.0, 1.0),
]
FIELDS = ["label","vin","vout_target","d","rload","vout_avg","iout_avg","pout_avg",
          "pin_avg","eta_pct","mode","ploss_q1","ploss_rect","ploss_d1","ploss_dcr1",
          "ploss_dcr2","ploss_rshunt","ploss_cout","ploss_sum","ploss_total_pin_pout",
          "vds_q1_max","vds_q2_max","ipk_pri","irms_pri","il2_end_of_period"]
rows = []
for label, vin, vout_t, d, rload, pout_t in POINTS:
    print(f"=== {label} ===")
    out = f"results/schottky_{label}.asc"
    r = run(vin, vout_t, d, rload, out=out, settle_periods=4000, measure_periods=100, pout=pout_t)
    if "vout_avg" not in r:
        print(f"  ECHEC: {r}")
        continue
    il2_end = r.get("il2_end_of_period", 0.0)
    ipk = r.get("ipk_pri", 1.0)
    mode = "CCM" if abs(il2_end) > 0.05*ipk else "DCM"
    ploss_sum = sum(r.get(k,0.0) for k in ["ploss_q1","ploss_rect","ploss_d1","ploss_dcr1","ploss_dcr2","ploss_rshunt","ploss_cout"])
    ploss_total = r["pin_avg"] - r["pout_avg"]
    row = {"label": label, "vin": vin, "vout_target": vout_t, "d": d, "rload": rload,
           "vout_avg": round(r["vout_avg"],4), "iout_avg": round(r["iout_avg"],4),
           "pout_avg": round(r["pout_avg"],4), "pin_avg": round(r["pin_avg"],4),
           "eta_pct": round(100*r["pout_avg"]/r["pin_avg"],2), "mode": mode,
           "ploss_q1": round(r.get("ploss_q1",0),4), "ploss_rect": round(r.get("ploss_rect",0),4),
           "ploss_d1": round(r.get("ploss_d1",0),4), "ploss_dcr1": round(r.get("ploss_dcr1",0),4),
           "ploss_dcr2": round(r.get("ploss_dcr2",0),4), "ploss_rshunt": round(r.get("ploss_rshunt",0),4),
           "ploss_cout": round(r.get("ploss_cout",0),4), "ploss_sum": round(ploss_sum,4),
           "ploss_total_pin_pout": round(ploss_total,4),
           "vds_q1_max": round(r.get("vds_q1_max",0),3), "vds_q2_max": round(r.get("vds_q2_max",0),3),
           "ipk_pri": round(r.get("ipk_pri",0),4), "irms_pri": round(r.get("irms_pri",0),4),
           "il2_end_of_period": round(il2_end,4)}
    rows.append(row)
    print(f"  Vout={row['vout_avg']}V Pout={row['pout_avg']}W eta={row['eta_pct']}% mode={mode} D1={row['ploss_d1']}W")

with open("results/envelope_schottky.csv","w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print(f"Ecrit results/envelope_schottky.csv ({len(rows)} points)")
