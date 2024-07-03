-- Podelitev pravic
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
GRANT CONNECT ON DATABASE sem2024_marcelb TO javnost;
GRANT ALL PRIVILEGES ON DATABASE sem2024_marcelb TO javnost;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO javnost;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO javnost;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO javnost;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO javnost;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO javnost;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO javnost;

-- Brisanje obstoječih tabel
DROP TABLE IF EXISTS podatki_o_tekmi;
DROP TABLE IF EXISTS tekma;
DROP TABLE IF EXISTS ekipa;
DROP TABLE IF EXISTS trener;
DROP TABLE IF EXISTS igralec;
DROP TABLE IF EXISTS fantasy_ekipa;
DROP TABLE IF EXISTS uporabnik;
DROP TABLE IF EXISTS fantasy_ekipa_trener;
DROP TABLE IF EXISTS fantasy_ekipa_igralci;
DROP TABLE IF EXISTS igralci_tocke;

-- Ustvarjanje novih tabel
CREATE TABLE uporabnik (
    uporabnik_id SERIAL PRIMARY KEY,
    uporabnisko_ime TEXT NOT NULL,
    geslo TEXT NOT NULL,
    last_login DATE
);

CREATE TABLE fantasy_ekipa (
    f_ekipa_id SERIAL PRIMARY KEY,
    tocke INT NOT NULL,
    lastnik INT NOT NULL REFERENCES uporabnik(uporabnik_id),
    ime_ekipe TEXT NOT NULL
);

CREATE Table igralec (
    igralec_id SERIAL PRIMARY KEY,
    ime TEXT NOT NULL,
    priimek TEXT NOT NULL,
    pozicija TEXT,
    visina INT NOT NULL,
    rojstvo DATE
);

CREATE Table trener (
    trener_id SERIAL PRIMARY KEY,
    ime TEXT NOT NULL,
    rojstvo DATE
);

CREATE TABLE fantasy_ekipa_trener (
    f_ekipa_id INT REFERENCES fantasy_ekipa(f_ekipa_id),
    trener_id INT REFERENCES trener(trener_id),
    PRIMARY KEY (f_ekipa_id, trener_id)
);

CREATE TABLE ekipa (
    ekipa_id TEXT PRIMARY KEY,
    ekipa_ime TEXT
);

CREATE TABLE tekma (
    id_tekma SERIAL PRIMARY KEY,
    domaca_ekipa TEXT NOT NULL,
    gostujoca_ekipa TEXT NOT NULL,
    domaca_ekipa_tocke INT,
    gostujoca_ekipa_tocke INT,
    datum DATE
);

CREATE TABLE podatki_o_tekmi (
    id_igralca INT REFERENCES igralec(igralec_id),
    id_tekme INT REFERENCES tekma(id_tekma),
    odstotek_meta FLOAT, 
    ukradene INT,
    bloki INT,
    izgubljene INT,
    skoki INT,
    podaje INT,
    odigrane_minute INT,
    tocke INT,
    izid BOOLEAN,
    PRIMARY KEY (id_igralca, id_tekme)
);

CREATE TABLE fantasy_ekipa_igralci (
    f_ekipa_id INT REFERENCES fantasy_ekipa(f_ekipa_id),
    igralec_id INT REFERENCES igralec(igralec_id),
    PRIMARY KEY (f_ekipa_id, igralec_id)
);

CREATE TABLE igralci_tocke (
    id_igralca INT NOT NULL REFERENCES igralec(igralec_id),
    id_tekme INT NOT NULL REFERENCES tekma(id_tekma),
    tocke INT,
    PRIMARY KEY (id_igralca, id_tekme)
);
