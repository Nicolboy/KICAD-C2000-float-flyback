# Validation — calcul, simulation, mesure

Étage flyback de `alim-flyback-filament`, redressement passif par la
diode de corps de Q2 (étape de validation avant le contrôleur de
redressement synchrone UCC24612).

> **État** : simulation étapes 1-4 faite avec les modèles réels
> (IPD050N10N5 Infineon, clamp D1 SMCJ43A). **Prototype non mesuré.** Les
> colonnes « Mesure » restent vides tant qu'elles n'ont pas été remplies
> au banc — jamais complétées par des valeurs simulées.

---

## 1. Conditions communes

| Paramètre       | Valeur                                                          |
| ---------------- | ---------------------------------------------------------------- |
| f_sw             | 200 kHz                                                          |
| Couplage         | Coilcraft MSD1514-103ME, 1:1, 10µH, k=0,99 (datasheet)          |
| MOSFET Q1/Q2     | IPD050N10N5 réel (Infineon, sous-circuit SPICE officiel OptiMOS5, `simulation/models/IPD050N10N5.lib`) |
| Redresseur       | Diode de corps de Q2 (gate à 0V) — pas de Schottky discret dans le vrai chemin de puissance |
| Clamp primaire   | D1 = SMCJ43A réel (Vbr=47,8V@1mA, Vc=69,4V@21,7A, `smcj43a.yaml`) |
| Clamp secondaire | **aucun modélisé** — voir §2, c'est la limite la plus importante de cette passe |
| Puissance visée  | 10W (6V et 12V), + un point à charge légère (~1W, mêmes duty cycle/Rload trouvés par itération) |
| Charge           | Rload = Vout_cible² / Pout_cible                                 |

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
puissance réellement délivrée dérive donc de 18,8 à 22,3W selon le point,
voir tableaux). `simulation/run_envelope_18w9.py`,
`simulation/results/envelope_18w9_schottky.csv`,
`simulation/results/envelope_18w9_sync.csv`.

**Passe 1 — Schottky idéal (même modèle rapide déjà validé à 10W, seule
la puissance change) :**

| Point | Vin | D | Vout | Pout | η | Ipk pri | Irms pri | Vds Q1 max | Vds Q2 max |
|---|---|---|---|---|---|---|---|---|---|
| 11V→6,3V  | 11V | 0,4006 | 6,38V | 19,38W | 85,6% | 6,19A | 3,29A | 54,9V | 20,0V |
| 11V→12,6V | 11V | 0,5502 | 12,60V | 18,89W | 90,7% | 4,90A | 2,64A | 53,5V | 25,5V |
| 20V→6,3V  | 20V | 0,2602 | 6,29V | 18,82W | 86,1% | 5,40A | 2,17A | 54,2V | 30,0V |
| 20V→12,6V | 20V | 0,4006 | 12,76V | 19,39W | 89,8% | 4,61A | 1,85A | 53,4V | 47,2V |
| 25V→6,3V  | 25V | 0,2194 | 6,33V | 19,09W | 85,3% | 5,30A | 1,92A | 54,3V | 35,3V |
| 25V→12,6V | 25V | 0,3462 | 12,70V | 19,20W | 87,9% | 4,57A | 1,64A | 53,5V | 44,2V |

Vds_Q2 reste modéré partout (≤47V) — **comme au §2bis**, le modèle Schottky
idéal ne reproduit pas la résonance non-linéaire du MOSFET réel, ces
chiffres ne disent rien sur le risque de dépassement 100V.

**Passe 2 — IPD050N10N5 réel + grille Q2 synchrone idéale (proxy
UCC24612) :**

| Point | Vin | D | Vout | Pout | η | Ipk pri | Irms pri | Vds Q1 max | Vds Q2 max | Perte redresseur |
|---|---|---|---|---|---|---|---|---|---|---|
| 11V→6,3V  | 11V | 0,4006 | 6,80V | 22,04W | 91,2% | 7,07A | 3,54A | 54,9V | **63,2V** | 0,32W |
| 11V→12,6V | 11V | 0,5502 | 13,09V | 20,41W | 94,2% | 5,30A | 2,81A | 52,3V | 86,3V | 0,20W |
| 20V→6,3V  | 20V | 0,2602 | 6,73V | 21,56W | 91,8% | 6,74A | 2,42A | 54,4V | **100,6V** ⚠ | 0,31W |
| 20V→12,6V | 20V | 0,4006 | 13,31V | 21,08W | 94,8% | 5,13A | 2,02A | 51,7V | **106,7V** ⚠ | 0,23W |
| 25V→6,3V  | 25V | 0,2194 | 6,85V | 22,32W | 92,8% | 7,01A | 2,17A | 52,2V | **106,7V** ⚠ | 0,44W |
| 25V→12,6V | 25V | 0,3462 | 13,22V | 20,80W | 93,5% | 5,04A | 1,78A | 52,4V | **106,8V** ⚠ | 0,29W |

