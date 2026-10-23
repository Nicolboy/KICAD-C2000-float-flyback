# Plan d'isolation et passage en 4 couches

Établi le 2026-10-23, à partir du commit `c535024`, du fichier
`KICAD-HT.kicad_pcb` et de `00-intention-conception.md`.

> **Révision 2, même jour.** La première version ramenait contrôle et
> primaire à un seul domaine, en supposant `GND_CTRL` reliée à `GND` par la
> masse du shield. C'est faux : le C2000 est alimenté par un convertisseur
> continu-continu isolé à faible capacité (3 pF) et sa masse est
> galvaniquement séparée. Les trois domaines sont réels, et la distance
> contrôle↔primaire passe de « aucune contrainte » à **8,5 mm**.

> **Mise à jour 2026-10-23, vérifiée contre le projet au-delà de
> `c535024`.** Ce plan a été établi avant la feuille
> `limitation-courant.kicad_sch` (§19 de `00-intention-conception.md`),
> qui occupe déjà `D5`, `D6`, `D7` et `R30`–`R32` — les repères proposés
> §3 et §8 (« À ajouter à la nomenclature ») collisionnent tous. Repères
> libres actuels (vérifiés par balayage de tout le projet) : `D8` et
> `R35`. Deux ajouts déjà faits, avec des repères différents de ceux
> proposés ici :
> - **Chemin 2, premier étage (RAIL_8V25)** : fait — `D2` (`Device:D_TVS`,
>   SMCJ10A) entre `RAIL_8V25` et `GND`, dans `alim.kicad_sch`.
> - **Chemin 1 (fusible `VIN`)** : fait — `F1` (`Device:Fuse`, **3 A**) en
>   série entre J1 et le net `VIN`, dans `alim.kicad_sch`. Type
>   temporisé/rapide et tension de service encore à préciser.
> - **Chemin 2, second étage (RAIL_3V3_PRI)** : déjà fait *avant* ce plan —
>   `D7` (`Device:D_TVS`, SMCJ04A) entre `RAIL_3V3_PRI` et `GND`, présent
>   dès `c535024`.
> - **TVS directe sur `VIN`** : ne sera **pas** posée sur `KICAD-HT` —
>   déjà présente sur `KICAD-C2000-powershield`, en amont au niveau
>   système (cohérent avec le §2 ci-dessous). Repère `D5`/`D8` abandonné.
> - **Résistances de référence inter-domaines (§3)** : faites, en
>   **chaîne de 3×1 MΩ par barrière** (motif, pas une seule résistance —
>   voir note sous le §3). Repères réels : `R35`/`R6`/`R36`
>   (contrôle↔secondaire), `R37`/`R38`/`R39` (contrôle↔primaire),
>   `R42`/`R41`/`R40` (primaire↔secondaire, ajoutée par cohérence bien que
>   non exigée par le §2 ci-dessous). Détail dans le §20 de
>   `00-intention-conception.md`.

> **Correction 2026-10-23 — 8,5 mm → 4 mm, partout dans ce document.**
> Les 8,5 mm supposés aux §2/§4/§7 ci-dessous reposaient sur une
> isolation **renforcée** non vérifiée pour tous les composants qui
> traversent réellement les barrières. Vérifié dans la datasheet
> `iso7710.pdf` (§5.6) : `ISO7710`/`ISO7710F` (`U3`, `U10`, `U19`), dans
> le boîtier D-8 effectivement monté, sont classés **« Basic
> Insulation »** — `CLR`/`CPG` = 4 mm, pas 8,5. Le renforcé n'existe que
> sur la variante DW-16 (large), non montée. Comme ces trois isolateurs
> font partie des barrières contrôle↔primaire et contrôle↔secondaire, la
> barrière entière hérite de leur classe, pas de celle des `AMC0302R`/
> `AMC0311R` (qui, eux, sont bien en boîtier large reinforced). Décision :
> aligner toute la distance contrôle↔{primaire,secondaire} sur **4 mm**,
> uniforme, plutôt que de faire varier la distance selon le composant
> précis à chaque point de la barrière. Règle `.kicad_dru` corrigée au
> §6. Le reste du raisonnement (pas de fente, bandeau de contrôle,
> disposition §4) reste valable à 4 mm au lieu de 8,5 — seule la valeur
> numérique change, pas la méthode.

