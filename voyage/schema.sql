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
