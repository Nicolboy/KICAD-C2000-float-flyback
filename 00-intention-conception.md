# Intention de conception — flyback flottant filament + préampli

| | |
|---|---|
| Révision | v0.2 — corners réels, clamp et filtrage tranchés |
| Établi le | 2026-09-28 |
| Statut | duty cycle et courants inductance vérifiés ; clamp TVS SMC et filtrage de sortie 50mV tranchés (§6, §7) |

Convention reprise de `composants-datasheets/CLAUDE.md` : `spec` = exigence
d'entrée · `déduit` = calculé · `?` = à trancher. Toute valeur `déduit` porte
sa formule et sa source.

## 1. Fonction

Flyback isolé flottant, 200kHz, alimentant un filament de chauffage tube +
étage de préamplification bas bruit. Secondaire flottant, élevable de 0 à
90V par pont 2×100k symétrique (Vout+/Vout- vers la source HV externe).

## 2. Grandeurs par nœud

| Nœud | Nominal | Max | Statut |
|---|---|---|---|
| `Vin` | 11 – 25 V | 25 V | spec |
| `Vout` | 5,5 – 13 V | 13 V | spec |
| `Iout` | — | 3 A | spec |
| `f_sw` | 200 kHz | — | spec |
| Bias secondaire (vers HV externe, 2×100k) | 0 – 90 V | 90 V | spec |

**Charge réelle — spec.** 10 filaments de tube préampli standard (12AX7 ou
EF86), câblage variable :

| Câblage | Vout | Iout | Pout |
|---|---|---|---|
| Parallèle | 6,3 V | 3 A | 18,9 W |
| Série (paires) | 12,6 V | 1,5 A | 18,9 W |

Les deux corners tombent à la **même puissance** (charge résistive de
filament à puissance constante). C'est ce couple qui pilote les calculs de
courant et de dissipation ci-dessous — **pas** le coin 13V/3A (39W) utilisé
en v0.1, qui surestimait largement la contrainte réelle. Le plafond `Vout
max = 13V` de la spec reste néanmoins la référence pour le dimensionnement
en **tension** (§5) : rien n'indique que 13V soit exclu, seulement que le
courant n'y atteint pas 3A dans l'usage prévu.

## 3. Étage primaire — duty cycle et courants

Coupled inductor MSD1514-103ME, 1:1 (k≈0,99), L=10µH chaque enroulement —
`datasheets/inductors/msd1514.pdf` p.2, tbl produit.

Rapport cyclique (1:1, pertes de diode ignorées au premier ordre) :
`D/(1-D) = Vout/Vin`

| Vin | Vout | D | Statut |
|---|---|---|---|
| 25 V | 6,3 V | 0,201 | déduit |
| 11 V | 12,6 V | 0,534 | déduit |
| 11 V | 6,3 V | 0,364 | déduit |

**Coin de pire cas retenu pour le courant primaire : Vin=11V (le plus
défavorable, courant d'entrée le plus élevé à puissance donnée), comparé
sur les deux câblages réels.**

Hypothèse de rendement **η=0,85** — **non sourcée, à vérifier au banc**,
basis: computed/assumed. C'est l'hypothèse la plus sensible de ce paragraphe.
Pin = 18,9 / 0,85 = 22,24 W dans les deux cas (même Pout).

```
                              Câblage 6,3V/3A    Câblage 12,6V/1,5A
D (à Vin=11V)                 0,364               0,534
Iin_avg = Pin/Vin              2,02 A              2,02 A
I_on_avg = Iin_avg/D            5,55 A              3,79 A
ΔI = Vin×D×T/L                  2,00 A              2,94 A
Ipk = I_on_avg + ΔI/2            6,55 A              5,25 A
Ivalley = I_on_avg − ΔI/2         4,55 A              2,32 A
I_on_rms                          5,58 A              3,88 A
I_primaire_rms = I_on_rms×√D        3,37 A              2,84 A
```

**Le câblage 6,3V/3A est le coin le plus contraignant** (Ipk et Irms les
plus élevés) — c'est lui qui pilote le clamp (§6) et le MOSFET primaire.

**Vérification vs MSD1514-103ME.** Le datasheet donne deux colonnes Irms :
« both windings » (5,4A) et « one winding » (7,6A) — la première vise les
topologies à conduction simultanée des deux enroulements (SEPIC/Zeta,
diagrammes typiques du même datasheet p.1), la seconde le flyback où les
deux enroulements conduisent en alternance, jamais ensemble. **C'est la
colonne « one winding » qui s'applique ici** (le flyback est un des schémas
typiques donnés pour ce composant, doc 1308-1 p.1).

