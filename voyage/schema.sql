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
