# Piste : régulation du flyback en mode courant crête cycle par cycle

> **Statut : hypothèse de travail (2026-11-23, révisée le même jour).**
> Rien n'est câblé ni validé par simulation. Le flyback est proposé comme
> **banc d'essai** de la régulation en courant crête faite par le C2000
> lui-même (voie B), avant de l'appliquer à `KICAD-HV`. La voie A, celle de
> la première version de ce document, est conservée en §7. Le §8 décrit une
> carte d'essai configurable par 0 Ω pour comparer les deux voies avec
> deux firmwares. **Préalable : la protection rapide actuelle est
> inopérante (§1).** Document de passation vers une session spécialisée en
> simulation de régulation.

## 1. Contexte

Flyback de la carte Filament/HT (`KICAD-HT`), 200 kHz, Vin 11–25 V, Vout
5,5–13 V, 18,9 W sur filament (`00-intention-conception.md` §1–§3).
L'inductance couplée MSD1514-103ME est en 1:1, L = 10 µH par enroulement
(`msd1514.pdf` p.2). Q1 = IPD050N10N5. La commande vient d'un
TMS320F28P551 (devkit B) via le powershield, connecteur `J21` (shield) ↔
`J2` (carte HT).

État vérifié sur la netlist exportée du schéma (2026-11-23) :

| Élément | Câblage actuel |
|---|---|
| Driver U1 (UCC27517) | IN+ = `EN_PRI_GATED` (U13 : `EN_PRI_OUT` ET `nQ_TRIP`), IN− = `PWM_PRI_OUT` |
| Polarité du PWM | **inversée** : OUT = IN+ · NOT(IN−), donc Q1 conduit quand `PWM_ht` est **bas** |
| U3 | ISO7710 (sortie haute par défaut : Q1 coupé si le côté commande disparaît) |
| Shunt R19 | 10 mΩ Kelvin, source de Q1 → `GND` |
| Clamp D1 (SMCJ43A) | cathode sur `SW_PRI`, anode sur `GND`, au même nœud que R19 |
| `J2.17` | `I_Shunt_ht_comp`, sortie de U19 (ISO7710F, retour `nTRIP` de la chaîne rapide) |
| `J2.9` / `J2.5` | `Vht_EN` → Q4 et `PWM_EN` → Q8 : **aucune broche libre** sur `J2` |

> **La chaîne de protection rapide du §19 ne fonctionne pas telle que
> câblée (relevé le 2026-11-23, netlist et fiches).** Deux défauts
> indépendants :
>
> 1. **Le symbole de U18 inverse Q et nQ.** Le symbole KiCad place `Q` en
>    broche 3 et `nQ` en broche 5. La fiche `sn74lvc1g74.pdf` (SCES794G,
>    p.4, *Pin Functions*) donne l'inverse : broche 3 = sortie inversée,
>    broche 5 = Q. Le net `~{Q_TRIP}` (U18.5 → U13.B) porte donc **Q**.
>    Le pinmap de `composants-datasheets/data/carte-flyback/sn74lvc1g74.yaml`
>    n'a jamais été vérifié sur capture d'empreinte (`verified: null`) :
>    c'est exactement le cas que la règle R15 vise.
> 2. **Le verrou est remis à zéro pendant toute la conduction.** nCLR
>    (U18.6) et le blanking (R33/C52 → U17.A) prennent `PWM_PRI_OUT`.
>    Or Q1 conduit quand `PWM_PRI_OUT` est **bas** (U1 IN−). Pendant la
>    conduction, nCLR est bas et le verrou ne peut pas se déclencher. Le
>    blanking, lui, se compte à partir de la **coupure** de Q1.
>
> **Conséquence sur la carte réelle :** pendant que `PWM_PRI_OUT` est
> bas, nCLR force Q bas, donc `EN_PRI_GATED` est bas. Pendant qu'il est
> haut, IN− est haut. **Q1 ne s'allume jamais.** Même avec un symbole
> juste, la protection serait inopérante (défaut 2).
>
> **Piste de correction**, à valider : rendre le PWM actif à l'état haut
> sur la carte (U1 IN+ = PWM, U3 en ISO7710F, comme la voie A du §7 le
> prévoyait), et prendre la sortie inversée (broche 3) pour le gating.

## 2. Principe retenu pour l'essai (voie B)

