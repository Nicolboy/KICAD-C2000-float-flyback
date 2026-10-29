# KICAD-C2000-float-flyback

- **18.9W** — real-world target power, simulated efficiency up to 94.8%
- **+5 points** efficiency from synchronous rectification (UCC24612) vs. body-diode
- **106.8V → 61–65V** — secondary overvoltage, resolved by a TVS clamp sized through simulation (×1.5 margin vs. the 100V MOSFET rating)

Flyback power supply for vacuum-tube filament heating and a low-noise
preamp stage, designed in KiCad 10, with the control side (C2000)
galvanically isolated from the power stage. **Update 2026-10-25**: the
secondary is no longer floating/galvanically isolated from the primary
in the final assembly — only the control↔power barrier remains isolated;
see `doc/plan-isolation-4couches.md` for the current barrier scope.
200kHz, 11–25V in → 5.5–13V/3A out, secondary liftable 0–90V for
cathode/filament stress reduction. Synchronous secondary rectification
(UCC24612, direct Vds sensing — no firmware timing) validated by SPICE at
the real 18.9W target, including a secondary-side overvoltage finding and
the clamp that fixes it — see *Validation* below for the figures and
`doc/sim-vs-mesure.md` for the full data.

Alimentation flyback pour le chauffage d'un filament de tube à vide et un
étage de préamplification bas bruit, conçue sous KiCad 10 — le côté
contrôle (C2000) reste isolé galvaniquement de l'étage de puissance.
**Mise à jour 2026-10-25** : le secondaire n'est plus flottant/isolé
galvaniquement du primaire dans le montage final — seule la barrière
contrôle↔puissance reste isolée ; voir `doc/plan-isolation-4couches.md`
pour le périmètre actuel des barrières.

Convertisseur flyback 200kHz, 11-25V en entrée → 5,5-13V/3A en sortie.
Secondaire élevable de 0 à 90V par un pont symétrique 2×100kΩ (une
résistance vers Vout+, une vers Vout-) — pour réduire le stress
cathode/chauffage sur un préamplificateur à tubes bas bruit (montage cascode).

<p align="center">
  <img src="doc/KICAD-HT-pcbway.png" alt="Rendu 3D de la carte d'alimentation flyback KiCad" width="700px">
</p>

---

## Le point de conception le plus notable

Le redressement synchrone secondaire (Q2) est piloté par un **UCC24612**, pas
par le C2000 : ce contrôleur détecte directement le Vds de Q2 (diode
emulation) et pilote sa grille tout seul — aucun signal PWM ni isolateur
dédié à faire traverser la barrière pour ce canal. Avant ça, la commande
passait par un ISO7710+UCC27517 secondaires pilotés en PWM depuis le C2000 :
un timing fixé par le firmware, « à l'aveugle », sans retour sur le vrai Vds
de Q2 — remplacé une fois ce défaut identifié. L'UCC24612 est alimenté
directement depuis Vout (VDD dans sa plage 4,5-28V, pas de bootstrap
nécessaire) ; côté primaire, l'isolation PWM/EN (ISO7710 + UCC27517 + DPC817)
reste inchangée.

Chaque composant de puissance (MOSFETs, clamp, condensateurs d'entrée et de
sortie) est sourcé avec sa propre fiche datasheet dans
[`composants-datasheets/data/carte-flyback/`](../composants-datasheets/data/carte-flyback)
— page citée, base (absolue / recommandée / typique / calculée), jamais de
valeur choisie à l'oeil. Ce sourcing a d'ailleurs fait revenir deux fois sur
le choix de Cin et Cout : le premier calcul prenait le coin 13V/3A (39W)
comme pire cas, avant d'être recorrigé sur les vrais coins d'usage — deux
câblages de filament qui tombent à **la même puissance réelle** (18,9W) et
divisent par deux la contrainte de courant et d'ondulation retenue au départ.
Le détail (formules, marges, historique des choix) est dans
[`00-intention-conception.md`](00-intention-conception.md).

---

## Architecture