---

## 1. L'architecture réelle

### Trois domaines, vérifiés au fichier

Le domaine contrôle est **intégralement alimenté depuis le C2000** : J2
amène `3V3_ISO` (broche 1) et `GND_CTRL` (dix broches). Aucun régulateur de
la carte ne produit `3V3_ISO` ; Reg2 fait `RAIL_3V3_PRI`, Reg3 fait
`RAIL_3V3_SEC`.

Les sept isolateurs sont correctement orientés, relus broche par broche :

| Composant | Côté champ | Côté contrôle |
|---|---|---|
| U8, U9, U11 (AMC03xxR) | `RAIL_3V3_PRI` / `GND` | `3V3_ISO` / `GND_CTRL` |
| U7 (AMC0311R) | `RAIL_3V3_SEC` / `VOUT_N` | `3V3_ISO` / `GND_CTRL` |
| U3, U10 (ISO7710) | `RAIL_3V3_PRI` / `GND` | `3V3_ISO` / `GND_CTRL` |
| U5 (DPC817) | `GND` / `EN_PRI_OUT` | `GND_CTRL` |

*Le document d'intention écrit `3V3_CTRL` (§15), le schéma écrit `3V3_ISO`.
Même net, deux noms — à unifier.*

### Ce que chaque masse voit du système

| Masse | Reliée à | Peut se retrouver à |
|---|---|---|
| `GND` | `Vin`, et par `Vin` la **carte 500 V** | référence basse d'un système 500 V, flottante au banc |
| `GND_CTRL` | C2000, via le DC/DC isolé 3 pF | **la terre**, par la sonde JTAG ou l'oscilloscope |
| `VOUT_N` | secondaire flottant, polarisé 0–78 V par `HV_BIAS` | 100 V au-dessus de `GND` (écrêté par D3) |

---

## 2. Les trois distances

### Contrôle ↔ primaire, et contrôle ↔ secondaire : **8,5 mm**

C'est le renversement par rapport à la révision 1.

`GND` est la référence d'un système 500 V. `GND_CTRL` peut être à la terre
dès qu'une sonde ou un lien JTAG est branché. En fonctionnement normal la
différence est nulle ; **ce n'est pas le fonctionnement normal qui
dimensionne une barrière**, c'est le défaut et la configuration de banc.

Tu possèdes déjà des composants certifiés **8,5 mm en isolation renforcée**.
Les honorer ne coûte que de la surface — 8,5 mm sur une carte de 70 mm de
haut, soit 12 % — et tu as répondu n'avoir aucune contrainte de contour.
Les sous-dimensionner reviendrait à payer la certification et à l'annuler au
dessin.

Ton choix d'un DC/DC à **3 pF** montre que tu as déjà traité le problème au
niveau système. Ne le défais pas au niveau carte.

**Pas de fente.** Sur une carte plane, 8,5 mm de distance dans l'air valent
8,5 mm de ligne de fuite. Une fente ne sert que lorsque la place manque, et
ici elle ne manque pas.

### Primaire ↔ secondaire : **2,5 mm**

| Critère | Valeur | Source |
|---|---|---|
| Tension maximale | 100 V | source 80 V, écrêtée par D3 (SMCJ100A) |
| Distance dans l'air, IPC-2221 B2 | 0,6 mm | table 51–100 V |
| Distance dans l'air, IPC-9592B | 1,1 mm | 0,1 + 0,01 × 100 |
| Ligne de fuite, IEC 60664-1, pollution 2 | 0,16 mm | table 100 V |
| **Retenu** | **2,5 mm** | marge ×2 sur la plus exigeante |

Cette barrière n'est traversée par **aucun composant** : seul le
transformateur la franchit, magnétiquement. Il n'y a donc aucune
certification de boîtier à honorer, et 2,5 mm suffisent largement.

**Point à vérifier** : le MSD1514 est une inductance couplée, pas un
transformateur d'isolement. Sa tenue enroulement à enroulement est à lire
dans sa fiche. À 100 V de service elle est probablement confortable, mais
c'est une valeur lue, pas supposée.

