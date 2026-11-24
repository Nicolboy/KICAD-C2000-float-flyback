# Proposition : carte d'étude de deux boucles de courant crête par le CMPSS

> **Statut : proposition à valider (2026-11-24), branche `etude-regulation`.**
> Rien n'est câblé. Les valeurs marquées **POSÉ** sont des points de départ
> à confirmer en simulation. Celles marquées **à vérifier** n'ont pas été
> relues dans la fiche du composant.

## 1. Objet

KICAD-HT devient une carte d'étude qui compare **deux boucles de
régulation en courant crête, toutes deux fermées par le CMPSS3 du C2000**.
Elles ne diffèrent que par la position du capteur, et une seule est active
à la fois, choisie par résistances 0 Ω :

| Configuration | Position du capteur | Ce qu'il voit |
|---|---|---|
| **PRE** | ACS37030 entre `VIN` (après C9) et `T1.1` | courant de l'enroulement primaire, sans le pic de décharge de D1 |
| **POST** | ACS37030 côté interrupteur Q1 (position à trancher, §4.2) | courant de Q1, pic de décharge de D1 compris |

- **Même capteur, même conditionnement, même comparateur et même
  firmware** dans les deux configurations : seul le point de mesure change.
- Les deux capteurs restent **toujours en série** dans l'étage de
  puissance, qui est donc identique dans les deux configurations.
- **Protection de surintensité locale conservée** : shunt R19, chaîne
  rapide côté primaire au seuil fixe de 8,43 A, indépendante du C2000.

Point de départ : `main` au commit `0bc3a07` (chaîne de limitation
corrigée, symbole de U18 corrigé).

## 2. Architecture

```
          côté primaire (GND, RAIL_3V3_PRI)            │ barrière │   côté commande (GND_CTRL, 3V3_ISO)
                                                        │          │
 VIN ─ C9 ─ IP ACS37030 « PRE » ─ T1.1                  │  VOUT, VREF « PRE » ──┐
 SW_PRI ─ Q1 ─ IP ACS37030 « POST » ─ R19 ─ GND (§4.2)  │  VOUT, VREF « POST » ─┤ JP1 / JP2 (0 Ω)
                                                        │          │            ▼
                                                        │          │   ampli d'instrumentation
                                                        │          │   2 × TSV791, G = 4,9
                                                        │          │            │ I_ACS
                                                        │          │            ▼
                                                        │          │   J2.17 ─► shield ─► ADC_8 ─► CMPSS3
                                                        │          │
 R19 ─► U14 (TSV791, G = 11) ─► U16 (LMV7219, 8,43 A)   │          │
   ─► U17 (blanking) ─► U18 (bascule) ─► Q ─► U1 IN−    │          │
                               Q̄ ─► U19 (ISO7710F) ════╪══════════╪══► J2.5 ─► GPIO11 du C2000
 U1 IN+ ◄── U3 (ISO7710F) ◄════════════════════════════╪══════════╪═══ J2.3 PWM_ht ◄─ EPWM3_A
```

- **Boucle de régulation** : capteur sélectionné → ampli d'instrumentation
  → `J2.17` → CMPSS3. Le DAC du CMPSS3 porte la consigne, son générateur
  de rampe la compensation de pente, une fenêtre de l'ePWM le blanking.
  Le déclenchement coupe EPWM3_A, donc `PWM_ht`, U3 et U1.
- **Protection locale** : inchangée sur la partie primaire (shunt R19,
  U14, U16, U17, U18). Seul le câblage autour de U18 et de U1 change (§6).
- **Traversées de la barrière** : le PWM (U3, inchangé), le drapeau de
  surintensité (U19, inchangé, qui sort désormais sur `J2.5`), et les deux
  capteurs eux-mêmes, qui chevauchent la barrière (§5).

## 3. Capteur : ACS37030LLZATR-020B3

Fiche : `composants-datasheets/datasheets/isolation/acs37030-32.pdf`
(Rev. 7, 20/05/2026), YAML `data/components/acs37030.yaml`, extraction en
deux passes concordantes.

