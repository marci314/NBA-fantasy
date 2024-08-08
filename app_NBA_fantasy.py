from Presentation.bottleext import *
import psycopg2, psycopg2.extras
import os
from functools import wraps
from Services.auth_service import AuthService
from Data.database import *
from Data.auth_public import host, dbname, user, password
import hashlib
from typing import List, Dict, Union

TEMPLATE_PATH.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'Presentation/views')))

# Inicializacija aplikacije in povezave z bazo
app = Bottle()

# Povezava z bazo podatkov
conn = psycopg2.connect(
    database=dbname,
    host=host,
    user=user,
    password=password
)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
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
        return redirect('/prijava')
    return decorated

#--------------------------DOMACA STRAN------------------------------------------------------------------------
@app.get('/')
def domaca_stran():
    return template('domaca_stran.html')


@app.route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='Presentation/static')

@app.get('/prijava')
def prijava_get():
    return template("prijava.html", napaka="")

@app.post('/prijava')
def prijava_post():
    uporabnisko_ime = request.forms.get('username')
    geslo = request.forms.get('password')
    
    if not uporabnisko_ime or not geslo:
        return template("prijava.html", napaka="Uporabniško ime in geslo sta obvezna.")
    
    user = auth_service.prijavi_uporabnika(uporabnisko_ime, geslo)

    if user is None:
        return template('prijava.html', napaka="Nepravilno uporabniško ime ali geslo.")

    response.set_cookie("uporabnisko_ime", uporabnisko_ime, path="/")
    return redirect('/homescreen')

@app.get('/odjava')
def odjava():
    response.delete_cookie("uporabnisko_ime")
    return redirect('/')

@app.get('/registracija')
def registracija_get():
    return template('registracija.html', napaka="")

@app.post('/registracija')
def registracija_post():
    uporabnisko_ime = request.forms.get('username')
    geslo = request.forms.get('password')
    teamname = request.forms.get('teamname')

    try:
        if auth_service.ali_obstaja_uporabnik(uporabnisko_ime):
            return template('registracija.html', napaka="Uporabniško ime že obstaja.")
        
        user_dto = auth_service.dodaj_uporabnika(uporabnisko_ime, geslo)
        dodaj_ekipo_ob_registraciji(user_dto.uporabnik_id, teamname)
        return redirect('/prijava')
    except Exception as e:
        return template('prijava.html', napaka=f"Račun je ustvarjen, prijavite se!")

def dodaj_ekipo_ob_registraciji(user_id, teamname):
    auth_service.connect()
    tocke = 0
    cur = auth_service.cur
    try:
        cur.execute("INSERT INTO fantasy_ekipa (tocke, lastnik, ime_ekipe) VALUES (%s, %s, %s)", (tocke, user_id, teamname))
        auth_service.conn.commit()
    except Exception as e:
        auth_service.conn.rollback()
        raise e