### Récapitulatif

| Barrière | Distance | Ce qui la traverse |
|---|---|---|
| contrôle ↔ primaire | **8,5 mm** | U3, U5, U8, U9, U10, U11 |
| contrôle ↔ secondaire | **8,5 mm** | U7 |
| primaire ↔ secondaire | **2,5 mm** | T1 seul, magnétiquement |

---

## 3. Le composant qui manque

**Rien ne définit le potentiel entre les trois domaines.** J'ai cherché tout
composant touchant deux masses : il n'y a que les sept isolateurs. Aucune
résistance, aucun condensateur.

Trois îlots flottants sans référence mutuelle. Le potentiel continu n'est
fixé que par les fuites et les capacités parasites. Sur une carte à 200 kHz
avec un nœud de commutation à fort dv/dt, le courant de mode commun injecté
par la capacité de barrière n'a pas de chemin de retour défini : il traverse
les isolateurs eux-mêmes. Et ce sont tes trois AMC03x qui ramènent tes
mesures.

L'absence de référence dégrade donc précisément ce que l'isolement protège.

**À ajouter : une résistance de 1 à 10 MΩ par barrière**, en parallèle de
l'isolement, pour fixer le potentiel continu sans créer de boucle. Un
condensateur de classe Y ferait le même travail en continu mais augmenterait
la capacité de barrière, donc dégraderait la CMTI — à éviter ici, d'autant
que tu as choisi un DC/DC à 3 pF pour la minimiser.

~~Ces résistances se placent sous le corps de l'isolateur ou à son
immédiate proximité, pour ne pas réduire la distance ailleurs qu'au seul
endroit où elle est déjà franchie.~~ **Corrigé (2026-10-23)** : cette
recommandation était insuffisante. Le footprint `R_0805_2012Metric` n'a
que 0,8 mm entre ses deux pastilles (mesuré directement dans le
`.kicad_mod`) — une seule résistance, où qu'elle soit posée, re-court-
circuite la barrière à 0,8 mm au lieu des 8,5 mm visés ; elle n'hérite en
rien de la distance interne certifiée de l'isolateur. Solution retenue :
une **chaîne de 3×1 MΩ physiquement espacée sur toute la largeur de la
barrière** (pas sous un seul composant), de façon que le chemin
cuivre-à-cuivre cumulé atteigne bien les 8,5 mm, et que les deux nœuds
intermédiaires ne soient approchés par aucune autre piste/via/
remplissage. Détail et repères réels au §20 de
`00-intention-conception.md`.

---

## 4. Forme du placement

### Ce que la topologie impose

| Barrière | Traversées |
|---|---|
| contrôle ↔ primaire | 6 isolateurs |
| contrôle ↔ secondaire | 1 isolateur (U7) |
| primaire ↔ secondaire | **0 composant** — T1 seul |

Un alignement `PRIMAIRE | CONTRÔLE | SECONDAIRE` placerait les deux
enroulements du MSD1514 aux extrémités opposées. À proscrire.

### La disposition retenue

```
 ┌──────────────────────────────────────────────────────┐
 │  CONTRÔLE   J2 · côté logique des 7 isolateurs       │
 │             découplage 3V3_ISO                        │
 ├════════════ 8,5 mm ═══════════════════════════════════┤
 │                            ║                          │
 │   PRIMAIRE                 ║      SECONDAIRE          │
 │   J1 · Cin · Q1 · D1       ║      Q2 · U12 · D4       │
 │   boucle chaude primaire   ║      Cout · Out1         │
 │                      ┌─────╨─────┐                    │
 │                      │ T1 MSD1514 │                   │
 │                      └─────╥─────┘                    │
 └────────────────────────────╨──────────────────────────┘
                        2,5 mm, traversée par T1 seul
```

- **Le transformateur est la barrière primaire↔secondaire.** Il se place à
  cheval, enroulement primaire d'un côté, secondaire de l'autre. Tout le
  reste se place autour de lui.
