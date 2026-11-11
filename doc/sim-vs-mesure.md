# Validation — calcul, simulation, mesure

Étage flyback de `KICAD-HT`, redressement passif par la
diode de corps de Q2 (étape de validation avant le contrôleur de
redressement synchrone UCC24612).

> **État** : simulation étapes 1-4 faite avec les modèles réels
> (IPD050N10N5 Infineon, clamp D1 SMCJ43A). **Prototype non mesuré.** Les
> colonnes « Mesure » restent vides tant qu'elles n'ont pas été remplies
> au banc — jamais complétées par des valeurs simulées.
>
> Les fichiers `simulation/results/*.csv` cités plus bas ne sont **pas
> versionnés** (`.gitignore`, trop volumineux) — seuls les graphes PNG le
> sont. Régénérables localement via les scripts `simulation/run_*.py`
> correspondants.

---

## 1. Conditions communes

| Paramètre       | Valeur                                                          |
| ---------------- | ---------------------------------------------------------------- |
| f_sw             | 200 kHz                                                          |
| Couplage         | Coilcraft MSD1514-103ME, 1:1, 10µH, k=0,9798 (fuite 0,40µH typ., datasheet — corrigé 2026-11-11, voir note sous ce tableau) |
| MOSFET Q1/Q2     | IPD050N10N5 réel (Infineon, sous-circuit SPICE officiel OptiMOS5, `simulation/models/IPD050N10N5.lib`) |
| Redresseur       | Diode de corps de Q2 (gate à 0V) — pas de Schottky discret dans le vrai chemin de puissance |
| Clamp primaire   | D1 = SMCJ43A réel (Vbr=47,8V@1mA, Vc=69,4V@21,7A, `smcj43a.yaml`) |
| Clamp secondaire | **aucun modélisé** — voir §2, c'est la limite la plus importante de cette passe |
| Puissance visée  | 10W (6V et 12V), + un point à charge légère (~1W, mêmes duty cycle/Rload trouvés par itération) |
| Charge           | Rload = Vout_cible² / Pout_cible                                 |

> **Note (2026-11-11)** : jusqu'ici, `K1 L1 L2` dans `simulation/gen_asc.py`
> prenait la colonne « coupling coefficient » arrondie du tableau
> `msd1514.pdf` (0,99), ce qui implique L_fuite = L×(1-k²) ≈ 0,20µH — la
> **moitié** de la fuite typique *directement publiée* pour ce modèle
> (0,40µH, même tableau), déjà celle utilisée telle quelle dans
> `00-intention-conception.md` §5/§6 pour l'énergie de clamp D1. Corrigé :
> k = sqrt(1-0,40/10) = 0,9798, dérivé de la fuite publiée plutôt que de la
> colonne arrondie (qui ne lui correspond pas exactement, les deux colonnes
> du tableau Coilcraft étant chacune une mesure « typ » arrondie
> indépendamment, pas une relation algébrique exacte entre elles).
> **Seules les sections §7/§7bis (18,9W) ont été rejouées avec la valeur
> corrigée** — §2/§2bis/§6 (10W) ci-dessous restent telles que simulées
> sous l'ancien k=0,99, non revalidées, à ne pas comparer directement à
> une future repasse 10W sans les rejouer aussi.

## 2. Résultats (étapes 1-4)

| Point | Vin | D | Vout | Pout | η | Mode | Ipk pri | Irms pri | Vds Q1 max | Vds Q2 max |
|---|---|---|---|---|---|---|---|---|---|---|
| 11V→6V  | 11V | 38,3% | 5,96V | 9,88W | 85,0% | **CCM** | 4,13A | 1,85A | 49,8V | 57,4V |
| 11V→12V | 11V | 53,6% | 11,98V | 9,96W | 90,2% | **CCM** | 3,41A | 1,63A | 49,4V | 74,4V |
| 20V→6V  | 20V | 25,0% | 5,96V | 9,87W | 84,9% | **CCM** | 4,26A | 1,38A | 49,6V | 88,5V |
| 20V→12V | 20V | 30,2% | 11,90V | 9,84W | 90,9% | DCM | 3,75A | 1,20A | 49,4V | 75,7V |
| 25V→6V  | 25V | 21,1% | 6,00V | 10,00W | 84,1% | **CCM** | 4,62A | 1,30A | 50,7V | **106,7V** ⚠ |
| 25V→12V | 25V | 26,3% | 12,05V | 10,08W | 89,3% | DCM | 3,97A | 1,19A | 48,8V | **106,8V** ⚠ |
| 20V→6V, charge légère (~1W) | 20V | 11,3% | 6,13V | 1,04W | 81,0% | CCM (limite) | 1,80A | 0,37A | 34,9V | 53,0V |

