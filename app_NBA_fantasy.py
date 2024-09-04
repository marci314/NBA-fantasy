import hashlib
import os
from functools import wraps
from typing import Dict, List, Union

import psycopg2
import psycopg2.extras

from Data.auth_public import dbname, host, password, user
from Data.database import *
from Presentation.bottleext import *
from Services.auth_service import AuthService

SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)

TEMPLATE_PATH.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'Presentation/views')))


repo = Repo()
auth_service = AuthService()

def password_hash(s):
    h = hashlib.sha512()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def cookie_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        uporabnisko_ime = request.get_cookie("uporabnisko_ime")
        if uporabnisko_ime:
            return f(*args, **kwargs)
        return redirect(url('prijava_get'))
    return decorated

#--------------------------DOMACA STRAN------------------------------------------------------------------------
@get('/')
def domaca_stran():
    return template('domaca_stran.html')

@route('/static/<filename:path>')
def static_files(filename):
    return static_file(filename, root='Presentation/static/Images')

@get('/prijava')
def prijava_get():
    return template("prijava.html", napaka="")

@post('/prijava')
def prijava_post():
    uporabnisko_ime = request.forms.get('username')
    geslo = request.forms.get('password')
    
    if not uporabnisko_ime or not geslo:
        return template("prijava.html", napaka="Uporabniško ime in geslo sta obvezna.")
    
    user = auth_service.prijavi_uporabnika(uporabnisko_ime, geslo)

    if user is None:
        return template('prijava.html', napaka="Nepravilno uporabniško ime ali geslo.")

    response.set_cookie("uporabnisko_ime", uporabnisko_ime, path="/")
    return redirect(url('domov'))

@get('/odjava')
def odjava():
    response.delete_cookie("uporabnisko_ime")
    return redirect(url('domaca_stran'))

@get('/registracija')
def registracija_get():
    return template('registracija.html', napaka="")

@post('/registracija')
def registracija_post():
    uporabnisko_ime = request.forms.get('username')
    geslo = request.forms.get('password')
    teamname = request.forms.get('teamname')

    try:
        if auth_service.ali_obstaja_uporabnik(uporabnisko_ime):
            return template('registracija.html', napaka="Uporabniško ime že obstaja.")
        
        user_dto = auth_service.dodaj_uporabnika(uporabnisko_ime, geslo)
        dodaj_ekipo_ob_registraciji(user_dto.uporabnik_id, teamname)
        return redirect(url('prijava_get'))
    except Exception as e:
        return template('prijava.html', napaka=f"Račun je ustvarjen, prijavite se!")

def dodaj_ekipo_ob_registraciji(user_id, teamname):
    auth_service.connect()
    tocke = 0
    cur = auth_service.cur
    try:
        repo.cur.execute("INSERT INTO fantasy_ekipa (tocke, lastnik, ime_ekipe) VALUES (%s, %s, %s)", (tocke, user_id, teamname))
        auth_service.conn.commit()
    except Exception as e:
        auth_service.conn.rollback()
        raise e