| Grandeur | Valeur | Source |
|---|---|---|
| Boîtier | LZ : SOIC-6 à broches fusionnées, corps étroit | p.1, p.27 (plan **préliminaire**) |
| Broches | 1 IP+, 2 IP−, 3 GND, 4 VREF, 5 VOUT, 6 VDD | p.4 |
| Plage, sensibilité | ±20 A, 66 mV/A, erreur ±2 % | p.7 |
| Sortie à 0 A, VREF | 1,65 V ; offset ±10 mV | p.7 |
| Bande passante, temps de réponse | 5 MHz ; 40 ns typ, pas de maximum | p.6 |
| Bruit | 50 mA eff. sur 5 MHz | p.6 |
| Charge de VOUT et VREF | ≥ 50 kΩ, ≤ 100 pF ; court-circuit 25 mA typ | p.6 |
| Alimentation | 3,0 à 3,6 V ; 20 mA typ, 30 mA max | p.6 |
| Conducteur | 0,68 mΩ, 2,2 nH | p.4 |
| Isolation | tenue 3 500 V_RMS ; ligne de fuite et distance dans l'air **4,1 mm** ; « certification pending » | p.3 |

- **Choix face à l'ACS37100** (comparatif du 2026-11-24, fiches
  officielles) : un peu plus rapide (40 contre 50 ns), deux fois moins
  d'inductance et de résistance dans la maille, et surtout un boîtier
  étroit dont la ligne de fuite (4,1 mm) tient dans la règle
  `barriere_controle` (4 mm). Contreparties : fiche en partie
  préliminaire, bruit plus élevé (50 contre 26 mA eff.), consommation
  plus forte (30 contre 20 mA max).
- **Concurrents examinés** : seul l'Infineon TLE4978 (54 ns, 9 MHz) est
  aussi rapide, mais sans sortie de référence (sortie ratiométrique, VDD/2).
  Les autres (TI TMCS11xx, Melexis, MPS, ACEINNA MCA2101 à 80 ns avec
  −45° dès 1,3 MHz) sont plus lents.
- **Disponibilité** : la référence est en stock chez Mouser (2026-11-24).
  La copie de fiche téléchargée chez Mouser est la version initiale de
  2023, sans contrainte de charge de sortie : ne pas l'utiliser.

## 4. Positions des capteurs

### 4.1 PRE

Entre `VIN`, après C9 (1 µF, découplage de la maille), et `T1.1`. Le
capteur doit rester **dans** la maille C9 → T1 → Q1 → R19 → C9 : placé en
amont de C9, il ne verrait que le courant d'entrée lissé. Conducteur au
potentiel de `VIN`, continu et calme.

### 4.2 POST — à trancher

| Position | Avantages | Inconvénients |
|---|---|---|
| Côté source : Q1 → ACS → R19 | conducteur près de la masse, sans fronts de tension | ses 2,2 nH s'ajoutent dans la boucle de grille (le driver revient sur `GND`) : une inductance commune de source ralentit la commutation, de l'ordre de L·di/dt ≈ 0,7 V à 0,33 A/ns (**POSÉ**) |
| Côté drain : `SW_PRI` → ACS → Q1 | hors de la boucle de grille | conducteur soumis aux fronts de `SW_PRI` ; la fiche ne publie aucune immunité aux transitoires de mode commun |

Les deux positions voient le pic de décharge de D1, comme R19. La
capacité de sortie de Q1 se décharge à l'intérieur du composant et
n'est vue par aucun des deux.

## 5. Placement et barrière d'isolement

Chaque ACS37030 **chevauche la barrière** : broches 1 et 2 (IP) côté
primaire, dans la maille ; broches 3 à 6 côté commande. Or, sur la carte
actuelle, l'étage de puissance est à 35 à 50 mm de la barrière
(isolateurs vers x ≈ 118 mm ; T1, C9, R19, Q1 entre x = 153 et 167 mm).
Deux façons de réconcilier les deux contraintes :

1. **Rapprocher l'étage de puissance de la barrière.** La maille reste
   compacte, mais `SW_PRI` se retrouve à 4 mm du domaine commande.
