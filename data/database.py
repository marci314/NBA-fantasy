import datetime
import psycopg2, psycopg2.extensions, psycopg2.extras, os
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) 
from typing import List, TypeVar, Type, Callable
from Data.Modeli import *
from datetime import date
import Data.auth_public as auth
import math
from typing import List, Dict

# Preberemo port za bazo iz okoljskih spremenljivk
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

class Repo:

    def __init__(self):
        # Ko ustvarimo novo instanco definiramo objekt za povezavo in cursor
        self.conn = psycopg2.connect(database=auth.dbname, host=auth.host, user=auth.user, password=auth.password, port=DB_PORT)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    def dodaj_igralca_v_fantasy_ekipo(self, f_ekipa_id: int, igralec_id: str) -> str:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT COUNT(*) FROM fantasy_ekipa_igralci
                WHERE f_ekipa_id = %s
            """, (f_ekipa_id,))
            count = cur.fetchone()[0]
            if count >= 5:
                return "Ekipa ima že 5 igralcev."

            cur.execute("""
                SELECT * FROM fantasy_ekipa_igralci
                WHERE f_ekipa_id = %s AND igralec_id = %s
            """, (f_ekipa_id, igralec_id))
            row = cur.fetchone()
            if row:
                return "Igralec je že v ekipi."

            cur.execute("""
                INSERT INTO fantasy_ekipa_igralci (f_ekipa_id, igralec_id)
                VALUES (%s, %s)
            """, (f_ekipa_id, igralec_id))
            self.conn.commit()
            return "Igralec je bil uspešno dodan."

    def odstrani_igralca_iz_fantasy_ekipe(self, f_ekipa_id: int, igralec_id: str) -> None:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Odstrani igralca iz fantazijske ekipe
            cur.execute("""
                DELETE FROM fantasy_ekipa_igralci
                WHERE f_ekipa_id = %s AND igralec_id = %s
                """, (f_ekipa_id, igralec_id))
            self.conn.commit()
            print(f"Igralec {igralec_id} je bil odstranjen iz ekipe {f_ekipa_id}.")
    
    def dodaj_trenerja_v_fantasy_ekipo(self, f_ekipa_id: int, trener_id: str) -> str:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT COUNT(*) FROM fantasy_ekipa_trener
                WHERE f_ekipa_id = %s
            """, (f_ekipa_id,))
            count = cur.fetchone()[0]
            if count >= 1:
                return "Ekipa že ima trenerja."

            cur.execute("""
                INSERT INTO fantasy_ekipa_trener (f_ekipa_id, trener_id)
                VALUES (%s, %s)
            """, (f_ekipa_id, trener_id))
            self.conn.commit()
            return "Trener je bil uspešno dodan."
    
    def odstrani_trenerja_iz_fantasy_ekipe(self, f_ekipa_id: int, trener_id: str) -> None:
        # Odstrani trenerja iz fantazijske ekipe
        self.cur.execute("""
            DELETE FROM fantasy_ekipa_trener
            WHERE f_ekipa_id = %s AND trener_id = %s
            """, (f_ekipa_id, trener_id))
        self.conn.commit()
        print(f"Trener {trener_id} je bil odstranjen iz ekipe {f_ekipa_id}.")

    def get_all_players(self) -> List[Dict]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM igralec")
            return cur.fetchall()
    
    def ustvari_fantasy_ekipo(self, fantasy_ekipa: FantasyEkipa) -> FantasyEkipa:
        # Preveri, da nima uporabnik več kot treh ekip
        self.cur.execute("""
            SELECT COUNT(*) FROM fantasy_ekipa
            WHERE lastnik = %s
            """, (fantasy_ekipa.lastnik,))
        count = self.cur.fetchone()[0]
        if count >= 3:
            return "Uporabnik ima že maksimalno dovoljeno število ekip."
        # Preveri, ali ekipa s tem imenom že obstaja
        self.cur.execute("""
            SELECT * FROM fantasy_ekipa
            WHERE ime_ekipe = %s
            """, (fantasy_ekipa.ime_ekipe,))
        row = self.cur.fetchone()
        if row:
            fantasy_ekipa.ime_ekipe = row['ime_ekipe']
            return fantasy_ekipa
        
        # Vstavi novo ekipo
        self.cur.execute("""
            INSERT INTO fantasy_ekipa (ime_ekipe)
            VALUES (%s)
            RETURNING f_ekipe_id
            """, (fantasy_ekipa.ime_ekipe))
        
        fantasy_ekipa.f_ekipa_id = self.cur.fetchone()['f_ekipa_id'] # morda treba dodati še za točke in igralce? ali je 0 default okj
        self.conn.commit()
        return fantasy_ekipa
    
    def lestvica(self) -> List[FantasyEkipa]:
        self.cur.execute("""
            SELECT ime_ekipe, lastnik, tocke FROM fantasy_ekipa
            ORDER BY tocke DESC
        """)
        return [FantasyEkipa(ime_ekipe, lastnik, tocke) for (ime_ekipe, lastnik, tocke) in self.cur.fetchall()]
    
    def pokazi_ekipo(self, ime_ekipe: str) -> dict:
        '''Pokaže uporabnikovo fantasy ekipo z imeni igralcev in trenerja ter njihovimi točkami.'''

        # Preveri, ali ekipa z danim imenom obstaja
        self.cur.execute("""
            SELECT f_ekipa_id, tocke, ime_ekipe
            FROM fantasy_ekipa
            WHERE ime_ekipe = %s
            """, (ime_ekipe,))
        team = self.cur.fetchone()

        if not team:
            print("Ekipa z imenom '{}' ne obstaja.".format(ime_ekipe))
            return {}

        team_id = team['f_ekipa_id']
        tocke = team['tocke']

        # Pridobi igralce v ekipi
        self.cur.execute("""
            SELECT i.igralec_id, i.ime, i.priimek, i.pozicija, i.visina, i.rojstvo
            FROM igralec i
            JOIN fantasy_ekipa_igralci fei ON i.igralec_id = fei.igralec_id
            WHERE fei.f_ekipa_id = %s
            """, (team_id,))
        players = self.cur.fetchall()

        # Pridobi trenerje v ekipi
        self.cur.execute("""
            SELECT t.trener_id, t.ime, t.priimek, t.rojstvo
            FROM trener t
            JOIN fantasy_ekipa_trenerji fet ON t.trener_id = fet.trener_id
            WHERE fet.f_ekipa_id = %s
            """, (team_id,))
        coaches = self.cur.fetchall()

        # Sestavi rezultat v obliki slovarja
        result = {
            'ime_ekipe': ime_ekipe,
            'tocke': tocke,
            'igralci': players,
            'trenerji': coaches
        }

        return result

    def odigraj_teden(self, izbrani_datum: datetime.date) -> str:
        '''Izvede tekme za naslednji teden in prišteje točke ekipam.'''
        
        # Izračunaj datum za naslednji teden
        naslednji_teden = izbrani_datum + datetime.timedelta(days=7)
        
        # Preveri, ali so podatki o tekmi za naslednji teden na voljo
        self.cur.execute("""
            SELECT id_tekma, domaca_ekipa, gostujoca_ekipa, datum 
            FROM tekma
            WHERE datum BETWEEN %s AND %s
            """, (izbrani_datum, naslednji_teden))
        tekme = self.cur.fetchall()

        if not tekme:
            return "Za izbrani datum ni podatkov o tekmah za naslednji teden."
        
        # Izvedi tekme za naslednji teden
        for tekma in tekme:
            id_tekma = tekma['id_tekma']
            rezultat = self.odigraj_kolo(id_tekma)
            print(rezultat)  # Izpis rezultata vsake odigrane tekme
        
        return "Tekme za naslednji teden so bile uspešno odigrane."

    def odigraj_kolo(self, id_tekme: int) -> str:
        '''Izvede tekmo za dano tekmo in prišteje točke ekipam.'''
        
        # Pridobi podatke o tekmi
        self.cur.execute("""
            SELECT * 
            FROM podatki_o_tekmi
            WHERE id_tekme = %s
            """, (id_tekme,))
        podatki_o_tekmi = self.cur.fetchall()

        if not podatki_o_tekmi:
            return "Ni podatkov o tekmi s tem ID."

        # Posodobi točke ekip glede na podatke o tekmi
        for podatki in podatki_o_tekmi:
            id_ekipa = podatki['id_ekipa']
            tocke = podatki['tocke']
            izid = podatki['izid']
            
            # Dodaj točke ekipi
            self.cur.execute("""
                UPDATE fantasy_ekipa
                SET tocke = tocke + %s
                WHERE f_ekipa_id = %s
                """, (tocke, id_ekipa))

        # Commit spremembe
        self.conn.commit()
        return "Tekma je bila uspešno odigrana."

    def izracunaj_tocke(self, podatki: PodatkiOTekmi) -> int:
        '''Funkcija na podlagi igralčeve statistike izračuna, koliko fantasy točk si je prislužil.
        Igralec dobi točko za vsako skok in asistenco, dve točki za vsako ukradeno žogo ali blok,
        minus dve točki za vsako izgubljeno žogo.
        Poleg tega dobi točke na podlagi tega, koliko točk je prinesel ekipi, vendar skalirano glede na odstotek meta iz igre.
        Dodatno dobi pet točk bonusa, če je njegova ekipa zmagala.'''
        tocke = 5 * podatki.izid + podatki.tocke * (0.2 + podatki.odstotek_meta) + podatki.skoki + podatki.podaje + 2 * podatki.bloki + 2 * podatki.ukradene - 2 * podatki.izgubljene
        return math.floor(tocke)