@get('/homescreen')
@cookie_required
def domov():
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    user = auth_service.klice_uporabnika(uporabnisko_ime)

    cur = auth_service.cur

    repo.cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.pozicija, igralec.visina, igralec.rojstvo, igralci_ekipe.id_ekipa
        FROM igralec
        JOIN fantasy_ekipa_igralci ON igralec.igralec_id = fantasy_ekipa_igralci.igralec_id
        JOIN fantasy_ekipa ON fantasy_ekipa.f_ekipa_id = fantasy_ekipa_igralci.f_ekipa_id
        LEFT JOIN igralci_ekipe ON igralci_ekipe.id_igralca = igralec.igralec_id
        WHERE fantasy_ekipa.lastnik = %s
    """, (user.uporabnik_id,))
    players = repo.cur.fetchall()

    repo.cur.execute("""
        SELECT trener.trener_id, trener.ime, trener.rojstvo, trenerji_ekipe.ekipa_id
        FROM trener
        LEFT JOIN fantasy_ekipa_trener ON trener.trener_id = fantasy_ekipa_trener.trener_id
        JOIN fantasy_ekipa ON fantasy_ekipa.f_ekipa_id = fantasy_ekipa_trener.f_ekipa_id
        LEFT JOIN trenerji_ekipe ON trenerji_ekipe.trener_id = trener.trener_id
        WHERE fantasy_ekipa.lastnik = %s
    """, (user.uporabnik_id,))
    coach = repo.cur.fetchone()

    if not players:
        players = []
    if not coach:
        coach = None

    return template('homescreen.html', players=players, coach=coach)

@post('/odstrani_igralca/<player_id>')
@cookie_required
def odstrani_igralca(player_id):
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    user = auth_service.klice_uporabnika(uporabnisko_ime)
    cur = auth_service.cur

    repo.cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user.uporabnik_id,))
    f_ekipa_id = repo.cur.fetchone()[0]

    repo.odstrani_igralca_iz_fantasy_ekipe(f_ekipa_id, player_id)
    return redirect(url('domov'))

@get('/odstrani_trenerja/<coach_id>')
@cookie_required
def odstrani_trenerja(coach_id):
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    user = auth_service.klice_uporabnika(uporabnisko_ime)
    cur = auth_service.cur

    repo.cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user.uporabnik_id,))
    f_ekipa_id = repo.cur.fetchone()[0]

    repo.odstrani_trenerja_iz_fantasy_ekipe(f_ekipa_id, coach_id)
    return redirect(url('domov'))

@get('/lestvica')
@cookie_required
def prikazi_lestvico():
    cur = auth_service.cur

    repo.cur.execute("""
        SELECT f_ekipa_id, ime_ekipe, tocke
        FROM fantasy_ekipa
        ORDER BY tocke DESC
    """)
    teams = repo.cur.fetchall()

    return template('lestvica.html', teams=list(enumerate(teams, start=1)))


@get('/spreminjaj_igralce')
def spreminjaj_igralce():
    repo.cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.pozicija, igralec.visina, igralec.rojstvo, COALESCE(igralci_ekipe.id_ekipa, 'Ni igral v tem časovnem oknu') AS id_ekipa
        FROM igralec
        LEFT JOIN igralci_ekipe ON igralci_ekipe.id_igralca = igralec.igralec_id
        LEFT JOIN ekipa ON ekipa.ekipa_id = igralci_ekipe.id_ekipa
    """)
    players = repo.cur.fetchall()
    return template('spreminjaj_igralce.html', players=players, error=None)

@post('/dodaj_igralca/<player_id>')
def dodaj_igralca(player_id):
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    if not uporabnisko_ime:
        return redirect(url('prijava_get'))

    if not player_id:
        players = repo.get_all_players()
        return template('spreminjaj_igralce.html', players=players, error="Prosim izberi igralca.")


    user = auth_service.klice_uporabnika(uporabnisko_ime)

    with auth_service.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        repo.cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user.uporabnik_id,))
        f_ekipa_id = repo.cur.fetchone()[0]

        cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.pozicija, igralec.visina, igralec.rojstvo, 
               COALESCE(ekipa.ekipa_ime, 'Ni ekipe') AS ekipa_ime
        FROM igralec
        LEFT JOIN igralci_ekipe ON igralci_ekipe.id_igralca = igralec.igralec_id
        LEFT JOIN ekipa ON ekipa.ekipa_id = igralci_ekipe.id_ekipa
        """)
        players = cur.fetchall()


    if not player_id:
        return template('spreminjaj_igralce.html', players=players, error="Prosim izberi igralca.")

    rezultat = repo.dodaj_igralca_v_fantasy_ekipo(f_ekipa_id, player_id)

    repo.cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.pozicija, igralec.visina, igralec.rojstvo, COALESCE(igralci_ekipe.id_ekipa, 'Ni ekipe') AS id_ekipa
        FROM igralec
        LEFT JOIN igralci_ekipe ON igralci_ekipe.id_igralca = igralec.igralec_id
    """)
    players = repo.cur.fetchall()


    if "Ekipa ima že 5 igralcev." in rezultat or "Igralec je že v ekipi." in rezultat:
        return template('spreminjaj_igralce.html', players=players, error=rezultat)  
    return redirect(url('spreminjaj_igralce'))


@get('/spreminjaj_trenerja')
def spreminjaj_trenerja():
    repo.cur.execute("""
        SELECT trener.trener_id, trener.ime, trener.rojstvo, COALESCE(trenerji_ekipe.ekipa_id, 'Ni ekipe') AS ekipa_id
        FROM trener
        LEFT JOIN trenerji_ekipe ON trenerji_ekipe.trener_id = trener.trener_id
    """)
    coaches = repo.cur.fetchall()
    return template('spreminjaj_trenerja.html', coaches=coaches, error=None)

