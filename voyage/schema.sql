-- voyage/schema.sql
CREATE TABLE IF NOT EXISTS etat_case (
    voyage       TEXT    NOT NULL,
    proprietaire TEXT    NOT NULL,
    theme        TEXT    NOT NULL,
    objet        TEXT    NOT NULL,
    coche        BOOLEAN NOT NULL DEFAULT FALSE,
    maj_le       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (voyage, proprietaire, theme, objet)
);

-- Cache des normales climatiques : une ligne par lieu (coordonnées arrondies à 0.01°, ~1 km) et par mois.
-- Les normales sur 10 ans ne bougent pas : calculées une fois, relues ensuite (plus d'appel API).
CREATE TABLE IF NOT EXISTS normales_climat (
    latitude          NUMERIC(7,2)     NOT NULL,
    longitude         NUMERIC(7,2)     NOT NULL,
    mois              SMALLINT         NOT NULL CHECK (mois BETWEEN 1 AND 12),
    tmin              DOUBLE PRECISION NOT NULL,
    tmax              DOUBLE PRECISION NOT NULL,
    jours_pluie       INTEGER          NOT NULL,
    jours_forte_pluie DOUBLE PRECISION NOT NULL,
    calcule_le        TIMESTAMPTZ      NOT NULL DEFAULT now(),
    PRIMARY KEY (latitude, longitude, mois)
);

-- Page de checklist publiée par valise.py : le serveur (local ou en ligne) la sert depuis la base,
-- car valise.html n'existe que sur le Mac. Une seule page "courante" à la fois.
CREATE TABLE IF NOT EXISTS page_valise (
    cle     TEXT        PRIMARY KEY DEFAULT 'courante',
    html    TEXT        NOT NULL,
    maj_le  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Mémoire des voyages (bilan de fin de séjour) -------------------------------------------
-- Un voyage = un code stable "date de départ + itinéraire" : régénérer la même valise
-- (même date, mêmes étapes) retombe sur le même voyage et garde les cases cochées.
CREATE TABLE IF NOT EXISTS voyages (
    code        TEXT        PRIMARY KEY,               -- "2027-01-10 Tokyo › Bangkok"
    libelle     TEXT        NOT NULL,                  -- "Tokyo › Bangkok"
    depart      DATE        NOT NULL,
    personnes   TEXT[]      NOT NULL,                  -- {Julien,Laetitia}
    itineraire  JSONB       NOT NULL,                  -- étapes : destination, jours, mois, activités, pays, normales
    jours_types JSONB       NOT NULL,                  -- {"chaud": 11, "ville": 18} : le contexte climatique
    cree_le     TIMESTAMPTZ NOT NULL DEFAULT now(),
    maj_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Photo de la valise proposée : la référence pour dire "en trop" ou "pas servi".
CREATE TABLE IF NOT EXISTS valise_objets (
    voyage       TEXT    NOT NULL REFERENCES voyages(code) ON DELETE CASCADE,
    proprietaire TEXT    NOT NULL,
    theme        TEXT    NOT NULL,
    objet        TEXT    NOT NULL,
    quantite     INTEGER NOT NULL,
    PRIMARY KEY (voyage, proprietaire, theme, objet)
);

-- Bilan de fin de voyage : un verdict par objet et par personne.
-- 'manque' = objet NON proposé qui a manqué (texte libre) ; quantite_utilisee sert à 'trop'.
CREATE TABLE IF NOT EXISTS retours (
    voyage            TEXT        NOT NULL REFERENCES voyages(code) ON DELETE CASCADE,
    proprietaire      TEXT        NOT NULL,
    objet             TEXT        NOT NULL,
    verdict           TEXT        NOT NULL CHECK (verdict IN ('utile', 'trop', 'pas_servi', 'manque')),
    quantite_utilisee INTEGER     CHECK (quantite_utilisee >= 0),
    maj_le            TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (voyage, proprietaire, objet)
);

-- Apprentissage (session 3) -------------------------------------------------------------
-- Un voyage archivé (essai, voyage annulé…) est ignoré par l'historique, sans être supprimé.
ALTER TABLE voyages ADD COLUMN IF NOT EXISTS archive BOOLEAN NOT NULL DEFAULT false;

-- Oublis ajoutés "toujours" : remis automatiquement dans la valise de cette personne.
CREATE TABLE IF NOT EXISTS regles_perso (
    personne TEXT        NOT NULL,                   -- "Julien", "Laetitia" ou "Partagé"
    objet    TEXT        NOT NULL,
    theme    TEXT        NOT NULL,
    quantite INTEGER     NOT NULL DEFAULT 1 CHECK (quantite > 0),
    cree_le  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (personne, objet)
);

-- Régénération sans terminal (météo J-7, saisie en ligne) ------------------------------
-- Les réglages du voyage, pour pouvoir le reconstruire depuis la base. Les étapes gardent
-- aussi leurs coordonnées (latitude/longitude) dans le JSON de l'itinéraire.
ALTER TABLE voyages ADD COLUMN IF NOT EXISTS conduit BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE voyages ADD COLUMN IF NOT EXISTS lessive INTEGER CHECK (lessive > 0);   -- NULL = pas de lessive

-- Avant de partir : date d'expiration du passeport de chaque voyageur (ni numéro, ni scan).
-- Sert à vérifier la règle « valide 6 mois après le retour » sans rien demander.
CREATE TABLE IF NOT EXISTS passeports (
    personne  TEXT        PRIMARY KEY,
    expire_le DATE        NOT NULL,
    maj_le    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Mode « bagage cabine seulement » (réglage du voyage) : vêtements plafonnés, liquides ≤ 100 ml.
ALTER TABLE voyages ADD COLUMN IF NOT EXISTS cabine BOOLEAN NOT NULL DEFAULT false;

-- Infos de chaque étape (hôtel, adresse, réservation…), saisies à deux dans la rubrique Sur place.
-- Une ville visitée deux fois (aller / retour) a deux fiches : rang 1, rang 2.
CREATE TABLE IF NOT EXISTS infos_etape (
    voyage      TEXT        NOT NULL REFERENCES voyages(code) ON DELETE CASCADE,
    destination TEXT        NOT NULL,
    rang        SMALLINT    NOT NULL DEFAULT 1,
    hebergement TEXT        NOT NULL DEFAULT '',
    adresse     TEXT        NOT NULL DEFAULT '',
    reservation TEXT        NOT NULL DEFAULT '',
    arrivee     TEXT        NOT NULL DEFAULT '',
    notes       TEXT        NOT NULL DEFAULT '',
    maj_le      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (voyage, destination, rang)
);

-- Dépenses partagées (rubrique Sur place) : montant dans la devise payée, converti en euros au
-- moment de la saisie (taux du téléphone) pour que le solde ne bouge plus ensuite.
CREATE TABLE IF NOT EXISTS depenses (
    id          SERIAL        PRIMARY KEY,
    voyage      TEXT          NOT NULL REFERENCES voyages(code) ON DELETE CASCADE,
    libelle     TEXT          NOT NULL,
    montant     NUMERIC(14,2) NOT NULL CHECK (montant > 0),
    devise      TEXT          NOT NULL,
    montant_eur NUMERIC(12,2) NOT NULL CHECK (montant_eur >= 0),
    paye_par    TEXT          NOT NULL,
    pour        TEXT[]        NOT NULL,
    jour        DATE          NOT NULL,
    cree_le     TIMESTAMPTZ   NOT NULL DEFAULT now()
);
