"""Meme circuit que gen_bias_fb.py (topologie verifiee par netlist), mais
avec Q6/Q7 = VRAI BSS127I (proxy datasheet, voir models/BSS127I.lib) et
U21 = op-amp IDEAL (UniversalOpAmp2, le primitif comportemental natif
LTspice "level2", deja utilise et robuste tout du long de ce projet) mais
PARAMETRE avec les vraies caracteristiques electriques du MCP6001 lues
dans sa datasheet (DS20001733L), PAS le macromodele PSpice complet du
fondeur.

Pourquoi pas le macromodele MCP6001 complet (simulation/models/MCP6001.lib,
syntaxiquement corrige et valide seul -- voir validate_mcp6001.py) :
confirme, par 4 remedes de convergence testes independamment (gmin eleve,
.ic sur les noeuds externes, resistance de stabilisation interne sur la
boucle de bruit du modele, .nodeset direct sur le noeud interne signale),
INCOMPATIBLE avec cette boucle fermee precise (echec systematique
"trouble with node u21:21" des le point de fonctionnement initial, meme
avec des MOSFET Q6/Q7 ideaux -- donc le probleme est interne au
macromodele MCP6001 lui-meme dans ce type de boucle, pas une interaction
avec BSS127I.lib). Coherent avec les retours de la communaute LTspice
("the output often sticks or generates time step too small/singularity
errors", forum.allaboutcircuits.com, groups.io/g/LTspice) -- probleme
connu du fichier vendeur, pas une erreur de montage de ce projet.

Parametres MCP6001 sources (DS20001733L, Microchip, 2002-2020) :
  Avol = 25,1k V/V (88dB MIN -- volontairement le pire cas garanti, pas
    un "typ" -- donne une estimation CONSERVATRICE (majorante) de
    l'erreur residuelle de boucle, coherent avec la question deja posee
    dans ce projet sur la tension residuelle inevitable).
  GBW = 1MHz typ (titre du produit "1 MHz Low Power Op Amp").
  Slew = 0,6V/us typ = 600k V/s.
  Rail = 25mV (VOL/VOH : VSS+25mV a VDD-25mV, VDD=5,5V, surcharge
    d'entree 0,5V -- swing rail-to-rail quasi complet).
  Vos = 0 (reel : max +-7mV -- neglige ici, <0,3% sur une plage de
    sortie 0-80V/0-3V, simplification documentee, pas une valeur
    sourcee a 0).
  Ilimit, Rin, bruit (En/Enk/In/Ink) : laisses aux valeurs generiques
    par defaut d'UniversalOpAmp2 (non sourcees MCP6001 specifiquement --
    Ilimit n'a aucun impact ici, les courants reels restent <1mA ;
    Rin/bruit non pertinents pour une regulation DC).

Q6/Q7 : le proxy BSS127I.lib (niveau 1, seuil dur, AUCUNE conduction
sous VTO) a produit une oscillation large (~9Vcc, plusieurs centaines
de kHz) sur tout le balayage -- confirme par un test de controle (meme
oscillation, PIRE, avec un ampli-op aux parametres ideaux a la place du
MCP6001 parametre) que la cause est le coude artificiellement raide du
proxy, pas la bande passante de l'ampli-op. Pour trancher, Q6/Q7 utilise
ici IPD050N10N5 (sous-circuit REEL Infineon OptiMOS5, deja utilise et
valide pour Q1/Q2 dans ce meme projet, 100V/TO-252 -- demande
explicitement par l'utilisateur comme "mosfet 100V TO252 deja utilise"
en remplacement d'un composant invente) : c'est un modele fondeur
complet avec une transition bien plus progressive qu'un niveau-1, meme
si son seuil (2,2-3,0-3,8V typ) et son calibre (80A/5mOhm) ne
correspondent pas au vrai BSS127I de la carte -- un compromis de
modelisation assume pour disposer d'un canal MOSFET "physique" valide,
pas le composant reellement monte."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_asc import Sheet, two_pin, PIN as _BASE_PIN  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))

PIN = dict(_BASE_PIN)
PIN["opamp2"] = {
    "IN+": (-32, 16), "IN-": (-32, -16),
    "V+": (0, -32), "V-": (0, 32), "OUT": (32, 0),
}

MCP6001_PARAMS = dict(avol="25.1k", gbw="1Meg", slew="600k", rail="25m", vos="0")


def place_mcp6001_real(s, x, y, inst):
    ox, oy = s.symbol("UniversalOpAmp2", x, y, rot="R0", inst=inst)
    s.lines.append(f"SYMATTR Value2 Avol={MCP6001_PARAMS['avol']} "
                    f"GBW={MCP6001_PARAMS['gbw']} Slew={MCP6001_PARAMS['slew']}")
    s.lines.append(f"SYMATTR SpiceLine Ilimit=25m Rail={MCP6001_PARAMS['rail']} "
                    f"Vos={MCP6001_PARAMS['vos']}")
    return ox, oy


def build(out_path, v_lo=0.0, v_hi=3.0, tramp=2e-3,
          hv80in=80.0, rail_3v3=3.3,
          r47=1e3, r48=100e3, r49=1e3, r50=100e3, r53=100e3, r52=3.9e3,
          r36=10e3, maxstep=1e-6,
          q_model="IPD050N10N5", q_lib="IPD050N10N5.lib", q_prefix="X",
          c_node_raw=None, c_hv_bias=None, rs6=None):
    s = Sheet()
    s.comment(40, 20,
              f"Rampe quasi-statique VAR_GATE {v_lo}V->{v_hi}V sur {tramp*1e3:.2f}ms -- "
              f"Q6/Q7={q_model}, U21=MCP6001 PARAMETRE (datasheet, pas macromodele "
              f"-- voir docstring de ce fichier). R53=100k R52=3,9k (valeurs reelles "
              f"appliquees sur la carte, meme ratio que 1M/39k precedent).")

    q_lib_path = os.path.join(_HERE, "models", q_lib).replace("\\", "/")
    s.directive(40, 460, f'.lib "{q_lib_path}"')
    s.directive(40, 500, ".model DCLAMP_SMCJ100A D(BV=100 IBV=1m RS=1.0)")

    two_pin(s, "voltage", 80, 120, "Vvargate",
            f"PWL(0 {v_lo} {tramp*1e3:.6f}m {v_hi})", "vargate", "0")
    two_pin(s, "voltage", 80, 340, "Vhv80in", f"{hv80in}", "hv80_in", "0")
    two_pin(s, "voltage", 80, 560, "Vrail", f"{rail_3v3}", "rail_3v3_pri", "0")

    two_pin(s, "res", 240, 120, "R47", f"{r47:.0f}", "vargate", "node_a")
    two_pin(s, "res", 400, 220, "R48", f"{r48:.0f}", "node_a", "0")

    two_pin(s, "res", 400, 460, "R53", f"{r53:.0f}", "hv_bias", "node_sense")
    two_pin(s, "res", 400, 620, "R52", f"{r52:.0f}", "node_sense", "0")
    two_pin(s, "res", 240, 700, "R36", f"{r36:.0f}", "node_sense", "node_fb_sense")

    ox, oy = place_mcp6001_real(s, 600, 160, "U21")
    s.flag(ox + PIN["opamp2"]["IN-"][0], oy + PIN["opamp2"]["IN-"][1], "node_a")
    s.flag(ox + PIN["opamp2"]["IN+"][0], oy + PIN["opamp2"]["IN+"][1], "node_fb_sense")
    s.flag(ox + PIN["opamp2"]["V+"][0], oy + PIN["opamp2"]["V+"][1], "rail_3v3_pri")
    s.flag(ox + PIN["opamp2"]["V-"][0], oy + PIN["opamp2"]["V-"][1], "0")
    s.flag(ox + PIN["opamp2"]["OUT"][0], oy + PIN["opamp2"]["OUT"][1], "node_opout")

    two_pin(s, "cap", 760, 400, "C58", "100n", "rail_3v3_pri", "0")
    two_pin(s, "res", 840, 160, "R49", f"{r49:.0f}", "node_opout", "node_gate")
    two_pin(s, "res", 1000, 80, "R50", f"{r50:.0f}", "hv80_in", "node_raw")
    two_pin(s, "diode", 1140, 160, "D8", "DCLAMP_SMCJ100A", "0", "node_raw")

    mx, my = s.symbol("nmos", 1000, 280, rot="R0", inst="Q6",
                       value=q_model, prefix=q_prefix)
    s.flag(mx + PIN["nmos"]["D"][0], my + PIN["nmos"]["D"][1], "node_raw")
    s.flag(mx + PIN["nmos"]["G"][0], my + PIN["nmos"]["G"][1], "node_gate")
    if rs6:
        s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "q6_src")
        two_pin(s, "res", 1000, 420, "Rs6", f"{rs6:.0f}", "q6_src", "0")
    else:
        s.flag(mx + PIN["nmos"]["S"][0], my + PIN["nmos"]["S"][1], "0")

    qx, qy = s.symbol("nmos", 1280, 280, rot="R0", inst="Q7",
                       value=q_model, prefix=q_prefix)
    s.flag(qx + PIN["nmos"]["D"][0], qy + PIN["nmos"]["D"][1], "hv80_in")
    s.flag(qx + PIN["nmos"]["G"][0], qy + PIN["nmos"]["G"][1], "node_raw")
    s.flag(qx + PIN["nmos"]["S"][0], qy + PIN["nmos"]["S"][1], "hv_bias")

    if c_node_raw:
        two_pin(s, "cap", 1420, 460, "Ccomp", f"{c_node_raw}", "node_raw", "0")
    if c_hv_bias:
        two_pin(s, "cap", 1420, 620, "Cout", f"{c_hv_bias}", "hv_bias", "0")

    s.directive(40, 620, f".tran 0 {tramp*1e3:.6f}m 0 {maxstep*1e9:.4f}n")

    s.write(out_path)
    print(f"Ecrit {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "bias_fb_ramp_real.asc"
    build(out)
