import os
from datetime import date
from typing import Union

import bcrypt
import psycopg2
import psycopg2.extras

from Data.auth_public import dbname, host, password, user
from Data.Modeli import Uporabnik, UporabnikDTO

DB_PORT = os.environ.get('POSTGRES_PORT', 5432)


class AuthService:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.connect()

    def connect(self):
        if not self.conn or self.conn.closed != 0:
            self.conn = psycopg2.connect(
                database=dbname,
                host=host,
                user=user,
                password=password,
                port = DB_PORT
            )
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def ali_obstaja_uporabnik(self, uporabnik: str) -> bool:
        self.connect()
        user = self.klice_uporabnika(uporabnik)
        return user is not None

    def prijavi_uporabnika(self, uporabnisko_ime: str, geslo: str) -> Union[UporabnikDTO, None]:
        self.connect()
        uporabnik = self.klice_uporabnika(uporabnisko_ime)
        if uporabnik is None:
            return None

        geslo_bytes = geslo.encode('utf-8')
        if self.preveri_geslo(uporabnik.geslo, geslo_bytes):
            uporabnik.last_login = date.today().isoformat()
            self.posodobi_uporabnika(uporabnik)
            return UporabnikDTO(
                uporabnik_id=uporabnik.uporabnik_id,
                uporabnisko_ime=uporabnik.uporabnisko_ime,
                last_login=uporabnik.last_login
            )
        else:
            return None

    def preveri_geslo(self, hashed: str, geslo: bytes) -> bool:
        return bcrypt.checkpw(geslo, hashed.encode('utf-8'))

    def dodaj_uporabnika(self, uporabnik: str, geslo: str) -> UporabnikDTO:
        self.connect()
        bytes = geslo.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(bytes, salt)

        u = Uporabnik(
            uporabnisko_ime=uporabnik,
            geslo=password_hash.decode(),
            last_login=date.today().isoformat()
        )
        self.cur.execute("""
            INSERT INTO uporabnik (uporabnisko_ime, geslo, last_login)
            VALUES (%s, %s, %s) RETURNING uporabnik_id
        """, (u.uporabnisko_ime, u.geslo, u.last_login))
        u.uporabnik_id = self.cur.fetchone()[0]
        self.conn.commit()
        return UporabnikDTO(
            uporabnik_id=u.uporabnik_id,
            uporabnisko_ime=u.uporabnisko_ime,
            last_login=u.last_login
        )

    def klice_uporabnika(self, username: str) -> Union[Uporabnik, None]:
        self.connect()
        self.cur.execute("""
            SELECT uporabnik_id, uporabnisko_ime, geslo, last_login
            FROM uporabnik
            WHERE uporabnisko_ime = %s
        """, (username,))
        user_data = self.cur.fetchone()
        if user_data:
            return Uporabnik(
                uporabnik_id=user_data['uporabnik_id'],
                uporabnisko_ime=user_data['uporabnisko_ime'],
                geslo=user_data['geslo'],
                last_login=user_data['last_login']
            )
        else:
            return None

    def posodobi_uporabnika(self, uporabnik: Uporabnik):
        self.connect()
        self.cur.execute("""
            UPDATE uporabnik SET last_login = %s WHERE uporabnisko_ime = %s
        """, (uporabnik.last_login, uporabnik.uporabnisko_ime))
        self.conn.commit()