Un capteur de courant **isolé et rapide** remplace la nécessité de
recréer seuil, rampe et logique côté chaud. La boucle traverse la barrière
deux fois, par des composants qui le font déjà :

```
 côté puissance (GND)                │ barrière │   côté commande (3V3_ISO)
                                      │          │
 VIN ─ conducteur ACS37100 ─ T1.1 ═══╪═► sortie ACS ─► tampon ─► J2.17 ─► CMPSS3
                                      │          │                         │
                                      │          │             DAC + rampe, blanking ePWM
                                      │          │                         │
 Q1 ◄─ U1 UCC27517 ◄─ U3 ISO7710 ◄═══╪══════════╪══ J2.3 PWM_ht ◄─ EPWM3_A
```

- **Mesure** : ACS37100-025B3 (±25 A), en série entre `VIN` (après C1/C9)
  et `T1.1`. Son conducteur est côté puissance ; sa sortie et son
  alimentation sont côté commande, sur `3V3_ISO`.
- **Comparaison** : CMPSS3 du C2000, avec la consigne sur son DAC, la
  compensation de pente par son générateur de rampe et le blanking par
  l'ePWM.
- **Coupure** : trip de l'EPWM3, transmis par le chemin PWM existant
  (shield → U3 → U1).
- **Protection fixe indépendante du C2000** : la chaîne rapide existante
  du §19 (TSV791 U14, LMV7219 U16, verrou U18) **reste**, avec ses valeurs
  corrigées (§5). C'est ce que la voie B perdrait sur une carte sans chaîne
  locale, et la carte HT l'a déjà.

### Pourquoi le flyback est un bon banc d'essai

1. **Le shield est déjà prêt.** `J21.17` arrive sur `ADC_8_MCU`, broche
   physique 15 du boîtier 64PM, entrée valide de `CMPSS3`, comparateur
   libre dans ce projet (vérifié sous SysConfig, decision #26 de
   `KICAD-C2000-powershield/doc/decisions.md`). Le trio de protection est
   en R = 22 Ω, prévu pour un chemin comparateur.
2. **La protection fixe locale existe** (voir ci-dessus).
3. **Le courant de sortie est déjà mesuré** (R25 + U22, `I_Out_ht`, §18),
   ce qui permet la limitation au démarrage sur filament froid.
4. **Ni le devkit ni le shield ne changent**, et le driver, U3, U13 et le
   chemin `PWM_EN` restent tels quels.

## 3. Chaîne de mesure

### 3.1 Capteur

| Grandeur | Valeur | Source |
|---|---|---|
| Sensibilité, version -025B3 | 52,8 mV/A | ACS37100-DS Rev. 4 p.2 et p.7 |
| Sortie à 0 A | 1,65 V (mi-tension) | p.7 |
| Offset VOE | ±8 mV max, soit ±152 mA | p.7 |
| Bruit sur 10 MHz | 26 mA eff. | p.6 |
| Temps de réponse tRESP | 50 ns typ, **pas de maximum publié** | p.6 |
| Conducteur | 1,2 mΩ, 4,2 nH | p.4 |
| Seuil FAULT interne | 50 % de IPR, soit 12,5 A | p.6 |
| Isolation | 800 Vpk en renforcé, 5 000 Vrms 60 s, 8 mm de ligne de fuite | p.3 |
| Consommation | 10 mA typ, 20 mA max | p.6 |

Les valeurs reprennent le chapitre 6 de `LTSPICE-boost`
(`06-mesure-courant/calcul_isole.py`, `resultats_isole.md` §9.3), où la
fiche a été relue. La fiche est dans
`composants-datasheets/telechargement/ACS37100-Datasheet.pdf` ; **aucune
fiche YAML n'existe encore** pour ce composant.

### 3.2 Position : côté `VIN` de l'enroulement plutôt qu'à la source

- **Mode commun** : `VIN`, continu et calme (11–25 V), jamais le nœud
  `SW_PRI`.
- **Le pic de D1 n'y passe pas.** À l'allumage, la capacité du SMCJ43A se
  décharge par Q1, R19 et `GND` jusqu'à son anode : elle traverse R19,
  pas l'enroulement.
- **Le pic réfléchi du secondaire y passe.** Recouvrement de la diode
  interne de Q2 en CCM, Coss de Q2, capacité entre enroulements : le gain
  sur le blanking est donc moindre que dans un boost. À quantifier en
  simulation (§6).
