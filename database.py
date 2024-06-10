from datetime import datetime as dt, timedelta
import psycopg2, psycopg2.extensions, psycopg2.extras
from typing import List, TypeVar, Type, Callable
from Data.Modeli import *    
from datetime import date
from Data.auth_public import auth_public

class Repo:

    def __init__(self):
        self.conn = psycopg2.connect(database=auth_public.db, host=auth_public.host, user=auth_public.user, password=auth_public.password, port=5432)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    
    def tabela_uporabnik(self) -> List[Uporabnik]:
        self.cur.execute("""
            SELECT * FROM uporabnik
        """)
        return [Uporabnik(uporabnik_id, uporabnisko_ime, geslo) for (uporabnik_id, uporabnisko_ime, geslo) in self.cur.fetchall()]

    def dodaj_uporabnika(self, uporabnik: Uporabnik) -> Uporabnik:
        # Preveri, ali uporabnik že obstaja v tabeli
        self.cur.execute("""
            SELECT * FROM uporabnik
            WHERE uporabnisko_ime = %s
            """, (uporabnik.uporabnisko_ime,))
        row = self.cur.fetchone()
        if row:
            uporabnik.uporabnik_id = row['uporabnik_id']
            return uporabnik
        
        # Vstavi novega uporabnika
        self.cur.execute("""
            INSERT INTO uporabnik (uporabnisko_ime, geslo)
            VALUES (%s, %s)
            RETURNING uporabnik_id
            """, (uporabnik.uporabnisko_ime, uporabnik.geslo))
        
        uporabnik.uporabnik_id = self.cur.fetchone()['uporabnik_id']
        self.conn.commit()
        return uporabnik

    def dodaj_igralca_v_fantasy_ekipo(self, f_ekipa_id: int, igralec_id: str) -> None:
         # Preveri, ali ima ekipa že 5 igralcev
        self.cur.execute("""
            SELECT COUNT(*) FROM fantasy_ekipa_igralci
            WHERE f_ekipa_id = %s
            """, (f_ekipa_id,))
        count = self.cur.fetchone()[0]
        if count >= 5:
            return "Ekipa ima že 5 igralcev."

        # Preveri, ali igralec že obstaja v ekipi
        self.cur.execute("""
            SELECT * FROM fantasy_ekipa_igralci
            WHERE f_ekipa_id = %s AND igralec_id = %s
            """, (f_ekipa_id, igralec_id))
        row = self.cur.fetchone()
        if row:
            print("Igralec je že v ekipi.")
            return

        # Dodaj igralca v fantazijsko ekipo
        self.cur.execute("""
            INSERT INTO fantasy_ekipa_igralci (f_ekipa_id, igralec_id)
            VALUES (%s, %s)
            """, (f_ekipa_id, igralec_id))
        self.conn.commit()
        print(f"Igralec {igralec_id} je bil dodan v ekipo {f_ekipa_id}.")

    def odstrani_igralca_iz_fantasy_ekipe(self, f_ekipa_id: int, igralec_id: str) -> None:
        # Odstrani igralca iz fantazijske ekipe
        self.cur.execute("""
            DELETE FROM fantasy_ekipa_igralci
            WHERE f_ekipa_id = %s AND igralec_id = %s
            """, (f_ekipa_id, igralec_id))
        self.conn.commit()
        print(f"Igralec {igralec_id} je bil odstranjen iz ekipe {f_ekipa_id}.")





    def dodaj_post(self, Post: Post) -> Post:
        self.cur.execute("""
            INSERT INTO post ("text")
             VALUES (%s); """, (Post.post))
        self.conn.commit()
        return Student