- **Les deux boucles chaudes restent entières**, chacune dans sa région
  (flyback : les deux côtés sont critiques, PUI-01). Primaire :
  Cin → Q1 → enroulement. Secondaire : enroulement → Q2/D4 → Cout.
- **Le bandeau de contrôle** longe un bord, séparé de tout par 8,5 mm. Les
  six isolateurs s'alignent sur son arête avec le primaire ; U7 va à
  l'extrémité côté secondaire. Les isolateurs sont les seuls composants
  autorisés dans la bande de 8,5 mm.
- Le contour de 90 × 70 mm reste confortable : le bandeau coûte 8,5 mm de
  hauteur, la barrière interne 2,5 mm de largeur.

Ton cadrage initial — « moins optimiser le placement pour respecter les
zones » — ne tient pas : la boucle chaude se serre **à l'intérieur** d'une
région. Tu ne la perds que si une frontière la traverse, ce qui n'arrive pas
ici.

---

## 5. Empilage 4 couches

| Couche | Rôle |
|---|---|
| **F.Cu** | composants et routage court, les deux boucles chaudes |
| **In1.Cu** | **masses**, découpées en trois régions : `GND_CTRL`, `GND`, `VOUT_N` |
| **In2.Cu** | alimentations et routage, découpé selon le même tracé |
| **B.Cu** | composants, routage, remplissage de masse de la région locale |

### Deux règles qui tuent les cartes isolées

**Les découpes doivent être alignées verticalement sur les quatre couches.**
Un plan interne continu passant sous une barrière l'annule : le composant
isolé est enjambé par en dessous, et sa certification ne vaut plus rien.

**Les régions ne doivent pas se superposer d'une couche à l'autre.** Deux
plans de domaines différents qui se recouvrent forment un condensateur, qui
augmente la capacité de barrière et dégrade la CMTI — exactement ce que ton
DC/DC à 3 pF cherche à éviter.

Ça semble contredire EMP-04, « le plan de masse reste entier ». Ce n'est pas
le cas : la non-coupure vaut **à l'intérieur d'un domaine**. À travers une
barrière, **la coupure est l'isolement**. À écrire dans le fichier 06 de la
base de règles.

### Ce que les 4 couches apportent

Pas « trois plans de masse » : tu les as déjà, le fichier contient cinq
zones dont `GND`, `GND_CTRL` (« masse cpu ») et `VOUT_N` (« masse
filament »). Ce que tu gagnes :

- une référence **continue à 0,1 mm** sous les signaux de chaque région, au
  lieu d'un remplissage fragmenté entre les pistes ;
- les faces externes libérées, donc les plans restent entiers ;
- la place de router le bandeau de contrôle sans entamer les 8,5 mm.

Chez Multi-CB, demander l'empilage défini **4L-01**, 1,6 mm, sans surcoût.
Relever ses épaisseurs réelles de préimprégné avant de figer le routage.

---

## 6. Ce qui manque, indépendamment du nombre de couches

Aucune règle n'impose aujourd'hui la moindre distance. Le fichier n'a
**qu'une classe de nets**, `Default`, isolement 0,2 mm, et **aucun fichier
`.kicad_dru`**. Les 2,21 mm actuels entre primaire et secondaire et les
0,89 mm entre contrôle et primaire sont le résidu du routage, pas une
contrainte. Au prochain tracé, rien ne les empêche de tomber à 0,2 mm — et
0,89 mm sur une barrière qui en demande 8,5 est déjà dix fois trop court.

### Classes de nets

| Classe | Nets | Piste | Isolement |
|---|---|---|---|
| `CTRL` | `3V3_ISO`, `GND_CTRL`, signaux de J2 | 0,25 mm | 0,2 mm |
| `PRI` | `GND`, `RAIL_3V3_PRI`, signaux primaires | 0,25 mm | 0,2 mm |
| `PRI_PWR` | `Vin`, nœud de commutation, drain Q1, clamp | 1,4 mm | 0,3 mm |
| `SEC` | `VOUT_N`, `VOUT_P`, `3V3_ISO` secondaire | 0,25 mm | 0,3 mm |
| `SEC_PWR` | sortie de puissance secondaire | 2,2 mm | 0,3 mm |