- **Inductance ajoutée** : 4,2 nH dans la maille primaire, environ 1 % de
  la fuite de 0,40 µH (fiche MSD1514, valeur reprise par
  `simulation/gen_asc.py`).
- **Perte** : 1,2 mΩ × (3,37 A)² ≈ 14 mW au point le plus contraignant
  (Irms primaire, `00-intention-conception.md` §3).

### 3.3 Tampon vers `J2.17`

Le soustracteur du chapitre 6 (§9.5) se place **sur la carte HT**, côté
commande : la référence de l'ACS37100 reste locale, et une seule voie
unipolaire part sur `J2.17`. Cela lève la contrainte de voie VREF relevée
pour `KICAD-HV`.

- **Ampli** : TSV791, déjà dans la nomenclature (GBP 35 MHz min à 3,3 V,
  `tsv791.pdf` p.8).
- **Point de départ, à recalculer** : 1 k / 3,9 k (E12), soit G = 4,90 et
  k = 0,259 V/A, avec un décalage Vb = 0,2 V. Cela donne −0,77 A lu à 0 V
  et 11,8 A à 3,25 V (chapitre 6, `resultats_isole.md` §9.5).
- **Pleine échelle utile** : consigne maximale sous le seuil fixe de
  8,39 A, plus la rampe Se·t_on (§4.2). Avec un rapport cyclique maximal
  **POSÉ** à 0,6, soit 3 µs, le DAC monte à environ 10,3 A équivalents,
  soit 2,87 V, sous son plafond de 3,3 V.
- **Résolution de la consigne** : DAC du CMPSS sur 12 bits (TRM F28P55x
  p.2123, §16.4.1), soit 0,81 mV ou **3,1 mA par pas**. C'est dix fois
  mieux que la consigne par PWM filtré de la voie A, et sans HRPWM.

## 4. Budget de temps et conséquences

### 4.1 Retard de la chaîne de coupure

| Maillon | Retard | Source |
|---|---|---|
| ACS37100, tRESP | 50 ns (typ, pas de max) | ACS37100-DS p.6 |
| Tampon TSV791 à G = 4,9, 1/(2π·GBP/G) | 22 ns | calculé, `tsv791.pdf` p.8 |
| Trio `J21.17` (22 Ω, 100 pF) | 2 ns | decisions #26 du shield |
| CMPSS, réponse à un échelon | 60 ns max | F28P551SG DS p.153 |
| Trip de l'ePWM, td(TZ-PWM) | 25 ns max | F28P551SG DS p.168 |
| GPIO et piste | 5 ns | **POSÉE** |
| Trio de `PWM_ht` (100 Ω, 100 pF) | 10 ns | decisions du shield (gabarit des trios, addendum de la #17) |
| ISO7710 U3, tPLH/tPHL | 18,5 ns max | `iso7710.pdf` p.14 |
| UCC27517 U1, tD2 (IN− → OUT) | 23 ns max | `ucc27517.pdf` p.7 |
| Coupure de Q1 (IPD050N10N5, R11 = 1 Ω) | 20 ns | **POSÉE** |
| **Total** | **≈ 236 ns** | |

### 4.2 Conséquences chiffrées

Pente montante du primaire :

$$\Large m_1 = \frac{V_{in}}{L} = 1{,}1 \dots 2{,}5\ \mathrm{A/\mu s}$$

- **Dépassement du courant crête**, ΔI = m₁·t_d : **0,26 A à 11 V,
  0,59 A à 25 V.** À pleine charge sous 11 V (Ipk = 6,55 A, §3), cela fait
  4 %. Le dépassement est connu et proportionnel à Vin. La carte HT ne
  mesure pas Vin, donc l'intégrateur de la boucle de tension l'absorbe ;
  sinon, une correction dans le firmware demande une mesure de Vin.
- **Conduction minimale** : blanking de 160–200 ns (chapitre 6, README
  §9.4) plus le retard, soit environ 440 ns. À 25 V
  cela donne un courant crête minimal de 1,1 A, et en DCM :

$$\Large P_{min} = \tfrac{1}{2} L\, I_{pk,min}^2\, f \approx 1{,}2\ \mathrm{W}$$

  C'est sous la plus faible charge à chaud prévue (5,5 V sur 8,4 Ω, soit
  3,6 W), mais le démarrage et le fonctionnement à vide imposent un mode
  rafale : le C2000 saute des cycles.