@app.get('/homescreen')
@cookie_required
def domov():
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    user = auth_service.klice_uporabnika(uporabnisko_ime)

    cur = auth_service.cur

    # Preveri igralce
    cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.pozicija, igralec.visina, igralec.rojstvo, igralci_ekipe.id_ekipa
        FROM igralec
        JOIN fantasy_ekipa_igralci ON igralec.igralec_id = fantasy_ekipa_igralci.igralec_id
        JOIN fantasy_ekipa ON fantasy_ekipa.f_ekipa_id = fantasy_ekipa_igralci.f_ekipa_id
        LEFT JOIN igralci_ekipe ON igralci_ekipe.id_igralca = igralec.igralec_id
        WHERE fantasy_ekipa.lastnik = %s
    """, (user.uporabnik_id,))
    players = cur.fetchall()

    # Preveri trenerja
    cur.execute("""
        SELECT trener.trener_id, trener.ime, trener.rojstvo, trenerji_ekipe.ekipa_id
        FROM trener
        LEFT JOIN fantasy_ekipa_trener ON trener.trener_id = fantasy_ekipa_trener.trener_id
        JOIN fantasy_ekipa ON fantasy_ekipa.f_ekipa_id = fantasy_ekipa_trener.f_ekipa_id
        LEFT JOIN trenerji_ekipe ON trenerji_ekipe.trener_id = trener.trener_id
        WHERE fantasy_ekipa.lastnik = %s
    """, (user.uporabnik_id,))
    coach = cur.fetchone()

    if not players:
        players = []
    if not coach:
        coach = None

    return template('homescreen.html', players=players, coach=coach)

@app.get('/odstrani_igralca/<player_id>')
@cookie_required
def odstrani_igralca(player_id):
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    user = auth_service.klice_uporabnika(uporabnisko_ime)
    cur = auth_service.cur

    cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user.uporabnik_id,))
    f_ekipa_id = cur.fetchone()[0]

    repo.odstrani_igralca_iz_fantasy_ekipe(f_ekipa_id, player_id)
    return redirect('/homescreen')

@app.get('/odstrani_trenerja/<coach_id>')
@cookie_required
def odstrani_trenerja(coach_id):
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    user = auth_service.klice_uporabnika(uporabnisko_ime)
    cur = auth_service.cur

    cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user.uporabnik_id,))
    f_ekipa_id = cur.fetchone()[0]

    repo.odstrani_trenerja_iz_fantasy_ekipe(f_ekipa_id, coach_id)
    return redirect('/homescreen')

@app.get('/lestvica')
@cookie_required
def prikazi_lestvico():
    cur = auth_service.cur

    cur.execute("""
        SELECT f_ekipa_id, ime_ekipe, tocke
        FROM fantasy_ekipa
        ORDER BY tocke DESC
    """)
    teams = cur.fetchall()

    return template('lestvica.html', teams=teams)


@app.route('/izberi_datum', method=['GET', 'POST'])
def izberi_datum():
    if request.method == 'POST':
        izbrani_datum = request.forms.get('datum')
        izbrani_datum = datetime.datetime.strptime(izbrani_datum, '%Y-%m-%d').date()
        
        rezultat = repo.odigraj_teden(izbrani_datum)
        
        return template('odigrane_tekme', rezultat=rezultat)
    
    return template('izberi_datum_form')

@app.get('/spreminjaj_igralce')
def spreminjaj_igralce():
    cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.pozicija, igralec.visina, igralec.rojstvo, COALESCE(igralci_ekipe.id_ekipa, 'Ni ekipe') AS id_ekipa
        FROM igralec
        LEFT JOIN igralci_ekipe ON igralci_ekipe.id_igralca = igralec.igralec_id
    """)
    players = cur.fetchall()
    return template('spreminjaj_igralce.html', players=players, error=None)


@app.post('/dodaj_igralca')
def dodaj_igralca():
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    if not uporabnisko_ime:
        return redirect('/prijava')

    player_id = request.forms.get('player')
    if not player_id:
        players = repo.get_all_players()
        return template('spreminjaj_igralce.html', players=players, error="Prosim izberi igralca.")

    user = auth_service.klice_uporabnika(uporabnisko_ime)
    with auth_service.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user.uporabnik_id,))
        f_ekipa_id = cur.fetchone()[0]

    rezultat = repo.dodaj_igralca_v_fantasy_ekipo(f_ekipa_id, player_id)
    players = repo.get_all_players()
    if "Ekipa ima že 5 igralcev." in rezultat or "Igralec je že v ekipi." in rezultat:
        return template('spreminjaj_igralce.html', players=players, error=rezultat)
    return redirect('/spreminjaj_igralce')

@app.get('/spreminjaj_trenerja')
def spreminjaj_trenerja():
    cur.execute("""
        SELECT trener.trener_id, trener.ime, trener.rojstvo, COALESCE(trenerji_ekipe.ekipa_id, 'Ni ekipe') AS ekipa_id
        FROM trener
        LEFT JOIN trenerji_ekipe ON trenerji_ekipe.trener_id = trener.trener_id
    """)
    coaches = cur.fetchall()
    return template('spreminjaj_trenerja.html', coaches=coaches, error=None)


@app.get('/dodaj_trenerja/<coach_id>')
def dodaj_trenerja(coach_id):
    uporabnisko_ime = request.get_cookie("uporabnisko_ime")
    if not uporabnisko_ime:
        return redirect('/prijava')
    
    user = auth_service.klice_uporabnika(uporabnisko_ime)
    cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user.uporabnik_id,))
    f_ekipa_id = cur.fetchone()[0]
    
    rezultat = repo.dodaj_trenerja_v_fantasy_ekipo(f_ekipa_id, coach_id)
    cur.execute("SELECT * FROM trener")
    coaches = cur.fetchall()
    if "Ekipa že ima trenerja." in rezultat:
        return template('spreminjaj_trenerja.html', coaches=coaches, error=rezultat)
    return redirect('/spreminjaj_trenerja')