2. **Avancer une presqu'île du domaine commande** (`GND_CTRL`, `3V3_ISO`,
   4 mm de garde de chaque côté) jusqu'à la zone C9 / T1.1 / Q1 / R19.
   Les deux capteurs y sont proches l'un de l'autre ; la presqu'île
   accueille leurs côtés signal et l'ampli d'instrumentation, et `I_ACS`
   remonte vers `J2` à l'intérieur. Les pistes primaires contournent la
   presqu'île.

Règles communes : côté IP tourné vers la maille ; plans `GND` et
`GND_CTRL` arrêtés à la limite de la barrière sous chaque boîtier ;
`SW_PRI` aussi petit que possible et éloigné de la presqu'île ;
découplage de VDD et ampli d'instrumentation au plus près des broches 4
et 5. Choix de l'option et placement : à faire à la main (§10).

## 6. Conditionnement : ampli d'instrumentation à deux TSV791

Repris du chapitre 6 de `LTSPICE-boost` (`06-mesure-courant/README.md`
§9.5), côté commande, alimenté par `3V3_ISO`. VOUT et VREF du capteur
sélectionné n'attaquent que des entrées non inverseuses : la contrainte de
50 kΩ et 100 pF est respectée sans tampon.

```
VREF ──► U_A (+)    U_A (−) : R1 = 1 k vers la sortie de U_A, R2 = 3,9 k vers GND_CTRL
VOUT ──► U_B (+)    U_B (−) : R1 = 1 k vers la sortie de U_A, R2 = 3,9 k ∥ Cf vers la sortie de U_B
U_B ── 47 Ω ──► J2.17 (I_ACS)
```

$$\Large I_{ACS} = \left(1 + \frac{R_2}{R_1}\right)(V_{OUT} - V_{REF}) = 4.9 \times 0.066 \times I = 0.323\ \mathrm{V/A} \times I$$

- **G = 4,9** au lieu des 5,7 du chapitre 6, à cause des 66 mV/A de
  l'ACS37030 :
  - sortie de U_A = 1,65 × 4,9/3,9 = 2,07 V ;
  - sortie de U_B = 2,73 V au seuil de protection (8,43 A) ;
  - pleine échelle utile vers 3,25 V, soit environ 10 A.
- **Zéro à 0 V** (R2 de U_A à `GND_CTRL`, pas de décalage Vb). L'offset du
  capteur (±10 mV, soit ±49 mV en sortie, ±0,15 A) n'est lisible par
  l'ADC que s'il est positif. Un décalage Vb, comme au chapitre 6,
  permettrait de le lire dans les deux sens, mais sa source ajoute son
  impédance à R2 : non retenu.
- **Bande passante** : 35 MHz / 4,9 = 7,1 MHz minimum (GBP minimal du
  TSV791, `tsv791.pdf` p.7). **Cf = 8,2 pF** (**POSÉ**) place un pôle à
  5,0 MHz et réduit le bruit du capteur ; retard total du conditionnement
  d'environ 55 ns (**POSÉ**).
- **47 Ω en série** vers `J2.17` : isole U_B de la capacité de la nappe
  et du trio de protection du shield (22 Ω, 100 pF). Le TSV791 demande
  une étude de stabilité au-delà de 22 pF de charge (`tsv791.pdf`, §
  application).
- **Résistances à 0,1 %** : la précision de la soustraction dépend de
  l'égalité des deux rapports R2/R1.
- **Résolution de la consigne** : DAC du CMPSS sur 12 bits, soit environ
  0,8 mV ou 2,5 mA par pas à 0,323 V/A (DAC de 3,3 V **supposé**).

## 7. Logique et driver