(Point 11V→6,3V : première tentative non convergente — `results/
point18w9_sync_ideal_11V_6V3.log` coupe net après les warnings de
largeur de MOSFET, aucun résultat — même symptôme intermittent que §6.
Relancé à l'identique, convergé sans autre changement.)

### Verdict

**Courant/saturation — pas un facteur limitant, confirme le calcul à la
main (§3/§4 du document d'intention).** Pire cas réel observé (11V→6,3V,
retenté) : Ipk=7,07A vs Isat 10%-drop=13,4A (marge ×1,9, et toujours sous
le 20%-drop=15,0A) ; Irms=3,54A vs 7,6A one-winding (marge ×2,15) —
`msd1514.pdf` p.2. Même avec la puissance réellement délivrée dérivant
jusqu'à 22,3W (au-dessus du haut de la fourchette demandée), aucune marge
courant n'est entamée.

**Rendement — l'UCC24612 apporte un gain réel et substantiel à cette
puissance.** Comparaison aux mêmes D/Vin/Vout (ex. 20V→12,6V) :
89,8%→94,8% (+5,0 points), perte redresseur secondaire 0,70W→0,23W.
Confirme la motivation initiale (la diode de corps seule, à 18-20W,
dissiperait trop pour rester un choix raisonnable).

**⚠ Vds_Q2 — le redressement synchrone NE règle PAS le dépassement
100V, et la situation est PIRE qu'à 10W.** Avec le modèle réel + grille
synchrone, Vds_Q2 dépasse déjà 100V (tenue IPD050N10N5, `ipd050n10n5.yaml`
vds_max) **dès Vin=20V** (100,6V) — pas seulement Vin≥23V comme à 10W
(§2) — et plafonne vers 106,7-106,8V sur tout le haut de la plage Vin
(20-25V), quel que soit le coin Vout. Seul Vin=11V reste largement sous
la limite (63,2V). Cohérent avec l'hypothèse posée en entrant dans cette
passe : c'est un phénomène de résonance d'inductance de fuite
(proportionnel à Ipk², donc à la puissance), **indépendant du mode de
redressement** — l'UCC24612 améliore le rendement mais ne change rien au
risque de claquage de Q2.

**D1 (clamp primaire) — toujours large marge.** Pire cas observé (passe
sync_ideal, 11V→6,3V) : 0,91W vs 5W (`smcj43a.yaml` P_av) — pas un point
dur, même conclusion qu'au §2bis.

**Conclusion : 18-20W n'est pas tenable en l'état (sans clamp secondaire),
même avec l'UCC24612.** Le point ouvert déjà identifié en
`00-intention-conception.md` §10 (« Snubber/clamp éventuel côté
secondaire ... pas encore traité ») passe de souhaitable à
**bloquant** pour viser cette puissance — l'UCC24612 reste pertinent pour
le rendement mais ne peut pas se substituer à un clamp sur Q2. Avant toute
décision matérielle : dimensionner ce clamp (TVS ou RCD, à partir de
l'énergie de fuite au nouveau Ipk, cf. méthode déjà utilisée pour D1 en
`00-intention-conception.md` §6) et le valider par une nouvelle passe
SPICE avec ce clamp réellement modélisé, avant de modifier le schéma
KiCad.

**Réserves à garder en tête** (mêmes limites que §3, §6 ci-dessus,
inchangées par cette passe) : `Lmesh_sec`/`Cinter_ESTIME` toujours
quasi nuls (non sourcés) — la résonance réelle sur PCB est probablement
**sous-estimée**, pas surestimée, donc ces chiffres ne sont pas
pessimistes par excès de prudence. Proxy `sync_ideal` ≠ UCC24612 réel (pas
de modèle du comparateur/des seuils réels de détection Vds, pas de
dynamique VDD/REG). D non re-résolu pour la passe réelle (Pout dérive de
18,8 à 22,3W selon le point, cf. tableau) — lecture qualitative valable,
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
| 11V→6,3V  | 11V | 50,0V | 0,12W | 61,0V | 0,03W |
| 11V→12,6V | 11V | 51,3V | 0,33W | 63,0V | 0,21W |
| 20V→6,3V  | 20V | 52,0V | 0,49W | 63,7V | 0,34W |
| 20V→12,6V | 20V | 52,5V | 0,81W | 64,4V | 0,53W |
| 25V→6,3V  | 25V | 52,8V | 0,86W | 64,7V | 0,59W |
| 25V→12,6V | 25V | 52,9V | **1,29W** | 64,9V | **0,76W** |

**Réponse à la question posée (dissipation du SMCJ43A proposé)** : 0,12W
à 1,29W selon le point, pire cas 25V→12,6V. Marge vs le P_av=5W de la
série SMCJ (`smcj43a.yaml` / `bourns-smcj-series.pdf` p.1) : **×3,9 au
pire cas** — pas un point dur. Et il fait le travail : Vds_Q2 clampé à
~50-53V partout, marge ×1,9 vs les 100V du MOSFET. Contrairement à
l'inquiétude initiale (un seuil aussi bas que 47,8V pourrait conduire en
continu pendant le fonctionnement normal, pas seulement pendant le pic de
résonance), la dissipation réelle reste modeste — le clamp écrête bien le
sommet de la résonance mais ne conduit pas assez longtemps par cycle pour
peser lourd en moyenne.