# alternativen odigraj_teden za minimalni vzorec podatkov: (tu je pogoj, da se v tabelo tekma doda nek nov stolpec s tedni kot integerji)
    def odigraj_teden2(self, st_tedna) -> str:
        '''Izvede tekme za naslednji teden in prišteje točke ekipam.'''
        # Preveri, ali so podatki o tekmi za naslednji teden na voljo
        self.cur.execute("""
            SELECT id_tekma, domaca_ekipa, gostujoca_ekipa, datum 
            FROM tekma
            WHERE teden = %s 
            """, (st_tedna,)) 
        tekme = self.cur.fetchall()

        if not tekme:
            return "Za izbrani datum ni podatkov o tekmah za naslednji teden."
        
        # Izvedi tekme za naslednji teden
        for tekma in tekme:
            id_tekma = tekma['id_tekma']
            rezultat = self.odigraj_tekmo(id_tekma)
            print(rezultat)  # Izpis rezultata vsake odigrane tekme
        
        return "Tekme za naslednji teden so bile uspešno odigrane."

    def odigraj_tekmo(self, id_tekme: int) -> str:
        '''Izvede tekmo in prišteje točke ekipam.'''
        
        # Pridobi podatke o tekmi
        self.cur.execute("""
            SELECT * 
            FROM podatki_o_tekmi
            WHERE id_tekme = %s
            """, (id_tekme,))
        podatki_tekme = self.cur.fetchall()

        if not podatki_tekme:
            return "Ni podatkov o tekmi s tem ID."

        # Posodobi točke ekip glede na podatke o tekmi
        for podatki_o_tekmi in podatki_tekme:
            t = self.izracunaj_tocke(podatki_o_tekmi)
            self.cur.execute("""
            INSERT INTO igralci_tekme (id_igralca, id_tekme, tocke) 
            VALUES (%s, %s, %s);      
            """, (podatki_o_tekmi.id_igralca, podatki_o_tekmi.id_tekme, t))
            
        # Dodaj točke fantazijskim ekipam (izbere vse igralce na tekmi, nato za vsakega igralca posebej doda točke vsem ekipam, ki ga imajo)
        self.cur.execute("""                      
            WHERE id_tekme = %s"""
        ), (id_tekme)
        rows = self.cur.fetchall()
        for row in rows:
            id_igr = row[0]
            tocke_igr = row[1]
                                            
            self.cur.execute("""
                SELECT f_ekipa_id 
                FROM fantasy_ekipa_igralci
                WHERE igralec_id = %s
                """, (id_igr,))
            ekipe = self.cur.fetchall()

            for ekipa in ekipe:
                f_ekipa_id = ekipa[0]
                self.cur.execute("""
                    UPDATE fantasy_ekipa
                    SET tocke = tocke + %s
                    WHERE f_ekipa_id = %s
                    """, (tocke_igr, f_ekipa_id))
        # Commit spremembe
        self.conn.commit() 
        return "Tekma je bila uspešno odigrana."
