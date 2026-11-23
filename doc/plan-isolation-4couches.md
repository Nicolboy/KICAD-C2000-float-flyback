# Plan d'isolation et passage en 4 couches

Établi le 2026-10-23, à partir du commit `c535024`, du fichier
`KICAD-HT.kicad_pcb` et de `00-intention-conception.md`.

> **Révision 4 (2026-11-14) — le corps du document mis en cohérence avec
> la carte ; la correction du 2026-10-25 n'était qu'un correctif en tête,
> le §1, le §2, le récapitulatif et le schéma du §4 continuaient de
> décrire l'ancienne architecture sans annotation.** Corrigé ci-dessous
> par biffage (même convention que le §3), pas par suppression. Vérifié
> dans les fichiers réels avant d'écrire, pas supposé :
>
> - **§1** : deux domaines galvaniques réels restent, pas trois —
>   contrôle (`CTRL`) d'une part, primaire + secondaire réunis de l'autre.
>   La classe de nets `SEC` existe toujours dans `KICAD-HT.kicad_pro`
>   (organisation/documentation), mais sans contrainte de barrière face à
>   `PRI` dans `KICAD-HT.kicad_dru` — confirmé en lisant les deux fichiers.
> - **`barriere_controle` (4 mm)** : confirmé dans `KICAD-HT.kicad_dru`,
>   sans clause de couche (s'applique donc aussi en interne, pas
>   seulement `F.Cu`/`B.Cu` comme `HT_distance_90V`). C'est voulu, pas un
>   oubli — voir §6bis, nouveau, pour la mesure et le raisonnement.
> - **Tenue enroulement à enroulement du MSD1514 (500 Vrms/1 min)** :
>   n'est plus une valeur de barrière à vérifier (elle ne l'était que
>   dans la sous-section primaire↔secondaire, retirée ci-dessous) — reste
>   une caractéristique du composant, sans conséquence sur une barrière
>   réelle de cette carte. Retirée des « Points ouverts ».
> - **Nomenclature du §8** : des 7 composants listés, vérifiés présents
>   (schéma **et** PCB, pas l'un sans l'autre) : `F1`, `D2` (ex-`D6`),
>   `D7`. `D8` (TVS directe sur `VIN`) reste une décision assumée de ne
>   pas la poser ici, pas un oubli — déjà noté au §20 de
>   `00-intention-conception.md`.
> - **Chaînes de résistances de référence inter-domaines : retirées par
>   décision, pas incomplètes par oubli — correction du point précédent
>   (indication de l'utilisateur, 2026-11-14).** Une première relecture
>   de cette révision avait trouvé `R35`/`R36`/`R37`/`R40`/`R41`/`R42`
>   présents et `R6`/`R38`/`R39` absents, et conclu à « 2 chaînes sur 3
>   incomplètes, 1 complète ». **C'est faux** : aucune des trois chaînes
>   n'existe — vérifié par les nets PCB réels des six repères survivants,
>   tous câblés sur des fonctions sans rapport (mesure de courant, pont
>   `3V3_ISO`, pull-down `PWM_EN`...). Les repères `R35`–`R42`(+`R6`) ont
>   été réemployés ailleurs, pas complétés. **Raison, donnée par
>   l'utilisateur** : la règle `barriere_controle` (4 mm) est
>   impossible à respecter avec les pastilles d'une résistance 0805 à
>   cette barrière — la chaîne de 3×1 MΩ décrite au §3 (pensée pour
>   répartir la distance sur 3 maillons plutôt qu'un seul 0805 à 0,8 mm,
>   voir `regles-pcb-V2/06-haute-tension.md` HT-09) ne suffit pas non
>   plus en pratique, et la mitigation entière a été abandonnée. **Reste
>   ouvert, à ce jour sans parade** : le problème du §3 (aucune référence
>   de potentiel continu entre `GND_CTRL` et `{GND,VOUT_N}` — le
>   mode commun de barrière traverse les isolateurs eux-mêmes faute de
>   chemin de retour défini) n'est donc pas résolu pour la barrière
>   `CTRL`↔{`PRI`,`SEC`}. Le réseau `R9`/`R10`/`R22`/`R23` (polarisation,
>   voir « Points ouverts » plus bas) fournit bien une référence
>   `GND`↔`VOUT_N`/`VOUT_P`, mais ne touche pas `GND_CTRL` — il ne
>   referme pas cette barrière-là.
> - **Valeurs de `F1`/`D2`/`D7`, deuxième relecture (2026-11-14) : trois
>   écarts non vus à la première passe de cette révision.** Lu
>   directement dans `alim.kicad_sch` (propriété `Value`, pas supposé) :
>   `F1` = **`2A-T`**, pas `3A` comme écrit plus bas (et au §20 de
>   `00-intention-conception.md`) ; `D2` = **`SMBJ9`**, pas `SMCJ10A` ;
>   `D7` = **`SMBJ05`**, pas `SMCJ04A`. Les trois composants existent
>   bien, au bon endroit, sur le bon net — seule la valeur écrite dans ce
>   document (et dans `00-intention-conception.md` §20) ne correspond
>   plus à ce qui est réellement posé. Cause non déterminée dans cette
>   passe (valeur changée depuis la rédaction du §20, ou lecture
>   d'origine jamais vérifiée contre le fichier) — à trancher par
>   l'utilisateur, pas par une relecture de plus.
> - **Classes de nets (§6)** : la table ci-dessous liste 5 classes
>   (`CTRL`/`PRI`/`PRI_PWR`/`SEC`/`SEC_PWR`). `KICAD-HT.kicad_pro` n'en
>   définit que 4 (`CTRL`/`PRI`/`SEC`/`Default`) — `PRI_PWR` et `SEC_PWR`
>   n'existent pas comme classes séparées. Signalé ici, pas corrigé dans
>   la table historique du §6 (elle documente l'intention d'origine) ;
>   conséquence sur les largeurs de piste réellement posées non vérifiée
>   dans cette passe (hors périmètre documentation).

> **Correction majeure 2026-10-25 — la barrière primaire↔secondaire est
> retirée.** Décision utilisateur : dans le montage final, le secondaire
> de puissance ne sera plus flottant ni isolé galvaniquement du primaire.
> Toute la section « Primaire ↔ secondaire : 2,5 mm » du §2, la ligne
> correspondante du récapitulatif, et la règle `barriere_primaire_secondaire`
> du §6 **ne s'appliquent plus** — laissées ci-dessous à titre historique
> (pourquoi cette distance avait été calculée), mais `KICAD-HT.kicad_dru`
> ne la contient plus (commentée, pas supprimée, dans le fichier réel).
> Seule la barrière **contrôle ↔ {primaire, secondaire}** reste une
> isolation galvanique réelle sur cette carte — voir le §20bis de
> `00-intention-conception.md` pour le détail et ce qui reste à vérifier
> électriquement (le nœud qui relie désormais `GND` et `VOUT_N`).

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
>   ~~SMCJ10A~~ **`SMBJ9` au 2026-11-14, voir tête de document**) entre
>   `RAIL_8V25` et `GND`, dans `alim.kicad_sch`.
> - **Chemin 1 (fusible `VIN`)** : fait — `F1` (`Device:Fuse`, ~~**3 A**~~
>   **`2A-T` au 2026-11-14, voir tête de document**) en
>   série entre J1 et le net `VIN`, dans `alim.kicad_sch`. Type
>   temporisé/rapide et tension de service encore à préciser.
> - **Chemin 2, second étage (RAIL_3V3_PRI)** : déjà fait *avant* ce plan —
>   `D7` (`Device:D_TVS`, ~~SMCJ04A~~ **`SMBJ05` au 2026-11-14, voir tête
>   de document**) entre `RAIL_3V3_PRI` et `GND`, présent dès `c535024`.
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

### ~~Trois domaines~~ Deux côtés d'une barrière, vérifiés au fichier

**Révision 4 (2026-11-14).** Depuis le retrait de la barrière
primaire↔secondaire (§20bis, 2026-10-25), il ne reste que **deux côtés
galvaniquement séparés** : contrôle (`CTRL`) d'un côté, primaire et
secondaire réunis de l'autre. Le tableau des isolateurs ci-dessous reste
exact (l'orientation de chaque isolateur n'a pas changé) ; seul le
nombre de domaines qu'ils séparent passe de trois à deux.

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
| `VOUT_N` | ~~secondaire flottant~~ relié au primaire depuis le 2026-10-25 (§20bis) — nœud exact de la liaison non revérifié électriquement dans cette passe, polarisé 0–78 V par `HV_BIAS` | 100 V au-dessus de `GND` (écrêté par D3) |

---

## 2. ~~Les trois distances~~ La distance restante

**Révision 4 (2026-11-14)** : il ne reste qu'**une seule** barrière
réelle sur cette carte — contrôle ↔ {primaire+secondaire}, retenue à
**4 mm** (pas 8,5 — voir §6 pour la correction d'origine du 2026-10-23,
et §6bis pour l'enregistrement complet de la valeur retenue et sa
justification). Les deux sous-sections ci-dessous (contrôle↔{primaire,
secondaire} à 8,5 mm, primaire↔secondaire à 2,5 mm) et le récapitulatif
qui suit décrivent l'état d'avant le 2026-10-25 — lus comme journal de
conception, pas comme l'état actuel.

### ~~Contrôle ↔ primaire, et contrôle ↔ secondaire : 8,5 mm~~ (historique)

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

### ~~Primaire ↔ secondaire : 2,5 mm~~ — retirée le 2026-10-25 (§20bis)

**Toute cette sous-section est caduque depuis le 2026-10-25** : le
secondaire n'étant plus isolé du primaire, il n'y a plus de barrière à
dimensionner entre les deux. Conservée ci-dessous à titre historique
(pourquoi 2,5 mm avait été calculée), pas comme état actuel.

| Critère | Valeur | Source |
|---|---|---|
| Tension maximale | 100 V | source 80 V, écrêtée par D3 (SMCJ100A) |
| Distance dans l'air, IPC-2221 B2 | 0,6 mm | table 51–100 V |
| Distance dans l'air, IPC-9592B | 1,1 mm | 0,1 + 0,01 × 100 |
| Ligne de fuite, IEC 60664-1, pollution 2 | 0,16 mm | table 100 V |
| **Retenu (historique)** | **2,5 mm** | marge ×2 sur la plus exigeante |

Cette barrière n'était traversée par **aucun composant** : seul le
transformateur la franchissait, magnétiquement.

~~**Point à vérifier** : le MSD1514 est une inductance couplée, pas un
transformateur d'isolement. Sa tenue enroulement à enroulement est à lire
dans sa fiche.~~ **Devenu sans objet (2026-11-14)** : sans barrière
primaire↔secondaire, la tenue enroulement à enroulement du MSD1514
(500 Vrms/1 min, essai diélectrique de type — pas une tension de
service, voir « Chemin 3 » plus bas) n'est plus une valeur à vérifier
contre quoi que ce soit ; c'est une caractéristique du composant parmi
d'autres, sans conséquence sur une barrière réelle de cette carte.
Retirée des « Points ouverts ».

### ~~Récapitulatif~~ (état avant le 2026-10-25, historique)

| Barrière | Distance | Ce qui la traverse |
|---|---|---|
| contrôle ↔ primaire | ~~8,5 mm~~ 4 mm (voir §6bis) | U3, U5, U8, U9, U10, U11 |
| contrôle ↔ secondaire | ~~8,5 mm~~ 4 mm (voir §6bis) | U7 |
| ~~primaire ↔ secondaire~~ | ~~2,5 mm~~ *(retirée 2026-10-25)* | ~~T1 seul, magnétiquement~~ |

**État actuel, une seule ligne** :

| Barrière | Distance | Ce qui la traverse |
|---|---|---|
| contrôle ↔ {primaire + secondaire} | **4 mm** | U3, U5, U7, U8, U9, U10, U11 |

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
~~une **chaîne de 3×1 MΩ physiquement espacée sur toute la largeur de la
barrière** (pas sous un seul composant), de façon que le chemin
cuivre-à-cuivre cumulé atteigne bien les 8,5 mm, et que les deux nœuds
intermédiaires ne soient approchés par aucune autre piste/via/
remplissage.~~ **Retiré par décision (2026-11-14, indication de
l'utilisateur)** : même en chaîne de 3, la contrainte `barriere_controle`
(4 mm, révisée depuis 8,5 — §6bis) ne se respecte pas avec des pastilles
0805 à cette barrière. La mitigation de ce §3 est abandonnée, pas
seulement incomplète — voir « Points ouverts » pour ce que ça laisse
ouvert côté `GND_CTRL`. Repères historiques (jamais menés à terme) au
§20 de `00-intention-conception.md`.

---

## 4. Forme du placement

**Révision 4 (2026-11-14) — toute cette section décrit la disposition
envisagée avant le 2026-10-25**, avec T1 à cheval sur une barrière
primaire↔secondaire de 2,5 mm qui n'existe plus. Le placement et le
routage réels sont **terminés** depuis (§29 de
`00-intention-conception.md`, DRC 0 violation) sur une disposition qui a
pu diverger de celle décrite ici — ce document ne reflète pas
nécessairement le placement final. Conservée à titre de méthode
(pourquoi grouper par boucle chaude, pourquoi T1 ne doit pas être
écartelé) plutôt que de plan d'exécution.

### Ce que la topologie imposait (historique)

| Barrière | Traversées |
|---|---|
| contrôle ↔ primaire | 6 isolateurs |
| contrôle ↔ secondaire | 1 isolateur (U7) |
| ~~primaire ↔ secondaire~~ | ~~**0 composant** — T1 seul~~ *(barrière retirée)* |

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

## 6bis. Valeur retenue, enregistrée (2026-11-14)

**4 mm**, `barriere_controle`, confirmé directement dans
`KICAD-HT.kicad_dru`. Deux justifications, pas une seule :

1. **Composant réellement monté** (déjà établie ci-dessus, 2026-10-23) :
   `ISO7710`/`ISO7710F` en boîtier D-8 sont classés *Basic Insulation*
   par la datasheet, `CLR`/`CPG` = 4 mm. Le renforcé (8,5 mm) n'existe
   que sur la variante DW-16, non montée.
2. **Isolement fonctionnel assumé, pas une revendication renforcée** :
   la barrière ne vise plus une certification de sécurité galvanique
   complète, seulement une séparation fonctionnelle suffisante pour
   l'écart de potentiel réellement rencontré (voir §1, `GND_CTRL` à la
   terre par une sonde, pas à 500 V). Vérifié contre les deux tables déjà
   citées au §2 historique, **pas supposé** :
   - IPC-2221 B2 (table déjà utilisée dans ce document) : la tranche
     301–500 V ne demande que 2,5 mm — 4 mm la couvre avec marge, y
     compris pour un défaut à pleine tension système (500 V).
   - IPC-9592B (`regles-pcb-V2/06-haute-tension.md`, HT-02) : la formule
     n'est **pas** `0,1 + 0,01 × V` partout — seulement de 30 à 100 V.
     Au-dessus de 100 V (le régime pertinent ici, l'écart visé étant la
     pleine tension système) : `0,6 + 0,005 × V`, continue avec l'autre
     tronçon à V=100 (1,1 mm des deux côtés), et qui redonne bien les
     3,1 mm à 500 V déjà cités au §2 historique. Résoudre `0,6+0,005×V=4`
     pour `V` donne **680 V**, pas 390. (Une première version de cette
     note avait appliqué le tronçon 30–100 V hors de son domaine de
     validité et concluait l'inverse — **erreur trouvée et corrigée le
     2026-11-14, deuxième relecture**, cf. l'avertissement du fichier
     source : « ne reproduit pas les normes elles-mêmes ».) **4 mm
     couvre donc cette formule-ci jusqu'à ~680 V**, avec une marge même
     plus confortable qu'IPC-2221 B2 (~800 V, même méthode : 2,5 mm à
     500 V + 0,005 mm/V au-delà) sur le même écart — les deux tables
     s'accordent, aucune n'est le point faible.