- **Compensation de pente** : au point 11 V et 12,6 V / 1,5 A, D = 0,534
  en CCM (§3), donc la compensation est obligatoire. Avec un rapport 1:1,
  la pente descendante vaut m₂ = Vout/L, soit 1,3 A/µs à 13 V. Point de
  départ **POSÉ** : Se = m₂/2 ≈ 0,65 A/µs, réglé par le STEPVAL de la rampe
  CMPSS, puis vérifié par Qp sur toute la plage de Vout, comme au
  chapitre 6.
- **Gigue** : le bruit de 26 mA efficaces est réduit par m₁/(m₁ + Se) au
  trip. Il reste négligeable devant les 3,1 mA de résolution et le
  dépassement.

### 4.3 Seuil FAULT de l'ACS37100

12,5 A (p.6), soit 10 à 15 A avec sa tolérance (chapitre 6). Cela couvre
la saturation du MSD1514 (13,4 A d'après la première version de ce
document, page de la fiche à confirmer ; le §3 de l'intention retient
Isat − 10 % = 12,2 A) : ce n'est **pas** une protection de
l'inductance. La protection reste la chaîne fixe locale à 8,39 A. Le FAULT
n'a d'ailleurs aucune broche libre sur `J2`.

## 5. Modifications de la carte HT pour la voie B seule (branche dédiée)

KICAD-HT est routée et réputée prête pour la production : toute
modification se fait sur une branche dédiée, avec reprise de la zone
d'isolement. Ce paragraphe décrit le minimum pour la voie B. La carte
d'essai qui compare les deux voies est au §8. Dans les deux cas, la
correction du verrou (§1) est un préalable.

| # | Modification | Pourquoi |
|---|---|---|
| 1 | Ajouter l'ACS37100-025B3 entre `VIN` (après C1/C9) et `T1.1`, à cheval sur la barrière | mesure isolée rapide |
| 2 | Ajouter le tampon TSV791, 4 résistances et la référence Vb, côté commande | sortie unipolaire 0–3,3 V |
| 3 | `J2.17` : passer de la sortie de U19 à la sortie du tampon | entrée CMPSS3 |
| 4 | Corriger la chaîne fixe aux valeurs du §19 : R29 = 9,09 k, R30 = 2,67 k, R31 = 16,5 k, R32 = 8,45 k, R33 = 1,5 k | le schéma (R29 = 10 k, R30 = R31 = R33 = 1 k, R32 = 10 k) déclenche aujourd'hui vers 20,7 A, au-dessus de la saturation |
| 5 | Vérifier C47 (entre IN+ et IN− du TSV791 U14 au lieu de la masse) | relevé dans la première version |

Ce qui **ne change pas** : U1, U3 (reste ISO7710, pas F), U13, le chemin
`PWM_EN` (DPC817, Q8), le shield et le devkit.

**Point ouvert, à trancher** : U19 perd sa broche. Le C2000 ne reçoit
plus le déclenchement de la protection fixe. Plusieurs pistes sont
possibles, à discuter :

- garder U19 pour la seule LED `Q_TRIP` ;
- utiliser le second comparateur du CMPSS3, à un seuil juste sous 8,39 A.
  Attention, il perturbe le DAC voisin de 100 LSB au plus (DS p.154) ;
- détecter par logiciel une coupure sans trip du CMPSS.

**Budget `3V3_ISO`** : l'ACS37100 et le tampon ajoutent 10 à 20 mA plus
l'ampli. À reporter au bilan `3V3_ISO` des decisions du shield.
D'après `nappes-shield.md`, la carte HT n'utilise que `J21`, donc ce
courant ne se compte qu'une fois.

## 6. Firmware (description, pas de code)

- **Polarité** : sur la carte actuelle, Q1 conduit quand `PWM_ht` est bas
  (U1 IN−) ; le trip devrait alors **forcer EPWM3_A à l'état haut**. Avec
  la correction du §1, reprise au §8.1 (PWM actif haut), le trip **force
  l'état bas**. C'est la configuration retenue pour la carte d'essai.
- **CMPSS3** : DAC = consigne, générateur de rampe synchronisé sur EPWM3
  (STEPVAL pour Se), sortie vers l'ePWM par la X-Bar, événement Digital
  Compare en trip cycle par cycle, blanking par fenêtre de l'ePWM. Noms de
  registres à confirmer dans le TRM.