| Élément | Aujourd'hui (`main`) | Proposé |
|---|---|---|
| U1 IN+ | `PWM_PRI_OUT` | inchangé |
| U1 IN− | `~{EN_PRI_GATED}` = NAND(`EN_PRI_OUT`, `~{Q_TRIP}`), sortie de U13 | **`Q_TRIP`** (U18 broche 5) directement |
| U13 (1G132) | NAND d'enable | **supprimé** |
| U18 | inchangé | inchangé : seule la protection fixe le déclenche |
| LED D6 | sur `Q_TRIP` | inchangée : elle signale toujours la surintensité |
| U19 (ISO7710F) | `~{Q_TRIP}` → `J2.17` | `~{Q_TRIP}` → **`J2.5`** |
| Chaîne d'enable | `J2.5` → Q8 → opto U5 → R4 → `EN_PRI_OUT` | **supprimée** (U5, Q8, R3, R4) |
| R37 (100 k, `PWM_EN` → `GND_CTRL`) | tirage de l'entrée d'enable | conservé : tire `J2.5` bas si U19 n'est pas alimenté, ce qui se lit comme un défaut |

$$\Large Q1_{ON} = PWM \cdot \overline{Q_{TRIP}}$$

- La coupure d'arrêt passe par l'arrêt du PWM, qui coupe Q1 par
  construction (U3 en ISO7710F, IN+ de U1).
- Le drapeau dure du déclenchement jusqu'au front descendant suivant du
  PWM. Si le déclenchement arrive juste avant ce front, l'impulsion est
  très courte : le C2000 doit la mémoriser (capture ou trip-zone sur
  GPIO11 via la X-Bar d'entrée).

## 8. Résistances 0 Ω

| Repère | Position A : configuration PRE | Position B : configuration POST |
|---|---|---|
| **JP1** : entrée + de U_B | VOUT du capteur PRE | VOUT du capteur POST |
| **JP2** : entrée + de U_A | VREF du capteur PRE | VREF du capteur POST |
| **JP3** : VDD du capteur PRE | peuplé | non peuplé |
| **JP4** : VDD du capteur POST | non peuplé | peuplé |

- JP1 et JP2 sont des 0 Ω 0402 à deux positions sur une pastille commune.
  Ils se changent toujours ensemble.
- JP3 et JP4 n'alimentent que le capteur utilisé : 30 mA max sur
  `3V3_ISO` au lieu de 60.
- Le capteur non alimenté reste dans la maille : son conducteur passe le
  courant normalement, ses sorties sont déconnectées par JP1 et JP2.
- Pastilles de JP1 et JP2 au plus près des entrées de l'ampli : la
  charge capacitive de VOUT et VREF doit rester sous 100 pF.

## 9. Retards et conséquences

| Maillon | Retard | Source |
|---|---|---|
| ACS37030, tRESP | 40 ns typ, pas de max | p.6 |
| Ampli d'instrumentation avec Cf | ≈ 55 ns | **POSÉ** (§6) |
| Trio `J21.17` (22 Ω, 100 pF) | 2 ns | decisions #26 du shield |
| CMPSS, réponse à un échelon | 60 ns max | F28P551SG DS p.153 (document de piste §4.1) |
| Trip de l'ePWM | 25 ns max | F28P551SG DS p.168 (idem) |
| GPIO et piste | 5 ns | **POSÉ** |
| Trio de `PWM_ht` (100 Ω, 100 pF) | 10 ns | decisions du shield |
| ISO7710F U3 | 18,5 ns max | `iso7710.pdf` p.14 |
| UCC27517 U1 | 23 ns max | `ucc27517.pdf` p.7 |
| Coupure de Q1 | 20 ns | **POSÉ** |
| **Total** | **≈ 260 ns**, identique en PRE et en POST | |

$$\Large \Delta I = \frac{V_{in}}{L}\, t_d \approx 0{,}29 \dots 0{,}65\ \mathrm{A} \quad (11 \dots 25\ \mathrm{V})$$

- Conduction minimale = blanking (réglable dans l'ePWM, 160 à 200 ns
  **POSÉ**) + retard : environ 0,46 µs. À 25 V, cela donne un courant
  crête minimal d'environ 1,15 A et une puissance minimale d'environ
  1,3 W avant mode rafale.
- La protection locale, plus courte (environ 130 ns, **POSÉ**), reste
  plus rapide que la boucle de régulation.
- La consigne maximale programmée doit rester sous 8,43 A, moins le
  dépassement et la rampe.

## 10. Nomenclature

**Retirés** : U5 (DPC817), Q8 (MMBF170), R3 (470 Ω), R4 (10 k), U13
(SN74LVC1G132) et son 100 nF.

**Ajoutés** :

| Fonction | Pièce | Fiche locale | YAML |
|---|---|---|---|
| Capteurs PRE et POST | 2 × ACS37030LLZATR-020B3 + 2 × 100 nF | `isolation/acs37030-32.pdf` | existe (composant) |
| Ampli d'instrumentation | 2 × TSV791 + 2 × 100 nF | `tsv791.pdf` | existe |
| Résistances de gain | 2 × 1 k, 2 × 3,9 k (0,1 %) | — | — |
| Filtre et sortie | Cf 8,2 pF, 47 Ω | — | — |
| Configuration | JP1, JP2 (0 Ω 0402 à deux positions), JP3, JP4 (0 Ω) | — | — |

**Budget `3V3_ISO`** : +30 mA max pour le capteur actif, plus les deux
TSV791 ; −4,5 mA environ pour l'opto retiré. Le budget du LDO `3V3_ISO`
du shield est **à vérifier** (decisions du shield, domaine isolation).
`RAIL_3V3_PRI` n'est plus chargé par les capteurs : la question
thermique de Reg2 disparaît.

## 11. Firmware

- **EPWM3_A** (`PWM_ht`) : horloge à fréquence fixe et rapport cyclique
  maximal (**POSÉ** à 0,6), actif haut ; coupé cycle par cycle par le
  CMPSS3.
- **CMPSS3** sur `ADC_8` : DAC = consigne ; générateur de rampe
  synchronisé sur EPWM3 (STEPVAL pour Se) ; sortie vers l'ePWM par la
  X-Bar, événement Digital Compare en trip cycle par cycle ; blanking par
  fenêtre de l'ePWM. Noms de registres à confirmer dans le TRM.
- **`ADC_8`** est aussi lisible par l'ADC : calibration de l'offset
  positif hors conduction, et observation du courant.
- **GPIO11** (`J2.5`) devient une **entrée** : drapeau de surintensité,
  bas sur un déclenchement. Capture par la X-Bar d'entrée (eCAP ou
  trip-zone). Mode analogique AMSEL à désactiver (broche partagée avec
  A24).