| Bloc | Rôle |
|---|---|
| Primaire | Cin, MOSFET N (TO-252), clamp TVS D1 (boîtier SMC), UCC27517 + ISO7710 (PWM) |
| Isolation | ISO7710 (PWM primaire) + DPC817 (EN) — plus de canal PWM dédié au secondaire |
| Secondaire (non isolé du primaire depuis 2026-10-25) | MOSFET N potentiel bas (rectification synchrone), UCC24612 (détection Vds, alimenté direct depuis Vout) + clamp TVS D4, banc Cout, pont bias 2×100kΩ |
| Couplage | Coilcraft MSD1514, 1:1 (k≈0,99), 10µH par enroulement |
| Limitation de courant (§19) | TSV791 (×10,09) + LMV7219 (comparateur) + 74LVC1G132/74LVC1G74 (blanking/verrou) + ISO7710F, 100% primaire sauf le retour isolé `I_Shunt_ht_comp` — coupe Q1 en ~100ns sur défaut, indépendant du C2000 |

Ce tableau n'a pas suivi toutes les évolutions depuis §13 (U8/U9, feuille
`polarisation.kicad_sch`, connecteur `J2`) — `00-intention-conception.md`
reste la source de vérité pour l'architecture actuelle.

L'isolation fonctionnelle (barrière contrôle↔puissance, via les AMC03xx/
ISO7710/DPC817) est dimensionnée pour l'écart réel présent sur la carte,
pas pour la tenue diélectrique complète des isolateurs (5000V) — pas de
slot d'isolation dans le PCB. Le primaire et le secondaire de puissance,
eux, ne sont plus traités comme deux domaines isolés (2026-10-25) : voir
`doc/plan-isolation-4couches.md`.

---

## Le schéma est généré, les feuilles sont ensuite routées à la main

```
00-intention-conception.md      source de vérité (calculs, marges, sourcing)
        │
        ├── gen_symboles.py        → lib/custom_parts.kicad_sym
        │                            (UCC27517, ISO7710, MSD1514, MOSFET 3 broches)
        │
        └── gen_composants.py      → alim.kicad_sch / flyback.kicad_sch /
              ▲                       isolation.kicad_sch (feuilles hiérarchiques)
              │                       kicad_gen.py — primitives communes
        étiquettes globales uniquement, aucun fil posé par script
```

Une fois qu'une feuille a été reprise à la main dans KiCad (repositionnement
des composants, rotation, déplacement des étiquettes Référence/Valeur), elle
devient un **fichier de travail permanent** : les générateurs ne sont plus
rejoués dessus.

ERC sur la hiérarchie complète des 3 feuilles : 0 erreur. Empreintes custom
(`lib_fp/*.pretty/`) pour l'inductance couplée MSD1514, le MOSFET TO-252 et le
condensateur KEMET A786MW (V-chip), toutes construites à partir des cotes
mécaniques des datasheets plutôt que d'une empreinte générique approximative.

Placement et routage du PCB restent manuels, comme pour les autres cartes de
ce workspace.

---

## Validation — simulation et mesure

| Étape                       | État                                   |
| --------------------------- | --------------------------------------- |
| Calcul analytique           | fait — [`00-intention-conception.md`](00-intention-conception.md) |
| Simulation LTspice (diode, 10W)       | étapes 1-4 faites, modèles réels (MOSFET Infineon, clamp D1) |
| Simulation LTspice (18,9W, synchrone) | faite — proxy UCC24612, clamp secondaire dimensionné |
| Redressement synchrone (KiCad)        | implémenté — UCC24612 (U12) + clamp D4 |
| Prototype                   | à fabriquer                            |
| Mesures au banc             | à faire                                |

Balayage à Vin=11/20/25V, 6V et 12V à 10W (+ un point à charge légère) :
rendement 84-91%, et la tension drain de Q2 dépasse déjà 100V (sa tenue
en tension) à Vin≥23V environ, sans clamp secondaire modélisé à ce
stade.

<p align="center">
  <img src="simulation/plots/envelope_eta_vds.png" alt="Rendement et Vds Q2 vs Vin, 10W, redressement par diode de corps" width="100%">
</p>

Autre résultat notable : la plupart des points réels fonctionnent en
**CCM**, pas en DCM comme une estimation rapide l'avait d'abord suggéré —
déterminé sur la forme d'onde (passage par zéro de I(L2)), pas supposé.
Comparé à un modèle Schottky générique simplifié (rapide mais pas le
composant réel) pour chiffrer la perte dans le clamp D1 :

<p align="center">
  <img src="simulation/plots/compare_real_vs_schottky.png" alt="Rendement modele reel vs simplifie, et perte dans le clamp D1" width="100%">
</p>

