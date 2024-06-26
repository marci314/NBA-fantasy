from Presentation.bottleext import *
import psycopg2, psycopg2.extras
import os
from functools import wraps
from Services.auth_service import AuthService
from Data.database import *
from Data.auth_public import host, dbname, user, password
import hashlib

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
        return template("domaca_stran.html")
    return decorated

@app.get('/')
def domaca_stran():
    return template('domaca_stran.html')

@app.route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='Presentation/static')

@app.get('/prijava')
def prijava_get():
    return template("prijava.html", napaka="")

# Prijavna stran POST
@app.post('/prijava')
def prijava_post():
    uporabnisko_ime = request.forms.get('username')
    geslo = request.forms.get('password')
    
    if not uporabnisko_ime or not geslo:
        return template("prijava.html", napaka="Uporabniško ime in geslo sta obvezna.")
    
    user = auth_service.prijavi_uporabnika(uporabnisko_ime, geslo)

    if user == None:
        return template('prijava.html', napaka="Nepravilno uporabniško ime ali geslo.")

    response.set_cookie("uporabnisko_ime", uporabnisko_ime, path="/")
    return redirect('/homescreen')

# Odjava
@app.get('/odjava')
def odjava():
    response.delete_cookie("uporabnisko_ime")
    return template("domaca_stran.html")

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
    print(f"Uporabnik {uporabnisko_ime} dostopa do homescreen.")
    user = auth_service.klice_uporabnika(uporabnisko_ime)

    cur = auth_service.cur

    # Preveri igralce
    cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.priimek, igralec.pozicija, igralec.visina, igralec.rojstvo
        FROM igralec
        JOIN fantasy_ekipa_igralci ON igralec.igralec_id = fantasy_ekipa_igralci.igralec_id
        JOIN fantasy_ekipa ON fantasy_ekipa.f_ekipa_id = fantasy_ekipa_igralci.f_ekipa_id
        WHERE fantasy_ekipa.lastnik = %s
    """, (user.uporabnik_id,))
    players = cur.fetchall()

    # Preveri trenerja
    cur.execute("""
        SELECT trener.trener_id, trener.ime, trener.rojstvo
        FROM trener
        LEFT JOIN fantasy_ekipa_trener ON trener.trener_id = fantasy_ekipa_trener.trener_id
        JOIN fantasy_ekipa ON fantasy_ekipa.f_ekipa_id = fantasy_ekipa_trener.f_ekipa_id
        WHERE fantasy_ekipa.lastnik = %s
    """, (user.uporabnik_id,))
    coach = cur.fetchone()

    # Preveri, ali so podatki prazni
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

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)

@app.route('/izberi_datum', method=['GET', 'POST'])
def izberi_datum():
    if request.method == 'POST':
        izbrani_datum = request.forms.get('datum')
        izbrani_datum = datetime.datetime.strptime(izbrani_datum, '%Y-%m-%d').date()
        
        # Uporabi funkcijo odigraj_teden iz instance db
        rezultat = repo.odigraj_teden(izbrani_datum)
        
        return template('odigrane_tekme', rezultat=rezultat)
    
    return template('izberi_datum_form')

# HTML predloga za obrazec za izbiro datuma
@app.route('/izberi_datum_form')
def izberi_datum_form():
    return '''
        <form action="/izberi_datum" method="post">
            <label for="datum">Izberite datum:</label>
            <input type="date" id="datum" name="datum" required>
            <button type="submit">Izberi</button>
        </form>
    '''

@app.get('/spreminjaj_igralce')
def spreminjaj_igralce():
    cur.execute("SELECT * FROM igralec")
    players = cur.fetchall()
    return template('spreminjaj_igralce.html', players=players)

@app.get('/dodaj_igralca/<player_id>')
def dodaj_igralca(player_id):
    user_id = request.get_cookie("user_id", secret='tvoja_tajna_kljuc')
    if not user_id:
        return redirect('/prijava')
    
    cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user_id,))
    f_ekipa_id = cur.fetchone()[0]
    
    rezultat = dodaj_igralca_v_fantasy_ekipo(f_ekipa_id, player_id)
    return redirect('/domov')

def dodaj_igralca_v_fantasy_ekipo(f_ekipa_id, igralec_id):
    cur.execute("SELECT COUNT(*) FROM fantasy_ekipa_igralci WHERE f_ekipa_id = %s", (f_ekipa_id,))
    count = cur.fetchone()[0]
    if count >= 5:
        return "Ekipa ima že 5 igralcev."

    cur.execute("SELECT * FROM fantasy_ekipa_igralci WHERE f_ekipa_id = %s AND igralec_id = %s", (f_ekipa_id, igralec_id))
    row = cur.fetchone()
    if row:
        return "Igralec je že v ekipi."

    cur.execute("INSERT INTO fantasy_ekipa_igralci (f_ekipa_id, igralec_id) VALUES (%s, %s)", (f_ekipa_id, igralec_id))
    conn.commit()
    return f"Igralec {igralec_id} je bil dodan v ekipo {f_ekipa_id}."

@app.get('/spreminjaj_trenerja')
def spreminjaj_trenerja():
    cur.execute("SELECT * FROM trener")
    coaches = cur.fetchall()
    return template('spreminjaj_trenerja.html', coaches=coaches)

@app.get('/dodaj_trenerja/<coach_id>')
def dodaj_trenerja(coach_id):
    user_id = request.get_cookie("user_id", secret='tvoja_tajna_kljuc')
    if not user_id:
        return redirect('/prijava')
    
    cur.execute("SELECT f_ekipa_id FROM fantasy_ekipa WHERE lastnik = %s", (user_id,))
    f_ekipa_id = cur.fetchone()[0]
    
    rezultat = dodaj_trenerja_v_fantasy_ekipo(f_ekipa_id, coach_id)
    return redirect('/domov')

def dodaj_trenerja_v_fantasy_ekipo(f_ekipa_id, trener_id):
    cur.execute("SELECT COUNT(*) FROM fantasy_ekipa_trener WHERE f_ekipa_id = %s", (f_ekipa_id,))
    count = cur.fetchone()[0]
    if count >= 1:
        return "Ekipa že ima izbranega trenerja."

    cur.execute("INSERT INTO fantasy_ekipa_trener (f_ekipa_id, trener_id) VALUES (%s, %s)", (f_ekipa_id, trener_id))
    conn.commit()
    return f"Trener {trener_id} je bil dodan v ekipo {f_ekipa_id}."

@app.get('/lestvica')
def lestvica():
    cur.execute("SELECT f_ekipa_id, ime_ekipe, tocke FROM fantasy_ekipa ORDER BY tocke DESC")
    teams = cur.fetchall()
    return template('lestvica.html', teams=teams)

@app.get('/spored_tekem')
def spored_tekem():
    cur.execute("SELECT id_tekma, domaca_ekipa, gostujoca_ekipa, datum FROM tekma")
    matches = cur.fetchall()
    return template('spored_tekem.html', matches=matches)

@app.get('/domaca_stran')
def domaca_stran():
    return template('domaca_stran.html')

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)