- **Même code pour PRE et POST** : une seule constante de calibration par
  configuration (sensibilités et offsets des deux capteurs).
- **Boucles** : boucle de tension sur `Vht` qui fixe la consigne de
  courant crête ; limitation lente sur `I_Out_ht` pendant la chauffe du
  filament ; mode rafale sous la puissance minimale.

## 12. Modifications hors carte HT

- **Devkit** : aucune.
- **Powershield** : aucune modification matérielle. Documentation à
  mettre à jour : `J21.17` (`I_Shunt_ht_comp`) devient une voie analogique,
  `J21.5` (`PWM_EN`) devient un retour de défaut vers le C2000. `PWM_EN`
  sort aussi sur la nappe GPIO-1 (`J4.11`) : une autre carte fille qui
  l'utiliserait en sortie entrerait en conflit.

## 13. Ce que la carte ne teste pas

- **Le shunt comme capteur de régulation** : son signal ne peut pas
  rejoindre le CMPSS assez vite à travers la barrière (AMC0302R :
  1,6 à 2,1 µs).
- **Une boucle de courant locale** (comparateur sur la carte, voie A du
  document de piste) : évaluée le 2026-11-24 puis écartée. Elle était plus
  rapide (environ 130 à 180 ns), mais demandait une douzaine de circuits
  intégrés, des réglages figés par les composants, et ne valide pas
  l'architecture prévue pour KICAD-HV.

## 14. Ce qui reste à établir

1. **Position du capteur POST** (§4.2).
2. **Option de placement** sur la barrière (§5), puis relevé du pinmap de
   chaque ACS37030 sur capture d'empreinte (R15) : fiche de couche carte
   `data/carte-flyback/acs37030.yaml`.
3. **Empreinte du boîtier LZ** : plan encore préliminaire (p.27), à
   reprendre à la sortie de la version définitive.