**Conséquence assumée** : cette barrière protège maintenant contre un
défaut/une configuration de banc à l'écart de potentiel réel attendu
(une sonde à la terre, pas un système entier à 500 V appliqué
directement à travers elle), pas contre la pleine excursion 500 V avec
la marge d'une isolation renforcée certifiée. Cohérent avec le composant
réellement monté (raison 1) — les deux raisons convergent, elles ne se
contredisent pas.

**Pas de clause de couche (`F.Cu`/`B.Cu` uniquement), contrairement à
`HT_distance_90V` — et c'est voulu, pas un oubli.** Les deux règles ne
protègent pas la même chose : `HT_distance_90V` encode une ligne de
fuite dans l'air, sans objet sur du cuivre enterré (d'où sa clause
externe uniquement, déjà commentée dans le `.kicad_dru`). `barriere_controle`
encode une séparation **galvanique** de région, qui doit tenir sur les
quatre couches à la fois — un plan interne continu qui passerait sous la
barrière l'annulerait par en dessous (déjà le raisonnement du §5,
« Deux règles qui tuent les cartes isolées »). Ajouter une clause de
couche ici supprimerait une protection réelle, pas un coût superflu.

**Mesuré directement sur les polygones remplis du `.kicad_pcb`
(`filled_polygon`, pas la silhouette de zone déclarée), pas estimé** —
l'écart réel entre régions `CTRL` et non-`CTRL` sur les couches
internes :