Largeurs de puissance : IPC-2221 externe, cuivre 35 µm, ΔT 10 °C, d'après
les courants de §3 et §4 du document d'intention — I_rms primaire 3,37 A,
I_rms secondaire 4,45 A. **À recalculer si η = 0,85 est révisé au banc**,
cette hypothèse étant signalée comme la plus fragile du document.

### Règles personnalisées

**Mise à jour 2026-10-23 — 8,5 mm → 4 mm.** Vérifié directement dans la
datasheet `iso7710.pdf` (§5.6) : le boîtier réellement utilisé pour
`ISO7710`/`ISO7710F` (`U3`, `U10`, `U19`) est le **D-8** (SOIC-8 étroit,
`Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`), explicitement classé
**« Basic Insulation »** dans la datasheet — `CLR`/`CPG` = 4 mm, pas 8,5.
Le renforcé 8,5 mm n'existe que sur la variante **DW-16** (large) du même
composant, non montée ici. Les `AMC0302R`/`AMC0311R` (`U8`, `U9`, `U11`),
eux, sont bien en boîtier large (`SOIC_DWV:SOIC-8_DWV_5.85x11.5mm_P1.27mm`,
reinforced 8,5 mm confirmé) — seuls les isolateurs numériques sont
concernés par la correction. Choix retenu : aligner la barrière
contrôle↔primaire/secondaire sur **4 mm**, cohérent avec le composant
réellement monté, isolation **basique** et non renforcée.
`DPC817` (`U5`) mesuré à ≈5 mm, au-dessus du seuil, pas de changement à
faire sur ce chemin.

```
(version 1)

(rule "barriere_controle"
  (condition "A.hasNetclass('CTRL') && !B.hasNetclass('CTRL') && A.Reference != B.Reference")
  (constraint clearance (min 4mm)))

(rule "barriere_primaire_secondaire"
  (condition "(A.hasNetclass('SEC') || A.hasNetclass('SEC_PWR')) && (B.hasNetclass('PRI') || B.hasNetclass('PRI_PWR')) && A.Reference != B.Reference")
  (constraint clearance (min 2.5mm)))
```

Conditions écrites **par classe de nets et sans zone** : sur KiCad 10 la
contrainte `creepage` ignore les conditions de zone (anomalie 24853,
corroborée par un second rapport en février 2026). Ici `clearance` suffit,
la ligne de fuite n'étant jamais la contrainte sur une carte plane.

**Correction 2026-10-23, par test réel (`kicad-cli pcb drc`), pas par
lecture du fichier.** Une règle d'exception **séparée** pour « même
composant » — testée avec `A.Reference == B.Reference`, puis avec huit
règles explicites une par isolateur pour écarter un doute sur cette
syntaxe précise — **ne fait rien** : 139 violations identiques avant et
après, y compris entre pastilles du même composant. KiCad n'applique pas
ici « la première règle qui correspond gagne » pour `clearance`, contre
ce que suggéraient les sources consultées sur l'ordre d'évaluation.
**Ce qui marche** : l'exclusion `A.Reference != B.Reference` intégrée
directement dans la condition de la règle de barrière elle-même, comme
ci-dessus — mesuré : 139 → 36 violations de dégagement sur `KICAD-HT`
après correction (les 5 restantes, entre pastilles d'un même repère, sont
un problème de boîtier `U18`/VSSOP-8 sans rapport avec cette règle).
Vérifier aussi que la contrainte de dégagement minimum globale
(Board Setup → Design Rules → Constraints) n'est pas réglée au-dessus de
`0,2 mm` : cette valeur prévaut toujours sur une règle personnalisée qui
tenterait de descendre plus bas.

---

## 7. Ordre des opérations

1. Créer les cinq classes de nets et le `.kicad_dru`. **Avant** de placer.
2. Ajouter les trois résistances de référence inter-domaines (§3).
3. Poser T1 sur la barrière primaire↔secondaire, puis les deux boucles
   chaudes autour.
4. Poser le bandeau de contrôle, 8,5 mm de tout, et aligner les sept
   isolateurs sur ses arêtes.