CSV complet (avec le détail des pertes par poste) : `simulation/results/envelope.csv`.
Figure : `simulation/plots/envelope_eta_vds.png`.

**Mode de conduction déterminé sur la forme d'onde** (I(L2) juste avant le
rallumage de Q1, comparé au pic de courant primaire — pas supposé) : la
majorité des points réels sont **CCM**, pas DCM comme une première analyse
rapide l'avait suggéré à tort pour certains points. Seuls 20V→12V et
25V→12V ressortent DCM, et le point à charge légère est à la limite
(5,6% du pic, à retraiter avec plus de marge sur les seuils si on veut
trancher plus finement).

### ⚠ Constat le plus important de cette passe

**Vds_Q2 dépasse 100V (la tenue de l'IPD050N10N5) à Vin≥23V environ**,
côté secondaire, pendant la résonance qui suit le pic de conduction — sans
qu'aucun clamp secondaire ne soit modélisé (seul D1 côté primaire
existe). Vin_max de la spec est 25V (`00-intention-conception.md`) : les
points 25V→6V et 25V→12V simulent 106,7V et 106,8V, **au-delà de la
tenue en tension du composant réellement sourcé**. À traiter avant
d'aller plus loin : soit un clamp secondaire dédié, soit revérifier si le
réseau Lmesh_sec/Cinter ESTIMÉ (non sourcé, voir §3) exagère la résonance,
soit réduire Vin_max d'usage réel.

### Pertes — total fiable (Pin−Pout), décomposition non publiée

Pour chaque point, la somme des postes (Q1 total non séparé, diode de
corps Q2 totale non séparée, DCR primaire/secondaire, shunt, ESR Cout)
**ne retombe pas** sur Pin−Pout à ±5% (écart résiduel ~8-12% de Pin−Pout
selon le point, contre plusieurs dizaines de % avec l'ancien modèle de
substitution — nettement amélioré mais pas encore résolu). Conformément
à la règle de travail : **Pin−Pout fait foi comme perte totale**, la
décomposition Q1/Q2 n'est **pas** séparée en conduction/commutation/Coss
dans cette passe (reste à faire si besoin, étape 3 du plan complet).

## 3. Paramètres ESTIMÉS (non sourcés — à ne jamais traiter comme mesurés)

| Paramètre | Valeur utilisée | Pourquoi ESTIMÉ |
|---|---|---|
| `Lmesh_pri`, `Lmesh_sec` (inductances de maille primaire/secondaire) | ~0 (placeholder numérique, 1pH) dans cette passe | Aucune mesure de routage disponible avant le PCB réel. Le plan prévoit un balayage 0/nominal/2× — pas encore fait. |
| `Cinter_ESTIME` (capacité inter-enroulements) | 0 (composant présent dans le générateur, pas instancié dans cette passe) | Non publiée par Coilcraft pour le MSD1514-103ME. Sert à l'étape 6 (bruit de mode commun), hors scope ici. |
| Perte cœur transformateur (calculateur Coilcraft) | **pas recalculée** pour ces points | Les 282mW/291mW obtenus précédemment correspondent aux anciens points (modèle MOSFET de substitution, pas de clamp réel) — courants différents maintenant, à redemander à l'utilisateur sur les nouveaux Ipk/Irms de ce tableau si on veut un chiffre à jour. |

