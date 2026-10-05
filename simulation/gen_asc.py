"""Generateur de schema LTspice (.asc) pour l'etage primaire+transfo+
redressement de la carte alim-flyback-filament.

Modeles utilises (tous sources, voir composants-datasheets/data/carte-flyback/) :
  - Q1 et Q2 (redressement passif par diode de corps) : IPD050N10N5 reel
    (sous-circuit Infineon, simulation/models/IPD050N10N5.lib -- voir ce
    fichier pour la provenance exacte).
  - D1 (clamp primaire) : modele zener/TVS construit sur 2 points sources
    de la datasheet SMCJ43A (Vbr=47,8V@1mA, Vc=69,4V@21,7A) --
    composants-datasheets/data/carte-flyback/smcj43a.yaml.
  - Transformateur MSD1514-103ME : L=10uH, DCR=15mOhm typ, k=0,99
    (datasheets/inductors/msd1514.pdf). Capacite inter-enroulements :
    AUCUNE valeur publiee -> .param ESTIME, a ne jamais traiter comme
    une valeur sourcee.
  - Cin/Cout : ESR reels (A786MW 10mOhm, 2x16SVPG330M 6,5mOhm chacun).
  - Parasites de routage (mailles primaire/secondaire) : .param ESTIME,
    aucune mesure reelle disponible avant le routage du PCB.

Convention de cablage (cf. 00-intention-conception.md / doc/sim-vs-mesure.md) :
chaque patte de composant recoit un FLAG place exactement a sa coordonnee,
jamais de WIRE explicite. Sheet.flag() leve une erreur si deux pattes de
nets differents atterrissent sur la meme coordonnee apres arrondi a la
grille -- c'est ce garde-fou qui avait revele le bug de polarite L2/Rdcr2
corrige precedemment ; ne jamais le contourner.
"""

GRID = 16


def snap(v):
    return int(round(v / GRID) * GRID)