| | Calculé (coin 6,3V/3A) | Limite (one winding) | Marge |
|---|---|---|---|
| Irms primaire | 3,37 A | 7,6 A | ×2,26 |

Marge large, pas de point dur sur l'inductance côté courant. Isat au pire
cas (Ipk=6,55A) est très en dessous de Isat-10% (12,2A) — pas de
saturation.

## 4. Étage secondaire — courants

Secondaire 1:1, conduction complémentaire du primaire (jamais simultanée).
Par continuité du flux (couplage k≈0,99), le courant secondaire démarre à
Ipk et redescend à Ivalley sur la durée (1-D)×T. Au coin dimensionnant
(6,3V/3A, Vin=11V, D=0,364) :

```
I_off_rms = même formule que I_on_rms = 5,58 A  (mêmes Ipk/Ivalley, durée différente)
I_secondaire_rms = I_off_rms × √(1-D) = 5,58 × √0,636 = 4,45 A
```

| | Calculé | Limite (one winding) | Marge |
|---|---|---|---|
| Irms secondaire | 4,45 A | 7,6 A | ×1,71 |

## 5. Contrainte en tension MOSFET primaire

Dimensionnement en **tension** : référencé au plafond de spec (13V), pas
au coin de charge réel — la tenue en tension ne dépend pas du courant tiré
à cette tension.

```
Vds_regime = Vin_max + Vout_max_reflected(1:1) + Vf_redresseur
           = 25 + (13 + 1) = 39 V     (Vf=1V, hypothèse diode de corps en phase bootstrap)
```

Reste à ajouter la surtension de commutation due à l'inductance de fuite
(0,40µH typ, même tableau datasheet) — voir §6, elle fixe le niveau de
clamp et donc la tenue en tension à viser pour le MOSFET.

## 6. Clamp primaire — TVS SMC, tranché

Énergie de fuite par cycle, au coin de charge réel dimensionnant
(6,3V/3A, Ipk=6,55A — §3) :

```
E_fuite = ½ × L_fuite × Ipk² = 0,5 × 0,40µH × 6,55² = 8,59 µJ
P_clamp = E_fuite × f_sw = 8,59µJ × 200kHz ≈ 1,72 W
```

Nettement plus raisonnable que l'estimation v0.1 (3,4W, basée sur le coin
13V/3A surestimé). **1,7W est tenable par un TVS en boîtier SMC/DO-214AB**
avec un cuivre de dissipation correct — décision retenue : **TVS/zener,
boîtier SMC**. Tension de claquage à sourcer pour couvrir les 39V de
Vds_regime (§5) avec marge de clamp, sans dépasser la tenue en tension du
MOSFET primaire retenu.

## 7. Filtrage de sortie — banc de condensateurs, tranché

Cible relâchée à **50mV** d'ondulation crête-crête max (décision utilisateur),
Iout et D pris au coin de charge réel dimensionnant (6,3V/3A, D=0,364,
Ipk=6,55A — §3, plus contraignant que 12,6V/1,5A).

**Composante capacitive** (le cap seul alimente la charge pendant Ton) :
```
ΔQ = Iout × D × T = 3 × 0,364 × 5µs = 5,46 µC
Pour ΔV_C = 20mV (part du budget) : C = ΔQ / ΔV_C ≈ 273 µF
```

