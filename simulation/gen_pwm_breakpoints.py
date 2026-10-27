"""Genere une table PWL explicite (time, value) pour un signal PWM dont le
rapport cyclique suit un profil lineaire par morceaux -- un seul point par
transition, utilisee via 'PWL FILE=' sur une source "voltage" standard.

Pourquoi pas une expression comportementale IF(TIME mod Tsw < duty*Tsw, ...) :
confirme par simulation (100026 points, maxstep=1us) que le solveur adaptatif
de LTspice ne voit que 15 impulsions ON sur ~5000 attendues -- une formule
arbitraire en TIME ne declare aucun breakpoint, le solveur saute par-dessus
les creneaux etroits (50ns a duty=1%) sans jamais les evaluer. Une table PWL
force un point exact a chaque transition (comportement natif de LTspice pour
PULSE/PWL, pas pour les sources comportementales)."""
import sys

DUTY_BREAKPOINTS = [
    (0.0, 0.01), (0.5, 0.60), (1.0, 0.60), (1.5, 0.99),
    (2.0, 0.99), (2.5, 0.40), (3.0, 0.01), (3.5, 0.01),
]


def duty_at(t, breakpoints=DUTY_BREAKPOINTS):
    for (t0, d0), (t1, d1) in zip(breakpoints, breakpoints[1:]):
        if t0 <= t <= t1:
            if t1 == t0:
                return d0
            frac = (t - t0) / (t1 - t0)
            return d0 + frac * (d1 - d0)
    return breakpoints[-1][1]


def build(out_path, tsw=5e-6, tstop=3.5, tedge=1e-9, vhigh=3.0, vlow=0.0):
    n_periods = int(tstop / tsw)
    with open(out_path, "w") as f:
        for k in range(n_periods):
            tk = k * tsw
            d = duty_at(tk)
            d_on = d * tsw
            f.write(f"{tk:.12e} {vhigh}\n")
            f.write(f"{tk + d_on:.12e} {vhigh}\n")
            f.write(f"{tk + d_on + tedge:.12e} {vlow}\n")
            f.write(f"{tk + tsw - tedge:.12e} {vlow}\n")
        f.write(f"{tstop:.12e} {vlow}\n")
    print(f"Ecrit {out_path} ({n_periods} periodes, {n_periods * 4 + 1} points)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "results/pwm_breakpoints.txt"
    build(out)