| Couche | Paire de zones | Écart mesuré (centre de trace) |
|---|---|---|
| `In1.Cu` | `GND_CTRL` ↔ `GND` | **4,25 mm** |
| `In2.Cu` | `3V3_ISO` ↔ `RAIL_3V3_PRI` | **4,29 mm** |

Dans les deux cas, l'écart réel dépasse le minimum de seulement
0,25–0,29 mm : la contrainte est déjà appliquée **au plus juste** en
interne, pas comme sous-produit accidentel d'une règle trop large. Le
gain d'une clause de couche serait de cet ordre (un quart de mm), sur
deux paires de zones seulement — marginal, et il irait à l'encontre du
raisonnement du §5. **Recommandation : ne pas ajouter de clause de
couche à `barriere_controle`.**

---

## 7. Ordre des opérations

**État vérifié au 2026-11-14 (schéma, PCB, `kicad-cli`), pas supposé :**

1. **Fait, partiellement.** Classes de nets et `.kicad_dru` créés et
   présents. Mais 4 classes (`CTRL`/`PRI`/`SEC`/`Default`), pas cinq —
   `PRI_PWR`/`SEC_PWR` n'existent pas séparément (voir révision 4 en
   tête de §6).
2. **Retiré par décision, pas fait.** Les trois chaînes de référence
   inter-domaines n'existent pas — la règle `barriere_controle` (4 mm)
   ne se respecte pas avec les pastilles d'une résistance 0805 à cette
   barrière, même en chaîne de 3 (détail à la nomenclature, plus bas).