- **Boucles** :
  - une boucle de tension sur `Vht` (AMC0311R) qui fixe la consigne de
    courant crête ;
  - une limitation lente sur `I_Out_ht` qui plafonne cette consigne
    pendant la chauffe du filament.
- **Mode rafale** sous P_min (§4.2) : pas de PWM sur certains cycles.
- **Offset de l'ACS37100** : calibration hors conduction. Q1 bloqué et
  secondaire démagnétisé, le courant primaire est nul, à la résonance près
  en DCM.

## 7. Voie A, alternative : comparateur local et consigne transmise

C'est la première version de ce document. Le comparateur LMV7219 compare
`ISNS_AMP` à une consigne V_TH. Celle-ci est transmise par un PWM du
C2000 (EPWM6_B, GPIO11, broche 31 en 64PM, Table 5-6 p.49 de la fiche
F28P551SG), via `PWM_EN`, un ISO7710F à la place du DPC817 et un filtre RC
du 2ᵉ ordre. U1 est recâblé (IN+ = PWM, IN− = nQ) et U3 passe en ISO7710F.

Une revue du 2026-11-23 y a relevé quatre défauts :

1. **Un PWM de consigne à 100 kHz tombe à fsw/2.** L'ondulation résiduelle
   alterne d'un cycle à l'autre, ce qui injecte une sous-harmonique. Il
   faut 200 kHz ou un multiple, synchronisé sur EPWM3.
2. **La pleine échelle de 2,5 V vaut 24,8 A.** Avec 750 pas à 200 kHz, il
   reste environ 33 mA par pas, soit un cycle limite de Vout d'environ 3 %
   à 1 A de crête. Un pont diviseur avant le filtre ramène la pleine
   échelle vers 0,85 V. Le HRPWM ne sert alors qu'à la consigne, avec un
   pas de 152 ps max (DS p.169), et seulement si EPWM6 a la haute
   résolution : 16 canaux sur 24 l'ont (DS p.207).
3. **Le comparateur déclenche à chaque cycle.** `I_Shunt_ht_comp` ne peut
   plus signaler un défaut ; c'est la protection fixe qui doit remonter.
4. **U13 devient inutile.**

Ses avantages : la coupure ne dépend pas du C2000, et la chaîne est plus
courte (environ 100 ns, **POSÉ**). Ses défauts : plus de composants et de
reprise côté chaud, une consigne filtrée, donc retardée et ondulée, et une
compensation de pente à refaire en analogique.

## 8. Carte d'essai configurable A/B

But : **comparer les deux voies sur la même carte**, avec le même étage
de puissance et la même boucle de tension sur `Vht`. Seule la boucle de
courant change, d'un firmware à l'autre et par quelques 0 Ω. Les deux
chaînes sont peuplées en permanence.

### 8.1 Socle commun (corrige aussi le défaut du §1)

- **PWM actif à l'état haut sur la carte** : U3 passe en **ISO7710F**, et
  `PWM_PRI_OUT` haut signifie conduction. Si le côté commande disparaît,
  la sortie par défaut basse coupe Q1 (`iso7710.pdf` p.19–20, tableaux
  7-1 et 7-2, relus au §19 de l'intention).
- **U1 (UCC27517)** : IN+ = `PWM_GATED`, IN− = `GND`. IN− flottant
  bloquerait la sortie à l'état bas (`ucc27517.pdf` p.4), d'où le
  raccordement franc.
- **`PWM_GATED` = `PWM_PRI_OUT` ET `nQ` du verrou ET `EN_SEL`**, par deux
  SN74LVC1G08 en cascade (U13 existant et un second).
- **Verrou U18** :
  - nCLR = `PWM_PRI_OUT` : le verrou est remis à zéro pendant le blocage
    et armé pendant la conduction ;
  - la sortie de gating est la **broche 3** (sortie inversée,
    `sn74lvc1g74.pdf` p.4) ;
  - nPRE = `TRIP_n` (ci-dessous) ;
  - le symbole KiCad doit être corrigé (§1).
- **Blanking** : R33/C52 sur `PWM_PRI_OUT`. Il se compte désormais à
  partir de l'allumage.
- **Deux comparateurs LMV7219**, sur la même sortie `ISNS_AMP` du TSV791
  U14. Sortie push-pull rail à rail (`lmv7219.pdf` p.1).
  - `COMP_OCP` : seuil fixe `V_TH_OCP` = 0,847 V par ATL431 et R31/R32
    (§19), soit 8,39 A. **Actif dans les deux voies.**
  - `COMP_REG` : seuil `V_TH_REG`, la consigne filtrée de la voie A.
- **Combinaison** : chaque comparateur attaque son propre NAND de Schmitt
  SN74LVC1G132, avec l'autre entrée sur `PWM_LEB` (U17 existant et un
  second). Les deux sorties, actives à l'état bas, sont combinées par un
  SN74LVC1G08 : `TRIP_n` = `TRIP_OCP_n` ET `TRIP_REG_n`. Ce sont trois
  références déjà sourcées.