4. **Budget `3V3_ISO`** du shield (§10).
5. **Simulation** :
   - courant crête idéal puis retard réel de la chaîne (≈ 260 ns) ;
   - pic d'allumage vu en PRE et en POST, et blanking nécessaire ;
   - choix de Se et marge de la boucle de tension ;
   - effet de l'inductance commune de source si POST est côté source.

## 15. Possibilités ouvertes par cette chaîne

Le courant mesuré arrive à la fois sur le CMPSS3 et sur l'ADC (`ADC_8`).
Le C2000 peut donc observer la forme du courant à chaque cycle, en plus de
le comparer. Pistes d'essai, par ordre de faisabilité.

### 15.1 Ce que permet l'ADC

Fiche F28P551SG (`composants-datasheets/datasheets/microc/tms320f28p551sg.pdf`) :
- cinq ADC 12 bits à 3,9 MSPS (p.1) ; 4,1 MSPS avec SYSCLK = 160 MHz
  (tableau des caractéristiques ADC, p.134) ;
- fenêtre d'échantillonnage minimale de 67 ns pour une source de 50 Ω ou
  moins (p.134). Ici la source vaut 47 Ω + 22 Ω : fenêtre à allonger
  légèrement, à calculer avec le modèle d'entrée (p.142) ;
- conversion en 14 cycles d'ADCCLK à 80 MHz, soit 175 ns (p.135) ;
- la broche `ADC_8` (broche 15) est reliée aux ADC A, B et C (A0, B15,
  C15, `brochage-devkit.csv` du shield). Deux ADC différents peuvent
  donc l'échantillonner à deux instants rapprochés, sans attendre la
  conversion du premier.

Deux échantillons dans une conduction de 0,5 µs sont donc possibles, avec
des déclenchements de l'ePWM.

### 15.2 Pistes

1. **Compenser le dépassement sans mesurer Vin.** La carte ne mesure pas
   Vin, et le dépassement dû au retard (0,29 à 0,65 A, §9) en dépend. Deux
   échantillons pendant la conduction donnent la pente du courant, donc
   Vin, et le C2000 corrige la consigne à chaque cycle :

$$\Large m_1 = \frac{\Delta I}{\Delta t} \;\Rightarrow\; V_{in} = L\, m_1 \qquad I_{consigne,corrigée} = I_{consigne} - m_1\, t_d$$

2. **Surveiller la saturation du MSD1514.** À Vin constant, une pente qui
   augmente en fin de conduction signale la chute de l'inductance. Le
   C2000 peut baisser la consigne avant que la protection fixe ne
   déclenche.
3. **Compensation de pente adaptative.** La pente idéale vaut environ la
   moitié de la pente descendante, proportionnelle à Vout. Le C2000 peut
   réécrire la pente du générateur de rampe à chaque période au lieu d'une
   valeur figée au pire cas.
4. **Courant moyen en conduction continue.** Un échantillon au milieu de
   la conduction donne le courant moyen. Le C2000 peut combiner courant
   crête et courant moyen, ou détecter le passage entre conduction
   continue et discontinue.
5. **Logique dans le CLB.** Le F28P551SG a 4 CLB (schéma bloc p.5). Ils
   peuvent gérer en matériel la conduction minimale, le mode rafale ou
   une validation cycle par cycle, sans charger le CPU. Une tuile n'agit
   directement que sur l'ePWM de même numéro (vérifié pour le F28P550SJ,
   §15.4) : agir sur EPWM3, qui génère `PWM_ht`, suppose la tuile 3,
   absente du F28P550SJ.

### 15.3 Limites vérifiées

- **Pas de NPU sur le F28P551SG.** La fiche ne mentionne ni NPU ni réseau
  de neurones (recherche dans tout le texte, 2026-11-24). La détection
  d'anomalies par apprentissage n'est donc pas une option matérielle sur
  ce composant.