**Composante ESR** (démonstration : le saut de courant dans le
condensateur vaut Ipk à l'ouverture, Ivalley à la fermeture — le premier
domine ; ΔV_ESR,pk-pk = ESR × Ipk, formule standard flyback, pas les 9,2A
de battement grossièrement estimés en v0.1) :
```
Pour ΔV_ESR = 30mV (reste du budget) : ESR_max = 30mV / 6,55A ≈ 4,6 mΩ
```

**4,6mΩ est atteignable par un petit banc de condensateurs polymère bas
ESR en parallèle** (ESR unitaire typique 10-15mΩ en boîtier CMS courant →
2 à 3 en parallèle suffisent, ESR combiné = ESR_unitaire / N). Décision
retenue : **banc de 2-3 condensateurs polymère CMS en parallèle**, cible
combinée ESR ≤ 4,6mΩ et C ≥ 273µF. Références précises à sourcer (§ sourcing
composants).

## 8. Condensateurs — Cin, Cout, Cboot, tranchés

**Cin** (entrée, coin de charge réel 6,3V/3A, D=0,364, §3) :

```
I_on_rms = 5,58A, I_on_avg = 5,55A  (§3)
Icin_rms = √(D×(I_on_rms² − D×I_on_avg²))
         = √(0,364×(5,58² − 0,364×5,55²)) = 2,69A
```

Première solution retenue : 2× UCM1V222M1MS (Nichicon UCM, 2200µF/35V,
45mΩ) — 4,12A de marge ripple mais 22,5mΩ combiné, soit ~149mV
d'ondulation d'entrée réelle (calcul complet ci-dessous, pas de cible
formelle contrairement à la sortie). **Remplacée** (utilisateur,
2026-09-29) par **1× KEMET A786MW477M1VLAV010** (hybride polymère,
470µF/35V, ESR=10mΩ) —
`composants-datasheets/data/carte-flyback/a786mw477m1vlav010.yaml` :

```
ΔV_ESR = 10mΩ × 6,553A (Ipk, §3)                         ≈ 65,5mV
ΔV_C   = (I_on_avg−Iin_avg)×D×T / C = 3,532A×0,364×5µs/470µF ≈ 13,7mV
Total  ≈ 79,2mV — contre 148,9mV avec l'ancienne solution (2×UCM)
```

Un seul exemplaire suffit (comparé à l'option 2× qui donnait 39,6mV — écartée
par l'utilisateur au profit d'un seul composant). Ripple current très
large marge (5,6A@125°C vs 2,69A requis, ×2,08). Marge tension ×1,4 (35V
vs 25V Vin_max), identique à l'ancienne solution.

**Cout** (sortie, cible relâchée à 50mV — décision utilisateur du
2026-09-28, coin de charge réel 6,3V/3A, Ipk=6,55A, D=0,364, §3) :

```
ΔQ = Iout×D×T = 3×0,364×5µs = 5,46µC
ΔV_ESR(N) = (ESR_unitaire/N) × Ipk        ΔV_C(N) = ΔQ/(C_unitaire×N)
```

Un électrolytique « low impedance » classique (famille UCM, ~24-45mΩ pour
un gros boîtier) ne permet pas d'approcher l'ESR combiné visé sans un
nombre de boîtiers déraisonnable. Première solution retenue (5×
Panasonic 25SVPF100M, 100µF/25V, ESR=24mΩ) donnait 42,4mV — marge 15%
seulement. **Remplacée** (utilisateur, 2026-09-29) par **2× Panasonic
16SVPG330M** (330µF/16V, ESR=6,5mΩ — le plus bas de sa série) —
`composants-datasheets/data/carte-flyback/16svpg330m.yaml` :

```
ΔV_ESR = (6,5mΩ/2)×6,55A ≈ 21,3mV
ΔV_C   = 5,46µC/660µF    ≈ 8,3mV
Total  ≈ 29,6mV < 50mV — marge 41%. (N=1 donne 59,1mV, insuffisant.)
```

