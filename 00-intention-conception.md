# Intention de conception — flyback flottant filament + préampli

| | |
|---|---|
| Révision | v0.7 — feuille Polarisation : pilotage actif HV_BIAS 0-90V depuis 400V |
| Établi le | 2026-09-28, mis à jour 2026-10-02 |
| Statut | duty cycle et courants inductance vérifiés ; clamp TVS SMC et filtrage de sortie 50mV tranchés (§6, §7) ; retour ADC isolé AMC0311S ajouté (§12) ; UCC5304 essayé puis abandonné côté secondaire, marge UVLO insuffisante pour un filament réglable (§12bis) ; retours température MOSFET/transfo et courant primaire ajoutés, isolateurs migrés vers la famille ratiométrique AMC03x1R/AMC03x2R (§13) ; isolation C2000 rendue réelle — U3/U4/U5/U7/U8/U9 migrés sur GND_CTRL/3V3_CTRL, connecteur scindé CpuOut/CpuIn (§14) ; nouvelle feuille Polarisation — HV_BIAS piloté activement 0-90V depuis une source 400V externe, connecteurs C2000 agrandis à 16 broches (§15) |

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
| Empreinte Q1/Q2 | — | `lib_fp/TO252.pretty/TO252-3_TabPin2.kicad_mod`, custom (3 pastilles, cotes Figure 1 du datasheet IPD050N10N5 fournies par l'utilisateur) — remplace la générique KiCad jugée peu lisible (4 pastilles). **Pin1(Gate)/Pin3(Source) permutées (2026-10-01)** — voir point ouvert résolu ci-dessous. Modèle 3D (2026-10-01) : d'abord le `.step` fourni avec KiCad (miroir corrigé par `scale -1 1 1`), puis **remplacé** par `composants-datasheets/datasheets/to_252_2.step` (step.parts.com, 3 broches + tab, boîtier compact — fourni par l'utilisateur). Transform identité par défaut, alignement à confirmer dans le visualiseur 3D (pas de rendu possible de mon côté) |
| Clamp primaire | D1 | SMCJ43A (SMC/DO-214AB) | `data/carte-flyback/smcj43a.yaml` |
| Rail 8,25V primaire | Reg1 | LM317M (SOT-223) + R1=100Ω/R2=560Ω | `data/carte-flyback/lm317m.yaml` |
| LDO ISO7710 primaire | Reg2 | MCP1703-3302 (SOT-23A, 3,3V) | `data/carte-flyback/mcp1703.yaml` |
| LDO auxiliaire secondaire | Reg3 | MCP1703-3302 (SOT-23A, 3,3V) — alimente VCC2 de l'ISO7710 secondaire (U4) et VDD1 de l'AMC0311S (U7) | `data/carte-flyback/mcp1703.yaml` |
| Cin | C1 | A786MW477M1VLAV010 (KEMET, 470µF/35V, 10mΩ) | `data/carte-flyback/a786mw477m1vlav010.yaml` |
| Cout | C3, C4 | 2× Panasonic 16SVPG330M (330µF/16V, 6,5mΩ) | `data/carte-flyback/16svpg330m.yaml` |
| Cboot | — | 4,7µF X7R 0805/25V (générique) | non sourcé séparément (§8) |
| Ampli isolé retour Vout | U7 | AMC0311R (DWV-8, ratiométrique) — retour Vout isolé vers C2000 (§12, renommé depuis AMC0311S en §13) | à sourcer (`composants-datasheets/data/carte-flyback/amc0311r.yaml`, session dédiée) |
| Diode bootstrap secondaire | D2 | BAT54C (SOT-23, Schottky double cathode commune — un seul canal utilisé, pin2/2e anode en réserve) | à sourcer (remplace BAT54/SOD-123, §12bis) |
| Empreinte U7/U8/U9 | — | `lib_fp/SOIC_DWV.pretty/SOIC-8_DWV_5.85x11.5mm_P1.27mm.kicad_mod`, custom (boîtier DWV renforcé, cotes land pattern fournies par l'utilisateur) — modèle 3D `DWV0008A.stp` fourni par l'utilisateur, transform identité à affiner (§13) |
| Thermistance temp. primaire | TH1 | NTC 10k/B=4000, 0805 | non sourcé séparément (§13) |
| Ampli isolé retour température | U8 | AMC0311R (DWV-8, ratiométrique) — retour température primaire isolé vers C2000 (§13) | à sourcer |
| Shunt courant primaire | R19 | 1210, valeur provisoire 7,5mΩ | à sourcer (valeur et dissipation, §13) |
| Ampli isolé retour courant | U9 | AMC0302R (DWV-8, ratiométrique, ±50mV) — retour courant primaire isolé vers C2000, protection surcourant Q1 (§13) | à sourcer |

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
- [x] **Pin1(Gate)/Pin3(Source) de l'empreinte TO252-3_TabPin2 étaient
      permutées** (2026-10-01) — la réserve initiale du fichier
      d'empreinte (« pin1=haute/pin3=basse, pas confirmé par capture
      photo ») était fondée. L'utilisateur a fourni un croquis Infineon
      TO220/DPAK (languette en haut, broches 1-2-3 gauche-à-droite,
      1=Gate/2+tab=Drain/3=Source). Recalcul géométrique : en tournant la
      pièce réelle pour amener la languette à gauche (notre disposition),
      Gate doit tomber en bas-droite et Source en haut-droite — l'inverse
      de ce qui était posé. Pastilles 1 et 3 permutées (tab/pin2 inchangé).
      **À confirmer malgré tout sur pièce réelle avant premier reflow**,
      même règle que pour toute empreinte custom de ce dépôt (R15,
      `composants-datasheets/CLAUDE.md`).
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
- [x] Marge VDD de l'UCC5304 au coin bas — **résolu en revenant à
      ISO7710+UCC27517 sur le secondaire** (§12bis) : le plancher réel
      d'usage n'est pas 6,3V mais jusqu'à 5,8V (filament réglable -5 à
      -10% sur 6,3V nominal), ce qui aurait mis VBOOT sous le seuil UVLO
      *garanti* (pas juste recommandé) de l'UCC5304 — voir calcul précis
      §12bis avec les seuils UVLO réels du datasheet (p.8 tbl 6.9).
- [ ] Valeurs du filtre RC en sortie de l'AMC0311S (R15=100Ω, C24=1nF,
      §12) — proposées par défaut (fc≈1,6MHz, n'entame pas la bande
      passante propre de l'ampli ~120kHz), à revoir une fois la spec
      d'entrée de l'ADC côté C2000 connue.
- [ ] R11/R12 (résistances de grille en sortie des UCC, 1Ω/0805) — valeur
      retenue par l'utilisateur directement dans KiCad, pas de calcul de
      dimensionnement tracé ici (amortissement/EMI, ordre de grandeur
      courant pour ce type d'application).

## 11. État du projet KiCad

Schéma généré par script (`gen_composants.py`, méthode reprise de
shield-c2000 : étiquettes globales uniquement, aucun fil, empreintes posées
sur l'instance). **Restructuré en feuilles hiérarchiques** sur demande de
l'utilisateur (2026-09-28) : une feuille racine (`alim-flyback-filament.kicad_sch`,
3 blocs `(sheet ...)`) + trois sous-feuilles —

| Feuille | Fichier | Contenu | Composants |
|---|---|---|---|
| Alimentation | `alim.kicad_sch` | Connecteurs, Reg1/Reg2/Reg3 (LDO), PWR_FLAG | 17 (initial) |
| Flyback | `flyback.kicad_sch` | Cin, T1, Q1/Q2, clamp D1, bootstrap D2/C8, Cout | 15 (initial) |
| Isolation_Drivers | `isolation.kicad_sch` | UCC27517×2, ISO7710×2, DPC817 (initial) | 9 (initial) |

Les étiquettes globales se relient à travers toute la hiérarchie sans rien
changer au câblage — le découpage est purement organisationnel, suit la
frontière fonctionnelle (et pour partie la frontière d'isolement primaire/
secondaire) plutôt que la connectivité.

**Depuis (2026-09-30), les 3 feuilles sont des fichiers de travail
hand-edited** (placement, câblage et réorganisation faits à la main dans
KiCad par l'utilisateur, plus jamais régénérés par script) — voir §12 pour
le détail des changements les plus récents (UCC5304, AMC0311S, Cpu1).
Composants redistribués entre feuilles par l'utilisateur au passage :
`J1→In1`, `J3→Out1`, `J4→Bias1` (renommés), `Reg3/C11/C12/R9/R10` déplacés
vers Flyback, `J2→Cpu1` déplacé vers Isolation_Drivers, `C1` déplacé vers
Alimentation — connectivité inchangée (les étiquettes globales ignorent la
feuille physique), seule l'organisation visuelle a bougé.

PCB généré avec contour de carte (70×55mm, à ajuster) — placement et
routage sont les étapes manuelles suivantes, comme pour les autres cartes
de ce workspace.

Fichiers : `alim-flyback-filament.kicad_pro/.kicad_sch/.kicad_pcb`,
`lib/custom_parts.kicad_sym`, `kicad_gen.py`, `gen_symboles.py`,
`gen_composants.py` (génération initiale, ne plus rejouer sur les feuilles
hand-edited).

**Modèles 3D des empreintes custom (2026-10-01)** : les trois empreintes
custom (Q1/Q2, T1, C1) ont chacune un `.step` référencé dans leur bloc
`(model ...)`. Source de chaque fichier :
- Q1/Q2 (`TO252.pretty`) : `composants-datasheets/datasheets/to_252_2.step`
  (step.parts.com, 3 broches + tab, boîtier compact)
- T1 (`MSD1514.pretty`) : `composants-datasheets/datasheets/inductors/MSD1514.STEP`
  (modèle fabricant Coilcraft, téléchargé par l'utilisateur), rotation
  `(rotate (xyz 270 0 90))` nécessaire pour le redresser
- C1 (`A786.pretty`) : `composants-datasheets/datasheets/capacitors/A786MW477M1VLAV010.step`
  (modèle Mouser/SamacSys, téléchargé par l'utilisateur)

Alignement vérifié visuellement dans KiCad par l'utilisateur au fur et à
mesure — pas de rendu 3D possible côté agent, uniquement validation
syntaxique (`kicad-cli fp export svg`).

## 12. Secondaire UCC5304 + retour Vout isolé AMC0311S (2026-09-30)

Deux changements demandés par l'utilisateur, ajoutés par édition
chirurgicale de `isolation.kicad_sch` (suppression/ajout de blocs ciblés,
jamais de régénération — voir note ci-dessus) :

**1. ISO7710 (U4) + UCC27517 (U2) secondaires → UCC5304 (U6) seul.**
UCC5304 (`datasheets/isolation/ucc5304.pdf`, p.3 tbl Pin Functions, DWV-8) :
driver de grille isolé renforcé 4A source/6A sink, une seule puce fait ce
que faisaient les deux composants combinés (isolation + drive). Brochage :
IN(1)=PWM_SEC_IN, VCCI(2,3)=RAIL_3V3_PRI, GND(4)=GND, VSS(5,6)=VOUT_N,
OUT(7)=SEC_GATE_DRV (→ R12 → GATE_Q2, résistance de grille déjà posée par
l'utilisateur), VDD(8)=VBOOT. Empreinte
`Package_SO:SOIC-8_7.5x5.85mm_P1.27mm` (standard KiCad — comparaison
pastille-à-pastille contre le land pattern datasheet p.30 : 1,8×0,6mm,
pas 1,27mm, correspondance quasi-exacte, pas d'empreinte custom requise).

Le canal secondaire ne recevait déjà pas de signal EN isolé (IN+ de
l'ancien U2 était câblé sur VBOOT, toujours actif dès le bootstrap monté)
— remplacer par UCC5304 (une seule broche IN) ne perd donc aucune
fonction.

**Point ouvert (marge VDD)** : VBOOT ≈ Vout_min − Vf(D2) ≈ 6,3 − 0,3~0,5 ≈
5,8-6,0V au coin réel le plus bas (§3) — juste à la limite basse
recommandée de VDD (6V) de l'UCC5304, quoique nettement au-dessus de son
UVLO réel (5V typ, p.1/p.4). Marge plus courte que l'ancien UCC27517
(4,5V mini) — à surveiller au banc.

**2. Retour Vout isolé — AMC0311S (U7), nouveau, absent de la spec
initiale.** AMC0311S (`datasheets/isolation/amc0311s.pdf`, p.3 tbl 5-1,
DWV-8) : ampli isolé précision, gain fixe 1V/V, entrée linéaire 0-2,25V
(clipping doux à 2,56V, p.4 tbl 6.3). Reg3 (MCP1703, déjà en place pour
l'ancien ISO7710 secondaire) est **réutilisé**, pas orphelin : il
alimentait VCC2 de U4, alimente maintenant VDD1 de U7.

```
Côté secondaire (field, VOUT_N-référencé) :
  VDD1=RAIL_3V3_SEC (Reg3)   GND1=VOUT_N   SNSN=VOUT_N (« connect to GND1 »)
  INP=VOUT_SENSE (point milieu diviseur R13/R14)
Côté primaire (control, GND-référencé) :
  VDD2=RAIL_3V3_PRI   GND2=GND   REFIN=GND (« connect to GND2 if unused »)
  OUT=VOUT_FBACK_RAW (→ filtre R15/C24 → VOUT_FBACK, vers Cpu1)
```

**Diviseur R13/R14** (sonde VOUT_P/VOUT_N vers INP), + **C23 = 100pF**
en parallèle de R14 sur demande explicite de l'utilisateur (compense la
réponse HF du pont) :
```
R13 = 51k (haut)   R14 = 10k (bas)   ratio = 10/61 = 0,1639
Vout=13V (spec max)    → INP=2,13V   (< 2,25V linéaire, marge 0,12V)
Vout=12,6V (coin réel) → INP=2,07V
Vout=6,3V  (coin réel) → INP=1,03V
```

**Filtre RC de sortie** (R15=100Ω série, C24=1nF vers GND, sur demande de
l'utilisateur) : fc≈1,6MHz — valeurs par défaut, n'entament pas la bande
passante propre de l'AMC0311S (~120kHz typ), à revoir une fois la spec
d'entrée ADC du C2000 connue (point ouvert, §10bis).

**Découplage (règle utilisateur, 100nF/0805 par CI)**, appliquée à U6/U7
uniquement (pas de retrofit sur U1/U3/U5, décision explicite) :
C25 (RAIL_3V3_PRI-GND, U6 VCCI), C26 (VBOOT-VOUT_N, U6 VDD), C27
(RAIL_3V3_SEC-VOUT_N, U7 VDD1), C28 (RAIL_3V3_PRI-GND, U7 VDD2).

**3. Cpu1 (ex-J2, connecteur de commande vers le C2000 externe) agrandi de
4 à 16 broches** (8 signaux + 8 masses en alternance stricte 1:1) — reprend
le motif déjà en place sur `shield-c2000` (liaison shield↔puissance,
4 nappes 2×8). Meilleure intégrité de signal sur les fronts PWM isolés et
le retour analogique (masse dédiée adjacente à chaque signal plutôt
qu'une masse unique partagée) et marge pour signaux futurs :
```
1=PWM_PRI_IN 2=GND 3=EN_PRI_IN 4=GND 5=PWM_SEC_IN 6=GND
7=VOUT_FBACK 8=GND 9/11/13/15=réserve (no_connect) 10/12/14/16=GND
```
Cpu1 (ancienne version 4 broches) n'était en réalité **pas câblé** au
moment de sa découverte — déplacé/renommé depuis J2 sans que les
étiquettes suivent le déplacement. Aucune connectivité perdue en le
remplaçant par la version 16 broches.

Vérification : `kicad-cli sch erc` sur la hiérarchie complète après
édition — **0 erreur**, 4 avertissements (tous attendus : `lib_symbol_mismatch`
MSD1514 déjà documenté comme bénin, + `ground_pin_not_ground` sur U6 VSS×2
et U7 GND1 — même motif déjà accepté pour l'ancien U4, le secondaire
flottant est référencé à `VOUT_N` et non à un net nommé `GND` par
conception).

## 12bis. Retour sur UCC5304 — marge UVLO insuffisante pour un filament réglable (2026-09-30)

**UCC5304 abandonné côté secondaire, retour à ISO7710 (U4) + UCC27517
(U2)** comme avant §12. Cause : l'utilisateur veut pouvoir régler la
tension filament 5 à 10% en dessous du nominal 6,3V, donc supporter
Vout≈5,8V **en régime établi**, pas seulement en transitoire.

Seuils UVLO réels de l'UCC5304 (`datasheets/isolation/ucc5304.pdf`, p.8
tbl 6.9 Electrical Characteristics — pas la valeur unique simplifiée
« 5V UVLO » de la page de garde) :

| Seuil | Min | Typ | Max |
|---|---|---|---|
| VDD UVLO montée (démarrage) | 5,0V | 5,5V | 5,9V |
| VDD UVLO descente (reste actif) | 4,7V | 5,2V | 5,6V |

À Vout=5,8V : VBOOT ≈ 5,8 − Vf(D2) ≈ 5,4-5,5V (Vf BAT54 à faible courant,
§8) — **en dessous du seuil de démarrage typique (5,5V) et du seuil de
maintien pire-cas (5,6V)**. Risque réel de non-démarrage ou de décrochage
UVLO en régime établi, pas qu'une marge « recommandée » entamée comme au
coin 6,3V (§12). L'ancien UCC27517 (UVLO ≈4,2V typ, `carte-puissance/
ucc27517.yaml`) conserve une marge large jusqu'à 5,8V. **U7 (AMC0311S) et
le retour Vout isolé sont conservés inchangés** — ce point ne concernait
que le choix du driver secondaire.

**D2 : BAT54 (SOD-123, 2 broches) → BAT54C (SOT-23, Schottky double
cathode commune)**, décision utilisateur indépendante prise au même
moment : pin1(A)=VOUT_P, pin3(K commune)=VBOOT, pin2 (2e anode) en
réserve (`no_connect`). Objectif : grappiller de la marge sur Vf en
prévision d'un futur ajustement, la référence exacte reste à sourcer
(`composants-datasheets/data/carte-flyback/`, remplace `bat54.yaml` s'il
existait déjà une fiche pour l'ancien BAT54 — à vérifier).

Édition chirurgicale : retrait de U6/C25/C26 (+ leurs étiquettes, qui ne
sont PAS des enfants du bloc symbole dans ce format de fichier et doivent
être retirées séparément), repose de U4/U2 au brochage d'origine, D2
remplacé. `kicad-cli sch erc` : **0 erreur**, 3 avertissements — retour
exact à la même catégorie d'avertissements que la toute première version
du schéma (MSD1514 + GND2 de U4 + GND1 de U7, ce dernier n'existant pas
avant l'ajout du retour Vout).

## 13. Retours température primaire et courant primaire isolés, migration AMC0311S→AMC0311R (2026-10-02)

**Bug trouvé et corrigé — C20/C22 n'étaient pas les seuls.** En vérifiant
le câblage de U7 avant de le dupliquer pour un nouveau capteur, C18
(découplage côté `VDD1`/`GND1` de U7, censé être `RAIL_3V3_SEC`/`VOUT_N`
comme le reste du secondaire flottant) s'est révélé câblé
`RAIL_3V3_SEC`/**`GND`** — même défaut que C20/C22 (§ séance précédente,
pont AC vers le primaire sur un rail flottant). Corrigé : label `GND` du
côté concerné → `VOUT_N`.

**AMC0311S → AMC0311R (U7), et AMC0302R introduit (U9).** TI a réorganisé
cette famille d'amplis isolés en deux lignées : suffixe **R** = sortie
single-ended ratiométrique (calée sur `REFIN`, branchable directement sur
un ADC sans étage supplémentaire), suffixe **D** = sortie différentielle à
gain fixe (nécessite soit un réseau résistif précis soit un ampli-op
tampon pour respecter l'impédance source voulue par l'ADC SAR du C2000).
U7 est renommé AMC0311S→**AMC0311R** (même brochage VDD1/INP/SNSN/GND1 —
GND2/REFIN/OUT/VDD2, fiche `datasheets/isolation/amc0311r.pdf`). Nouveau
boîtier : **DWV** (SOIC-8 large, 5,85×11,5mm, isolation renforcée 5kVrms)
— aucune empreinte KiCad standard ne couvre cette taille (le plus grand
SOIC-8 bundled plafonne à 7,5×5,85mm), empreinte custom créée :
`lib_fp/SOIC_DWV.pretty/SOIC-8_DWV_5.85x11.5mm_P1.27mm.kicad_mod`, cotes
du land pattern fournies par l'utilisateur (crop datasheet, 2026-10-02) :
8 pastilles 1,8×0,6mm, pas 1,27mm, entraxe gauche-droite 10,9mm (9,1mm de
creepage nominal entre les deux groupes — c'est cet écart qui impose le
boîtier large). Modèle 3D `DWV0008A.stp` fourni par l'utilisateur, attaché
en transformation identité (offset/rotate à affiner dans KiCad comme pour
les autres empreintes custom).

**U8 — AMC0311R, retour température primaire isolé** (nouveau, absent de
la spec initiale). Surveille la température MOSFET/transformateur côté
primaire. Diviseur NTC (TH1, 10k/B=4000, 0805) + R16 (680Ω) :
`RAIL_3V3_PRI`→TH1→nœud→R16→`GND`, nœud sur `INP` ; `SNSN`=`GND`. NTC en
haut (sortie croissante avec la température, meilleure résolution côté
chaud) : ≈0,21V à 25°C, ≈2,19V à 125°C — dans la plage linéaire 0-2,25V de
l'AMC0311R, marge avant l'écrêtage souple à 2,56V. C29 (100pF) en
compensation `INP`-`SNSN`, comme sur U7. Sortie filtrée R17(100Ω)/C30(1nF)
→ `TEMP_PRI_FBACK`. Découplage C25/C26 (100nF).

**U9 — AMC0302R, retour courant primaire isolé** (nouveau, protection
MOSFET primaire). Shunt bas côté (R19, 1210, valeur provisoire 7,5mΩ — à
sourcer en passe dédiée) inséré en série entre la source de Q1 et `GND`
dans `flyback.kicad_sch`, lu en différentiel par U9 : `INP`=`ISENSE_P`
(côté source Q1), `INN`=`GND` (un shunt 2 bornes n'a pas de masse de sens
séparée — même nœud physique que le retour de courant). AMC0302R choisi
plutôt que la famille ±250mV (AMC0300R/AMC0202R) : avec Ipk=6,55A/
Irms=3,37A (coin 6,3V/3A, §3), un shunt ±50mV (≈7,5mΩ) dissipe ≈0,09W en
régime établi contre ≈0,43W pour un shunt ±250mV (≈38mΩ) — marge plus
confortable sur un boîtier 1210. Sortie filtrée R18(100Ω)/C33(1nF) →
`ISENSE_PRI_FBACK`. Découplage C31/C32 (100nF).

**Les deux nouveaux isolateurs étaient d'abord câblés côté contrôle sur
`RAIL_3V3_PRI`/`GND`** (comme U7 à l'époque) — migré vers `GND_CTRL`/
`3V3_CTRL` dans la même session, voir §14.

Édition chirurgicale sur `isolation.kicad_sch` et `flyback.kicad_sch`
(insertion de R19 en série sur une broche déjà câblée de Q1). Bug
d'outillage rencontré et corrigé en cours de route : une suppression de
fil par recherche de chaîne à indentation fixe a coupé un bloc
multi-lignes au mauvais endroit (le texte `'\t)\n'` matchait aussi
l'intérieur de `'\t\t)\n'`), laissant un fragment orphelin qui décalait
tous les niveaux de parenthèses du fichier d'un cran — détecté par
comparaison du nombre de `(` et de `)` sur le fichier entier (3482 contre
3483), corrigé en retirant le fragment exact. Deuxième bug trouvé via le
même type de symptôme : le cache `(lib_symbols ...)` embarqué dans
`isolation.kicad_sch` n'avait jamais été mis à jour (resté sur
`AMC0311S`, jamais eu `AMC0302R` ni `Device:Thermistor_NTC`) —
`kicad-cli` résout les pins depuis CE cache, pas depuis la bibliothèque
externe ; symptôme : tous les pins d'un symbole renvoyés en
`pintype "unspecified"` sur un faux net unique, ce qui fait remonter en
ERC des `pin_not_connected`/`label_dangling` épars et trompeurs. Les deux
leçons sont documentées en détail dans la mémoire de session. `kicad-cli
sch erc` final : **0 erreur**, warnings restants = avertissements attendus
déjà présents (GND2/GND1 sur net flottant `VOUT_N`, cache MSD1514
préexistant) + désalignements de grille cosmétiques sur les nouveaux
composants (replacement manuel prévu par l'utilisateur, comme pour tous
les ajouts précédents sur ces feuilles).

## 14. Isolation réelle du C2000 — GND_CTRL/3V3_CTRL, connecteur scindé en 2 (2026-10-02)

Mise en œuvre du point ouvert du §13 : jusqu'ici U3 (et dans une moindre
mesure U4/U5/U7/U8/U9 côté contrôle) partageaient `RAIL_3V3_PRI`/`GND`
des deux côtés de leur barrière d'isolation — la puce isolante existait,
mais sans séparation galvanique réelle vis-à-vis du C2000 externe, les
deux « côtés » étant en fait le même rail/masse générés localement sur
cette carte.

**Câblage migré vers `3V3_CTRL`/`GND_CTRL`** (alimentation/masse
réellement importées depuis la carte C2000, sans lien cuivre avec
`RAIL_3V3_PRI`/`GND`) :

| Composant | Broches migrées | Broches inchangées |
|---|---|---|
| U3 (ISO7710, PWM primaire) | VCC1(1,3), GND1(4) | VCC2(8)/GND2(5) → primaire local (vers U1) |
| U4 (ISO7710, PWM secondaire) | VCC1(1,3), GND1(4) | VCC2(8)/GND2(5) → `RAIL_3V3_SEC`/`VOUT_N`, secondaire flottant |
| U5 (DPC817, EN) | pin2 (cathode) | pins3/4 (sortie) → primaire local |
| U7 (AMC0311R, retour Vout) | VDD2(8)/GND2(5)/REFIN(6) | VDD1/GND1/SNSN → secondaire flottant |
| U8 (AMC0311R, retour température) | VDD2(8)/GND2(5)/REFIN(6) | VDD1/GND1/SNSN → primaire local (thermistance) |
| U9 (AMC0302R, retour courant) | VDD2(8)/GND2(5)/REFIN(6) | VDD1/GND1/INN → primaire local (shunt) |

Chaque composant migré garde son découplage 100nF propre, lui aussi
basculé sur `3V3_CTRL`/`GND_CTRL` (C15 pour U3, C17 pour U4, C28 pour U7,
C26 pour U8, C32 pour U9).

**Connecteur Cpu1 (8 broches, un seul) scindé en deux nappes 2x4**,
séparées par sens de signal :

```
CpuOut (sorties C2000 -> carte)      CpuIn (entrées C2000 / ADC)
1 = 3V3_CTRL                         1 = 3V3_CTRL
2 = GND_CTRL                         2 = GND_CTRL
3 = PWM_PRI_IN                       3 = VOUT_FBACK
4 = GND_CTRL                         4 = GND_CTRL
5 = EN_PRI_IN                        5 = TEMP_PRI_FBACK
6 = GND_CTRL                         6 = GND_CTRL
7 = PWM_SEC_IN                       7 = ISENSE_PRI_FBACK
8 = GND_CTRL                         8 = GND_CTRL
```

Les 4 broches de marge prévues sur CpuIn (§13bis) ont été consommées par
les deux nouveaux retours température/courant — plus de marge disponible
sur ce connecteur pour un futur ajout, à rouvrir si besoin.

**`PWR_FLAG` ajoutés sur `3V3_CTRL`/`GND_CTRL`** (sur CpuOut) : ces rails
sont importés depuis la carte C2000, invisibles pour l'ERC de cette
feuille — même convention déjà utilisée dans `alim.kicad_sch` pour
`VIN`/`GND`/`VBOOT`/`VOUT_N`, sans quoi ERC lève `power_pin_not_driven`
sur chaque pin `power_in` de ce nouveau rail.

Édition chirurgicale (22 renommages de label ciblés par coordonnée exacte
— jamais de remplacement global `RAIL_3V3_PRI`→`3V3_CTRL`, qui aurait
cassé le primaire — + suppression de Cpu1 et ses 8 étiquettes + ajout de
2 connecteurs + 2 PWR_FLAG). Même bug de cache `lib_symbols` que le §13,
cette fois sur `power:PWR_FLAG` (jamais utilisé dans cette feuille avant
ces 2 flags) — diagnostiqué et corrigé par la même méthode. `kicad-cli
sch erc` final : **0 erreur**, 37 avertissements (même famille que §13 :
désalignements de grille cosmétiques sur les nouveaux objets +
avertissements `GND`-flottant déjà acceptés).

**Reste à faire côté utilisateur** : replacement de CpuOut/CpuIn et de
tous les composants migrés dans KiCad (positions provisoires côté
script), mise à jour du PCB (F8), et vérification visuelle que le
système C2000 externe n'a pas déjà une masse reliée à celle de cette
carte par un autre chemin (boîtier, câble blindé) — auquel cas la
séparation serait refaite ailleurs sans que le schéma le montre.

## 15. Nouvelle feuille « Polarisation » — pilotage actif de HV_BIAS depuis une source 400V (2026-10-02)

Besoin exprimé : piloter depuis le C2000 la tension du point milieu du
pont symétrique existant (R9/R10, 2×100kΩ entre `VOUT_P` et `VOUT_N`,
`flyback.kicad_sch`) — ce point (`HV_BIAS`, déjà posé par l'utilisateur
avec un connecteur-témoin `Bias1`) fixe de combien le secondaire flottant
est élevé au-dessus du primaire. Jusqu'ici réglé passivement ; nouveau
besoin : le rendre réglable 0-90V depuis une alimentation externe 400V
max, pilotée/lue par le C2000.

**Nouvelle feuille `polarisation.kicad_sch`**, raccrochée à la racine
(page 5). Chaîne complète :

**Source de courant 300µA** (400V→`HV_BIAS`, remplace un simple pont
résistif après calcul du courant de fuite probable) : Q3 (BSS127I,
600V, élément de puissance) + Q4 (MMBT2222, boucle de régulation) + R25
(2kΩ, fixe I=Vbe/R25≈300µA) + R26-R29 (4×2M7 en série, polarisation
grille Q3 depuis 400V, chaîne pour la tenue en tension — un seul 0805 ne
tient que ~150V). Pourquoi un courant constant plutôt qu'un pont
résistif classique : le courant de fuite chauffage-cathode des tubes
(~1µA/tube ×10 tubes ≈10µA max, à confirmer sur le datasheet du tube
réel) doit rester négligeable devant le courant de polarisation — marge
×30 avec 300µA, la boucle logicielle absorbe le reste.

**Protection `HV_BIAS`** : D3 (TVS SMCJ100A, même famille que D1)
clampe à ~100V si Q5 se bloque ; R21 (1MΩ) tire la grille de Q5 vers
`RAIL_3V3_PRI`, donc une perte de commande sature Q5 (HV_BIAS→~0V,
sens sûr) plutôt que de le bloquer.

**Commande grille Q5 (BSS127I, résistance variable 0-180kΩ à 300µA
pour balayer 0-90V)** : PWM du C2000 → U10 (ISO7710, traverse
`GND_CTRL`↔`GND` comme U3/U4) → filtre R20(10k)/C36(100nF) → grille Q5.
Logic-level (Vth max 2,6V) choisi spécifiquement pour ce rôle — un
MOSFET de puissance standard (Vth 3-4V) ne garantirait pas de conduire
avec seulement 3,3V de commande.

**Retour mesure `BIAS_FBACK`** : diviseur R22(470k)/R23(10k) (ratio
calé pour amener 100V→2,08V, sous le plafond 2,25V de l'AMC0311R) + C40
(100pF comp.) → U11 (AMC0311R, 4e instance, même famille que
U7/U8/U9) → filtre R24(100Ω)/C41(1nF) → `BIAS_FBACK`.

**Connecteurs C2000 agrandis 2x04→2x08 (16 broches)**, décision de
l'utilisateur pour garder de la marge et rester standard avec
d'autres cartes (shield, devkits) : `CpuOut`/`CpuIn` recréés en
`Connector_Generic:Conn_01x16` / `PinHeader_2x08_P2.54mm_Vertical`,
8 signaux existants conservés + `PWM_BIAS_IN`/`BIAS_FBACK` nouveaux +
6 broches de marge (3 par connecteur) pour de futurs ajouts. Nouveau
connecteur dédié `J1` (`HV400_IN`) pour l'alimentation 400V externe,
avec son propre `PWR_FLAG`.

**Composants ajoutés à `lib/custom_parts.kicad_sym`** : BSS127I et
MMBT2222, construits en autonome (pas de mécanisme `extends` de la
bibliothèque standard KiCad — `Transistor_FET:BSS127S` hérite de
`Q_NMOS_GSD`, ambigu à mettre en cache correctement dans une feuille,
cf. mémoire de session) avec le même brochage que les symboles standard
KiCad (G/S/D ou B/E/C aux mêmes coordonnées), mais pointant vers la
datasheet Infineon réellement sourcée plutôt que la référence
générique Diodes Inc. du symbole KiCad.

Deux bugs trouvés et corrigés en cours de route (détaillés en mémoire
de session) : (1) `Device:D_TVS` a des broches horizontales
`(-3.81,0)/(3.81,0)`, pas verticales comme `Device:R`/`Device:C` — un
générateur de coordonnées validé sur R/C donnait des broches "non
connectées" en ERC pour D3 tant que ce n'était pas corrigé ; (2) le
cache `lib_symbols` de `isolation.kicad_sch` n'avait pas
`Connector_Generic:Conn_01x16` (jamais utilisé dans cette feuille avant
l'agrandissement des connecteurs C2000) — même symptôme et même
diagnostic que pour `AMC0302R`/`power:PWR_FLAG` au §14.

`kicad-cli sch erc` sur le projet complet (4 feuilles) : **0 erreur
inattendue** — seules les 6 broches de marge volontairement non
connectées (NC) sur les connecteurs 16 broches remontent en erreur
(attendu pour des broches de réserve), plus les avertissements déjà
documentés (grille cosmétique sur les nouveaux composants, `GND`
flottant sur `VOUT_N`, cache MSD1514 préexistant).

**Reste à sourcer/vérifier** : courant de fuite réel du tube utilisé
(datasheet constructeur, remplace l'hypothèse 1µA/tube), valeur
définitive de R25 (dépend de la vraie plage de conduction du BSS127I
mesurée au banc, pas juste du Vbe), et le repositionnement de tous les
nouveaux composants dans KiCad (placés par script à des coordonnées
provisoires, comme d'habitude sur ces feuilles).
