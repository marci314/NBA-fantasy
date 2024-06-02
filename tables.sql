GRANT ALL ON DATABASE sem2024_marcelb TO jostp WITH GRANT OPTION;
GRANT ALL ON SCHEMA public TO jostp WITH GRANT OPTION;
GRANT ALL ON DATABASE sem2024_marcelb TO gasperdr WITH GRANT OPTION;
GRANT ALL ON SCHEMA public TO gasperdr WITH GRANT OPTION;
GRANT ALL ON DATABASE sem2024_marcelb TO majg WITH GRANT OPTION;
GRANT ALL ON SCHEMA public TO majg WITH GRANT OPTION;
GRANT ALL ON ALL TABLES IN SCHEMA public TO gasperdr WITH GRANT OPTION;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO gasperdr WITH GRANT OPTION;
GRANT ALL ON ALL TABLES IN SCHEMA public TO majg WITH GRANT OPTION;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO majg WITH GRANT OPTION;

DROP TABLE IF EXISTS podatki_o_tekmi;
DROP TABLE IF EXISTS tekma;
DROP TABLE IF EXISTS ekipa;
DROP TABLE IF EXISTS trener;
DROP TABLE IF EXISTS igralec;
DROP TABLE IF EXISTS fantasy_ekipa;
DROP TABLE IF EXISTS uporabnik;


CREATE TABLE uporabnik (
    uporabnik_id PRIMARY KEY,
    uporabnisko_ime TEXT NOT NULL,
    geslo TEXT NOT NULL
);

CREATE TABLE fantasy_ekipa (
    f_ekipa_id PRIMARY KEY,
    tocke INT NOT NULL,
    lastnik INT NOT NULL REFERENCES uporabnik(uporabnik_id),
    ime_ekipe TEXT NOT NULL
);

CREATE Table igralec (
    igralec_id TEXT PRIMARY KEY,
    ime TEXT NOT NULL,
    priimek TEXT NOT NULL,
    pozicija TEXT,
    visina INT NOT NULL,
    rojstvo DATE
);

CREATE Table trener (
    trener_id TEXT PRIMARY KEY,
    ime TEXT NOT NULL,
    priimek TEXT NOT NULL,
    rojstvo DATE
);

CREATE TABLE ekipa (
    ekipa_id PRIMARY KEY
);

CREATE TABLE tekma (
    id_tekma PRIMARY KEY,
    domaca_ekipa TEXT NOT NULL,
    gostujoca_ekipa TEXT NOT NULL,
    datum DATE
);

CREATE TABLE podatki_o_tekmi (
    id_igralca TEXT,
    id_tekme SERIAL,
    id_trenerja TEXT,
    id_ekipa INT,
    odstotek_meta FLOAT, 
    ukradene INT,
    bloki INT,
    izgubljene INT,
    skoki INT,
    podaje INT,
    odigrane_minute INT,
    tocke INT,
    izid BOOLEAN,
    FOREIGN KEY (id_igralca) REFERENCES igralec(igralec_id),
    FOREIGN KEY (id_tekme) REFERENCES tekma(id_tekma),
    FOREIGN KEY (id_trenerja) REFERENCES trener(trener_id),
    FOREIGN KEY (id_ekipa) REFERENCES ekipa(ekipa_id)
);