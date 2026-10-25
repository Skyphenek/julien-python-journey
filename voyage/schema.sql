-- voyage/schema.sql
CREATE TABLE etat_case (
    voyage       TEXT    NOT NULL,
    proprietaire TEXT    NOT NULL,
    theme        TEXT    NOT NULL,
    objet        TEXT    NOT NULL,
    coche        BOOLEAN NOT NULL DEFAULT FALSE,
    maj_le       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (voyage, proprietaire, theme, objet)
);
