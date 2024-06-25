from Data.database import Repo
from Data.Modeli import *
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
            user = self.repo.dobi_uporabnika(uporabnik)
            return True
        except:
            return False
        
    def prijavi_uporabnika(self, uporabnik: str, geslo: str) -> Union[UporabnikDTO, bool]:
        """
        Prijavi uporabnika z preverjanjem gesla in posodobi čas zadnje prijave.
        """
        # Najprej dobimo uporabnika iz baze
        user = self.repo.dobi_uporabnika(uporabnik)
    
        # Če uporabnik ne obstaja, vrni False
        if not user:
            return False
    
        geslo_bytes = geslo.encode('utf-8')
    
        # Preverimo hash iz gesla, ki ga je vnesel uporabnik
        succ = bcrypt.checkpw(geslo_bytes, user.password_hash.encode('utf-8'))
    
        if succ:
            # Posodobimo last login time
            user.last_login = date.today().isoformat()
            self.repo.posodobi_uporabnika(user)
    
            # Vrni DTO za uporabnika brez role
            return UporabnikDTO(username=user.uporabnisko_ime)
        
        return False     


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
            last_login=date.today().isoformat()  # Nastavimo trenutni datum kot last_login
        )
    
        # Dodamo uporabnika v bazo
        self.repo.dodaj_uporabnika(u)
    
        # Vrne DTO za uporabnika
        return UporabnikDTO(username=uporabnik)   

    def klice_uporabnika(self, username: str) -> Uporabnik:
        return self.repo.klice_uporabnika(username)
    
    