5. Rentrer J2 dans le contour — il est actuellement à 11,4 mm à l'extérieur.
6. Ajuster le contour au placement, puis router.
7. `kicad-cli pcb drc`, et vérifier à l'œil que les découpes des quatre
   couches se superposent et que les régions ne se recouvrent pas.

---

## Points ouverts

- **Tenue enroulement à enroulement du MSD1514**, à lire dans sa fiche
  Coilcraft. C'est une inductance couplée, pas un transformateur
  d'isolement.
- **Valeur des résistances de référence** (§3) : 1 à 10 MΩ est la plage
  usuelle, le choix exact dépend du courant de fuite acceptable sur les
  entrées des AMC03x.
- **`3V3_CTRL` (document) contre `3V3_ISO` (schéma)** : deux noms pour un
  net, à unifier.
- **La spec affiche 90 V alors que la source en délivre 78 utiles** (§11,
  déjà noté). Sans incidence sur l'isolement, 100 V restant le plafond du
  clamp.
- **η = 0,85 non sourcé**, et les largeurs de piste de puissance en
  dépendent.

---

# 8. Confinement de défaut — protéger le C2000

Ajouté le 2026-10-23. L'objectif déclaré de toute cette architecture est que
le C2000 survive à la mort d'un composant de cette carte.

**L'isolement galvanique ne couvre qu'un des cinq chemins.** Les barrières
arrêtent ce qui *traverse* ; elles ne font rien contre ce qui *remonte le
rail commun*, ni contre une cascade interne au domaine primaire.

| # | Chemin | État actuel | Gravité |
|---|---|---|---|
| 1 | Rail `VIN` partagé | **aucune protection** | la plus probable |
| 2 | Cascade Reg1 → Reg2 → six isolateurs | **aucune protection** | un défaut, six barrières |
| 3 | À travers une barrière | bien couvert | faible |
| 4 | Broches de J2 | partiellement couvert | faible |
| 5 | Énergie stockée dans C1 | confinée si §1 traité | moyenne |

---

## Chemin 1 — le rail `VIN`, le plus probable

`VIN` alimente trois choses à la fois : le primaire du flyback, le
convertisseur isolé qui nourrit le C2000, et la carte 500 V.

```
In1 ──┬── C1 470µ ── C9 1µ
      ├── Reg1 (LM317M) ── RAIL_8V25 ── Reg2 ── RAIL_3V3_PRI
      └── T1 primaire ── SW_PRI ── Q1 ── shunt ── GND
```

**Q1 claque en court-circuit** — le mode de défaillance normal d'un MOSFET.
`SW_PRI` tombe à la masse, `VIN` se retrouve court-circuitée à travers les
10 µH du primaire et quelques milliohms. Toute la puissance que la source
peut fournir y passe. `VIN` s'effondre ou part en transitoire.

Et `VIN` est l'entrée du convertisseur isolé du C2000. **Le défaut ne
traverse aucune barrière : il contourne les sept.**

Le fichier ne contient **ni fusible, ni PTC, ni TVS sur `VIN`**. Les trois
TVS présentes — D1 sur `SW_PRI`, D3 sur `HV_BIAS`, D4 sur `SW_SEC` —
protègent les nœuds de commutation, pas l'entrée.

### Parade

1. **Fusible à l'entrée In1.** C'est la pièce maîtresse : cette carte qui
   meurt doit ouvrir *son* fusible, pas tirer `VIN` vers le bas. Calibre
   3 à 4 A temporisé — le courant moyen d'entrée est de 2,02 A au coin
   dimensionnant (§3), et il faut encaisser l'appel dans C1, 470 µF.
2. **TVS sur `VIN`, en aval du fusible.** Blocage au-dessus des 25 V
   maximum : SMCJ28A ou SMCJ30A. L'ordre compte — en aval, une surtension
   durable fait fondre le fusible ; en amont, elle cuit la TVS.
3. **Au niveau système** : le convertisseur isolé du C2000 prend `VIN` **en
   amont du fusible de cette carte**, directement à la source. C'est là que
   le confinement devient réel. Trois cartes, trois fusibles, un raccordement
   en étoile sur la source.

---

## Chemin 2 — la cascade des régulateurs