- **Retour de défaut** : U19 (ISO7710F) prend **`TRIP_OCP_n` seul**, et
  jamais la régulation, qui déclenche à chaque cycle.

### 8.2 Les quatre points de configuration

| Repère | Voie A (comparateur local) | Voie B (ACS37100 → CMPSS3) |
|---|---|---|
| **JP1** : source de `J2.17` | sortie de U19 (défaut fixe) | sortie du tampon de l'ACS37100 |
| **JP2** : `EN_SEL` | `RAIL_3V3_PRI` (toujours actif) | `EN_PRI_OUT` (DPC817, enable du C2000) |
| **JP3** : entrée B du NAND de régulation | `COMP_REG` | `GND` (régulation locale neutralisée) |
| **JP4** : alimentation de l'ACS37100 et de son tampon | non peuplé | peuplé |

- Chaque JP est un **0 Ω 0402 à deux positions** sur une pastille
  commune ; on en peuple une seule.
- **JP1 au plus près de `J2.17`**, sans tronçon laissé en l'air sur la
  voie rapide.
- **JP4** sort 10 à 20 mA (ACS37100-DS p.6), plus le tampon, du bilan
  `3V3_ISO` en voie A.
- **`J2.5` (`PWM_EN`)** reste raccordé en permanence aux deux entrées :
  le DPC817 via Q8, et l'ISO7710F de consigne. Ce sont deux entrées à
  haute impédance. En voie A, l'enable qui découle du DPC817 est ignoré
  grâce à JP2. En voie B, la consigne filtrée est ignorée grâce à JP3.

### 8.3 Voie A : chaîne de consigne et compensation

- **Consigne** :
  - entrée sur `J2.5` ;
  - un ISO7710F de consigne ;
  - un tampon 74LVC1G17 alimenté par la référence 2,5 V de l'ATL431
    (fiche dans `datasheets/logic/`, pas encore de YAML) ;
  - un pont diviseur qui ramène la pleine échelle vers 0,8 V, soit
    environ 7,9 A (**POSÉ**), sous le seuil fixe ;
  - un filtre RC du 2ᵉ ordre ;
  - la sortie donne `V_TH_REG`.
- **PWM de consigne** à 200 kHz synchronisé sur EPWM3, et non 100 kHz
  (§7, défaut 1). En option, HRPWM si EPWM6 l'a.
- **Budget de courant de l'ATL431** : il alimente déjà le pont R31/R32
  (~100 µA) avec ~300 µA de polarisation par R30 = 2,67 k (§19), et son
  minimum est de 35 µA (`atl431.pdf` p.4). Le tampon et le filtre s'y
  ajoutent : **à vérifier**. Sinon, R30 est à réduire.
- **Compensation de pente** : une rampe RC synchronisée sur
  `PWM_PRI_OUT`, sommée par un réseau résistif sur l'entrée + du **seul**
  `COMP_REG`. `COMP_OCP` doit voir le courant brut pour que son seuil
  reste à 8,39 A. Le réseau est à dimensionner sur Se ≈ 0,65 A/µs
  (**POSÉ**, §4.2).

### 8.4 Deux firmwares, mêmes broches

| Broche C2000 | Firmware A | Firmware B |
|---|---|---|
| EPWM3_A → `J2.3` | horloge et rapport cyclique maximal, actif haut | idem, coupé par le trip du CMPSS3 (forcer **bas**) |
| GPIO11 (EPWM6_B) → `J2.5` | PWM de consigne à 200 kHz synchronisé | GPIO d'enable |
| `ADC_8` (broche 15) ← `J2.17` | CMPSS3 contre un DAC à ~1,65 V : détecte les déclenchements du seuil fixe sur un niveau logique | CMPSS3 en courant crête : DAC = consigne, rampe = Se, blanking par l'ePWM |
| `Vht`, `I_Out_ht`, `I_Shunt_ht` | boucle de tension, limitation au démarrage, puissance d'entrée | idem |