3. **Sans objet / fait selon la partie.** La barrière primaire↔secondaire
   n'existe plus (rien à poser T1 « sur » elle) ; T1 et les deux boucles
   chaudes sont posés, le placement est terminé (§29 de
   `00-intention-conception.md`).
4. **Fait, à 4 mm** (pas 8,5 — §6bis), sept isolateurs alignés — confirmé
   par le DRC propre (0 violation de clearance, voir plus bas).
5. **Fait.** `J2` à (102,0 ; 93,7)mm, largement à l'intérieur du contour
   85×70mm (96–181 ; 47–117) — vérifié sur les coordonnées réelles, plus
   question d'être « à 11,4 mm à l'extérieur ».
6. **Fait.** Contour 85×70mm (mesuré sur `Edge.Cuts`, cohérent avec le
   85×70mm annoncé au §29), routé à 100%.
7. **Fait.** `kicad-cli pcb drc` relancé le 2026-11-14 : **3 violations**,
   toutes `lib_footprint_mismatch` (désynchronisation empreinte/librairie
   sur `In1`, `J2`, `Out1` — sans rapport avec le dégagement ou les
   barrières). 0 violation de `clearance`/`creepage`. Écart avec le « 0
   violation » du §29 (2026-10-29) non expliqué dans cette passe — les
   trois empreintes ont pu être retouchées depuis sans mise à jour de la
   copie embarquée (mécanisme déjà documenté au §27 de
   `00-intention-conception.md`), à vérifier si l'occasion se présente.

