# Intention de conception — flyback flottant filament + préampli

| | |
|---|---|
| Révision | v0.9 — secondaire plus isolé/flottant du primaire dans le montage final (§20bis) ; v0.8 — redressement synchrone secondaire réel : UCC24612 (U12) remplace U2/U4, clamp D4 ajouté |
| Établi le | 2026-09-28, mis à jour 2026-10-25 |
| Statut | duty cycle et courants inductance vérifiés ; clamp TVS SMC et filtrage de sortie 50mV tranchés (§6, §7) ; retour ADC isolé AMC0311S ajouté (§13) ; UCC5304 essayé puis abandonné côté secondaire, marge UVLO insuffisante pour un filament réglable (§13bis) ; retours température MOSFET/transfo et courant primaire ajoutés, isolateurs migrés vers la famille ratiométrique AMC03x1R/AMC03x2R (§14) ; isolation C2000 rendue réelle — U3/U4/U5/U7/U8/U9 migrés sur GND_CTRL/3V3_CTRL, connecteur scindé CpuOut/CpuIn (§15) ; nouvelle feuille Polarisation — HV_BIAS piloté activement 0-78V utiles depuis une source 80V externe fixe, connecteurs C2000 agrandis à 16 broches (§16) ; cible 18,9W validée par simulation sous réserve d'un clamp secondaire, U2(UCC27517)+U4(ISO7710) remplacés par U12(UCC24612, détection Vds) + D4(SMCJ54A) (§17) |

Convention reprise de `composants-datasheets/CLAUDE.md` : `spec` = exigence
d'entrée · `déduit` = calculé · `?` = à trancher. Toute valeur `déduit` porte
sa formule et sa source.

## 1. Fonction

Flyback 200kHz, alimentant un filament de chauffage tube + étage de
préamplification bas bruit. Secondaire élevable de 0 à 90V par pont 2×100k
symétrique (Vout+/Vout- vers la source HV externe). **Depuis le
2026-10-25, le secondaire n'est plus isolé galvaniquement du primaire**
dans le montage final — voir §20bis. La barrière isolée réelle du système
est désormais uniquement contrôle (C2000) ↔ puissance (primaire +
secondaire), via les AMC03xx/ISO7710/DPC817.

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

**Cboot — composant retiré (§17, 2026-10-04), calcul conservé pour mémoire.** (stockage bootstrap secondaire, alimentait UCC27517-secondaire en direct + MCP1703 en amont de l'ISO7710-secondaire — architecture validée avec l'utilisateur en amont de cette session)
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
| LDO auxiliaire secondaire | Reg3 | MCP1703-3302 (SOT-23A, 3,3V) — VI depuis VOUT_P direct (§17), alimente VDD1 de U7 (AMC0311R) | `data/carte-flyback/mcp1703.yaml` |
| Cin | C1 | A786MW477M1VLAV010 (KEMET, 470µF/35V, 10mΩ) | `data/carte-flyback/a786mw477m1vlav010.yaml` |
| Cout | C3, C4 | 2× Panasonic 16SVPG330M (330µF/16V, 6,5mΩ) | `data/carte-flyback/16svpg330m.yaml` |
| Ampli isolé retour Vout | U7 | AMC0311R (DWV-8, ratiométrique) — retour Vout isolé vers C2000 (§13, renommé depuis AMC0311S en §14) | à sourcer (`composants-datasheets/data/carte-flyback/amc0311r.yaml`, session dédiée) |
| Empreinte U7/U8/U9 | — | `lib_fp/SOIC_DWV.pretty/SOIC-8_DWV_5.85x11.5mm_P1.27mm.kicad_mod`, custom (boîtier DWV renforcé, cotes land pattern fournies par l'utilisateur) — modèle 3D `DWV0008A.stp` fourni par l'utilisateur, transform identité à affiner (§14) |
| Thermistance temp. primaire | TH1 | NTC 10k/B=4000, 0805 | non sourcé séparément (§14) |
| Ampli isolé retour température | U8 | AMC0311R (DWV-8, ratiométrique) — retour température primaire isolé vers C2000 (§14) | à sourcer |
| Shunt courant primaire | R19 | 1210, valeur provisoire 7,5mΩ | à sourcer (valeur et dissipation, §14) |
| Ampli isolé retour courant | U9 | AMC0302R (DWV-8, ratiométrique, ±50mV) — retour courant primaire isolé vers C2000, protection surcourant Q1 (§14) | à sourcer |
| Redressement synchrone secondaire | U12 | UCC24612 (SOT23-5) — remplace U2(UCC27517)+U4(ISO7710), détection Vds (§17) | à sourcer (`datasheets/ucc24612.pdf` déjà présent, pas encore de yaml) |
| Clamp secondaire | D4 | SMCJ54A (SMC/DO-214AB, même boîtier/famille que D1) — dimensionné `doc/sim-vs-mesure.md` §7bis (§17) | à sourcer (`datasheets/bourns-smcj-series.pdf` déjà présent, pas encore de yaml) |
| Découplage U12 | C42, C43 | 2,2µF (REG) + 100nF (VDD, bypass HF local) (§17) | non sourcé séparément, générique comme Cboot |

## 11. Points ouverts

- [ ] Rendement η=0,85 utilisé en §3 — hypothèse, à vérifier au banc
- [ ] Vf du redresseur secondaire en phase bootstrap (§5) — 1V pris par
      hypothèse. IPD050N10N5 (sourcé, Q2) donne Vf_body_diode=1,2V max à 40A
      (très au-dessus du courant réel ~6,55A) — conforte l'hypothèse comme
      raisonnablement conservatrice.
- [x] Diode de bootstrap secondaire (Vout → Cboot) — **devenue sans objet** :
      Cboot et le bootstrap associé sont retirés (§17), Reg3 (MCP1703) est
      câblé directement sur VOUT_P, plus de diode ni de chute Vf dans ce
      chemin
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
      ISO7710+UCC27517 sur le secondaire** (§13bis) : le plancher réel
      d'usage n'est pas 6,3V mais jusqu'à 5,8V (filament réglable -5 à
      -10% sur 6,3V nominal), ce qui aurait mis VBOOT sous le seuil UVLO
      *garanti* (pas juste recommandé) de l'UCC5304 — voir calcul précis
      §13bis avec les seuils UVLO réels du datasheet (p.8 tbl 6.9).
