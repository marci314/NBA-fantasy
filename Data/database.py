import datetime
import os
import psycopg2
import psycopg2.extensions
import psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) 
import math
from datetime import date
from typing import Callable, Dict, List, Type, TypeVar

import Data.auth_public as auth
from Data.Modeli import *


DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

class Repo:

    def __init__(self):
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


    def izracunaj_tocke(self, podatki: PodatkiOTekmi) -> int:
        '''Funkcija na podlagi igralčeve statistike izračuna, koliko fantasy točk si je prislužil.
        Igralec dobi točko za vsako skok in asistenco, dve točki za vsako ukradeno žogo ali blok,
        minus dve točki za vsako izgubljeno žogo.
        Poleg tega dobi točke na podlagi tega, koliko točk je prinesel ekipi, vendar skalirano glede na odstotek meta iz igre.
        Dodatno dobi pet točk bonusa, če je njegova ekipa zmagala.'''
        tocke = 5 * podatki.izid + podatki.tocke * (0.2 + podatki.odstotek_meta) + podatki.skoki + podatki.podaje + 2 * podatki.bloki + 2 * podatki.ukradene - 2 * podatki.izgubljene
        return math.floor(tocke)