class Sheet:
    def __init__(self, width=1400, height=900):
        self.lines = ["Version 4", f"SHEET 1 {width} {height}"]
        self._flag_coords = {}

    def symbol(self, name, x, y, rot="R0", inst=None, value=None, prefix=None):
        x, y = snap(x), snap(y)
        self.lines.append(f"SYMBOL {name} {x} {y} {rot}")
        if inst:
            self.lines.append(f"SYMATTR InstName {inst}")
        if value is not None:
            self.lines.append(f"SYMATTR Value {value}")
        if prefix is not None:
            self.lines.append(f"SYMATTR Prefix {prefix}")
        return x, y

    def flag(self, x, y, net):
        x, y = snap(x), snap(y)
        prev = self._flag_coords.get((x, y))
        if prev is not None and prev != net:
            raise ValueError(
                f"Collision de coordonnees apres snap() : ({x},{y}) porte deja "
                f"le net '{prev}', tentative d'y placer '{net}' -- deux pattes "
                f"trop proches fusionneraient silencieusement dans LTspice. "
                f"Ecarter les composants concernes.")
        self._flag_coords[(x, y)] = net
        self.lines.append(f"FLAG {x} {y} {net}")

    def directive(self, x, y, text):
        x, y = snap(x), snap(y)
        self.lines.append(f"TEXT {x} {y} Left 2 !{text}")

    def comment(self, x, y, text):
        x, y = snap(x), snap(y)
        self.lines.append(f"TEXT {x} {y} Left 2 ;{text}")

    def write(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("\r\n".join(self.lines) + "\r\n")


PIN = {
    "res": {"A": (16, 16), "B": (16, 96)},
    "cap": {"A": (16, 0), "B": (16, 64)},
    "ind": {"A": (16, 16), "B": (16, 96)},
    "voltage": {"A": (0, 16), "B": (0, 96)},
    "nmos": {"D": (48, 0), "G": (0, 80), "S": (48, 96)},
    "diode": {"A": (16, 0), "B": (16, 64)},
}


def two_pin(sheet, symname, x, y, inst, value, net_a, net_b, rot="R0"):
    x, y = sheet.symbol(symname, x, y, rot=rot, inst=inst, value=value)
    pa = PIN[symname]["A"]
    pb = PIN[symname]["B"]
    sheet.flag(x + pa[0], y + pa[1], net_a)
    sheet.flag(x + pb[0], y + pb[1], net_b)


import os

_HERE = os.path.dirname(os.path.abspath(__file__))


def build(point_name, vin, vout_target, pout, d, dead, period, out_path,
          rload=None, lib_dir=None, lmesh_pri=1e-12, lmesh_sec=1e-12,
          c_inter=0.0, settle_periods=4000, measure_periods=100,
          rectifier="schottky", sec_clamp_bv=None):
    """sec_clamp_bv : si renseigne (V), ajoute un clamp TVS D2sec (meme
    modele diode zener/BV que D1, cathode=n_sec2/anode=GND -- meme
    orientation, cf. commentaire D1 ci-dessous) entre drain Q2 et masse
    secondaire, pour chiffrer la dissipation d'un clamp secondaire
    candidat (exploratoire, pas encore un composant sourced/retenu).

    rectifier :
      - "schottky" (defaut) : diode generique simple (IS=100n N=1 RS=5m),
        rapide et robuste a simuler -- pour comparer le rendement vite,
        PAS le composant reellement monte (il n'y en a pas de discret,
        voir docstring du module).
      - "body_diode" : diode de corps du vrai modele IPD050N10N5 (Q2 avec
        gate a 0V) -- plus fidele mais beaucoup plus lent/capricieux a
        converger (reseau Miller non-lineaire complet).
      - "sync_ideal" : Q2 = vrai IPD050N10N5 (meme sous-circuit que
        "body_diode", la diode de corps reste physiquement presente
        pendant le temps mort), mais grille pilotee par un PULSE ideal
        complementaire a Vg1 (ON pendant tout le temps bas de Q1, moins
        `dead` de chaque cote). Sert de PROXY RAPIDE du comportement
        qu'un UCC24612 realise par diode emulation -- aucun modele SPICE
        UCC24612 n'est sourcable (controleur analogique a detection de
        Vds, pas de macromodele publie TI) -- jamais a confondre avec une
        simulation du composant reel ni avec une mesure."""
    ton1 = d * period
    s = Sheet()
    s.comment(40, 20,
              f"Point {point_name} : Vin={vin}V Vout_cible={vout_target}V "
              f"Pout_cible={pout}W D={d:.4f} 200kHz -- masse commune (pas de "
              f"HV_BIAS), redressement passif (diode de corps Q2, gate=0V)")

    if lib_dir is None:
        lib_dir = os.path.join(_HERE, "models")
    lib_path = os.path.join(lib_dir, "IPD050N10N5.lib").replace("\\", "/")
    s.directive(40, 580, f'.lib "{lib_path}"')
    s.directive(40, 600, ".model DCLAMP_SMCJ43A D(BV=47.8 IBV=1m RS=1.0)")
    if rectifier == "schottky":
        s.directive(40, 620, ".model DSCHOTTKY D(IS=100n N=1 RS=5m)")

    # --- Vin + Cin reel (A786MW, 470uF, ESR=10mOhm) ---
    two_pin(s, "voltage", 80, 120, "V1", str(vin), "vin", "0")
    two_pin(s, "cap", 240, 120, "Cin", "470u", "vin", "n_cin_r")
    two_pin(s, "res", 240, 260, "Rcin_esr", "10m", "n_cin_r", "0")

    # --- Transfo primaire : L1 (dot=vin) -> Rdcr1 -> Lmesh_pri -> Q1 drain
    two_pin(s, "ind", 440, 60, "L1", "10u ic=0", "vin", "n_pri1")
    two_pin(s, "res", 440, 220, "Rdcr1", "15m", "n_pri1", "n_pri1b")
    two_pin(s, "ind", 440, 340, "Lmesh_pri", f"{lmesh_pri}", "n_pri1b", "n_pri2")

    mx, my = s.symbol("nmos", 440, 460, rot="R0", inst="M1", value="IPD050N10N5", prefix="X")
    s.flag(mx + PIN["nmos"]["D"][0], my + PIN["nmos"]["D"][1], "n_pri2")
    s.flag(mx + PIN["nmos"]["G"][0], my + PIN["nmos"]["G"][1], "g1")
    s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "n_q1s")
    two_pin(s, "res", 440, 600, "Rshunt", "7.5m", "n_q1s", "0")

    # --- clamp primaire D1 (SMCJ43A reel) : cathode=n_pri2, anode=GND,
    # monte seul entre SW_PRI et GND (cf. smcj43a.yaml) ---
    two_pin(s, "diode", 280, 460, "D1", "DCLAMP_SMCJ43A", "0", "n_pri2")

    # --- capacite inter-enroulements ESTIMEE (non sourcee datasheet) ---
    if c_inter > 0:
        two_pin(s, "cap", 640, 180, "Cinter_ESTIME", f"{c_inter}", "n_pri1", "n_sec1")

    # --- grille Q1 : PULSE ideale, ON de t=0 a t=Ton1, periode T ---
    two_pin(s, "voltage", 760, 460,
            "Vg1", f"PULSE(0 10 0 2n 2n {ton1*1e6:.4f}u {period*1e6:.4f}u)",
            "g1", "0")

    # --- Transfo secondaire : L2 (dot=n_sec1, PAS vout) -> Rdcr2 ->
    # Lmesh_sec -> redresseur (Schottky generique ou diode de corps Q2) ---
    two_pin(s, "ind", 960, 60, "L2", "10u ic=0", "n_sec1", "vout")
    two_pin(s, "res", 960, 220, "Rdcr2", "15m", "n_sec1", "n_sec1b")
    two_pin(s, "ind", 960, 340, "Lmesh_sec", f"{lmesh_sec}", "n_sec1b", "n_sec2")

    if rectifier == "schottky":
        two_pin(s, "diode", 960, 460, "Drect", "DSCHOTTKY", "0", "n_sec2")
    else:
        mx2, my2 = s.symbol("nmos", 960, 460, rot="R0", inst="M2", value="IPD050N10N5", prefix="X")
        s.flag(mx2 + PIN["nmos"]["D"][0], my2 + PIN["nmos"]["D"][1], "n_sec2")
        s.flag(mx2 + PIN["nmos"]["G"][0], my2 + PIN["nmos"]["G"][1], "g2")
        s.flag(mx2 + PIN["nmos"]["S"][0], my2 + PIN["nmos"]["S"][1], "0")
        if rectifier == "sync_ideal":
            # proxy UCC24612 (diode emulation idealisee) : ON pendant tout
            # le temps bas de Q1, moins `dead` de chaque cote.
            td2 = ton1 + dead
            pw2 = period - ton1 - 2 * dead
            two_pin(s, "voltage", 1160, 460,
                    "Vg2", f"PULSE(0 10 {td2*1e6:.4f}u 2n 2n "
                           f"{pw2*1e6:.4f}u {period*1e6:.4f}u)",
                    "g2", "0")
        else:
            two_pin(s, "voltage", 1160, 460, "Vg2", "0", "g2", "0")

    # --- clamp secondaire candidat (exploratoire, pas pose sur la vraie
    # carte) : meme orientation que D1 (anode=GND, cathode=n_sec2) ---
    if sec_clamp_bv:
        s.directive(40, 560, f".model DCLAMP_SEC D(BV={sec_clamp_bv} IBV=1m RS=1.0)")
        two_pin(s, "diode", 1060, 600, "D2sec", "DCLAMP_SEC", "0", "n_sec2")

    # --- Cout reel (2x 16SVPG330M, 330uF/ESR=6.5mOhm chacun, paralleles) + Rload ---
    two_pin(s, "cap", 1280, 460, "Cout1", f"330u ic={vout_target}", "vout", "n_cout1_r")
    two_pin(s, "res", 1280, 600, "Rcout1_esr", "6.5m", "n_cout1_r", "0")
    two_pin(s, "cap", 1360, 460, "Cout2", f"330u ic={vout_target}", "vout", "n_cout2_r")
    two_pin(s, "res", 1360, 600, "Rcout2_esr", "6.5m", "n_cout2_r", "0")

    if rload is None:
        rload = (vout_target ** 2) / pout
    two_pin(s, "res", 1280, 700, "Rload", f"{rload:.4f}", "vout", "0")

    s.directive(40, 640, "K1 L1 L2 0.99")

    tstop = settle_periods * period
    tstart = (settle_periods - measure_periods) * period
    s.directive(40, 680, f".tran 0 {tstop*1e6:.2f}u {tstart*1e6:.2f}u 10n uic")

    f0, f1 = f"{tstart*1e6:.2f}u", f"{tstop*1e6:.2f}u"
    s.directive(40, 720, f".meas TRAN Vout_avg AVG V(vout) FROM {f0} TO {f1}")
    s.directive(40, 740, f".meas TRAN Iout_avg AVG I(Rload) FROM {f0} TO {f1}")
    s.directive(40, 760, f".meas TRAN Pout_avg AVG (V(vout)*I(Rload)) FROM {f0} TO {f1}")
    s.directive(40, 780, f".meas TRAN Pin_avg AVG (-V(vin)*I(V1)) FROM {f0} TO {f1}")
    # Id() ne resout pas sur une instance X (sous-circuit) -- on utilise le
    # courant des inductances de maille, en serie directe avec D de M1/M2,
    # comme proxy exact du courant de drain.
    s.directive(40, 800, f".meas TRAN Ploss_Q1 AVG (I(Lmesh_pri)*(V(n_pri2)-V(n_q1s))) FROM {f0} TO {f1}")
    s.directive(40, 820, f".meas TRAN Ploss_Rect AVG (I(Lmesh_sec)*V(n_sec2)) FROM {f0} TO {f1}")
    s.directive(40, 840, f".meas TRAN Ploss_DCR1 AVG (I(Rdcr1)*I(Rdcr1)*0.015) FROM {f0} TO {f1}")
    s.directive(40, 860, f".meas TRAN Ploss_DCR2 AVG (I(Rdcr2)*I(Rdcr2)*0.015) FROM {f0} TO {f1}")
    s.directive(40, 880, f".meas TRAN Ploss_Rshunt AVG (I(Rshunt)*I(Rshunt)*0.0075) FROM {f0} TO {f1}")
    # perte dans le clamp primaire D1 (inquietude explicite de l'utilisateur) :
    # P = I(D1)*(Vanode-Vcathode) = I(D1)*(V(0)-V(n_pri2)), formule generale
    # correcte en conduction directe ET en claquage (pas besoin de signe a part).
    s.directive(40, 900, f".meas TRAN Ploss_D1 AVG (-I(D1)*V(n_pri2)) FROM {f0} TO {f1}")
    if sec_clamp_bv:
        s.directive(40, 920, f".meas TRAN Ploss_D2sec AVG (-I(D2sec)*V(n_sec2)) FROM {f0} TO {f1}")
    s.directive(1160, 720, f".meas TRAN Ploss_Cout AVG (I(Rcout1_esr)*I(Rcout1_esr)*0.0065+"
                           f"I(Rcout2_esr)*I(Rcout2_esr)*0.0065) FROM {f0} TO {f1}")
    s.directive(1160, 740, f".meas TRAN Vds_Q1_max MAX (V(n_pri2)-V(n_q1s)) FROM {f0} TO {f1}")
    s.directive(1160, 760, f".meas TRAN Vds_Q2_max MAX V(n_sec2) FROM {f0} TO {f1}")
    s.directive(1160, 780, f".meas TRAN Ipk_pri MAX I(L1) FROM {f0} TO {f1}")
    s.directive(1160, 800, f".meas TRAN Irms_pri RMS I(L1) FROM {f0} TO {f1}")
    # mode de conduction : I(L2) juste avant le rallumage de Q1 (fin de
    # periode) -- proche de 0 = DCM, significatif = CCM (cf. plan etape 1/4)
    t_end_check = tstop - 0.05e-6
    s.directive(1160, 820, f".meas TRAN IL2_end_of_period FIND I(L2) AT {t_end_check*1e6:.4f}u")

    s.write(out_path)
    print(f"Ecrit {out_path} (D={d:.4f}, Ton1={ton1*1e6:.4f}us, Rload={rload:.4f} Ohm)")
    return rload


if __name__ == "__main__":
    import sys
    T = 1 / 200e3
    stage_vin = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    vout_t = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    d_val = float(sys.argv[3]) if len(sys.argv) > 3 else 0.242
    rload_val = float(sys.argv[4]) if len(sys.argv) > 4 else None
    out = sys.argv[5] if len(sys.argv) > 5 else "test_point.asc"
    build("test", stage_vin, vout_t, 10.0, d_val, 100e-9, T, out, rload=rload_val)