- **Commutation au creux de tension : marginale, pas impossible.** En
  conduction discontinue, après la démagnétisation, l'inductance
  magnétisante oscille avec la capacité du nœud `SW_PRI`. Le courant
  d'oscillation traverse l'enroulement primaire (vu en PRE) et la
  capacité de sortie de Q1 (vu en POST côté source).
  - Capacité du nœud : au moins la Coss de Q1, 560 pF typ à 50 V
    (`ipd050n10n5.yaml`, p.4), plus celle de D1 et la capacité ramenée du
    secondaire, non chiffrées. Hypothèse de 0,56 à 1,5 nF.
  - Amplitude du courant, avec Z₀ = √(L/C) = 82 à 134 Ω et une amplitude
    de tension égale à Vout (rapport 1:1) : environ **40 à 70 mA à 5,5 V,
    100 à 160 mA à 13 V**, à une fréquence de 1,3 à 2,1 MHz.
  - Bruit du capteur : 50 mA eff. sur 5 MHz (p.6), environ 35 mA eff. une
    fois limité à 2,5 MHz, soit environ ±100 mA crête.
  - Conclusion : un passage par zéro ne se détecte pas de façon fiable à
    chaque cycle. En revanche, la période d'oscillation est répétitive :
    elle peut être mesurée par l'ADC en moyennant plusieurs cycles, puis
    l'instant du creux **prédit** pour la commutation suivante. À évaluer
    en simulation puis au banc.

### 15.4 Variante de MCU : F28P550SJ9 (NPU, 2 CLB)

Le passage du devkit au TMS320F28P550SJ9PM est envisagé pour disposer du
NPU. Rien n'est tranché : ce paragraphe consigne ce qui est vérifié.

- **Compatibilité du devkit.** Brochage 64PM identique à celui du
  F28P551SG, à l'étiquetage des DAC près. Multiplexage des GPIO identique
  pour les fonctions utilisées par le devkit (fiche SPRSP85D, p.54–55).
  Le NPU n'existe que sur les variantes SJ9/SG9 (Table 4-1, p.7).
- **Ce que le firmware doit changer.** L'horloge passe à 150 MHz au lieu de
  160 MHz, et il n'y a plus que 2 tuiles CLB au lieu de 4.
- **Tuiles CLB et ePWM** (TRM SPRUJ53D, Table 30-4, p.3592–3594, lue sur
  image). Chaque tuile ne remplace que les signaux de l'ePWM de même
  numéro :
  - **CLB1** remplace HRPWM1A/B (et leurs validations de sortie) et
    EPWM1A/B, à l'étage qualificateur d'action ou à l'étage temps mort ;
  - **CLB2** fait de même sur **EPWM2 / HRPWM2** ;
  - **aucune tuile n'atteint EPWM3**, qui génère `PWM_ht`.
- **Contournement 1 : X-BAR ePWM** (TRM, Table 11-3, p.1330). Les sorties
  CLB1_OUT12/13 et CLB2_OUT12/13 sont proposées en colonne 2 des groupes
  G1, G3, G5 et G7. Elles atteignent donc les entrées TRIPx du module
  Digital Compare d'EPWM3.
  - Ce sont les sorties de tuile non registrées, asynchrones à l'horloge
    CLB (p.3590).
  - Cela suffit pour couper un cycle, forcer la sortie, faire du mode
    rafale ou imposer une conduction minimale.
  - Cela ne permet pas de réécrire la forme d'onde.
  - Pas de conflit avec la comparaison de CMPSS3 : chaque TRIPx a ses
    propres multiplexeurs, dont les sorties sont combinées en OU (§11.2.1.1).
- **Contournement 2 : EPWM1 sur la broche GPIO4** (fiche SPRSP85D,
  Table 5-6, p.54). GPIO4 accepte EPWM1_A en position 15 du multiplexeur.
  Le PWM peut alors être généré dans EPWM1/HRPWM1, sous le contrôle
  direct de CLB1, et sortir sur la broche déjà câblée vers `PWM_ht`, sans
  modifier le matériel.
  - Contrepartie : EPWM1_A sort déjà sur GPIO0, qui porte `PWM1_A` du
    shield (broche B5, `spec-devkit.md` du powershield). Ce signal serait
    perdu, ou il faudrait réaffecter GPIO0.
  - Non vérifié : que le front de haute résolution de l'HRPWM traverse
    tel quel cette position 15 du multiplexeur.