Moins de composants (2 au lieu de 5), meilleure marge d'ondulation, mais
marge en tension plus courte : 16V vs Vout_max=13V = ×1,23 (23%), contre
×1,92 pour l'ancienne solution — acceptée explicitement par l'utilisateur
après avoir vu le calcul.

**Cboot** (stockage bootstrap secondaire, alimente UCC27517-secondaire en
direct + MCP1703 en amont de l'ISO7710-secondaire — architecture validée
avec l'utilisateur en amont de cette session) :

```
Qg(IPB020N10N5) = 210nC (max, composants-datasheets/data/carte-flyback/ipb020n10n5.yaml)
Iq(UCC27517+MCP1703+ISO7710) ≈ 5mA (ordre de grandeur, non individuellement sourcé)
Intervalle de décharge = Ton (primaire) au pire cas = D×T = 0,364×5µs = 1,82µs
ΔQ ≈ Qg + Iq×Ton ≈ 210nC + 5mA×1,82µs ≈ 219nC
Pour ΔV_droop = 200mV (marge sous l'hystérésis UVLO UCC27517, 300mV typ) :
C_boot = ΔQ/ΔV ≈ 1,1µF minimum
```

Retenu : **4,7µF X7R 0805, 25V** — céramique standard (pas de fiche
sourcée séparée : composant passif générique, cohérent avec la pratique du
reste du dépôt pour le découplage). Marge large même avec déclassement en
tension continue typique du X7R (effective ~2-3µF sous polarisation
~6-12,5V, encore ≥ le minimum calculé).

## 9. Alimentation auxiliaire primaire — ajout non prévu dans la spec initiale

En construisant le schéma, un trou est apparu : rien n'alimente l'UCC27517
et l'ISO7710 côté **primaire** (référencé masse, pas de problème de
flottement contrairement au secondaire, mais Vin=11-25V dépasse la plage
recommandée de l'UCC27517 — 4,5-18V — et l'absolu de l'ISO7710 — 5,5V max).
Il faut une alim auxiliaire primaire, absente de la spec initiale.

Repris à l'identique du montage déjà en service sur l'autre carte de ce
workspace (`00-intention-conception-v12.md` §7/§10, dual-boost) : **LM317M
+ pont 100Ω/560Ω → 8,25V** pour l'UCC27517-primaire (`data/carte-puissance/
lm317m.yaml`, déjà sourcé — repris pour `carte-flyback` avec ses propres
repères), puis **MCP1703-3302 en cascade depuis ce rail 8,25V** (déjà
sourcé pour le secondaire, `data/carte-flyback/mcp1703.yaml`) → 3,3V pour
l'ISO7710-primaire. Deux avantages à cascader plutôt que deux régulateurs
depuis Vin directement : le MCP1703 n'a plus à encaisser les 25V de Vin_max
(son propre Vin_max est 16V, insuffisant en direct), et aucun nouveau
composant à sourcer.

```
Vout(LM317M) = 1,25×(1+R2/R1) = 1,25×(1+560/100) = 8,25V   (mêmes valeurs que l'autre carte)
Différentiel au point bas : Vin_min − Vout = 11 − 8,25 = 2,75V
```

Sous le dropout min publié (3,0V, `lm317m.yaml`) — **même marge que l'autre
carte**, qui traite déjà ce point comme acceptable (« clôt la question du
dropout » dans son propre document d'intention). Pas retranché ici.

Dissipation estimée (Q1 Qg=72nC×200kHz≈14,4mA + ISO7710 primaire ~1,7mA +
marges ≈20mA) : P=(25−8,25)×20mA≈0,34W. Avec Rth_ja=245°C/W (boîtier
SOT-223, empreinte minimale — même valeur élevée déjà notée comme
suspecte sur l'autre carte) : ΔT≈82°C, Tj≈107°C à 25°C ambiant — chaud
mais sous Tj_max=150°C. Cuivre de dissipation à soigner au routage, comme
sur l'autre carte.

## 10. Composants sourcés — récapitulatif

| Rôle | Réf. | Composant | Fiche |
|---|---|---|---|
| MOSFET primaire+secondaire | Q1, Q2 | IPD050N10N5 (TO-252/DPAK, 100V, 5mΩ) | `data/carte-flyback/ipd050n10n5.yaml` |
| Empreinte Q1/Q2 | — | `lib_fp/TO252.pretty/TO252-3_TabPin2.kicad_mod`, custom (3 pastilles, cotes Figure 1 du datasheet IPD050N10N5 fournies par l'utilisateur) — remplace la générique KiCad jugée peu lisible (4 pastilles) |
| Clamp primaire | D1 | SMCJ43A (SMC/DO-214AB) | `data/carte-flyback/smcj43a.yaml` |
| Rail 8,25V primaire | Reg1 | LM317M (SOT-223) + R1=100Ω/R2=560Ω | `data/carte-flyback/lm317m.yaml` |
| LDO ISO7710 primaire | Reg2 | MCP1703-3302 (SOT-23A, 3,3V) | `data/carte-flyback/mcp1703.yaml` |
| LDO ISO7710 secondaire | Reg3 | MCP1703-3302 (SOT-23A, 3,3V) | `data/carte-flyback/mcp1703.yaml` |
| Cin | C1 | A786MW477M1VLAV010 (KEMET, 470µF/35V, 10mΩ) | `data/carte-flyback/a786mw477m1vlav010.yaml` |
| Cout | C3, C4 | 2× Panasonic 16SVPG330M (330µF/16V, 6,5mΩ) | `data/carte-flyback/16svpg330m.yaml` |
| Cboot | — | 4,7µF X7R 0805/25V (générique) | non sourcé séparément (§8) |

## 10. Points ouverts

- [ ] Rendement η=0,85 utilisé en §3 — hypothèse, à vérifier au banc
- [ ] Vf du redresseur secondaire en phase bootstrap (§5) — 1V pris par
      hypothèse. IPB020N10N5 (sourcé) donne Vf_body_diode=1,2V max à 100A
      (très au-dessus du courant réel ~6,55A) — conforte l'hypothèse comme
      raisonnablement conservatrice sans la remplacer par une lecture de
      courbe précise (fig.12 du datasheet, non faite)
- [ ] Diode de bootstrap secondaire elle-même (Vout → Cboot) — pas encore
      choisie ; la chute Vf≈0,5V utilisée en §"Alim secondaire" pour le
      calcul de marge du MCP1703 est une hypothèse à confirmer une fois le
      composant sourcé
- [x] Pertes de conduction Q1/Q2 — résolu par le passage en TO-252
      (IPD050N10N5, 2026-09-28) : Rds_on max 5mΩ contre 77mΩ pour l'ancien
      IRF540S. Pertes recalculées négligeables (~113-198mW, ΔT≈15°C même en
      empreinte minimale) — l'ancien point dur (1,75W, proche de la limite
      D2PAK) n'existe plus.
- [ ] Snubber/clamp éventuel côté secondaire (Q2 voit aussi une surtension
      de commutation, cf. plan initial) — pas encore traité, à revoir avant
      le routage final
- [x] Empreinte MSD1514 — corrigée (`lib_fp/MSD1514.pretty/MSD1514.kicad_mod`)
      à partir d'un crop fourni par l'utilisateur du « Recommended Land
      Pattern » (doc 1308-3 p.3), lu directement plutôt que ré-interprété
      depuis une vue pleine page. Mes deux premières lectures (pastilles
      4,2×2,8mm, différentes valeurs de pas) étaient fausses. Valeurs
      retenues : **pastilles carrées 3,7×3,7mm, pas X=7,9mm/Y=6,0mm**,
      dérivées de gapX=4,2mm/gapY=2,3mm avec vérification croisée
      (pitch−gap = 3,7mm des deux côtés). Numérotation
      pin3=haut-gauche/pin2=haut-droite/pin4=bas-gauche/pin1=bas-droite,
      lue sur ce même diagramme — **toujours pas confirmée par capture
      photo de la pièce réelle**, à vérifier avant le premier reflow (même
      discipline que R15 de `composants-datasheets/CLAUDE.md`).
- [x] Empreinte A786MW477M1VLAV010 (Cin) — corrigée quatre fois par
      l'utilisateur (2026-09-29) : (1) confusion D×L=footprint vs corps
      cylindrique (V-chip monté vertical, D=10mm de diamètre, L=16,7mm de
      HAUTEUR, pas une dimension de pastille), (2) pas pastilles affiné
      4,6→7,6mm, (3) rectangle à coins coupés ajouté — mal placé au
      premier essai (autour de la pastille), (4) corrigé : le rectangle
      chanfreiné représente l'**implantation totale du composant**
      (10,3×10,3mm, coins coupés côté positif), superposé au cercle D10mm
      (le corps cylindrique) — deux silhouettes silkscreen distinctes, pas
      un contour de pastille. `lib_fp/A786.pretty/A786MW_VChip.kicad_mod`.
- [x] Empreinte MSD1514 — corrigée deux fois (2026-09-29) : première
      lecture du land pattern (pastilles 3,7×3,7mm, pas 7,9×6,0mm)
      fausse ; cotes réelles pastilles 4,6×2,5mm, pas X=12,6mm/Y=3,8mm
      (Y affiné de 3,5 à 3,8mm) — le pas X dépasse le corps 15×15mm
      (pattes gull-wing débordant du corps, normal pour ce boîtier),
      courtyard élargi en conséquence. Numérotation des broches inchangée
      (pin3=HG/pin2=HD/pin4=BG/pin1=BD).
- [ ] Polarité du point de couplage L2 (pin2 vs pin4 du MSD1514, §
      symboles) déduite par symétrie du schéma simplifié du datasheet, pas
      explicitement marquée — à confirmer sur pièce réelle avant simulation.

## 11. État du projet KiCad

Schéma généré par script (`gen_composants.py`, méthode reprise de
shield-c2000 : étiquettes globales uniquement, aucun fil, empreintes posées
sur l'instance). **Restructuré en feuilles hiérarchiques** sur demande de
l'utilisateur (2026-09-28) : une feuille racine (`alim-flyback-filament.kicad_sch`,
3 blocs `(sheet ...)`) + trois sous-feuilles —

| Feuille | Fichier | Contenu | Composants |
|---|---|---|---|
| Alimentation | `alim.kicad_sch` | Connecteurs, Reg1/Reg2/Reg3 (LDO), PWR_FLAG | 17 |
| Flyback | `flyback.kicad_sch` | Cin, T1, Q1/Q2, clamp D1, bootstrap D2/C8, Cout | 15 |
| Isolation_Drivers | `isolation.kicad_sch` | UCC27517×2, ISO7710×2, DPC817 | 9 |

Les étiquettes globales se relient à travers toute la hiérarchie sans rien
changer au câblage — le découpage est purement organisationnel, suit la
frontière fonctionnelle (et pour partie la frontière d'isolement primaire/
secondaire) plutôt que la connectivité. **41 composants au total**, ERC sur
la hiérarchie complète : **0 erreur, 1 avertissement attendu** (GND2 de U4,
feuille Isolation_Drivers, relié à `VOUT_N` et non à un net nommé `GND` —
c'est la référence locale du secondaire flottant, volontairement différente
de la masse primaire).

PCB généré avec contour de carte (70×55mm, à ajuster) mais **rien n'est
encore placé** — F8 dans KiCad (« Mettre à jour le PCB depuis le schéma »)
puis placement et routage sont les étapes manuelles suivantes, comme pour
les autres cartes de ce workspace.

Fichiers : `alim-flyback-filament.kicad_pro/.kicad_sch/.kicad_pcb`,
`lib/custom_parts.kicad_sym`, `kicad_gen.py`, `gen_symboles.py`,
`gen_composants.py`.