Rejoué à la cible réelle (**18,9W**) avec un proxy de redressement
synchrone : le dépassement empire (dès Vin=20V, jusqu'à 106,8V) —
indépendant du redresseur, c'est une résonance de l'inductance de fuite.
Le passage en synchrone (UCC24612) apporte jusqu'à +5 points de
rendement, mais ne corrige pas la surtension :

<p align="center">
  <img src="simulation/plots/envelope_eta_vds_18w9.png" alt="Rendement et Vds Q2 vs Vin, 18,9W, Schottky vs reel+synchrone" width="100%">
</p>

D'où le clamp secondaire **D4 (SMCJ54A)**, qui ramène Vds_Q2 à 61-65V
(marge ×1,5) pour 0,03-0,76W de dissipation (marge ×6,6 vs les 5W du
composant) — comparé au SMCJ43A (même réf. que D1, déjà au BOM) qui tient
aussi mais coûte jusqu'à 2 points de rendement de plus :

<p align="center">
  <img src="simulation/plots/clamp_comparison_18w9.png" alt="Comparaison clamp secondaire SMCJ43A vs SMCJ54A, dissipation et tenue en tension" width="100%">
</p>

Le détail, le protocole de mesure et le tableau calcul / simulation /
mesure : [`doc/sim-vs-mesure.md`](doc/sim-vs-mesure.md) (§7/§7bis pour le
passage 18,9W) ; l'implémentation KiCad correspondante :
[`00-intention-conception.md`](00-intention-conception.md) §16.

### Linéarisation HV_BIAS (`polarisation.kicad_sch`)

La boucle qui linéarise la polarisation flottante du secondaire (MCP6001 +
Q6/Q7, contre-réaction sur HV_BIAS) a d'abord été validée avec des modèles
idéaux, puis rejouée avec les composants réels (MMBF170, MCP6001 paramétré
depuis sa datasheet) une fois le schéma modifié. Ce passage aux modèles
réels a révélé un défaut invisible sur le schéma seul : à consigne figée,
la boucle part en oscillation auto-entretenue — un cycle limite qui
grandit puis se stabilise en amplitude constante, pas du bruit de
simulation, confirmé en figeant `VAR_GATE` et en observant le régime sur
plusieurs millisecondes :

<p align="center">
  <img src="simulation/plots/hv_bias_oscillation_decouverte.png" alt="Oscillation auto-entretenue trouvee en simulation, consigne VAR_GATE figee" width="100%">
</p>

La simulation a aussi servi à trouver un premier correctif et à le vérifier
avant de toucher au vrai schéma : une résistance de dégénérescence sur la
source de Q6 (330Ω) supprime l'oscillation sans sacrifier l'accès à
`HV_BIAS`=0V, et un condensateur de compensation autour de l'ampli-op
(1nF, sortie → entrée inverseuse) élimine le dépassement en échelon, même
au pire cas (front de commande 10ns).

Ce correctif n'a été validé qu'avec un signal d'entrée déjà filtré
(échelon analogique propre) — pas avec le vrai PWM du C2000. En rejouant
la boucle avec le PWM réel, il a fallu élargir le filtre d'entrée
(1kΩ/1nF → 100kΩ/100nF) pour écraser l'ondulation résiduelle avant
l'ampli-op, ce qui a réintroduit une oscillation auto-entretenue
différente — ~700kHz cette fois, confirmée indépendante du PWM par un
échelon direct avant le filtre (l'oscillation persiste à l'identique sans
aucun PWM : c'est la boucle elle-même qui devient instable avec ce
nouveau filtre, pas une fuite du signal de commande). Le premier
correctif n'avait jamais été vérifié pour ce filtre élargi.

Reporté : résistance de dégénérescence à 1kΩ (au lieu de 330Ω) et
condensateur de compensation à 100pF (au lieu de 1nF) stabilisent la
boucle avec le nouveau filtre d'entrée — vérifié sur le profil complet de
commande PWM (rapport cyclique 1%→60%→palier→99%→palier→40%→1%, 3,5s),
ondulation résiduelle en sortie sous le mV grâce au filtre de sortie déjà
en place :

<p align="center">
  <img src="simulation/plots/final-pwm.png" alt="Validation finale sous excitation PWM reelle sur le profil complet de rapport cyclique" width="100%">
</p>

---

## Licence

CERN-OHL-S v2 — voir [`LICENSE`](LICENSE).
