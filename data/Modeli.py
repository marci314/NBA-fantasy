from dataclasses import dataclass, field
from datetime import date
from typing import Optional

@dataclass
class Uporabnik:
    uporabnik_id: int = field(default=0)
    uporabnisko_ime: str = field(default="")
    geslo: str = field(default="")

@dataclass
class FantasyEkipa:
    f_ekipa_id: int = field(default=0)
    tocke: int = field(default=0)
    lastnik: int = field(default=0)
    ime_ekipe: str = field(default="")

@dataclass
class Igralec:
    igralec_id: str = field(default="")
    ime: str = field(default="")
    priimek: str = field(default="")
    pozicija: Optional[str] = field(default="")
    visina: int = field(default=0)
    rojstvo: date = field(default=None)

@dataclass
class Trener:
    trener_id: str = field(default="")
    ime: str = field(default="")
    priimek: str = field(default="")
    rojstvo: date = field(default=None)

@dataclass
class Ekipa:
    ekipa_id: int = field(default=0)

@dataclass
class Tekma:
    id_tekma: int = field(default=0)
    domaca_ekipa: str = field(default="")
    gostujoca_ekipa: str = field(default="")
    datum: date = field(default=None)

@dataclass
class PodatkiOTekmi:
    id_igralca: str = field(default="")
    id_tekme: int = field(default=0)
    id_trenerja: str = field(default="")
    id_ekipa: int = field(default=0)
    odstotek_meta: Optional[float] = field(default=0.0)
    ukradene: int = field(default=0)
    bloki: int = field(default=0)
    izgubljene: int = field(default=0)
    skoki: int = field(default=0)
    podaje: int = field(default=0)
    odigrane_minute: int = field(default=0)
    tocke: int = field(default=0)
    izid: bool = field(default=False)
