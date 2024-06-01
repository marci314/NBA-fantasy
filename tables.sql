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
    id_igralca FOREIGN KEY REFERENCES igralec(igralec_id),
    id_tekme FOREIGN KEY REFERENCES tekma(tekma_id),
    id_trenerja FOREIGN KEY REFERENCES trener(trener_id),
    id_ekipa FOREIGN KEY REFERENCES ekipa(ekipa_id),
    odstotek_meta FLOAT, -- Pa če ni metal niti enkrat?
    ukradene INT,
    bloki INT,
    izgubljene INT,
    skoki INT,
    podaje INT,
    odigrane_minute INT,
    tocke INT,
    izid BOOLEAN -- 1 pomeni zmago, 0 poraz
);