Celui-ci est moins évident et compromet **six barrières d'un coup**.

```
VIN (≤25V) ── Reg1 LM317M ── RAIL_8V25 ── Reg2 MCP1703 ── RAIL_3V3_PRI
                                                              │
                        côté champ de U3, U8, U9, U10, U11 ────┘
```

Un régulateur série qui lâche sous surcharge ou surchauffe **passe son
entrée sur sa sortie** — c'est son mode dominant.

- Reg1 en court-circuit → jusqu'à 25 V sur `RAIL_8V25`, donc sur l'entrée
  de Reg2.
- Si cela dépasse la tension d'entrée maximale absolue du MCP1703
  (**datasheet**), Reg2 meurt à son tour, souvent en court-circuit.
- 25 V se retrouvent alors sur `RAIL_3V3_PRI`, c'est-à-dire sur
  l'alimentation côté champ de **cinq isolateurs simultanément**, dont les
  trois AMC03x qui portent tes mesures.
- Au-delà de la tension d'alimentation maximale absolue de ces composants
  (**datasheet**), ils sont détruits — et un isolateur détruit ne garantit
  plus sa barrière.

Un seul composant défaillant, et les cinq barrières primaire↔contrôle
deviennent incertaines en même temps.

### Parade

- **Une TVS sur `RAIL_8V25`**, blocage juste au-dessus de 8,25 V, donc
  autour de 9 à 10 V. Elle écrête avant que Reg2 ne voie sa limite.
- **Une seconde TVS ou diode Zener sur `RAIL_3V3_PRI`**, autour de 3,6 V, en
  deuxième ligne. Quelques centimes, et le rail des isolateurs devient
  borné quoi qu'il arrive en amont.

**À lire avant de choisir les valeurs** : tension d'entrée maximale absolue
du MCP1703, et tension d'alimentation maximale absolue de l'AMC0311R, de
l'AMC0302R et de l'ISO7710. Le mécanisme tient quelles que soient ces
valeurs ; les calibres de TVS en dépendent.

---

## Chemin 3 — à travers une barrière

Le mieux couvert, et c'est tant mieux.

Les AMC03x et les ISO7710 sont des composants renforcés, 8,5 mm de ligne de
fuite certifiée. Le DPC817 est un optocoupleur de la classe PC817, dont la
tenue d'isolement est à relever (**datasheet**) mais qui est typiquement
très au-dessus des besoins ici.

**Condition pour que ça reste vrai** : le dessin doit honorer les 8,5 mm
(§2). À 0,89 mm, l'état actuel du routage annule cette protection.

Le transformateur est la barrière la plus faible — 500 Vrms pendant une
minute est un **essai diélectrique de type**, pas une tension de service, et
ne qualifie le MSD1514 pour aucun niveau de sécurité. Mais **il n'est pas
sur le chemin du C2000** : entre le secondaire et le microcontrôleur il y a
U7, un AMC0311R renforcé. Un claquage du transformateur détruit le filament
et le préampli, pas le C2000.

La barrière la plus fragile protège ce qui coûte le moins cher. C'est le bon
ordre, et c'est à conserver tel quel.

---

## Chemin 4 — les broches de J2

Sept des neuf signaux ont leur résistance série et leur filtre :

| Signal | Protection série |
|---|---|
| `Vht`, `Temp_ht`, `I_Shunt_ht`, `V_bias` | 100 Ω + 1 nF |
| `PWM_EN` | 470 Ω |
| `PWM_ht`, `PWM_bias` | passent par un ISO7710 |
| **`Vht_EN`** | **aucune — net orphelin** |
| **`I_Shunt_ht_comp`** | **aucune — net orphelin** |

Les deux derniers ne touchent que J2 : ils n'existent nulle part ailleurs sur
la carte. Réserves pour plus tard, ou liaisons oubliées. **À trancher avant
de router** — une broche de réserve et une liaison manquante se ressemblent
beaucoup dans un fichier, et une réserve non tirée qui se retrouve câblée
plus tard arrivera sans sa résistance série.

### Parade

- Trancher le statut des deux nets orphelins, et les documenter comme tels.
- Si l'un des deux est câblé un jour, lui donner la même résistance série
  que ses voisins.
