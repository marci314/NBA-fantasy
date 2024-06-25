from Data.database import Repo
from Data.Modeli import Uporabnik, UporabnikDTO
from typing import Union
import bcrypt
from datetime import date

class AuthService:
    repo : Repo
    def __init__(self):
        self.repo = Repo()

    def ali_obstaja_uporabnik(self, uporabnik: str) -> bool:
        '''
        Preveri, če obstaja uporabnik
        '''
        try:
            user = self.repo.klice_uporabnika(uporabnik)
            return True
        except:
            return False
        
    def prijavi_uporabnika(self, uporabnisko_ime: str, geslo: str) -> UporabnikDTO:
        uporabnik = self.repo.klice_uporabnika(uporabnisko_ime)
        if uporabnik is None:
            return None
    
        geslo_bytes = geslo.encode('utf-8')
        if self.preveri_geslo(uporabnik.geslo, geslo_bytes):
            uporabnik.last_login = date.today().isoformat()  # Posodobi last_login
            self.repo.posodobi_uporabnika(uporabnik)
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
        """
        Doda novega uporabnika v tabelo 'uporabnik' brez uporabe 'role'.
        """
        # Zgradimo hash za geslo uporabnika
        bytes = geslo.encode('utf-8')  # Zakodiramo geslo kot seznam bajtov
        salt = bcrypt.gensalt()  # Ustvarimo salt
        password_hash = bcrypt.hashpw(bytes, salt)  # Ustvarimo hash gesla
    
        # Sedaj ustvarimo objekt Uporabnik in ga zapišemo bazo
        u = Uporabnik(
            uporabnisko_ime=uporabnik,
            password_hash=password_hash.decode(),  # Dekodiramo hash gesla
            last_login=date.today()  # Nastavimo trenutni datum kot last_login
        )
    
        # Dodamo uporabnika v bazo
        self.repo.dodaj_uporabnika(u)
    
        # Vrne DTO za uporabnika
        return UporabnikDTO(username=uporabnik)   

    def klice_uporabnika(self, username: str) -> Uporabnik:
        return self.repo.klice_uporabnika(username)
    
    