@app.get('/ekipa/<ekipa_id>')
def prikazi_ekipo(ekipa_id):
    cur = auth_service.cur

    # Initialize error as None
    error = None

    # Pridobimo podatke o ekipi
    cur.execute("""
        SELECT ime_ekipe, tocke
        FROM fantasy_ekipa
        WHERE f_ekipa_id = %s
    """, (ekipa_id,))
    team = cur.fetchone()

    if not team:
        error = "Ekipa ne obstaja."
        return template('ekipa.html', team=None, players=[], coach=None, error=error)

    # Pridobimo igralce v ekipi
    cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.pozicija, igralec.visina, igralec.rojstvo
        FROM igralec
        JOIN fantasy_ekipa_igralci ON igralec.igralec_id = fantasy_ekipa_igralci.igralec_id
        WHERE fantasy_ekipa_igralci.f_ekipa_id = %s
    """, (ekipa_id,))
    players = cur.fetchall()

    # Pridobimo trenerja v ekipi
    cur.execute("""
        SELECT trener.trener_id, trener.ime, trener.rojstvo
        FROM trener
        JOIN fantasy_ekipa_trener ON trener.trener_id = fantasy_ekipa_trener.trener_id
        WHERE fantasy_ekipa_trener.f_ekipa_id = %s
    """, (ekipa_id,))
    coach = cur.fetchone()

    return template('ekipa.html', team=team, players=players, coach=coach, error=error)

@app.get('/spored_tekem')
def spored_tekem():
    cur.execute("SELECT id_tekma, domaca_ekipa, gostujoca_ekipa, datum FROM tekma")
    matches = cur.fetchall()
    return template('spored_tekem.html', matches=matches)

@app.get('/tekma/<id_tekma>')
def prikazi_tekmo(id_tekma):
    # Fetch home team players and coach
    cur.execute("""
        SELECT i.igralec_id, i.ime, i.priimek, i.pozicija, i.visina, i.rojstvo
        FROM igralec i
        JOIN fantasy_ekipa_igralci fei ON i.igralec_id = fei.igralec_id
        JOIN tekma t ON fei.f_ekipa_id = t.domaca_ekipa::integer
        WHERE t.id_tekma = %s
    """, (id_tekma,))
    domaci_igralci = cur.fetchall()

    cur.execute("""
        SELECT tr.trener_id, tr.ime, tr.rojstvo
        FROM trener tr
        JOIN fantasy_ekipa_trener fet ON tr.trener_id = fet.trener_id
        JOIN tekma t ON fet.f_ekipa_id = t.domaca_ekipa::integer
        WHERE t.id_tekma = %s
    """, (id_tekma,))
    domaci_trener = cur.fetchone()

    # Fetch away team players and coach
    cur.execute("""
        SELECT i.igralec_id, i.ime, i.priimek, i.pozicija, i.visina, i.rojstvo
        FROM igralec i
        JOIN fantasy_ekipa_igralci fei ON i.igralec_id = fei.igralec_id
        JOIN tekma t ON fei.f_ekipa_id = t.gostujoca_ekipa::integer
        WHERE t.id_tekma = %s
    """, (id_tekma,))
    gostujoci_igralci = cur.fetchall()

    cur.execute("""
        SELECT tr.trener_id, tr.ime, tr.rojstvo
        FROM trener tr
        JOIN fantasy_ekipa_trener fet ON tr.trener_id = fet.trener_id
        JOIN tekma t ON fet.f_ekipa_id = t.gostujoca_ekipa::integer
        WHERE t.id_tekma = %s
    """, (id_tekma,))
    gostujoci_trener = cur.fetchone()

    return template('tekma.html', 
                    domaci_igralci=domaci_igralci, 
                    domaci_trener=domaci_trener, 
                    gostujoci_igralci=gostujoci_igralci, 
                    gostujoci_trener=gostujoci_trener)

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)
