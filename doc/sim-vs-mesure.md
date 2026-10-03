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
côté secondaire, pendant l'anneau qui suit le pic de conduction — sans
qu'aucun clamp secondaire ne soit modélisé (seul D1 côté primaire
existe). Vin_max de la spec est 25V (`00-intention-conception.md`) : les
points 25V→6V et 25V→12V simulent 106,7V et 106,8V, **au-delà de la
tenue en tension du composant réellement sourcé**. À traiter avant
d'aller plus loin : soit un clamp secondaire dédié, soit revérifier si le
réseau Lmesh_sec/Cinter ESTIMÉ (non sourcé, voir §3) exagère l'anneau,
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
- [ ] Tension drain Q1 — amplitude et amortissement de l'anneau
- [ ] **Tension drain Q2 — vérifier en priorité le dépassement 100V prédit à Vin≥23V**
- [ ] Ondulation de Vout

## 6. Inexpliqué / à vérifier

- Décomposition des pertes Q1/Q2 par poste (conduction/commutation/Coss)
  ne boucle pas avec Pin−Pout à ±5% — méthode de mesure à revoir (étape 3
  non terminée).
- Le point à charge légère (20V→6V, ~1W) est classé CCM à la limite
  (5,6% du pic de courant) — borderline, pas une conclusion ferme.
- Dépassement Vds_Q2 100V à Vin≥23V : pas encore confronté à une mesure
  réelle, ni revérifié avec un vrai modèle de Lmesh/Cinter (actuellement
  quasi nuls, donc l'anneau simulé est probablement **optimiste** par
  rapport au PCB réel — l'écart pourrait être pire en vrai, pas meilleur).
- Convergence SPICE intermittente sur certains points (le même point peut
  échouer à une relance et réussir à la suivante) — pas bloquant
  (nouvelle tentative suffit) mais pas expliqué.

## Méthode

Simulation préparée avec Claude Code (LTspice 26.1.1, mode batch).
Modèle MOSFET réel fourni par l'utilisateur (bibliothèque Infineon
OptiMOS5 100V, téléchargée directement depuis infineon.com). Vérifié à la
main : cohérence Pin/Pout par point, garde-fou anti-collision de coordonnées
dans le générateur (`simulation/gen_asc.py`, a déjà révélé un bug réel de
câblage lors d'une passe précédente), mode de conduction lu sur la forme
d'onde plutôt que supposé.

Fichiers pour rejouer la simulation : `simulation/`.