---

## Points ouverts

- ~~Tenue enroulement à enroulement du MSD1514, à lire dans sa fiche
  Coilcraft.~~ **Retiré (2026-11-14)** : n'est plus une valeur à
  vérifier contre une barrière, celle-ci ayant disparu (§2). Reste une
  caractéristique de composant parmi d'autres, sans conséquence sur
  l'isolement de cette carte.
- **Référence de potentiel continu `CTRL`↔{`PRI`,`SEC`} absente, par
  décision — pas un oubli (corrigé 2026-11-14, indication de
  l'utilisateur).** Les trois chaînes de référence inter-domaines
  (§3) ont été **retirées** : la règle `barriere_controle` (4 mm) ne se
  respecte pas avec les pastilles d'une résistance 0805 à cette
  barrière, même répartie en 3 maillons. `R35`–`R42`(+`R6`) ont été
  réemployés pour d'autres fonctions (mesure de courant, pont
  `3V3_ISO`...), vérifié par leurs nets PCB réels, pas de chaîne
  survivante même partielle. Le problème électrique du §3 (`GND_CTRL`
  sans référence continue vis-à-vis du reste de la carte — mode commun
  de barrière sans chemin de retour défini, traverse les isolateurs
  eux-mêmes) **reste donc entier pour cette barrière**, sans parade à ce
  jour. À distinguer du réseau `R9`/`R10`/`R22`/`R23` (polarisation,
  voir plus bas) : celui-ci référence bien `VOUT_N`/`VOUT_P` à `GND`,
  mais ne touche pas `GND_CTRL`. **Risque évalué par l'utilisateur
  (2026-11-14) : ni bloquant ni dangereux** — pas de parade retenue
  avant fabrication, solution à trouver empiriquement sur le prototype
  une fois construit (mesure réelle du potentiel flottant, pas une
  présomption de danger a priori). Décision assumée de différer, pas un
  point laissé par défaut.