- [ ] Valeurs du filtre RC en sortie de l'AMC0311S (R15=100Ω, C24=1nF,
      §13) — proposées par défaut (fc≈1,6MHz, n'entame pas la bande
      passante propre de l'ampli ~120kHz), à revoir une fois la spec
      d'entrée de l'ADC côté C2000 connue.
- [ ] R11/R12 (résistances de grille en sortie des UCC, 1Ω/0805) — valeur
      retenue par l'utilisateur directement dans KiCad, pas de calcul de
      dimensionnement tracé ici (amortissement/EMI, ordre de grandeur
      courant pour ce type d'application).

- [ ] **R19 sature l'AMC0302R au coin dimensionnant** — R19 × Ipk = 7,5mΩ × 6,55A ≈ 49,2mV contre ±50mV de pleine échelle (marge 1,6%), au régime nominal retenu comme dimensionnant (§3). U9 sert à la protection surcourant de Q1 (§14) : il doit voir au-dessus du pic nominal pour détecter un défaut, pas s'écrêter dessus. À trancher : R19 plus faible (ex. 5mΩ → 32,8mV, marge ×1,52, dissipation 57mW) ou plage AMC0300R/AMC0202R (±250mV) avec le shunt actuel — pas encore choisi.
- [ ] **Plage de `HV_BIAS` — spec 0-90V (§2) non atteignable avec le rail 80V retenu** (§16) : le courant de polarisation tombe à ~0 au-delà de ~78V (§16bis), accepté explicitement pour le comportement de la source mais pas reporté dans le tableau de spec, qui affiche toujours 90V. D3 (SMCJ100A) clampe à 100V — marge à revérifier contre la valeur retenue. À trancher : abaisser la spec à ~78V, ou lever le rail `HV80_IN` au-dessus de 90V + marge.

## 12. État du projet KiCad

Schéma généré par script (`gen_composants.py`, méthode reprise de
KICAD-C2000-devkit : étiquettes globales uniquement, aucun fil, empreintes posées
sur l'instance). **Restructuré en feuilles hiérarchiques** sur demande de
l'utilisateur (2026-09-28) : une feuille racine (`KICAD-HT.kicad_sch`,
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
KiCad par l'utilisateur, plus jamais régénérés par script) — voir §13 pour
le détail des changements les plus récents (UCC5304, AMC0311S, Cpu1).
Composants redistribués entre feuilles par l'utilisateur au passage :
`J1→In1`, `J3→Out1`, `J4→Bias1` (renommés), `Reg3/C11/C12/R9/R10` déplacés
vers Flyback, `J2→Cpu1` déplacé vers Isolation_Drivers, `C1` déplacé vers
Alimentation — connectivité inchangée (les étiquettes globales ignorent la
feuille physique), seule l'organisation visuelle a bougé.

PCB généré avec contour de carte (70×55mm, à ajuster) — placement et
routage sont les étapes manuelles suivantes, comme pour les autres cartes
de ce workspace.

Fichiers : `KICAD-HT.kicad_pro/.kicad_sch/.kicad_pcb`,
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

## 13. Secondaire UCC5304 + retour Vout isolé AMC0311S (2026-09-30)

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
d'entrée ADC du C2000 connue (point ouvert, §11).

**Découplage (règle utilisateur, 100nF/0805 par CI)**, appliquée à U6/U7
uniquement (pas de retrofit sur U1/U3/U5, décision explicite) :
C25 (RAIL_3V3_PRI-GND, U6 VCCI), C26 (VBOOT-VOUT_N, U6 VDD), C27
(RAIL_3V3_SEC-VOUT_N, U7 VDD1), C28 (RAIL_3V3_PRI-GND, U7 VDD2).

**3. Cpu1 (ex-J2, connecteur de commande vers le C2000 externe) agrandi de
4 à 16 broches** (8 signaux + 8 masses en alternance stricte 1:1) — reprend
le motif déjà en place sur `KICAD-C2000-devkit` (liaison shield↔puissance,
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

## 13bis. Retour sur UCC5304 — marge UVLO insuffisante pour un filament réglable (2026-09-30)

**UCC5304 abandonné côté secondaire, retour à ISO7710 (U4) + UCC27517
(U2)** comme avant §13. Cause : l'utilisateur veut pouvoir régler la
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
coin 6,3V (§13). L'ancien UCC27517 (UVLO ≈4,2V typ, `carte-puissance/
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

## 14. Retours température primaire et courant primaire isolés, migration AMC0311S→AMC0311R (2026-10-02)

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
`3V3_CTRL` dans la même session, voir §15.

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

## 15. Isolation réelle du C2000 — GND_CTRL/3V3_CTRL, connecteur scindé en 2 (2026-10-02)

Mise en œuvre du point ouvert du §14 : jusqu'ici U3 (et dans une moindre
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

Les 4 broches de marge prévues sur CpuIn (§13) ont été consommées par
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
2 connecteurs + 2 PWR_FLAG). Même bug de cache `lib_symbols` que le §14,
cette fois sur `power:PWR_FLAG` (jamais utilisé dans cette feuille avant
ces 2 flags) — diagnostiqué et corrigé par la même méthode. `kicad-cli
sch erc` final : **0 erreur**, 37 avertissements (même famille que §14 :
désalignements de grille cosmétiques sur les nouveaux objets +
avertissements `GND`-flottant déjà acceptés).

**Reste à faire côté utilisateur** : replacement de CpuOut/CpuIn et de
tous les composants migrés dans KiCad (positions provisoires côté
script), mise à jour du PCB (F8), et vérification visuelle que le
système C2000 externe n'a pas déjà une masse reliée à celle de cette
carte par un autre chemin (boîtier, câble blindé) — auquel cas la
séparation serait refaite ailleurs sans que le schéma le montre.

## 16. Nouvelle feuille « Polarisation » — pilotage actif de HV_BIAS depuis une source 80V (2026-10-02)

Besoin exprimé : piloter depuis le C2000 la tension du point milieu du
pont symétrique existant (R9/R10, 2×100kΩ entre `VOUT_P` et `VOUT_N`,
`flyback.kicad_sch`) — ce point (`HV_BIAS`, déjà posé par l'utilisateur
avec un connecteur-témoin `Bias1`) fixe de combien le secondaire flottant
est élevé au-dessus du primaire. Jusqu'ici réglé passivement ; nouveau
besoin : le rendre réglable depuis une alimentation externe dédiée fixe
80V (`J1`/`HV80_IN`), pilotée/lue par le C2000. (Première itération
envisagée à 400V avec une chaîne de 4 résistances en série pour la tenue
en tension ; simplifiée à 80V fixe — un seul 0805 suffit, cf. schéma
réel.)

**Nouvelle feuille `polarisation.kicad_sch`**, raccrochée à la racine
(page 5), régénérée en respectant les conventions du projet : étiquettes
globales uniquement (aucun segment de fil explicite), tous les
composants alignés sur la grille 1,27mm. Chaîne complète :

**Source de courant régulée** (`HV80_IN`→`HV_BIAS`, remplace un simple
pont résistif après calcul du courant de fuite probable) : Q3 (BSS127I,
élément de puissance) + Q4 (MMBT2222, boucle de régulation) + R25 (2kΩ,
fixe le point de régulation à I=Vbe/R25) + R26 (résistance unique,
polarisation grille Q3 depuis `HV80_IN` — valeur corrigée par simulation,
voir §16bis). Pourquoi un courant régulé plutôt qu'un pont résistif
classique : le courant de fuite chauffage-cathode des tubes (~1µA/tube
×10 tubes ≈10µA max, à confirmer sur le datasheet du tube réel) doit
rester négligeable devant le courant de polarisation — large marge dans
tous les cas, la boucle logicielle absorbe le reste.

**Protection `HV_BIAS`** : D3 (TVS SMCJ100A, même famille que D1)
clampe à ~100V si Q5 se bloque ; R21 (1MΩ) tire la grille de Q5 vers
`RAIL_3V3_PRI`, donc une perte de commande sature Q5 (HV_BIAS→~0V,
sens sûr) plutôt que de le bloquer.

**Commande grille Q5 (BSS127I, résistance variable 0-180kΩ)** : PWM du
C2000 → U10 (ISO7710, traverse `GND_CTRL`↔`GND` comme U3/U4) → filtre
R20(10k)/C36(100nF) → grille Q5. Logic-level (Vth max 2,6V) choisi
spécifiquement pour ce rôle — un MOSFET de puissance standard (Vth
3-4V) ne garantirait pas de conduire avec seulement 3,3V de commande.
Plage réelle de `HV_BIAS` atteignable : voir §16bis (bornée par la
source de courant, pas par Q5).

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
connecteur dédié `J1` (`HV80_IN`) pour l'alimentation 80V externe,
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
diagnostic que pour `AMC0302R`/`power:PWR_FLAG` au §15.

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

## 16bis. Simulation SPICE de la source de courant — R26 corrigé de 2M7 à 75k (2026-10-03)

Avant de sourcer les composants, simulation du sous-circuit Q3/Q4/R25/R26
sous ngspice (binaire console officiel, hors KiCad qui n'embarque
`ngspice.dll` que pour son usage interne), avec les modèles SPICE réels
du fabricant Diodes Inc. (second-source de la famille BSS127 et du
MMBT2222A — pas l'Infineon BSS127I réellement sourcé, donc résultat
indicatif sur la valeur exacte, fiable sur l'allure du comportement ; à
confirmer au banc avec la pièce réelle).

**Erreur de topologie trouvée** : l'hypothèse de conception initiale
(« R26 ne fournit qu'un léger courant de polarisation de grille, le
canal D-S de Q3 porte l'essentiel du courant régulé ») est fausse. La
simulation montre que le canal de Q3 reste quasi inerte (<1µA) sur toute
la plage : la contre-réaction via Q4 maintient Vgs(Q3) à peine au-dessus
du seuil, donc la quasi-totalité du courant imposé par R26 est détournée
par Q4 (collecteur→émetteur) vers R25, pas par le canal de Q3. Consé-
quence directe : **c'est R26 qui fixe le courant disponible**
(I ≈ (80V − HV_BIAS − ~3V de marge Vgs+Vbe)/R26), pas R25/Vbe seuls. Le
montage se comporte donc, sur toute sa plage utile, plus comme une
résistance (décroissance quasi linéaire du courant avec `HV_BIAS`) que
comme une vraie source de courant plate.

Avec la valeur d'origine (2M7, dimensionnée pour ~300µA sous l'hypothèse
fausse ci-dessus), le courant réellement disponible n'atteignait que
20-30µA en simulation — largement insuffisant.

**Courbe de compliance mesurée** (balayage de `HV_BIAS` forcé de 0 à
80V, modèle Vth=2,0V représentatif de l'Infineon BSS127I) pour R26=75k,
valeur retenue :

| HV_BIAS | Courant disponible |
|---|---|
| 0V | 1,01mA |
| 40V | 0,49mA |
| 60V | 0,23mA |
| 75V | 32µA |
| 78V | ≈0 |

Courant quasi nul au-delà de ~78V (marge de tension de la boucle
Q3/Q4 — Vgs(Q3)+Vbe(Q4)+chute R25, ~3V — épuisée face au rail fixe
80V) ; décision explicite de l'utilisateur d'accepter ce comportement
(1mA en bas de plage, encore quelques dizaines de µA à 75V) plutôt que
de viser une vraie source de courant plate sur toute la plage.

**R26 : 2M7 → 75k** (valeur standard E24) appliqué dans
`polarisation.kicad_sch`. Dissipation vérifiée au pire point (HV_BIAS=0V,
~75,3V aux bornes de R26, 1,01mA) : ~76mW, sous les 125mW d'un 0805 —
pas de changement de boîtier nécessaire. `kicad-cli sch erc` re-vérifié
sur le projet complet : aucune violation nouvelle (même base qu'au §16).

## 17. Redressement synchrone secondaire réel — UCC24612 (U12) remplace U2/U4, clamp D4 ajouté (2026-10-04)

Suite de `doc/sim-vs-mesure.md` §7/§7bis : la cible réelle (18,9W) a été
simulée avec un proxy de redressement synchrone (grille idéale) avant
d'intégrer le vrai composant. Verdict : tenable **à condition** d'ajouter
un clamp secondaire sur Q2 (absent jusqu'ici — point ouvert du §11
ci-dessus, passé de souhaitable à bloquant à cette puissance). Les deux
changements ci-dessous découlent de ce verdict chiffré, pas d'un choix a
priori.

**U2 (UCC27517) + U4 (ISO7710) retirés, remplacés par U12 (UCC24612).**
Cause : le canal secondaire était piloté « à l'aveugle » — PWM_SEC_IN
depuis le C2000, timing fixé par le firmware, aucun retour sur le vrai
Vds de Q2. L'UCC24612 élimine ce problème par construction (détection
Vds, diode emulation) : plus besoin d'isolateur ni de canal PWM dédié
pour ce rôle, net moins de composants (2 CI retirés, 1 plus petit
ajouté). Config **low-side** (source de Q2 déjà côté masse secondaire) :

```
VG(1)  -> R12 (déjà posée, inchangée) -> GATE_Q2
VS(2)  -> VOUT_N (même label que l'ancien GND de U2, position reprise)
REG(3) -> REG_SR -> C42 (2,2µF, obligatoire : courant de grille moyen
          Qg×fsw ≈ 10-13mA > seuil 5mA de la datasheet §9)
VDD(4) -> VOUT_P directement (recommandation datasheet §9 pour le
          low-side, Vout 5,8-13V dans la plage admise 4,5-28V — pas
          besoin d'enroulement auxiliaire ni de R-C-D, réservés au
          high-side) + C43 (100nF, bypass HF local, en plus du banc Cout)
VD(5)  -> SW_SEC (Kelvin direct vers le drain de Q2, piste dédiée hors
          chemin de puissance par construction — même nœud que T1 pin2
          et D4 cathode)
```

Nouveau symbole `custom_parts:UCC24612` (SOT23-5, même boîtier que
l'ancien UCC27517 — zéro changement d'empreinte), ajouté à
`lib/custom_parts.kicad_sym` sur le même modèle que UCC27517/ISO7710.
U12 reprend la position exacte de l'ancien U2 ; ses pins VG/VS tombent
sur les mêmes coordonnées que les anciens OUT/GND de U2, donc le fil
existant vers R12 et le label VOUT_N n'ont pas eu besoin d'être retouchés
— seuls VDD/VD/REG (anciens VDD/IN+/IN- de U2, sur VBOOT) ont été
rebranchés.

**D4 (SMCJ54A) ajouté** en clamp secondaire, cathode=SW_SEC (drain Q2),
anode=VOUT_N — même construction/orientation que D1. Choix chiffré en
détail dans `doc/sim-vs-mesure.md` §7bis : clampe Vds_Q2 à ~61-65V
(marge ×1,5 vs les 100V du MOSFET) pour 0,03-0,76W de dissipation (marge
×7 vs son propre P_av=5W). Le SMCJ43A (même réf. que D1) a aussi été
testé et tient les deux contraintes, mais coûte jusqu'à 2 points de
rendement système en plus (le clamp n'absorbe pas qu'une perte locale —
le couplage K1 L1 L2 relie les deux résonances, écrêter plus bas côté
secondaire fait tirer davantage sur Vin pour un Pout quasi identique) —
le SMCJ54A est donc retenu malgré la référence BOM supplémentaire.

**VBOOT/D2(BAT54C)/C8(Cboot)/C20/C22 retirés par l'utilisateur**
(édition GUI directe, même session) — vestigiaux depuis que VDD de
l'UCC24612 va directement sur VOUT_P, comme déjà noté ci-dessus. Mais
**ce nettoyage a cassé l'alimentation de Reg3** (MCP1703, LDO 3,3V
secondaire) sans que son rôle disparaisse : Reg3 reste nécessaire pour
VDD1 de U7 (AMC0311R, retour Vout isolé). Deux incidents trouvés et
corrigés dans la foulée (ERC + vérification croisée, pas juste visuel) :

1. Reg3 supprimé entièrement (pas juste rebranché) → son VI n'était plus
   alimenté. **Recréé** dans `flyback.kicad_sch`, VI câblé directement
   sur VOUT_P (au lieu de l'ancien VBOOT/D2) — Vin_max MCP1703=16V vs
   VOUT_P max=13V, marge ×1,23 (`mcp1703.yaml`), largement suffisant
   sans bootstrap.
2. **Plus grave** : en attendant, VDD1 de U7 avait été rebranché
   directement sur VOUT_P (13V) — or VDD1 de l'AMC0311R a un maximum
   absolu de **6,5V** (`amc0311r.pdf` §6.1) : ça aurait détruit le
   composant au premier démarrage à Vout élevé. Rebranché sur
   `RAIL_3V3_SEC` (sortie régulée de Reg3) à la place.

Les deux corrections ont été trouvées en recroisant `kicad-cli sch export
netlist` après l'édition GUI de l'utilisateur, pas par relecture visuelle
— la marge de l'AMC0311R en particulier n'était pas quelque chose
d'évident à repérer à l'œil sur le schéma.

**PWR_FLAG ajouté sur VOUT_P** (`alim.kicad_sch`, même rangée que les
PWR_FLAG VIN/GND/VOUT_N déjà en place) — nécessaire car VDD de U12 est le
premier pin de type *power input* jamais posé sur ce net (jusqu'ici
VOUT_P n'était touché que par des pins *passive*, qui n'ont pas besoin
d'un flag). Sans lui, ERC lève `power_pin_not_driven` sur VDD.

**Vérification.** `kicad-cli sch erc` sur le projet complet, état final
(après nettoyage utilisateur + corrections Reg3/U7 ci-dessus) : 213
violations (223 avant ce §17), **7 erreurs — même famille déjà connue et
acceptée** (broches de réserve CpuOut/CpuIn non connectées, §16 ; le
7e, `CpuOut1` pin 7 = ancien `PWM_SEC_IN`, rejoint cette catégorie
puisque l'UCC24612 n'a plus besoin de ce signal firmware). Aucune
violation `power_pin_not_driven` ni autre anomalie électrique restante.

**Marge UVLO à surveiller au banc (pas un point bloquant, juste plus
tendu que souhaité)** : à Vout_min=5,8V (filament réglé bas, §13bis),
VDD=VOUT_P=5,8V directement. Seuil UVLO réel de l'UCC24612
(`ucc24612.pdf` tbl 6.5, mesuré sur REG) : VREG_ON max=4,87V, dropout
max=0,45V à VDD=5V → VDD nécessaire ≈5,32V pire cas. Marge ≈0,48V —
positive (contrairement au rejet de l'UCC5304 en §13bis qui avait une
marge négative dans ce même scénario), mais plus courte que souhaité ;
à vérifier en charge réelle avant de considérer le point tranché.

**Reste à faire côté utilisateur** : replacement de U12/C42/C43/D4/Reg3
dans KiCad (positions provisoires côté script, mêmes désalignements de
grille cosmétiques que chaque ajout précédent) et mise à jour du PCB
(F8) — le nettoyage VBOOT/D2/C8/C20/C22 est fait.

## 18. `CpuOut1`/`CpuIn1` remplacés par `J2`, aligné pin-à-pin sur `J21` du shield (2026-10-21)

**Pourquoi.** `KICAD-C2000-powershield` a évolué (décision #26 de son
`doc/decisions.md`) : la carte Filament/HT ne partage plus un signal à
la fois sur les nappes génériques du devkit, elle reçoit désormais un
connecteur IDC 2×10 dédié, `J21` (symbole `NAPPE_FILAMENT_HT`, valeur
affichée renommée `DC_HT` depuis, 2026-10-28). `KICAD-HT`
utilisait encore deux connecteurs génériques 16 broches point-à-point
(`CpuOut1`/`CpuIn1`, `isolation.kicad_sch`), avec un jeu de noms de net
différent de celui du shield.

**Fait.** Les deux anciens connecteurs remplacés par un seul,
`J2` (`Connector_Generic:Conn_01x20`, footprint
`Connector_IDC:IDC-Header_2x10_P2.54mm_Vertical` — même footprint que
`J21` côté shield, compatibilité câble réelle), aligné pin-à-pin :

| Pin `J2`/`J21` | Net | Pin `J2`/`J21` | Net |
|---|---|---|---|
| 1 | `3V3_ISO` | 11 | `Vht` |
| 2 | `GND_CTRL` | 12 | `GND_CTRL` |
| 3 | `PWM_ht` | 13 | `I_Out_ht` |
| 4 | `GND_CTRL` | 14 | `GND_CTRL` |
| 5 | `PWM_EN` | 15 | `I_Shunt_ht` |
| 6 | `GND_CTRL` | 16 | `GND_CTRL` |
| 7 | `PWM_bias` | 17 | `I_Shunt_ht_comp` |
| 8 | `GND_CTRL` | 18 | `GND_CTRL` |
| 9 | `Vht_EN` | 19 | `V_bias` |
| 10 | `GND_CTRL` | 20 | `GND_CTRL` |

(`GND_CTRL` reste `GND_CTRL`, pas renommé en `GND` malgré le nom utilisé
côté shield — `KICAD-HT` a déjà un net `GND` séparé, la masse primaire
non isolée ; renommer aurait court-circuité silencieusement les deux
domaines par coïncidence de nom.)

7 nets renommés pour correspondre au vocabulaire du shield, partout où
ils apparaissent (`isolation.kicad_sch` et `polarisation.kicad_sch`) :
`PWM_PRI_IN`→`PWM_ht`, `EN_PRI_IN`→`PWM_EN` (confirmé : même signal, pas
une coïncidence de nom — la fonction « enable primaire » de cette carte
a convergé vers le drapeau système partagé du shield),
`PWM_BIAS_IN`→`PWM_bias`, `VOUT_FBACK`→`Vht`, `TEMP_PRI_FBACK`→`Temp_ht`,
`ISENSE_PRI_FBACK`→`I_Shunt_ht`, `BIAS_FBACK`→`V_bias`,
`3V3_CTRL`→`3V3_ISO`.

**`Temp_ht`→`I_Out_ht` (2026-10-28).** La mesure de température primaire
(TH1 + U8/AMC0311R) est retirée — remplacée par une mesure de courant de
sortie réel (nouveau shunt R25=10mΩ dans le retour `VOUT_N`, vers le
connecteur de sortie, + U22/AMC0302R, même topologie différentielle que
U9/R19 côté primaire). Le pin 13 de `J2` porte désormais `I_Out_ht` au
lieu de `Temp_ht` — renommé partout où il apparaît, y compris le motif
de netclasse `CTRL` dans `KICAD-HT.kicad_pro`.

**Deux broches posées mais non câblées en interne, par décision
explicite** (pas une fonction devinée) :
- `Vht_EN` (pin 9) — GPIO C2000 générique, jamais câblé nulle part sur
  cette carte jusqu'ici ; réserve.
- `I_Shunt_ht_comp` (pin 17) — réservé pour le futur signal de trip
  rapide (architecture de limitation de courant cycle-à-cycle locale,
  validée mais pas encore implémentée, branche
  `feat/limitation-courant-locale`). Dimensionné côté shield pour un
  chemin comparateur/Trip Zone (22Ω, pas 100Ω comme les autres voies).

**Piège rencontré en implémentant** : l'édition chirurgicale de
`isolation.kicad_sch` a d'abord produit un fichier structurellement
invalide à deux reprises (fragment de bloc orphelin, puis insertion du
nouveau connecteur à l'intérieur du bloc `lib_symbols` au lieu de la
zone des composants placés) — `kicad-cli sch erc` ne détectait pas ces
corruptions (résultats en apparence normaux mais en réalité incohérents
en aval), seule l'interface KiCad les a signalées au chargement. Les
deux corrigés en revenant à la dernière version commitée et en
reprenant avec une insertion à position fixe, vérifiée par rejeu de la
grammaire exacte du format `.kicad_sch` à chaque étape (pas seulement
l'équilibre des parenthèses). Trois étiquettes `GND_CTRL` de réserve de
l'ancien `CpuIn1` (ses broches 12/14/16, réellement câblées contrairement
aux broches 11/13/15) avaient aussi été oubliées lors du nettoyage
initial, retrouvées orphelines via l'ERC de l'interface KiCad et
retirées.

**Vérification finale** : `kicad-cli sch erc` sur la hiérarchie
complète, **0 erreur** — 219 avertissements restants, tous de la même
famille que ceux déjà présents avant ce changement (désalignements de
grille cosmétiques, `lib_symbol_mismatch` préexistant sur `T1`/`MSD1514`),
confirmé par comparaison structurée avec l'état avant modification.

## 19. Limitation de courant cycle-par-cycle locale au primaire + retour isolé `nTRIP` (2026-10-21)

**Pourquoi.** U9 (AMC0302R) a 1,6–2,1µs de retard de chaîne : inutilisable
pour couper Q1 avant dépassement sur un défaut rapide (pente jusqu'à
2,5A/µs à 25V). Ferme aussi le point ouvert §11 « R19 sature l'AMC0302R au
coin dimensionnant ». Architecture validée en principe lors d'une revue de
prompt précédente, implémentée ici : une chaîne **rapide, 100% primaire**
(ampli ×G + comparateur + verrou → coupe le driver en ~100ns, fonctionne
même C2000 planté) séparée d'une chaîne **lente isolée** (filtre moyenneur
→ AMC0302R → ADC C2000, courant moyen).

En parallèle, R19 passe de 7,5mΩ/1210/2 broches à **10mΩ, Yageo
`WSK1206R0100FEA`, 1206, 4 broches Kelvin** — changement physique intégré à
cette passe (`flyback.kicad_sch`).

### Trois écarts corrigés par rapport au prompt d'origine

Le prompt de départ décrivait un circuit supposé, pas le circuit réel.
Trois points ont dû être corrigés après vérification directe du schéma
(pas d'hypothèse non vérifiée, conformément à la règle du dépôt) :

1. **U3 reste `ISO7710` — pas `ISO7710F` comme demandé.** Vérifié dans
   `isolation.kicad_sch` : U1 (UCC27517) a `IN+`=`EN_PRI_OUT`,
   `IN−`=`PWM_PRI_OUT` (pas l'inverse supposé, et `IN−` n'était pas à
   `GND`). Avec `OUT(U1) = IN+ AND NOT(IN−)` (datasheet UCC27517,
   `composants-datasheets/datasheets/ucc27517.pdf`, p.3–4) : si `3V3_ISO`
   perd l'alimentation, `ISO7710` (pas F) donne `PWM_PRI_OUT` par défaut
   **haut** (`composants-datasheets/datasheets/isolation/iso7710.pdf`, p.19
   tbl 7-1 et p.20 tbl 7-2) → `NOT(haut)=bas` → `OUT(U1)=bas` → **Q1 déjà
   coupé, sûr par construction actuelle**. Passer U3 en `ISO7710F`
   (défaut bas) aurait **désactivé** cette protection en cas de perte du
   côté contrôle. U3 **non modifié**. Seul le nouvel isolateur `U19`
   (retour `nTRIP`, sens primaire→contrôle, inverse de U3) est
   `ISO7710F` : conforme au prompt, le sens de défaut-bas y est correct
   (primaire non alimenté ⇒ `I_Shunt_ht_comp` par défaut bas = trip vu du
   C2000).

2. **Verrou branché sur `IN+` de U1 (via un AND), pas sur `IN−` comme
   supposé.** `IN−` de U1 est déjà occupé par `PWM_PRI_OUT` (le vrai signal
   PWM), pas disponible pour le verrou. Solution retenue : nouveau
   `SN74LVC1G08` (AND, SOT-23-5, déjà sourcé localement — datasheet +
   fiches YAML + doc existantes pour ce composant, seule pièce de la
   chaîne logique déjà présente dans le dépôt datasheets), U13 dans
   `isolation.kicad_sch` : `EN_PRI_GATED = EN_PRI_OUT AND nQ_TRIP`,
   branché sur `IN+` ; `IN−` reste `PWM_PRI_OUT`, intouché. Vérifié sur la
   table de vérité du verrou (ci-dessous) : `nQ_TRIP` = H dans tous les
   états normaux, **L uniquement à l'état verrouillé (trip)** →
   `EN_PRI_GATED` suit `EN_PRI_OUT` en fonctionnement normal, forcé bas
   (donc `OUT(U1)=0`, Q1 coupé) dès que le verrou trippe, quel que soit
   l'état de `PWM_PRI_OUT`.

3. **Connecteur déjà prêt — rien à ajouter.** Le prompt demandait d'ajouter
   une broche `nTRIP_CTRL` à un connecteur. `J2` (§18, posé le même jour)
   a déjà une broche réservée exactement pour ce signal, `I_Shunt_ht_comp`
   (pin 17), dimensionnée côté shield avec une résistance série 22Ω (pas
   100Ω comme les autres voies) — anticipant déjà un usage comparateur/
   trip zone. La sortie isolée de `U19` est directement nommée
   `I_Shunt_ht_comp` (même net, pas de renommage, pas de modification du
   connecteur).

### Pièces : substitutions actées avec l'utilisateur

- **Comparateur** : `LMV7219` (SOT23-5) — inchangé du prompt. Datasheet
  `composants-datasheets/datasheets/opamp/lmv7219.pdf` : Vos max 6mV
  (p.5–6), tPD typ 7–11ns selon overdrive (p.5–7), plage de mode commun
  −0,2V à VCC−1V (p.11, texte — couvre confortablement 0,85V).
- **Référence de seuil : `ATL431`** (SOT-23-3, DBZ), pas le `LM4040` du
  prompt — demandé par l'utilisateur. Datasheet
  `composants-datasheets/datasheets/atl431.pdf` (SLVSCV5E) : Vref=2,500V
  typ, 2,475–2,525mV grade A (p.4, tbl 5.5), **Ika,min=35µA max** (p.4 —
  bien plus permissif qu'un TL431 classique ~1mA), **stable sans charge
  capacitive** (p.1 — pas de fenêtre d'ESR à respecter comme un TL431
  classique). Pinout ATL431 (pas ATL432, brochage différent) : 1=CATHODE,
  2=REF, 3=ANODE (p.3) — **identique au brochage standard TL431 DBZ**.
  Symbole/empreinte dans le schéma : `Reference_Voltage:TL431DBZ` (stock
  KiCad), pas un symbole custom — substitué à la main après coup (plus
  adapté qu'un symbole dessiné à la main, même brochage/footprint
  SOT-23 confirmé) ; la pièce réellement sourcée/montée reste l'ATL431
  (Value de l'instance = `ATL431`, Datasheet pointée vers
  `atl431.pdf`, pas la fiche TL431 générique du symbole stock). Montage :
  REF court-circuité sur CATHODE (mode 2 broches, sortie fixe 2,5V —
  c'est la sortie **minimale** possible d'un ATL431/TL431, on ne peut
  pas descendre en dessous de Vref par ce
  montage), polarisé depuis `RAIL_3V3_PRI`, puis **pont diviseur séparé**
  pour dériver `V_TH` (confirmé par l'utilisateur : « une pont diviseur ou
  une résistance »).
- **Logique : famille `SN74LVC1G`.** Aucun symbole/empreinte KiCad
  n'existait pour ces parts avant cette passe, seules les datasheets
  étaient déjà locales (sauf 1G08) :
  - `SN74LVC1G132` (NAND Schmitt, LEB) — **SOT-23-5** (DBV), A=1/B=2/
    GND=3/Y=4/VCC=5 (`sn74lvc1g132.pdf`, p.3 fig 4-1). VT+ = 0,79–1,16V à
    VCC≈3V (p.6, tbl 5.5, note (1) : typiques à VCC=3,3V).
  - `SN74LVC1G74` (verrou D) — **VSSOP-8** (package `DCU`, confirmé
    explicitement « Package Type: VSSOP, Package Drawing: DCU » dans
    l'addendum d'ordre, pas de variante SOT-23 dans cette révision malgré
    le souvenir initial) : CLK=1/D=2/Q=3/GND=4/`nQ`=5/`nCLR`=6/`nPRE`=7/
    VCC=8 (`sn74lvc1g74.pdf`, p.4 fig 5-1).
  - `SN74LVC1G08` (AND, gating `IN+` de U1) — **déjà sourcé localement**
    (datasheet + 2 fiches YAML + doc hw), SOT-23-5, même brochage que
    1G132.
- **Protection d'entrée : `BAT54S`** (pas un simple `BAT54` comme dans le
  prompt) — déjà utilisé 43 fois dans `KICAD-C2000-powershield` comme
  clamp bidirectionnel GND/rail sur signaux MCU, même pattern repris ici :
  pin1→`GND`, pin2→`RAIL_3V3_PRI`, pin3→nœud protégé (`IN+` du TSV791,
  après la résistance série R27). Symbole copié depuis
  `Power_Parts:BAT54S` (KICAD-C2000-powershield). Améliore le clamp
  simple du prompt : protège aussi contre un défaut positif, pas
  seulement l'undershoot ESL.

### Seuil et gain — méthode et valeurs

R19 passant de 7,5mΩ à 10mΩ, le courant de trip cible est repris identique
(~8,4A, cohérent avec la marge MSD1514 Isat=13,4A déjà discutée en §14) :

- **Gain TSV791 inchangé : ×10,09** (Rf=R29=9,09kΩ, Rg=R28=1,00kΩ, E96
  1%) — ne dépend pas de R19 ; la marge de non-saturation (pic ESL +0,3V
  → 3V en sortie, sous le rail 3,3V) ne dépend pas non plus de R19.
  TSV791 : GBP 35MHz min/50MHz typ à VCC=3,3V (`tsv791.pdf`, p.8, tbl 7 —
  valeur relue visuellement, l'extraction texte brute de ce tableau
  colonnes-fusionnées n'était pas fiable).
- **Seul le pont diviseur après l'ATL431 est recalculé** :
  `V_TH = Ipk_cible × gain × R19 = 8,4 × 10,09 × 0,010 ≈ 0,848V`
  (au lieu de 0,6345V avec le LM4040 du prompt original, calculé pour
  7,5mΩ). R31(16,5kΩ)/R32(8,45kΩ) → `V_TH = 2,5 × 8,45/(16,5+8,45) ≈
  0,847V` → `Ipk_trip ≈ 0,847/(10,09×0,010) ≈ 8,39A`. Courant du pont
  ≈100µA, négligeable devant Iref max 150nA de l'ATL431 (p.4) — l'erreur
  de charge sur le pont lui-même est négligeable (le pont est en aval du
  nœud 2,5V, pas sur la broche REF).
- **R30 (polarisation ATL431) = 2,67kΩ** : avec `RAIL_3V3_PRI`≈3,3V,
  courant de polarisation ≈(3,3−2,5)/2,67k≈300µA, très au-dessus du
  minimum 35µA (marge ×8,5 même en comptant les ~100µA tirés par le pont
  R31/R32).
- Seuil résultant **≈8,39A**, tolérance estimée du même ordre que le
  prompt d'origine (offset TSV791 ≤0,2mV, offset LMV7219 6mV max/gain,
  ATL431 grade A ±1%, gain ±1%) — valeurs à affiner au banc, non
  recalculées ici (déplacement du point de fonctionnement, pas de la
  méthode de calcul de marge).

### Chaîne lente (U9/AMC0302R) — deux corrections

- **Entrée déplacée sur les pastilles Kelvin de R19** (`ISNS_KP`/`ISNS_KN`,
  au lieu du chemin de puissance `ISENSE_P`/`GND`) — amélioration : gratuite
  une fois le Kelvin disponible, strictement plus précise (élimine l'IR-drop
  du chemin de puissance de la mesure).
- **Filtre de sortie R18/C33 retaillé** (100Ω/1nF → **1kΩ/47nF**, fc≈3,4kHz)
  pour réellement moyenner le courant sur une période de commutation
  (200kHz) au lieu de filtrer seulement du bruit HF — l'ancien
  dimensionnement (fc≈1,6MHz) ne moyennait rien. Valeur de premier jet,
  compromis réjection d'ondulation / temps de réponse de la boucle de
  contrôle non figé, à retoucher au banc selon la cadence d'échantillonnage
  ADC réellement utilisée côté C2000. Ferme le point ouvert §11 : au courant
  moyen nominal (~1,9A), 1,9×0,010=19mV, loin des ±50mV pleine échelle de
  l'AMC0302R — plus de saturation possible en régime établi, quelle que
  soit la valeur finale de R19 entre 7,5 et 10mΩ.
- Topologie d'entrée de l'AMC0302R (INP/INN directes, sans filtre dédié)
  laissée telle quelle : la recommandation fabricant (filtre différentiel
  symétrique R1=R2+C différentiel+caps mode commun, `amc0302r.pdf` p.30
  fig 8-2, confirmée par les images fournies par l'utilisateur) n'a pas été
  ajoutée dans cette passe — purement une amélioration de réjection EMI/HF,
  sans incidence sur le point ouvert §11 ni sur l'architecture de
  protection ; à faire dans une passe ultérieure si nécessaire.

### Table de vérité du verrou (`SN74LVC1G74`, U18)

| `PWM_PRI_OUT` | blanking | `COMP` | `nPRE` | `nCLR` | `Q` | `nQ_TRIP` | `EN_PRI_GATED` |
|---|---|---|---|---|---|---|---|
| bas | – | x | — | bas | bas | haut | suit `EN_PRI_OUT` |
| haut | non écoulé | x | haut | haut | maintien (bas) | haut | suit `EN_PRI_OUT` |
| haut | écoulé | bas (pas de défaut) | haut | haut | bas | haut | suit `EN_PRI_OUT` |
| haut | écoulé | **haut (défaut)** | **bas** | haut | **haut** (verrouillé jusqu'à `PWM_PRI_OUT`=bas) | **bas** | **forcé bas → Q1 coupé** |

Priorité `nPRE`/`nCLR` à l'état bas simultané (ligne impossible ici
puisque `nCLR` suit directement `PWM_PRI_OUT` et `nPRE` ne peut passer bas
que si `PWM_PRI_OUT` est haut) à confirmer explicitement sur la datasheet
`sn74lvc1g74.pdf` (§7 Device Functional Modes) avant le banc — non
bloquant pour cette implémentation schématique, noté pour la vérification
au banc.

### Blanking (LEB)

`R33`(1,5kΩ)/`C52`(100pF) sur `PWM_PRI_OUT` → `PWM_LEB`, entrée A du NAND
`U17`. Constante de temps RC ≈150ns ; durée réelle du blanking dépendant
du seuil VT+ réel du NAND Schmitt (0,79–1,16V à VCC≈3,3V, voir plus haut)
— à mesurer au banc, pas recalculée ici en valeur finale (dépend de la
forme exacte du front RC, pas juste de τ).

### Interface C2000 (description, pas de code — ce dépôt n'a pas de firmware)

- GPIO `I_Shunt_ht_comp` (côté C2000, après le connecteur) → X-Bar
  d'entrée → eCAP, front descendant, compteur synchronisé au zéro de
  l'ePWM ⇒ `t_trip` par cycle ⇒ estimation `L ≈ Vin·(t_trip − t_retard)/I_TH`.
  Option miroir : même signal → X-Bar ePWM → Digital Compare → CBC (le PWM
  du C2000 reflète alors la coupure réelle, pas de boucle instable
  puisque le verrou ne se libère qu'au PWM bas). Noms de registres/X-Bar
  à confirmer dans le TRM F28P55x.
- Défaut franc : N trips consécutifs ⇒ arrêt one-shot (TZ OSHT par
  logiciel).
- `I_Shunt_ht_comp` bas au démarrage = primaire non alimenté ⇒ ne pas
  démarrer le PWM (cohérent avec le défaut `ISO7710F` de `U19`).

### Limites connues (documentées, pas résolues dans cette passe)

- Pendant le blanking (~150ns), la protection est aveugle — un défaut où
  le courant primaire monte par l'inductance de fuite seule n'est limité
  qu'en fin de blanking.
- La chaîne lente ne voit plus le courant crête (filtre moyenneur) :
  l'info crête vient uniquement du timing eCAP de `I_Shunt_ht_comp`.
- Seuil fixe (pont résistif) — un seuil réglable par le C2000 est une
  évolution possible, hors périmètre ici.
- Topologie d'entrée symétrique recommandée par TI pour l'AMC0302R
  (ci-dessus) pas encore appliquée — EMI/HF uniquement, pas de protection
  fonctionnelle affectée.

### Datasheets et BOM — état de la vérification

Chaque valeur ci-dessus cite sa page. **Les fiches YAML formelles
(`composants-datasheets/data/*.yaml`) de ces 6 nouvelles pièces n'ont PAS
été produites dans cette passe** : le schéma
`.claude/rules/data-yaml.md` de ce dépôt annexe exige (a) une **passe de
vérification en double extraction** dans un worktree séparé avant de
considérer une fiche finalisée, (b) pour `pinmap`, une **capture
d'empreinte PCB réelle** — impossible ici, `KICAD-HT` n'a aucune piste/via
(0 PCB routé), et (c) pour `ATL431`/`LMV7219`, aucune `family` existante
du schéma ne correspond proprement (référence de tension ajustable /
comparateur — ni `opamp`, ni `logic`, ni `csa` ne collent sans forcer),
ce qui demanderait d'étendre le tableau de familles de
`.claude/rules/data-yaml.md` **et** `tools/lint_hw.py` dans le même
commit, hors périmètre de cette tâche schématique. Produire des fiches
qui ne passeraient pas cette rigueur (ou qui la contourneraient) irait
contre la règle cardinale du dépôt annexe (« aucune valeur sans
source », pas de `src` approximatif). **Suivi à faire séparément dans
`composants-datasheets`** : fiches `atl431.yaml`, `lmv7219.yaml`,
`sn74lvc1g132.yaml`, `sn74lvc1g74.yaml`, `bat54s.yaml`,
`wsk1206r0100fea.yaml` (`sn74lvc1g08.yaml` existe déjà). Deux valeurs
encore à relire proprement avant toute fiche formelle : VT+ du 1G132 à
3,3V précis (actuellement une plage min/max p.6, pas de typ isolé) et le
tableau GBP du TSV791 à 3,3V (p.8, relu visuellement cette fois — fiable,
mais la fiche `tsv791.yaml` existante cite encore l'extraction texte
d'origine à vérifier/recouper).

### Vérification finale

`kicad-cli sch erc` sur la hiérarchie complète (5 feuilles désormais) :
**0 erreur**, 220 avertissements — 216 `endpoint_off_grid` (famille
préexistante, désalignements cosmétiques), 1 `lib_symbol_mismatch`
préexistant (`T1`/`MSD1514`), 1 `ground_pin_not_ground` préexistant (U7),
2 `isolated_pin_label` (`Vht_EN` préexistant §18, `Q_TRIP` — sortie de
réserve du verrou, intentionnellement non consommée ailleurs). Comparé
point par point à l'état juste avant cette passe : aucune régression,
seul `Q_TRIP` est un avertissement réellement nouveau, attendu et
justifié. Validation grammaticale top-level + absence de fragment
résiduel sur les 4 fichiers touchés/créés (`flyback.kicad_sch`,
`isolation.kicad_sch`, `KICAD-HT.kicad_sch`, `limitation-courant.kicad_sch`),
même discipline que pour §18.

### Addendum 2026-10-21 — LED de défaut sur `Q_TRIP`

`Q_TRIP` (sortie de réserve du verrou, jusqu'ici non consommée) reçoit un
usage réel demandé par l'utilisateur : « simplement une led rouge 3mm sur
la sortie Q, avec une resistance 10k et reliee au 3V3 ». Ajout de `R34`
(10k, 0805) et `D6` (`Device:LED`, `LED_THT:LED_D3.0mm`, même symbole/
empreinte que les LED existantes de `KICAD-C2000-powershield`/
`KICAD-C2000-devkit`) : `RAIL_3V3_PRI` → `R34` → `D6` anode → `D6` cathode
→ `Q_TRIP`. Choix volontairement simple, pas de fiche YAML composant
produite (LED générique non référencée précisément, à la demande de
l'utilisateur — pas de valeur de datasheet à sourcer puisqu'aucune pièce
précise n'a été retenue).

**Polarité corrigée par l'utilisateur (2026-10-21, après coup)** :
câblage initial (`RAIL_3V3_PRI` → `R34` → `D6` → `Q_TRIP`) donnait une LED
allumée en fonctionnement normal, éteinte en défaut — contre-intuitif,
signalé ci-dessus. Corrigé à la main dans l'IHM : `R34` pin 1 déplacé de
`RAIL_3V3_PRI` vers `GND`, `D6` repositionnée (anode/`A` côté `Q_TRIP` =
sortie `Q` de `U18`, cathode/`K` côté `LED_Q_A` = `R34` pin 2). Vérifié
par export netlist (`kicad-cli sch export netlist`) : net `Q_TRIP` =
{`D6` pin 2 (`A`), `U18` pin 3 (`Q`)} ; net `LED_Q_A` = {`D6` pin 1 (`K`),
`R34` pin 2} ; `R34` pin 1 = `GND`. Chemin : `Q_TRIP` (haut en défaut,
anode) → `D6` → `R34` → `GND` — la LED s'allume maintenant **en défaut
latché**, sens intuitif correct.

Édition chirurgicale (pas de régénération par `gen_limitation_courant.py`)
car le fichier `limitation-courant.kicad_sch` a été entre-temps rouvert et
retravaillé à la main par l'utilisateur dans l'IHM KiCad : réannotation
globale du projet (ex. `C49`→`C57`, collision de référence avec une autre
feuille), repositionnement complet des composants, et ajout de fils réels
(15 `wire` + 4 `junction`, alors que la convention du projet jusqu'ici
était étiquettes globales seules). `R34`/`D6` suivent toujours la
convention étiquette globale, posés dans une zone vide du schéma
(bas-gauche, hors de tout composant existant), pas raccordés par fil.

**Correction 2026-10-21 (post-coup)** : l'édition chirurgicale ci-dessus
avait en réalité inséré le bloc `lib_symbols` de `Device:LED` au mauvais
endroit — pas juste avant la fermeture réelle de `(lib_symbols ...)`
(après la dernière définition `custom_parts:TSV791`), mais plus loin dans
le fichier, **imbriqué à l'intérieur de l'étiquette globale `ISNS_AMP`**
(entre sa propriété `Intersheetrefs` et sa propre parenthèse fermante) —
une fausse identification de « la fermeture de lib_symbols » faite sans
vérifier ce qui précédait réellement ce point dans le fichier. Résultat :
`kicad-cli sch export svg` sur la feuille seule échouait
(« Échec du chargement de la schématique »), et dans l'IHM la feuille
s'ouvrait sans composants (seuls les fils restaient visibles) — exactement
le symptôme signalé par l'utilisateur. Diagnostic mené par bissection
(retirer catégorie par catégorie, puis élément par élément, en
reconstruisant chaque variante avec un analyseur S-expression conscient
des chaînes entre guillemets, pas un simple comptage de parenthèses) :
isolé à l'étiquette `ISNS_AMP`, confirmé en relisant directement le
fichier réel (pas une reconstruction) autour de cette ligne. Corrigé en
déplaçant le bloc `Device:LED` à la vraie position (juste après
`custom_parts:TSV791`, avant le premier `junction`/`global_label` réel) ;
`ISNS_AMP` restaurée à sa forme d'origine. Revérifié : chargement
standalone OK, export hiérarchie complète OK, comptage des éléments
top-level identique avant/après (121, dont 26 `symbol`/70 `global_label`),
`Q_TRIP` toujours résolu par `D6`. Leçon retenue : un simple comptage de
parenthèses (`check_balance.py`) ne suffit pas à garantir qu'une insertion
est au bon ENDROIT, seulement qu'elle est équilibrée en nombre — vérifier
le contexte immédiat (ce qui précède/suit réellement) avant d'insérer,
pas seulement après.

**Trouvaille annexe, non corrigée ici** : `kicad-cli sch erc` (10.0.5) sur
ce fichier donne des résultats **non déterministes** d'une exécution à
l'autre (257 vs 253 violations totales constatées, composition différente
à chaque fois : `wire_dangling`, `unconnected_wire_endpoint` et
`pin_not_driven` apparaissent 0 à 8 fois selon le tirage). Vérifié par 6
exécutions répétées sur un fichier strictement inchangé (3 avec l'ajout
`R34`/`D6`, 3 sur une copie restaurée sans). Les deux jeux donnent
exactement les mêmes 3 `isolated_pin_label` restants (`nQ_TRIP`,
`Vht_EN`, `I_Shunt_ht_comp`) et la même composition flottante — **la
non-déterminisme préexiste au présent ajout, il n'en est pas la cause**.
Origine probable : de très courts segments de fil (quelques centièmes de
mm) laissés par l'édition manuelle, autour de la zone `U15`/`R31`/`R32`
(pont `V_TH`) et de `D5` — à probablement nettoyer (re-snapper ces
bouts de fil sur leur pastille) si l'utilisateur veut un ERC stable ;
non traité ici, hors périmètre de la demande (« juste la LED »).

## §20 — Confinement de défaut : fusible VIN et TVS RAIL_8V25

Ajouté le 2026-10-23, suite à `doc/plan-isolation-4couches.md` (revue
d'isolation 3 domaines + analyse de confinement de défaut, §8 du
document). Deux composants posés par l'utilisateur dans `alim.kicad_sch` :

- **`F1`** (`Device:Fuse`, valeur provisoire `Fuse` — calibre non encore
  choisi) en série entre `J1` et le net `VIN`. Ferme le « Chemin 1 » du
  plan : un défaut sur cette carte (ex. `Q1` en court-circuit) ne tire
  plus `VIN` vers le bas pour le reste du système, dont le convertisseur
  isolé qui alimente le C2000.
- **`D2`** (`Device:D_TVS`, SMCJ10A) entre `RAIL_8V25` et `GND`. Ferme le
  premier étage du « Chemin 2 » (cascade `Reg1`→`Reg2`) : borne
  `RAIL_8V25` avant que `Reg1` en défaut ne pousse son entrée sur sa
  sortie au-delà de ce que `Reg2` encaisse. Le second étage
  (`RAIL_3V3_PRI`, `D7`/SMCJ04A) était déjà posé avant ce plan.

Vérifié par calcul de position de broche (pas seulement par label) :
`F1` relie bien `J1` pin 1 (brut, non étiqueté) à l'étiquette `VIN`
post-fusible ; `D2` relie bien `RAIL_8V25` à `GND`, aucun des deux ne
flotte. Fichier `alim.kicad_sch` revérifié (équilibre parenthèses
conscient des chaînes, chargement standalone, export hiérarchie
complète) après l'incident du §19 — même discipline désormais
systématique après tout ajout de composant.

**Nomenclature** : les repères `D5`/`D6`/`D7`/`R30`–`R32` suggérés par le
plan collisionnent avec `limitation-courant.kicad_sch` (§19), rédigé
après le commit sur lequel le plan se base. Table corrigée directement
dans `doc/plan-isolation-4couches.md`. Repères réellement libres pour la
suite : `D8` (TVS directe sur `VIN`, chemin 1 restant) et `R35`–`R37`
(résistances de référence inter-domaines, §3 du plan).

**Mise à jour 2026-10-23** :

- **`F1` = 3 A** (décidé par l'utilisateur, `Value` mis à jour dans
  `alim.kicad_sch` ; type temporisé/rapide et tension de service non
  encore précisés).
- **TVS directe sur `VIN`** : ne sera **pas** posée sur `KICAD-HT` — elle
  existe déjà sur la carte `KICAD-C2000-powershield`, en amont au niveau
  système. Cohérent avec le §2 du plan (« le convertisseur isolé du C2000
  prend `VIN` en amont du fusible de cette carte »). `D8` retiré de la
  liste des ajouts pour ce projet.
- **Résistances de référence inter-domaines (§3 du plan)** : posées dans
  `isolation.kicad_sch`, en **chaîne de 3×1 MΩ par barrière** (pas une
  seule résistance — un seul 0805 n'a que 0,8 mm d'écart cuivre entre ses
  pastilles, bien en-deçà des 8,5 mm visés) :
  - `R35`/`R6`/`R36` : `GND_CTRL` ↔ `VOUT_N` (barrière contrôle↔secondaire,
    traversée par `U7`).
  - `R37`/`R38`/`R39` : `GND_CTRL` ↔ `GND` (barrière contrôle↔primaire,
    traversée par `U3`/`U5`/`U8`/`U9`/`U10`/`U11`).
  - `R42`/`R41`/`R40` : `GND` ↔ `VOUT_N` (barrière primaire↔secondaire —
    non exigée par le plan, qui notait qu'aucun composant ne la traverse
    électriquement, mais ajoutée par cohérence entre les trois domaines).
    Impédance 3 MΩ, 30× celle du pont `R9`/`R10` (100k/100k,
    `flyback.kicad_sch`) qui fixe déjà le biais de `VOUT_N` depuis
    `HV_BIAS` — influence négligeable sur ce point de fonctionnement,
    vérifié par comparaison d'impédance.
  - Nomenclature revérifiée sur tout le projet après ajout : aucune
    collision (`R6` était libre — son usage d'origine, `100k` sur
    `PWM_SEC_IN`, a disparu d'une réorganisation antérieure du schéma
    secondaire).
  - **Point d'attention pour le passage en 4 couches** : la disposition
    actuelle (feuille `isolation.kicad_sch`) n'est qu'un agencement
    *schématique*, sans rapport avec le placement PCB réel. Au placement,
    les trois résistances de chaque chaîne doivent être **physiquement
    espacées** le long des 8,5 mm de la barrière correspondante (pas
    regroupées), sans qu'aucune autre piste/via/remplissage n'approche les
    deux nœuds intermédiaires à moins de cette distance — sinon la chaîne
    ne protège rien de plus qu'une résistance unique.

Reste ouvert : type/tension de service de `F1`. Les classes de nets
(`CTRL`/`PRI`/`SEC`, dans `KICAD-HT.kicad_pro`) et le fichier
`KICAD-HT.kicad_dru` existent désormais — voir §20bis pour l'état actuel
et une correction importante sur la portée des barrières.

## §20bis — Le secondaire n'est plus isolé du primaire (2026-10-25)

Décision utilisateur : dans le montage final, le secondaire de puissance
(`VOUT_N`/`VOUT_P`, classe de nets `SEC`) **ne sera plus flottant ni isolé
galvaniquement du primaire** (`GND`, classe `PRI`). Ça contredit la
prémisse posée tout au long de ce document et du `README.md` (« secondaire
flottant », repris dans le titre anglais « floating-secondary ») — les
deux ont été corrigés pour refléter le nouvel état, mais les sections
antérieures de ce document (notamment §1, les tableaux U4/U7 vers les
lignes 660-662, et §16-17 sur `HV_BIAS`) décrivent encore l'ancienne
architecture à titre historique ; ne pas les prendre pour l'état actuel.

**Ce qui change concrètement** :
- La règle `.kicad_dru` `barriere_primaire_secondaire` (2,5 mm entre les
  classes `PRI` et `SEC`, ajoutée au §20 pour fermer ce qui semblait être
  la seule barrière restante après `T1`) est **retirée** — commentée dans
  `KICAD-HT.kicad_dru`, pas supprimée, pour garder une trace de pourquoi
  elle a existé.
- La classe de nets `SEC` est **conservée** dans `KICAD-HT.kicad_pro` à
  titre d'organisation/documentation (elle identifie toujours le
  sous-circuit secondaire), mais ne porte plus de contrainte de barrière
  vis-à-vis de `PRI`.
- La seule barrière réellement isolée qui reste sur cette carte est
  **contrôle (C2000, classe `CTRL`) ↔ puissance (`PRI`+`SEC`)**, via les
  sept isolateurs (`AMC0302R`/`AMC0311R`/`ISO7710`/`DPC817`) — la règle
  `barriere_controle` (4 mm) n'est pas affectée par ce changement, elle
  s'applique toujours à `CTRL` contre tout le reste, `SEC` inclus.

**Ce qui n'a pas été vérifié dans cette passe** : la conséquence
électrique précise du décloisonnement primaire/secondaire (quel nœud
relie désormais `GND` et `VOUT_N` dans le schéma — tie-point direct,
composant intermédiaire, ou autre — et l'impact sur `D1`/`D4`/les calculs
de surtension du §17, établis en supposant un secondaire flottant). À
vérifier avant de considérer la conception électrique close, pas seulement
la règle DRC retirée.

Non traité ici, hors périmètre de cette passe : réécriture complète des
sections historiques (§1, tableaux U4/U7, §16-17) pour refléter la
nouvelle architecture — elles restent lisibles comme journal de
conception, mais un lecteur pressé doit partir de ce §20bis, pas du §1.

## §21 — Via-stitching Q5 (VOUT_P) vers le plan de cuivre F.Cu (2026-10-28)

**Pourquoi.** Le tab de Q5 (TO-252, drain=`VOUT_P`) n'était relié à la
zone de cuivre `VOUT_P` sur `F.Cu` que par l'empreinte elle-même — aucune
liaison de cuivre explicite entre le `B.Cu` du composant et la zone top,
dimensionnement en courant jamais vérifié pour les 3A de sortie visés.

**Fait.** 18 vias (0,6mm/perçage 0,3mm, valeurs par défaut projet `FAB-01`
de `regles-pcb`) posés en couronne autour du pad `VOUT_P` de Q5, chacun
relié par un stub court (0,5mm, 0,3-0,8mm du bord du pad). Dimensionné
pour 3A à ~200mA/via (`ALI-03`) : 15 vias nécessaires, 18 posés (marge).
Vérifié par DRC : zéro erreur sur la zone concernée ; compteur
d'éléments non connectés passé de 153 à 152, confirmant la liaison
électrique réelle (pas seulement l'absence d'erreur).

**Méthode** : posé par script kipy, pas à la main — deux tentatives
ratées avant la bonne (court-circuit sur les pastilles `GND`/`HV_BIAS_IN`
de `J1`, puis piste de liaison traversant des pistes existantes
`V_HT_OUT`/`U15_OUTP` en cherchant un emplacement trop éloigné du pad
plutôt que juste à son bord). Protocole complet, incidents vécus et
script de référence dans `KICAD-EDITION-GROUPEE-KIPY.md` (racine de
l'atelier) — pas répété ici.

## §22 — Via-stitching VOUT_N, zone F.Cu vers zone In1.Cu — tentative initiale retirée (2026-10-28)

**Pourquoi.** Les deux coulées `VOUT_N` (une sur `F.Cu`, une sur
`In1.Cu`) qui se recouvrent autour de x=125-134/y=82-89 n'étaient reliées
par aucun via à cet endroit — deux plans de cuivre superposés, même net,
mais électriquement disjoints localement tant qu'aucune liaison
traversante ne les joint.

**Tentative initiale (retirée).** 1 via (0,6mm/perçage 0,3mm) posé en
(131,0 ; 84,0) — décalé d'environ 6mm par rapport au point indiqué par
l'utilisateur (125,82), qui tombe en réalité 0,5mm en dehors du contour
réel de la zone `F.Cu` (son bord haut est à y=82,5, pas y=82). Ce
positionnement ponctuel était **mauvais** : signalé par l'utilisateur
("il mord sur un pad de la diode") — à 1,64mm du pad 2 de `D4`, même net
donc aucune violation DRC levée (pas de règle de clearance entre
éléments du même net), mais un via posé physiquement sur/contre un pad
existant n'est pas une pose propre. **Retiré.**

**Clarification de méthode reçue à cette occasion** : le via-stitching
entre deux zones n'est pas « un via au point demandé », mais **une
répartition uniforme de vias sur toute la surface commune aux deux
zones, en évitant systématiquement tout pad et toute piste existants**
(pas seulement ceux d'un autre net). Méthode corrigée appliquée et
validée au §23 ci-dessous (grille `GND_CTRL`) — **le redo de ce
stitching `VOUT_N` avec la même méthode (grille sur la surface commune
F.Cu∩In1.Cu, pas encore choisi) reste à faire**, pas encore reposé au
moment de la rédaction de ce paragraphe.

**Point technique découvert au passage** (toujours valable, indépendant
du retrait ci-dessus) : la zone `VOUT_N` sur `In1.Cu` existait dans le
fichier (contour défini) mais n'était **pas remplie** (`filled=False`
côté API kipy) à ce moment — un via posé dans une zone non remplie ne
"voit" aucun cuivre réel sur cette couche, d'où une violation
`via_dangling` au premier DRC de cette tentative. Un appel à
`board.refill_zones()` (méthode kipy, pas de régénération manuelle)
a résolu l'incohérence — zones désormais remplies et à jour.

**Méthode (tentative initiale, incomplète)** : posé par script kipy, un
seul via pilote au point demandé — recherche par anneaux, rejeté par
manque de dégagement, élargi jusqu'à (131,84). C'est cette approche
« un seul point » qui était la mauvaise méthode, corrigée au §23.
Protocole de recherche par anneaux et piège `filled=False`/
`refill_zones()` documentés dans `KICAD-EDITION-GROUPEE-KIPY.md`.

## §23 — Via-stitching en grille : GND_CTRL, F.Cu∩In1.Cu∩B.Cu (2026-10-28/29)

**Pourquoi.** Trois coulées `GND_CTRL` (F.Cu, In1.Cu, B.Cu, même emprise
x:95-114,6/y:47-117, ≈20×70mm) se superposent sans via les reliant entre
elles dans cette zone — méthode demandée explicitement : grille
régulière de pas 5mm sur toute la surface commune, pas un point isolé
(voir correction de méthode au §22).

**Fait (v1, insuffisant).** 13 vias (0,6mm/perçage 0,3mm, `FAB-01`)
posés sur une grille 5mm alignée sur des coordonnées rondes
(x∈{100,105,110}, y multiples de 5), dans l'intersection des trois
contours de zone `GND_CTRL`, avec une marge intérieure de 0,4mm par
rapport au bord de cette intersection. 14 points candidats trouvés
initialement sur toute l'emprise (≈39 points de grille bruts, 25
écartés pour collision avec des pastilles/pistes existantes, toutes
nets confondus) ; un 14ᵉ (100,95) écarté *après* pose — trop proche
(1,66mm centre à centre) du pad 1 de `J2` (net `3V3_ISO`) sur `In2.Cu`,
en violation de l'isolement de la classe `CTRL` (0,2mm requis, 0,1664mm
réel) : l'approximation de taille de pastille (plus grande dimension de
`copper_layers[0]`) sous-estimait la vraie empreinte sur cette couche
interne. Retiré, grille à 13 vias, DRC propre — mais jugé **mal
couvert** par l'utilisateur : la grille alignée sur des multiples
absolus de 5mm démarrait à x=100/y=50, laissant une bande de ~4,5mm non
couverte le long du bord gauche (x=95-100) et du bord haut.

**Correction (v2, pas 5mm).** Les 13 vias v1 retirés, grille recalculée
en ancrant l'origine à 1mm du bord réel de l'intersection plutôt que sur
des coordonnées rondes (x₀=95+1=96, y₀=47+1=48, pas 5mm dans les deux
cas), toujours filtrée par la même intersection `shapely` et les mêmes
obstacles. Résultat : **31 vias** (plus du double), colonnes
x∈{96,101,106,111} au lieu de {100,105,110} — la colonne la plus proche
du bord (x=96) s'est révélée presque entièrement dégagée sur toute la
hauteur (14 vias), les composants du secteur étant plutôt groupés au
centre de la zone. Vérifié par DRC : diff complet contre un relevé pris
juste après le retrait de la v1, rigoureusement identique (164
violations, aucune ajoutée/retirée), non-connectés 75→73. **Confirmé
bon par l'utilisateur.**

**Resserré (v3, pas 4mm).** Même ancrage au bord (1mm), même
intersection et mêmes obstacles, pas réduit de 5mm à 4mm sur demande
explicite : 52 vias (contre 31), même grille de colonnes x∈{96,100,104,
108,112} (5 colonnes au lieu de 4, la dernière à x=112 encore à 1,5mm du
bord droit x=114,5). Vérifié par DRC contre un relevé pris juste après
le retrait de la v2 : rigoureusement identique au départ (164
violations, aucune ajoutée/retirée), non-connectés 75→73. Version
retenue à ce stade.

**Point technique découvert** : les zones d'**autres nets** ne sont des
obstacles réels que sur les couches **partagées** avec les zones que
l'on relie. Une zone `3V3_ISO` sur `In2.Cu` recouvre exactement la même
emprise que `GND_CTRL` (F.Cu/In1.Cu/B.Cu) mais n'est **pas** un obstacle
pour un via traversant : KiCad pose un anti-pad automatique autour du
via lors du remplissage sur toute couche où le net diffère — ignorer
cette distinction avait d'abord fait tomber le compte de candidats à 0
(l'intersection entière était classée "occupée" par erreur).

**Méthode** : script kipy, grille uniforme (pas demandé explicitement,
5mm) sur l'intersection `shapely` des contours des zones de même net,
pastilles/pistes/vias de **tous nets confondus** traités comme
obstacles (pas seulement ceux d'un autre net — consigne explicite),
zones d'autres nets traitées comme obstacles seulement sur les couches
partagées (voir ci-dessus). Origine de grille ancrée à 1mm du bord réel
de l'intersection (v2), pas sur des coordonnées rondes arbitraires (v1)
— correction reçue de l'utilisateur après constat visuel d'une
couverture insuffisante. Compte de candidats présenté avant la pose
(règle `07-stitching.md`/STI-02 de `regles-pcb`, pas par défaut 6,35mm
remplacé ici par le pas demandé de 5mm). Préalable « routage
terminé/gelé » de `07-stitching.md` non respecté ici (routage encore en
cours sur d'autres feuilles) — pose effectuée quand même sur demande
explicite de l'utilisateur, à reposer si `GND_CTRL` est redessiné
ensuite. Script de référence, piège `3V3_ISO`/couches-partagées et
ancrage de grille par le bord ajoutés à `KICAD-EDITION-GROUPEE-KIPY.md`.

## §24 — Via-stitching GND, toute la carte, pas 4mm ancré au bord réel (2026-10-29)

**Pourquoi.** Trois coulées `GND` (F.Cu, In1.Cu, B.Cu, x:118,9-180/
y:47-117, moitié droite de la carte) sans via les reliant entre elles —
demande explicite : "beaucoup de courant sur certaines zones", pas de
grille 4mm (plus serré que le 5/4mm de `GND_CTRL` au §23), ancré à 2mm
du **bord réel de la carte** (`Edge.Cuts`, un simple rectangle
95≤x≤180/47≤y≤117 — pas du bord de la zone, cette fois, contrairement au
§23) côté x=180mm nommé explicitement par l'utilisateur.

**Fait.** 36 vias (0,6mm/perçage 0,3mm, `FAB-01`) posés sur une grille
4mm, origine ancrée à (x=180−2=178, y=47+2=49) — colonne x la plus à
droite à 178, décroissant par pas de 4mm vers la gauche ; rangée y la
plus haute à 49, croissant par pas de 4mm. 255 points de grille bruts
sur l'emprise commune des 3 zones réduite au rectangle de la carte
moins 2mm ; seuls 36 dégagés de tout pad/piste/via (tous nets confondus)
et de toute zone d'un autre net partageant une couche — confirme la
remarque de l'utilisateur sur la forte densité de cette zone (8,5% de
taux de passage contre 59% et 60% pour les deux grilles `GND_CTRL`).
Vérifié par DRC contre un relevé pris juste avant la pose (lui-même déjà
à 170 violations/10 non-connectés, après les vias manuels ajoutés par
l'utilisateur entre-temps dans les zones denses) : **0 violation
ajoutée, 2 résolues en prime** (ratsnest comblés), non-connectés 10→8.

**Méthode** : même protocole que §23 (intersection `shapely`, obstacles
tous nets sur pads/pistes/vias, zones d'autres nets filtrées par couche
partagée), avec une différence clé — l'ancrage de grille se fait cette
fois sur le **contour de la carte** (`Edge.Cuts`, récupéré via
`board.get_shapes()` filtré par couche, un simple rectangle ici) et non
sur le contour de la zone elle-même, parce que la demande nommait
explicitement "le bord de la carte", pas le bord de la zone. Paramètres
clarifiés en plusieurs échanges (1mm jugé trop serré pour du stitching
de plan de masse → 4mm confirmé, marge du bord ajustée de 2mm à 2mm en
repassant par une fausse alerte à 2mm de pas avant confirmation finale)
— ne pas supposer qu'un chiffre donné en premier reste valide sans
confirmation explicite en cas d'échanges successifs contradictoires.

## §25 — Contour silkscreen SOIC-8 DWV corrigé (U7/U9/U11/U22) (2026-10-29)

**Pourquoi.** 48% des violations DRC de la carte (68/141) étaient du
silkscreen ; 32 d'entre elles venaient d'une seule cause géométrique :
l'empreinte partagée `SOIC_DWV` (`lib_fp_commun/SOIC_DWV.pretty/
SOIC-8_DWV_5.85x11.5mm_P1.27mm.kicad_mod`, utilisée par U7/U9/U11/U22)
dessine un contour de corps à x=±5,75mm alors que les pastilles (1,8mm
de large, bord à x=±6,35mm) débordent **des deux côtés** de ce contour —
le trait vertical du contour traverse donc les 4 pastilles de chaque
côté.

**Fait.** Contour corrigé dans le fichier source partagé : les 2 arêtes
verticales (qui traversaient les pastilles) remplacées par 4 courtes
amorces de coin (0,5mm), les 2 arêtes horizontales (haut/bas, qui ne
croisent rien) conservées. Répercuté sur les 4 instances posées dans ce
projet (empreintes **embarquées** dans le `.kicad_pcb`, pas de lien
live vers la bibliothèque — correction du fichier source seule
insuffisante, chaque instance éditée individuellement). **-32
violations DRC** (141→109), zéro nouvelle violation (diff DRC complet
avant/après).

**Deuxième cause, plus petite, trouvée au passage** : le point de
broche 1 (cercle silkscreen rempli, rayon 0,3mm, épaisseur de trait
0,3mm) empiétait aussi sur la pastille 1 — **l'épaisseur du trait
s'ajoute au rayon nominal** (rayon effectif = rayon + épaisseur/2 =
0,45mm, pas 0,3mm), ce qui n'était pas évident au premier essai (un
décalage de 0,2mm s'est révélé insuffisant, tout juste à la limite).
Décalé de 0,3mm au total (position finale : centre à -6,9mm au lieu de
-6,6mm) pour un dégagement réel. **-4 violations** supplémentaires sur
cette carte (109→105).

**Partagé avec KICAD-HV** (même empreinte, 5 instances posées) : même
correction appliquée là-bas, **-9 violations** (139→... puis -5 pour le
cercle), avec **1 nouvelle violation mineure résiduelle** signalée, pas
corrigée : le point de broche 1 de son `U9` se retrouve trop proche du
champ référence du composant voisin `R22` une fois décalé — propre à
cette carte (placement non figé, `R22` très proche), pas à l'empreinte
elle-même ; pas réduit en deçà de 0,3mm de décalage (testé), toujours
présent. Laissé tel quel : c'est un avertissement mineur sur une carte
dont le placement n'est explicitement pas encore figé (`CLAUDE.md` de
`KICAD-HV`), pas une empreinte à retoucher pour un seul voisinage.

**Méthode** : édition texte directe des 3 fichiers (bibliothèque
partagée + 2 `.kicad_pcb`), KiCad fermé pendant toute l'opération
(vérifié par `tasklist`, cf. le risque documenté dans
`KICAD-EDITION-GROUPEE-KIPY.md` sur l'édition texte d'un `.kicad_pcb`
ouvert). UUID des segments retirés réutilisés pour 2 des 4 nouvelles
amorces par instance, nouveaux UUID générés pour les 2 autres — pas de
collision constatée.