## 4. Protocole de mesure

À remplir avant la séance de banc.

| Élément            | Choix                                     |
| ------------------ | ----------------------------------------- |
| Alimentation       |                                           |
| Charge             | (électronique / résistive — préciser)     |
| Oscilloscope       | modèle, bande passante, limitation BW     |
| Sonde de tension   | rapport, masse courte (ressort) oui/non   |
| Mesure de courant  | sonde, ou shunt R19 + sonde différentielle |
| Mesure de Vout     | multimètre, au plus près de Cout          |
| Température        | ambiante, et des composants après 10 min  |

Données brutes : `mesures/` — exports CSV de l'oscilloscope, un fichier
par capture, nommé `AAAAMMJJ_point_grandeur.csv`.

### 4bis. Limitation de courant cycle-à-cycle (§19 de `00-intention-conception.md`)

À faire une fois la carte assemblée avec la feuille `limitation-courant.kicad_sch` :

- **Dépassement de trip** : sonde de courant sur Q1 (ou shunt R19 côté
  Kelvin) + sonde de tension Vds, seuil abaissé artificiellement (pont
  R31/R32 temporaire) pour déclencher à un courant mesurable sans
  dépasser le MOSFET, à Vin = 11V / 20V / 25V. Comparer le dépassement
  réel au budget de retard calculé en §19 (~0,2–0,26A à 25V).
- **Durée réelle du blanking** : sonde sur `PWM_LEB` (A du NAND `U17`) et
  `COMP` (sortie LMV7219), mesurer le temps entre front montant de
  `PWM_PRI_OUT` et le moment où `PWM_LEB` franchit VT+ (0,79–1,16V à
  VCC≈3,3V, datasheet `sn74lvc1g132.pdf` p.6) — comparer à la constante
  RC nominale (R33×C52≈150ns).
- **Suivi de `I_Shunt_ht_comp`** : vérifier que chaque trip produit bien un
  front descendant sur `I_Shunt_ht_comp` côté connecteur `J2` (donc côté
  C2000 après `J21`), et que le signal reste haut en fonctionnement
  normal, bas si le primaire est débranché/non alimenté (défaut
  `ISO7710F` de `U19`).

## 5. Comparaison des formes d'onde

Pour chaque point : la courbe simulée et la mesure superposées sur le
même graphique, depuis les CSV.

- [ ] Courant primaire I(L1)
- [ ] Courant secondaire I(L2) — fenêtre de conduction utile, mode CCM/DCM
- [ ] Tension drain Q1 — amplitude et amortissement de la résonance
- [ ] **Tension drain Q2 — vérifier en priorité le dépassement 100V prédit à Vin≥23V**
- [ ] Ondulation de Vout

## 2bis. Modèle simplifié (Schottky générique) — comparaison et perte clamp D1

Le modèle de redressement par diode de corps du vrai IPD050N10N5 (§2) est
fidèle mais lent (35-90s/point, convergence parfois capricieuse). Sur
demande explicite (comparer vite, et surtout **chiffrer la perte dans le
clamp D1** qui sera de toute façon présent quel que soit le choix de
redressement) : Q1 et D1 restent réels, le redressement secondaire est
remplacé par une Schottky générique simple (`.model D(IS=100n N=1
RS=5m)`, pas un composant réellement sourcé — juste un modèle rapide et
robuste pour ce comparatif).

| Point | η (diode de corps) | η (Schottky) | **Perte D1 (clamp)** |
|---|---|---|---|
| 11V→6V  | 85,0% | 88,0% | 336mW |
| 11V→12V | 90,2% | 91,5% | 327mW |
| 20V→6V  | 84,9% | 87,5% | 459mW |
| 20V→12V | 90,9% | 91,2% | 406mW |
| 25V→6V  | 84,1% | 86,5% | 616mW |
| 25V→12V | 89,3% | 87,9% | **891mW** |
| 20V→6V, charge légère | 81,0% | 85,8% | 0,8mW (négligeable) |

CSV : `simulation/results/envelope_schottky.csv`. Figure :
`simulation/plots/compare_real_vs_schottky.png`.