- **`3V3_CTRL` (document) contre `3V3_ISO` (schéma)** : deux noms pour un
  net, à unifier.
- **La spec affiche 90 V alors que la source en délivre 78 utiles** (§11,
  déjà noté). Sans incidence sur l'isolement, 100 V restant le plafond du
  clamp.
- **η = 0,85 non sourcé**, et les largeurs de piste de puissance en
  dépendent.
- ~~**Conséquence électrique du décloisonnement primaire↔secondaire non
  vérifiée** — quel nœud relie exactement `GND` et `VOUT_N`~~ **Trouvé
  (2026-11-14), confirmé par indication de l'utilisateur puis vérifié
  directement dans les fichiers (pas pris au mot)** : pas de liaison
  directe, mais un chemin résistif continu à travers le réseau de
  polarisation déjà documenté au §1/§3 — `VOUT_N` → `R10` (100k) →
  `HV_BIAS_OUT` → `R22` (470k) → `BIAS_SENSE` → `R23` (10k) → `GND`,
  soit **580 kΩ** série (`VOUT_P` a le même chemin via `R9`, valeur
  identique). `R9`/`R10`/`R22`/`R23` lus dans `flyback.kicad_sch`/
  `polarisation.kicad_sch`, continuité des nets vérifiée dans
  `KICAD-HT.kicad_pcb`. C'est le même réseau que celui qui pilote déjà
  la boucle de linéarisation (`polarisation.kicad_sch`, §16 de
  `00-intention-conception.md`) — pas un composant ajouté pour ce
  décloisonnement, une conséquence de son existence préalable. **Reste
  ouvert, non vérifié dans cette passe** : l'impact de ce chemin à 580kΩ
  (pas un flottement complet, mais pas une masse franche non plus) sur
  les calculs de surtension de `D1`/`D4` du §17, établis en supposant un
  secondaire flottant sans aucune référence résistive — conception
  électrique, pas rédaction, hors périmètre d'une passe documentation.

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
| `Vht`, `I_Shunt_ht`, `V_bias` | 100 Ω + 1 nF |
| `I_Out_ht` | 1 kΩ + 47 nF (R26/C60, filtre moyenneur fc≈3,4kHz — même gabarit que R18/C33 sur `I_Shunt_ht`, pas le simple 100Ω+1nF des autres voies, 2026-10-28) |
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
| F1 (**fait**, même repère) | fusible d'entrée, en série avec In1 | **`2A-T`, lu dans `alim.kicad_sch` (2026-11-14) — pas `3A`** comme écrit ici et au §20 de `00-intention-conception.md` avant cette relecture | posé dans `alim.kicad_sch` |
| D5 → D8 | TVS sur `VIN`, en aval de F1 | SMCJ28A ou SMCJ30A | **décidé absent** — protection prise au niveau système sur `KICAD-C2000-powershield`, pas un oubli (voir §20 de `00-intention-conception.md`). `D8` existe bien dans le projet mais sur `polarisation.kicad_sch`, sans rapport (`SMBJ100`, autre fonction) |
| D6 → **D2** (fait, repère différent) | TVS sur `RAIL_8V25` | **`SMBJ9`, lu dans `alim.kicad_sch` (2026-11-14) — pas `SMCJ10A`** comme écrit ici avant cette relecture | posé dans `alim.kicad_sch` |
| D7 (déjà fait avant ce plan, même repère par coïncidence) | TVS sur `RAIL_3V3_PRI` | **`SMBJ05`, lu dans `alim.kicad_sch` (2026-11-14) — pas `SMCJ04A`** comme écrit ici avant cette relecture | posé depuis `c535024` |
| R30–R32 → *(aucun — voir ci-dessous)* | référence inter-domaines (§3), en 3 chaînes de 3×1 MΩ | 1 MΩ | **retiré par décision, pas incomplet (corrigé 2026-11-14, indication de l'utilisateur)** — impossible de respecter `barriere_controle` (4 mm) avec des pastilles 0805 à cette barrière, même en chaîne de 3. `R35`–`R42`(+`R6`) réemployés pour d'autres fonctions, vérifié par leurs nets PCB réels — aucune chaîne survivante |

Sept composants visés à l'origine ; aujourd'hui, vérifié schéma + PCB :
`F1`, `D2`, `D7` posés, `D8` délibérément absent (protection système),
et les résistances de référence inter-domaines **retirées par décision**
(contrainte géométrique 0805 vs 4 mm), pas simplement incomplètes — la
référence `GND_CTRL`↔{`GND`,`VOUT_N`} reste donc sans parade.

---

## Ce que ça change pour le placement

- **F1 au ras de In1**, avant toute dérivation. Le fusible est le premier
  composant que `VIN` rencontre. ~~D5~~ sans objet, `D8` n'est pas posé
  sur cette carte (décision système, voir nomenclature ci-dessus).
- **D6 au ras de Reg1, D7 au ras de Reg2**, dans la région primaire.
- ~~**R30–R32** sous le corps de leur isolateur~~ **sans objet
  (2026-11-14)** : la chaîne de référence inter-domaines a été retirée
  par décision (impossible à respecter 4 mm avec des pastilles 0805 à
  cette barrière, voir nomenclature ci-dessus) — plus rien à placer ici
  tant qu'une autre parade n'est pas trouvée pour `GND_CTRL`.

Aucun de ces ajouts ne touche aux boucles chaudes ni aux barrières. Ils se
logent dans la périphérie que la disposition en bandeau libère naturellement.