**Où part l'énergie non dissipée dans le SMCJ54A ? Pas dans un autre
poste de pertes — elle n'est simplement plus tirée de Vin.** Décomposition
complète (mêmes 6 points, log LTspice relus en entier, pas juste
Ploss_D2sec) au pire coin (25V→12,6V) :

| | SMCJ43A | SMCJ54A | Δ |
|---|---|---|---|
| Pin_avg | 23,133W | 22,615W | **-0,518W** |
| Pout_avg | 20,848W | 20,838W | -0,010W (quasi identique) |
| Ploss_Q1 | 0,712W | 0,718W | +0,006W (identique) |
| Ploss_DCR1/DCR2/Rshunt/Cout (somme) | 0,152W | 0,150W | -0,002W (identique) |
| Ploss_D2sec | 1,293W | 0,756W | -0,537W |

Même constat (Pin baisse de ~0,5V, tous les autres postes inchangés,
seul le clamp lui-même varie) sur les 6 points — le tableau complet est
dans `results/point18w9_clamp_*.log`. Q1, les DCR, Rshunt, Cout ne
bougent quasiment pas entre les deux candidats : l'énergie "en moins"
dans le SMCJ54A **n'est pas redistribuée ailleurs dans le circuit**,
elle n'est simplement plus allée chercher côté primaire. Le couplage
K1 L1 L2 relie les deux résonances (primaire et secondaire) : écrêter
plus bas/plus tôt côté secondaire (SMCJ43A) modifie la dynamique vue par
le primaire et fait tirer davantage sur Vin pour un Pout quasi identique
— un vrai surcoût de rendement, pas juste un déplacement de chaleur d'un
composant à l'autre.

**Conséquence directe sur le rendement système**, même alignement D que
§7 (donc comparaison directe, un seul paramètre changé = le seuil du
clamp) :

| Point | η SMCJ43A | η SMCJ54A | Δ |
|---|---|---|---|
| 11V→6,3V  | 91,31% | 91,15% | -0,16 pt |
| 11V→12,6V | 93,42% | 93,73% | +0,31 pt |
| 20V→6,3V  | 91,85% | 92,55% | +0,70 pt |
| 20V→12,6V | 92,44% | 93,65% | +1,21 pt |
| 25V→6,3V  | 90,47% | 90,83% | +0,36 pt |
| 25V→12,6V | 90,12% | 92,15% | **+2,03 pt** |

**Recommandation révisée : SMCJ54A**, pas SMCJ43A. L'argument
« même référence que D1 » ne pèse pas lourd face à un gain de rendement
système réel et reproductible sur 5 des 6 points (jusqu'à +2 points au
pire coin) — et la marge de tension reste confortable (×1,5 vs 100V,
contre ×1,9 pour le SMCJ43A, les deux largement suffisants). La
dissipation du composant lui-même n'était de toute façon un point dur
pour aucun des deux candidats (×3,9 et ×7 de marge vs 5W respectivement)
— ce n'est donc pas le critère qui doit trancher ; le rendement, oui.

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