**Sur la perte clamp D1** : substantielle et monte avec Vin (jusqu'à
891mW à 25V/12V) — confirme que c'était une inquiétude fondée. Reste
large marge face à la tenue thermique du composant (P_av=5W max,
`smcj43a.yaml`) : marge ×5,6 au pire point. Pas un problème de
dimensionnement du composant, mais un vrai poste de rendement à ne pas
négliger dans le bilan global.

**Écart de rendement entre les deux modèles** : 1,5 à 3,5 points
d'efficacité selon le point (le Schottky simplifié est systématiquement
plus optimiste, sauf à 25V→12V où c'est l'inverse — à élucider, voir §6).
Cohérent avec l'attente : le modèle simplifié donne un ordre de grandeur
rapide, pas un chiffre de conception final — pour ça il faut soit le
modèle réel (lent), soit la mesure au banc.

**Vds_Q2 bien plus faible avec le modèle Schottky** (37-50V typiquement,
contre jusqu'à 106,8V avec le modèle réel, §2) — **ne pas conclure que le
dépassement 100V a disparu** : c'est le modèle simplifié qui ne reproduit
pas la résonance non-linéaire réelle du MOSFET. Le constat du §2 (Vds_Q2>100V à
Vin≥23V) reste la référence tant qu'il n'est pas infirmé par une mesure.

## 6. Inexpliqué / à vérifier

- Décomposition des pertes Q1/Q2 par poste (conduction/commutation/Coss)
  ne boucle pas avec Pin−Pout à ±5% — méthode de mesure à revoir (étape 3
  non terminée).
- Le point à charge légère (20V→6V, ~1W) est classé CCM à la limite
  (5,6% du pic de courant) — borderline, pas une conclusion ferme.
- Dépassement Vds_Q2 100V à Vin≥23V : pas encore confronté à une mesure
  réelle, ni revérifié avec un vrai modèle de Lmesh/Cinter (actuellement
  quasi nuls, donc la résonance simulée est probablement **optimiste** par
  rapport au PCB réel — l'écart pourrait être pire en vrai, pas meilleur).
- Point 20V→12V avec le modèle Schottky : Vout=10,84V, nettement sous la
  cible et sous le résultat du modèle réel (11,90V) au même D/Rload —
  seul point où le modèle simplifié donne un résultat moins favorable que
  le modèle réel (tous les autres vont dans l'autre sens). Pas élucidé,
  à revérifier avant de faire confiance à ce point précis.
- Convergence SPICE intermittente sur certains points (le même point peut
  échouer à une relance et réussir à la suivante) — pas bloquant
  (nouvelle tentative suffit) mais pas expliqué.

## 7. Passage à 18,9W (cible spec réelle) + redressement synchrone idéal (proxy UCC24612)

`00-intention-conception.md` §2 fixe la cible réelle de la carte à
**18,9W** (10 filaments, 6,3V/3A en parallèle ou 12,6V/1,5A en série,
même puissance dans les deux cas) — pas les 10W de validation initiale
ci-dessus. §3/§4 du même document avaient déjà fait, à la main (formule
idéale D/(1-D)=Vout/Vin, sans SPICE), le calcul de marge courant à ce
point précis : Irms primaire 3,37A / secondaire 4,45A vs limite datasheet
MSD1514-103ME 7,6A (« one winding »), marges ×2,26/×1,71. Cette passe
vérifie ce calcul par SPICE et répond à la question motivant l'UCC24612 :
**le redressement synchrone règle-t-il, en plus du rendement, le
dépassement Vds_Q2>100V déjà trouvé à 10W (§2) ?**

Aucun modèle SPICE sourcé n'existe pour l'UCC24612 (contrôleur analogique
à détection de Vds, pas de macromodèle publié par TI) — même situation
que la Schottky générique du §2bis. Proxy retenu, même esprit : Q2 reste
le vrai sous-circuit IPD050N10N5 (diode de corps toujours présente
pendant le temps mort), grille pilotée par un PULSE idéal complémentaire
à Q1 (temps mort 100ns) — approxime une diode emulation parfaite, **pas**
une simulation du composant réel ni une mesure. Implémenté dans
`simulation/gen_asc.py` (`rectifier="sync_ideal"`), en branchant le
paramètre `dead` de `build()` qui existait déjà dans la signature mais
n'était utilisé nulle part.

Méthode (conforme à la discipline « simple d'abord, un changement à la
fois ») : D trouvé par `find_duty.py` (modèle Schottky rapide déjà
validé) aux mêmes 6 coins Vin×Vout que l'enveloppe 10W mais à
Rload=Vout²/18,9 (2,1Ω au coin 6,3V, 8,4Ω au coin 12,6V) ; D réutilisé tel
quel pour la passe `sync_ideal` (pas re-résolu pour le modèle réel — la
puissance réellement délivrée dérive donc de 19,7 à 21,6W selon le point,
voir tableaux). `simulation/run_envelope_18w9.py`,
`simulation/results/envelope_18w9_schottky.csv`,
`simulation/results/envelope_18w9_sync.csv`.

**Passe 1 — Schottky idéal (même modèle rapide déjà validé à 10W, seule
la puissance change) :**

| Point | Vin | D | Vout | Pout | η | Ipk pri | Irms pri | Vds Q1 max | Vds Q2 max |
|---|---|---|---|---|---|---|---|---|---|
| 11V→6,3V  | 11V | 0,4006 | 6,07V | 17,57W | 81,2% | 5,96A | 3,14A | 55,0V | 18,9V |
| 11V→12,6V | 11V | 0,5502 | 12,33V | 18,11W | 86,5% | 4,89A | 2,64A | 53,8V | 26,1V |
| 20V→6,3V  | 20V | 0,2602 | 6,07V | 17,52W | 81,2% | 5,28A | 2,12A | 54,4V | 28,6V |
| 20V→12,6V | 20V | 0,4006 | 12,56V | 18,79W | 84,8% | 4,63A | 1,88A | 53,6V | 35,1V |
| 25V→6,3V  | 25V | 0,2194 | 6,15V | 17,99W | 79,7% | 5,23A | 1,91A | 54,4V | 34,4V |
| 25V→12,6V | 25V | 0,3462 | 12,55V | 18,74W | 81,5% | 4,61A | 1,69A | 53,7V | 43,0V |

Vds_Q2 reste modéré partout (≤44V) — **comme au §2bis**, le modèle Schottky
idéal ne reproduit pas la résonance non-linéaire du MOSFET réel, ces
chiffres ne disent rien sur le risque de dépassement 100V.

**Passe 2 — IPD050N10N5 réel + grille Q2 synchrone idéale (proxy
UCC24612) :**

| Point | Vin | D | Vout | Pout | η | Ipk pri | Irms pri | Vds Q1 max | Vds Q2 max | Perte redresseur |
|---|---|---|---|---|---|---|---|---|---|---|
| 11V→6,3V  | 11V | 0,4006 | 6,44V | 19,72W | 85,9% | 6,73A | 3,35A | 55,5V | 57,4V | 0,27W |
| 11V→12,6V | 11V | 0,5502 | 12,86V | 19,70W | 91,4% | 5,40A | 2,77A | 52,8V | 81,5V | 0,16W |
| 20V→6,3V  | 20V | 0,2602 | 6,64V | 20,98W | 90,7% | 6,56A | 2,34A | 52,8V | 92,7V | 0,25W |
| 20V→12,6V | 20V | 0,4006 | 13,07V | 20,33W | 89,4% | 5,31A | 2,01A | 53,1V | **107,2V** ⚠ | 0,20W |
| 25V→6,3V  | 25V | 0,2194 | 6,74V | 21,61W | 90,4% | 6,71A | 2,12A | 52,4V | **107,2V** ⚠ | 0,34W |
| 25V→12,6V | 25V | 0,3462 | 13,22V | 20,82W | 92,1% | 5,35A | 1,77A | 51,9V | **107,2V** ⚠ | 0,28W |

(Deux points non convergents à la première tentative — `schottky 25V→6,3V`
et `sync_ideal 20V→6,3V`, même symptôme intermittent déjà documenté au §6
et déjà vu avant le fix K1. Relancés à l'identique, convergés sans autre
changement — pas un effet de la correction de fuite.)

### Verdict

**Courant/saturation — pas un facteur limitant, confirme le calcul à la
main (§3/§4 du document d'intention).** Pire cas réel observé (11V→6,3V) :
Ipk=6,73A vs Isat 10%-drop=13,4A (marge ×2,0, et toujours sous le
20%-drop=15,0A) ; Irms=3,35A vs 7,6A one-winding (marge ×2,27) —
`msd1514.pdf` p.2. Même avec la puissance réellement délivrée dérivant de
19,7 à 21,6W selon le point, aucune marge courant n'est entamée.

**Rendement — l'UCC24612 apporte un gain réel et substantiel à cette
puissance.** Comparaison aux mêmes D/Vin/Vout (ex. 20V→12,6V) :
84,8%→89,4% (+4,6 points), perte redresseur secondaire 0,69W→0,20W.
Le gain mesuré varie de +4,6 à +10,7 points selon le point (plus fort aux
coins 25V, où le body-diode seul perd le plus) — confirme la motivation
initiale (la diode de corps seule, à 18-20W, dissiperait trop pour rester
un choix raisonnable).

**⚠ Vds_Q2 — le redressement synchrone NE règle PAS le dépassement
100V.** Avec le modèle réel + grille synchrone, Vds_Q2 dépasse 100V
(tenue IPD050N10N5, `ipd050n10n5.yaml` vds_max) **dès Vin=20V, mais
seulement au coin 12,6V** (107,2V) — le coin 6,3V à la même tension reste
juste sous la limite (92,7V). **À Vin=25V, les deux coins dépassent**
(107,2V chacun). Plafond observé une fois la résonance établie : ~107,2V,
quasi identique au coin 20V/12,6V et aux deux coins 25V — suggère une
butée (saturation de la résonance plutôt qu'une croissance continue avec
la puissance) plus qu'une simple proportionnalité à Ipk². Seul Vin=11V
reste largement sous la limite (57,4-81,5V). Conclusion inchangée malgré
le changement de détail par coin : c'est un phénomène de résonance
d'inductance de fuite, **indépendant du mode de redressement** —
l'UCC24612 améliore le rendement mais ne change rien au risque de
claquage de Q2.

**D1 (clamp primaire) — marge toujours confortable, mais nettement plus
réduite qu'estimé avant correction.** Pire cas observé (passe sync_ideal,
11V→6,3V) : 2,15W vs 5W (`smcj43a.yaml` P_av) — marge ×2,3, contre ×5,5
avec l'ancienne fuite sous-estimée (0,91W). Toujours pas un point dur,
mais la marge réelle est environ moitié moindre que ce que laissait penser
la simulation précédente — à garder à l'œil si d'autres paramètres
(Lmesh_pri réel, par exemple) réduisent encore cette marge plus tard.

**Conclusion : 18-20W n'est pas tenable en l'état (sans clamp secondaire),
même avec l'UCC24612** — inchangé par la correction : 3 des 6 coins
(20V/12,6V, 25V/6,3V, 25V/12,6V) dépassent toujours 100V. Le point ouvert
déjà identifié en `00-intention-conception.md` §10 (« Snubber/clamp
éventuel côté secondaire ... pas encore traité ») reste **bloquant** pour
viser cette puissance — l'UCC24612 reste pertinent pour le rendement mais
ne peut pas se substituer à un clamp sur Q2. Voir §7bis pour le
dimensionnement de ce clamp, lui aussi rejoué avec la fuite corrigée.

**Réserves à garder en tête** (mêmes limites que §3, §6 ci-dessus,
inchangées par cette passe) : `Lmesh_sec`/`Cinter_ESTIME` toujours
quasi nuls (non sourcés) — la résonance réelle sur PCB est probablement
**sous-estimée**, pas surestimée, donc ces chiffres ne sont pas
pessimistes par excès de prudence. Proxy `sync_ideal` ≠ UCC24612 réel (pas
de modèle du comparateur/des seuils réels de détection Vds, pas de
dynamique VDD/REG). D non re-résolu pour la passe réelle (Pout dérive de
19,7 à 21,6W selon le point, cf. tableau) — lecture qualitative valable,
pas un point de fonctionnement pinné exactement à 18,9W.

## 7bis. Clamp secondaire — SMCJ43A (même réf. que D1) vs SMCJ54A, dissipation chiffrée

Suite directe du verdict §7 (clamp secondaire bloquant pour viser
18-20W). Deux candidats TVS Bourns (`bourns-smcj-series.pdf` p.2, même
construction modèle que D1 : BV + IBV=1mA + RS=1Ω à partir des 2 points
datasheet, exploratoire, pas encore une fiche composant retenue) montés
en D2sec (même orientation que D1 : anode=masse secondaire,
cathode=drain Q2), modèle réel + synchrone idéal (proxy UCC24612), mêmes
6 points/D que §7 :

- **SMCJ43A** (Vbr_min=47,8V, Vc=69,4V@21,7A) — même référence que D1,
  déjà au BOM.
- **SMCJ54A** (Vbr_min=60V, Vc=87,1V@17,3A) — candidat alternatif à seuil
  plus haut.

`simulation/run_sec_clamp_candidates.py`,
`simulation/results/sec_clamp_candidates.csv`.

| Point | Vin | SMCJ43A : Vds_Q2 clampé | SMCJ43A : P(D2sec) | SMCJ54A : Vds_Q2 clampé | SMCJ54A : P(D2sec) |
|---|---|---|---|---|---|
| 11V→6,3V  | 11V | 49,1V | 0,07W | 58,4V | 0,00W |
| 11V→12,6V | 11V | 50,2V | 0,28W | 62,0V | 0,17W |
| 20V→6,3V  | 20V | 50,6V | 0,41W | 62,5V | 0,27W |
| 20V→12,6V | 20V | 51,2V | 0,80W | 63,2V | 0,52W |
| 25V→6,3V  | 25V | 51,2V | 0,74W | 63,2V | 0,49W |
| 25V→12,6V | 25V | 51,5V | **1,30W** | 63,5V | **0,76W** |

**Réponse à la question posée (dissipation du SMCJ43A proposé)** : 0,07W
à 1,30W selon le point, pire cas 25V→12,6V. Marge vs le P_av=5W de la
série SMCJ (`smcj43a.yaml` / `bourns-smcj-series.pdf` p.1) : **×3,8 au
pire cas** — pas un point dur. Et il fait le travail : Vds_Q2 clampé à
~49-51,5V partout, marge ×1,9 vs les 100V du MOSFET. Ces chiffres sont
quasi inchangés par la correction de fuite (§7 — anciennement 50-53V/
0,12-1,29W avec l'ancien k=0,99) : contrairement à la tension à vide
(§7, qui bouge de façon non triviale avec la fuite), **une fois le clamp
actif il fixe la tension près de son propre seuil quel que soit le
surplus d'énergie à absorber** — l'énergie en plus se traduit en
dissipation/durée de conduction, pas en tension plus haute. Contrairement
à l'inquiétude initiale (un seuil aussi bas que 47,8V pourrait conduire
en continu pendant le fonctionnement normal, pas seulement pendant le pic
de résonance), la dissipation réelle reste modeste.

**Où part l'énergie non dissipée dans le SMCJ54A ?** Décomposition
complète (mêmes 6 points, log LTspice relus en entier, pas juste
Ploss_D2sec) au pire coin (25V→12,6V) :

| | SMCJ43A | SMCJ54A | Δ |
|---|---|---|---|
| Pin_avg | 24,001W | 23,239W | **-0,763W** |
| Pout_avg | 20,483W | 20,654W | +0,171W |
| Ploss_Q1 | 1,954W | 1,543W | **-0,411W** |
| Ploss_D1 (clamp primaire) | 1,761W | 1,351W | **-0,409W** |
| Ploss_DCR1/DCR2/Rshunt/Cout (somme) | 0,150W | 0,148W | -0,002W (quasi identique) |
| Ploss_D2sec | 1,303W | 0,757W | -0,546W |

**Changement de narration par rapport à l'ancienne passe (k=0,99) : avec
la fuite corrigée, Q1 et D1 (côté primaire) bougent aussi de façon
notable entre les deux candidats** (-0,41W chacun) — l'ancienne version
de ce tableau concluait à tort que « Q1, les DCR, Rshunt, Cout ne
bougent quasiment pas » ; seuls les DCR/Rshunt/Cout (petits postes)
restent effectivement stables. Le mécanisme qualitatif reste le même
(le couplage K1 L1 L2 relie les deux résonances, écrêter plus bas/plus
tôt côté secondaire change la dynamique vue par le primaire) mais
affecte maintenant un poste primaire supplémentaire (D1), pas seulement
Pin global — cohérent avec une fuite doublée qui couple plus fortement
les deux côtés. Le tableau complet par point est dans
`results/point18w9_clamp_*.log`.

**Conséquence directe sur le rendement système**, même alignement D que
§7 (donc comparaison directe, un seul paramètre changé = le seuil du
clamp) :

| Point | η SMCJ43A | η SMCJ54A | Δ |
|---|---|---|---|
| 11V→6,3V  | 86,11% | 85,93% | -0,18 pt |
| 11V→12,6V | 89,62% | 89,80% | +0,18 pt |
| 20V→6,3V  | 87,11% | 87,09% | -0,02 pt |
| 20V→12,6V | 88,20% | 89,26% | +1,06 pt |
| 25V→6,3V  | 86,46% | 85,95% | -0,51 pt |
| 25V→12,6V | 85,34% | 88,88% | **+3,54 pt** |

**Recommandation révisée, inchangée malgré le fix : SMCJ54A**, pas
SMCJ43A — mais le tableau n'est plus uniformément favorable comme avant
(5 points sur 6 ; désormais **4 sur 6**, les deux négatifs restant petits
:  -0,02 et -0,51 pt au coin 6,3V). Le pire coin (25V→12,6V), celui qui
compte le plus pour le dimensionnement, montre un gain **encore plus
marqué qu'avant** (+3,54 pt contre +2,03 pt avec l'ancienne fuite) — ce
coin seul suffit à trancher. La marge de tension reste confortable
(×1,6 vs 100V, contre ×1,9 pour le SMCJ43A, les deux largement
suffisants ; marges quasi inchangées par la correction, contre ×1,5/×1,9
avant). La dissipation du composant lui-même n'était de toute façon un
point dur pour aucun des deux candidats (×6,6 et ×3,8 de marge vs 5W
respectivement) — ce n'est donc pas le critère qui doit trancher ; le
rendement, oui.

**Toujours ouvert avant de construire** : ce modèle clamp est construit
sur 2 points datasheet comme D1, pas encore vérifié avec les parasites
réels de PCB (`Lmesh_sec`/`Cinter_ESTIME` quasi nuls, §3/§7) — à
revalider une fois le routage connu. Orientation/empreinte D2sec à
choisir au placement, même discipline que D1
(`00-intention-conception.md` §6, `smcj43a.yaml` pinmap).

## Méthode

Simulation préparée avec Claude Code (LTspice 26.1.1, mode batch).
Modèle MOSFET réel fourni par l'utilisateur (bibliothèque Infineon
OptiMOS5 100V, téléchargée directement depuis infineon.com). Vérifié à la
main : cohérence Pin/Pout par point, garde-fou anti-collision de coordonnées
dans le générateur (`simulation/gen_asc.py`, a déjà révélé un bug réel de
câblage lors d'une passe précédente), mode de conduction lu sur la forme
d'onde plutôt que supposé.

Fichiers pour rejouer la simulation : `simulation/`.