@post('/dodaj_trenerja/<coach_id>')
def dodaj_trenerja(coach_id):
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    if not uporabnisko_ime:
        return redirect(url('prijava_get'))
    
    user = auth_service.klice_uporabnika(uporabnisko_ime)
    repo.cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user.uporabnik_id,))
    f_ekipa_id = repo.cur.fetchone()[0]
    
    rezultat = repo.dodaj_trenerja_v_fantasy_ekipo(f_ekipa_id, coach_id)
    
    if "Ekipa že ima trenerja." in rezultat:
        repo.cur.execute("""
            SELECT trener.trener_id, trener.ime, trener.rojstvo, COALESCE(trenerji_ekipe.ekipa_id, 'Ni ekipe') AS ekipa_id
            FROM trener
            LEFT JOIN trenerji_ekipe ON trenerji_ekipe.trener_id = trener.trener_id
        """)
        coaches = repo.cur.fetchall()
        return template('spreminjaj_trenerja.html', coaches=coaches, error=rezultat)  
    
    return redirect(url('spreminjaj_trenerja'))


@get('/ekipa/<ekipa_id>')
def prikazi_ekipo(ekipa_id):
    cur = auth_service.cur

    error = None

    repo.cur.execute("""
        SELECT ime_ekipe, tocke
        FROM fantasy_ekipa
        WHERE f_ekipa_id = %s
    """, (ekipa_id,))
    team = repo.cur.fetchone()

    if not team:
        error = "Ekipa ne obstaja."
        return template('ekipa.html', team=None, players=[], coach=None, error=error)

    repo.cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.pozicija, igralec.visina, igralec.rojstvo
        FROM igralec
        JOIN fantasy_ekipa_igralci ON igralec.igralec_id = fantasy_ekipa_igralci.igralec_id
        WHERE fantasy_ekipa_igralci.f_ekipa_id = %s
    """, (ekipa_id,))
    players = repo.cur.fetchall()

    repo.cur.execute("""
        SELECT trener.trener_id, trener.ime, trener.rojstvo
        FROM trener
        JOIN fantasy_ekipa_trener ON trener.trener_id = fantasy_ekipa_trener.trener_id
        WHERE fantasy_ekipa_trener.f_ekipa_id = %s
    """, (ekipa_id,))
    coach = repo.cur.fetchone()

    return template('ekipa.html', team=team, players=players, coach=coach, error=error)

@get('/spored_tekem')
def spored_tekem():
    repo.cur.execute("SELECT id_tekma, domaca_ekipa, gostujoca_ekipa, datum FROM tekma")
    matches = repo.cur.fetchall()
    return template('spored_tekem.html', matches=matches)

@get('/tekma/<id_tekma>')
def prikazi_tekmo(id_tekma):
    try:
        repo.cur.execute("""
            SELECT domaca_ekipa, gostujoca_ekipa
            FROM tekma
            WHERE id_tekma = %s
        """, (id_tekma,))
        tekma = repo.cur.fetchone()

        domaca_ekipa = tekma[0]
        gostujoca_ekipa = tekma[1]

        repo.cur.execute("""
            SELECT i.igralec_id, i.ime, i.pozicija, i.visina, i.rojstvo
            FROM igralec i
            JOIN igralci_ekipe ie ON i.igralec_id = ie.id_igralca
            WHERE ie.id_ekipa = %s
        """, (domaca_ekipa,))
        domaci_igralci = repo.cur.fetchall()

        repo.cur.execute("""
            SELECT tr.trener_id, tr.ime, tr.rojstvo
            FROM trener tr
            JOIN trenerji_ekipe te ON tr.trener_id = te.trener_id
            WHERE te.ekipa_id = %s
        """, (domaca_ekipa,))
        domaci_trener = repo.cur.fetchone()

        repo.cur.execute("""
            SELECT i.igralec_id, i.ime, i.pozicija, i.visina, i.rojstvo
            FROM igralec i
            JOIN igralci_ekipe ie ON i.igralec_id = ie.id_igralca
            WHERE ie.id_ekipa = %s
        """, (gostujoca_ekipa,))
        gostujoci_igralci = repo.cur.fetchall()

        repo.cur.execute("""
            SELECT tr.trener_id, tr.ime, tr.rojstvo
            FROM trener tr
            JOIN trenerji_ekipe te ON tr.trener_id = te.trener_id
            WHERE te.ekipa_id = %s
        """, (gostujoca_ekipa,))
        gostujoci_trener = repo.cur.fetchone()

        return template('tekma.html',
                        domaci_igralci=domaci_igralci,
                        domaci_trener=domaci_trener,
                        gostujoci_igralci=gostujoci_igralci,
                        gostujoci_trener=gostujoci_trener,
                        error=None)

    except Exception as e:
        return template('tekma.html',
                        domaci_igralci=[],
                        domaci_trener=None,
                        gostujoci_igralci=[],
                        gostujoci_trener=None,
                        error=str(e))

@get('/simuliraj_tekme')
def prikazi_izbor_tekem():
    try:
        repo.cur.execute("SELECT DISTINCT datum FROM tekma ORDER BY datum ASC")
        dates = repo.cur.fetchall()
        dates = [row[0] for row in dates] 
        return template('izberi_okno.html', dates=dates, error=None)  
    except Exception as e:
        return template('izberi_okno.html', dates=[], error=str(e))  


def pridobi_tekme_v_casovnem_oknu(conn, zacetni_datum, koncni_datum):
    with conn.cursor() as cur:
        repo.cur.execute("""
            SELECT id_tekma 
            FROM tekma 
            WHERE datum BETWEEN %s AND %s
        """, (zacetni_datum, koncni_datum))
        tekme = repo.cur.fetchall()
    return [tekma[0] for tekma in tekme]  


def pridobi_podatke_o_tekmi(conn, id_tekem):
    with conn.cursor() as cur:
        repo.cur.execute("""
            SELECT * 
            FROM podatki_o_tekmi 
            WHERE id_tekme = ANY(%s)
        """, (id_tekem,))
        podatki = repo.cur.fetchall()
    return podatki


def posodobi_tocke_za_fantasy_ekipe(conn, id_tekem, cur):

    repo.cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa")
    ekipe = repo.cur.fetchall()

    for ekipa in ekipe:
        f_ekipa_id = ekipa[0]

        repo.cur.execute("""
            SELECT igralec_id 
            FROM fantasy_ekipa_igralci 
            WHERE f_ekipa_id = %s
        """, (f_ekipa_id,))
        igralci = repo.cur.fetchall()

        if not igralci:
            continue
        
        skupne_tocke = 0
        
        repo.cur.execute("""
            SELECT * 
            FROM podatki_o_tekmi 
            WHERE id_igralca = ANY(%s) 
            AND id_tekme = ANY(%s)
        """, ([igralec[0] for igralec in igralci], id_tekem))
        podatki_o_tekmi = repo.cur.fetchall()
        
        for podatki in podatki_o_tekmi:
            tocke = izracunaj_tocke(podatki)
            skupne_tocke += tocke
        
        repo.cur.execute("""
            UPDATE fantasy_ekipa 
            SET tocke = tocke + %s 
            WHERE f_ekipa_id = %s
        """, (skupne_tocke, f_ekipa_id))


def simuliraj_tekme(conn, zacetni_datum, koncni_datum):
    """
    Simulira tekme v izbranem časovnem oknu in posodobi točke za fantasy ekipe.
    """
    with conn.cursor() as cur:
        repo.cur.execute("""
            SELECT id_tekma 
            FROM tekma 
            WHERE datum BETWEEN %s AND %s
        """, (zacetni_datum, koncni_datum))
        id_tekem = [row[0] for row in repo.cur.fetchall()]

        if not id_tekem:
            raise Exception("V izbranem časovnem oknu ni tekem.")

        posodobi_tocke_za_fantasy_ekipe(conn, id_tekem, cur)

        conn.commit()

def izracunaj_tocke(podatki):
    """
    Izračuna fantasy točke za enega igralca na podlagi podatkov o tekmi.
    Predvideva, da je 'podatki' tuple, zato se do elementov dostopa prek indeksov.
    """
    tocke = (5 * podatki[10] +  
             podatki[8] * (0.2 + podatki[2]) +  
             podatki[6] +  
             podatki[7] +  
             2 * podatki[4] +  
             2 * podatki[3] -  
             2 * podatki[5])  
    return math.floor(tocke)


@post('/simuliraj_tekme')
def simuliraj_tekme_route():
    zacetni_datum = request.forms.get('start_date')
    koncni_datum = request.forms.get('end_date')
    
    repo.cur.execute("SELECT DISTINCT datum FROM tekma ORDER BY datum ASC")
    dates = repo.cur.fetchall()
    dates = [row[0] for row in dates]

    if not zacetni_datum or not koncni_datum:
        return template('izberi_okno.html', error="Prosim izberi datume.", dates=dates)
    
    if koncni_datum < zacetni_datum:
        return template('izberi_okno.html', error="Končni datum mora biti enak ali večji od začetnega datuma.", dates=dates)
    
    try:
        simuliraj_tekme(repo.conn, zacetni_datum, koncni_datum)
        return redirect(url('domov'))
    except Exception as e:
        return template('izberi_okno.html', error=str(e), dates=dates)
    
@get('/ponastavi_tocke')
def ponastavi_tocke():
    try:
        repo.cur.execute("UPDATE fantasy_ekipa SET tocke = 0")
        repo.conn.commit()
    except Exception:
        pass
    return redirect(url('prikazi_lestvico')) 

@get('/pravila')
def pravila():
    return template('pravila.html')

if __name__ == '__main__':
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER)