- Les 100 Ω limitent à 250 mA sous 25 V — bien au-delà de ce qu'encaisse une
  diode de protection d'entrée de microcontrôleur. Augmenter n'est pas
  gratuit : 100 Ω avec 1 nF donne 1,6 MHz, et passer à 1 kΩ ramènerait à
  160 kHz, soit l'ordre de grandeur de la bande passante de l'AMC0311S.
  **À arbitrer contre la bande passante réelle dont tu as besoin**, une fois
  la spec d'entrée ADC connue (point ouvert §11).

---

## Chemin 5 — l'énergie stockée

C1 fait 470 µF. Sous 25 V, elle stocke **147 mJ** — de quoi vaporiser un fil
de bonding.

Cette énergie ne peut pas traverser les barrières. Mais elle se déverse dans
le défaut, et si rien ne sépare cette carte du rail commun, elle participe à
l'effondrement de `VIN` décrit au chemin 1.

Le fusible n'agit pas assez vite pour une décharge capacitive. Ce qu'il fait,
et qui suffit : il empêche la **source** de continuer à alimenter le défaut.
C1 se vide localement, puis c'est fini. Sans fusible, la source entretient
l'arc.

---

## Table de défaillance

| Composant | Mode | Conséquence | Chemin | Parade |
|---|---|---|---|---|
| Q1 | court-circuit | `VIN` court-circuitée par T1 | 1 | fusible + TVS |
| C1 | court-circuit | idem | 1, 5 | fusible |
| Reg1 | court-circuit | 25 V sur `RAIL_8V25` | 2 | TVS 9–10 V |
| Reg2 | court-circuit | 25 V sur le rail des isolateurs | 2 | TVS 3,6 V |
| T1 | claquage enroulements | secondaire exposé au primaire | 3 | aucune — hors chemin C2000 |
| D3 | ouverte + pointe sur `HV80_IN` | étage de polarisation en surtension | 3 | U11 tient la barrière |
| un isolateur | claquage de barrière | C2000 exposé | 3 | 8,5 mm au dessin |
| Q2, D4 | court-circuit | secondaire perturbé | — | hors chemin C2000 |

---

## À ajouter à la nomenclature

**Repères ci-dessous collisionnent avec `limitation-courant.kicad_sch`
(§19), ajoutée après ce plan — voir la mise à jour en tête de document.**
Table d'origine conservée pour la fonction/valeur ; repères réels entre
parenthèses.

| Repère | Fonction | Valeur | État |
|---|---|---|---|
| F1 (**fait**, même repère) | fusible d'entrée, en série avec In1 | provisoire, calibre 3–4 A à confirmer | posé dans `alim.kicad_sch` |
| D5 → **D8** | TVS sur `VIN`, en aval de F1 | SMCJ28A ou SMCJ30A | pas encore posé |
| D6 → **D2** (fait, repère différent) | TVS sur `RAIL_8V25` | SMCJ10A (10 V, dans la plage visée) | posé dans `alim.kicad_sch` |
| D7 (déjà fait avant ce plan, même repère par coïncidence) | TVS sur `RAIL_3V3_PRI` | SMCJ04A | posé depuis `c535024` |
| R30–R32 → **R35–R37** | référence inter-domaines (§3) | 1–10 MΩ, une par barrière | pas encore posé |

Sept composants visés, trois posés (`F1`, `D2`, `D7`). Aucun n'est critique
en précision, tous se placent en périphérie, et ensemble ils ferment les
deux chemins par lesquels ton C2000 meurt aujourd'hui.

---

## Ce que ça change pour le placement

- **F1, D5 au ras de In1**, avant toute dérivation. Le fusible est le premier
  composant que `VIN` rencontre.
- **D6 au ras de Reg1, D7 au ras de Reg2**, dans la région primaire.
- **R30–R32 sous le corps de leur isolateur**, pour ne pas entamer les
  8,5 mm ailleurs qu'au seul endroit déjà franchi.

Aucun de ces ajouts ne touche aux boucles chaudes ni aux barrières. Ils se
logent dans la périphérie que la disposition en bandeau libère naturellement.