- **La boucle de tension et la limitation au démarrage sont communes**,
  au même code près. Seule la sortie change : le rapport cyclique de
  GPIO11 en A, le DAC du CMPSS en B.
- **Se est identique dans les deux voies** pour que la comparaison soit
  juste.
- En voie A, lire le défaut par le CMPSS3 évite de dépendre du mode
  numérique de la broche `ADC_8`. Une impulsion de défaut dure quelques
  centaines de ns ; le statut verrouillé du CMPSS doit la retenir, **à
  vérifier dans le TRM**.
- En voie B, le C2000 ne voit pas le déclenchement du seuil fixe : `J2.17`
  est occupé. C'est la limite assumée de cette configuration.

### 8.5 Essais de comparaison

À même point de fonctionnement, dans les deux configurations :

1. Erreur de courant crête en fonction de Vin : la consigne contre le
   courant crête mesuré par R19 et l'oscilloscope.
2. Échelons de charge : dépassement et temps de rétablissement de Vout.
3. Cycle limite de Vout à faible charge, dû à la résolution de la
   consigne : environ 3 mA par pas en B, à mesurer en A.
4. Conduction minimale et entrée en mode rafale.
5. Démarrage sur filament froid, avec limitation par `I_Out_ht`.
6. Déclenchement du seuil fixe pendant chaque voie : coupure effective et
   remontée au C2000 (A seulement).

### 8.6 Nomenclature ajoutée par rapport à la carte actuelle

| Fonction | Pièce | Fiche locale | YAML |
|---|---|---|---|
| Capteur isolé | ACS37100-025B3 | `telechargement/ACS37100-Datasheet.pdf` | à produire |
| Tampon du capteur | TSV791 + 4 R + Vb | `tsv791.pdf` | existe |
| Comparateur de régulation | LMV7219 | `lmv7219.pdf` | existe |
| NAND du comparateur de régulation | SN74LVC1G132 | `sn74lvc1g132.pdf` | existe |
| Combinaison et gating | 2 × SN74LVC1G08 | `sn74lvc1g08.pdf` | existe |
| Isolateur de consigne | ISO7710F | `iso7710.pdf` | à produire |
| Tampon de consigne | 74LVC1G17 | `74LVC1G17.pdf` | à produire |
| Filtre, diviseur, rampe, 4 JP 0 Ω | passifs | — | — |

U3 passe d'ISO7710 à ISO7710F : même famille, empreinte à confirmer. Les
fiches YAML manquantes suivent `composants-datasheets/CLAUDE.md`, avec
pinmap relevé sur capture d'empreinte (R15).

## 9. À établir par la simulation

Dans l'ordre de la méthode incrémentale (modèle idéal d'abord, un défaut à
la fois) :

1. **Courant crête idéal**, seuil parfait sans retard : mesure multi-tons
   du procédé Vout/Ic en DCM et en CCM sur toute la plage. Choix de Se
   (Qp), marge de la boucle de tension sur `Vht`. Le modèle
   `06-mesure-courant/pcmc_ideal.py` du boost se transpose.
2. **Retard de 236 ns** puis **blanking** : dépassement contre Vin,
   conduction minimale, P_min.
3. **Pic d'allumage vu côté `VIN`** contre celui vu par R19, en CCM
   (recouvrement de la diode interne de Q2, Coss de Q2) : durée de blanking
   nécessaire.
4. **Comportements limites** : démarrage sur filament froid (limitation
   par `I_Out_ht`), mode rafale, vide, déclenchement de la protection fixe
   à 8,39 A pendant un essai en courant crête.
5. **Au banc** : tRESP réel de l'ACS37100 (pas de maximum publié), offset
   et sa dérive.

## 10. Périmètre matériel

- **Devkit `devkit_B_F28P551`** : aucune modification.
- **Powershield** : aucune modification. `J21.17` → `ADC_8_MCU` →
  `CMPSS3` est déjà en place (decision #26). Seule la documentation change :
  `I_Shunt_ht_comp` devient une voie analogique.
- **KICAD-HT** : seule carte modifiée, sur une branche dédiée (§5).
