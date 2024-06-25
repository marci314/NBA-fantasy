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
    """
    Dekorator, ki zahteva veljaven piškotek. Če piškotka ni, uporabnika preusmeri na stran za prijavo.
    """
    @wraps(f)
    def decorated( *args, **kwargs):
        cookie = request.get_cookie("uporabnik")
        if cookie:
            return f(*args, **kwargs)
        return template('prijava.html', uporabnik=None, napaka="Potrebna je prijava!")
    return decorated

@app.get('/')
def domaca_stran():
    return template('domaca_stran.html')

@route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='Presentation/static')

@get('/prijava') 
def prijava_get():
    return template("prijava.html")

# Prijavna stran POST
@post('/prijava')
def prijava_post():
    uporabnisko_ime = request.forms.get('uporabnisko_ime')
    geslo = request.forms.get('geslo')

    user = auth_service.prijavi_uporabnika(uporabnisko_ime, geslo)

    if isinstance(user, UporabnikDTO):
        response.set_cookie("uporabnisko_ime", uporabnisko_ime, path="/")
        return redirect('/homescreen')
    else:
        return template('prijava.html', napaka="Nepravilno uporabniško ime ali geslo!")
# Odjava
@get('/odjava')
def odjava():
    response.delete_cookie("uporabnisko_ime")
    return redirect('/')

@get('/registracija')
def registracija_get():
    return template('registracija.html')

# Registracijska stran POST
@post('/registracija')
def registracija_post():
    uporabnisko_ime = request.forms.get('username')
    geslo = request.forms.get('password')
    teamname = request.forms.get('teamname')

    if auth_service.ali_obstaja_uporabnik(uporabnisko_ime):
        return template('registracija.html', napaka="Uporabniško ime že obstaja.")
    
    try:
        auth_service.dodaj_uporabnika(uporabnisko_ime, geslo)
        user_id = cur.fetchone()[0]
        dodaj_ekipo_ob_registraciji(user_id, teamname)
        return redirect('/prijava')
    except Exception as e:
        return template('registracija.html', napaka=f"Napaka pri ustvarjanju računa: {str(e)}")

def dodaj_ekipo_ob_registraciji(user_id, teamname):
    tocke = 0
    cur.execute("INSERT INTO fantasy_ekipa (tocke, lastnik, ime_ekipe) VALUES (%s, %s, %s)", (tocke, user_id, teamname))
    conn.commit()

@app.get('/homescreen')
@cookie_required
def domov():
    user_id = request.get_cookie("user_id", secret='tvoja_tajna_kljuc')
    if not user_id:
        return redirect('/domaca_stran')
    
    cur.execute("""
        SELECT igralec.igralec_id, igralec.ime, igralec.priimek, igralec.pozicija, igralec.visina, igralec.datum_rojstva
        FROM igralec
        JOIN fantasy_ekipa_igralci ON igralec.igralec_id = fantasy_ekipa_igralci.igralec_id
        JOIN fantasy_ekipa ON fantasy_ekipa.f_ekipa_id = fantasy_ekipa_igralci.f_ekipa_id
        WHERE fantasy_ekipa.lastnik = %s
    """, (user_id,))
    players = cur.fetchall()

    cur.execute("""
        SELECT trener.trener_id, trener.ime, trener.rojstvo
        FROM trener
        JOIN fantasy_ekipa_trener ON trener.trener_id = fantasy_ekipa_trener.trener_id
        JOIN fantasy_ekipa ON fantasy_ekipa.f_ekipa_id = fantasy_ekipa_trener.f_ekipa_id
        WHERE fantasy_ekipa.lastnik = %s
    """, (user_id,))
    coach = cur.fetchone()

    return template('homescreen.html', players=players, coach=coach)



if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)


@route('/izberi_datum', method=['GET', 'POST'])
def izberi_datum():
    if request.method == 'POST':
        izbrani_datum = request.forms.get('datum')
        izbrani_datum = datetime.datetime.strptime(izbrani_datum, '%Y-%m-%d').date()
        
        # Uporabi funkcijo odigraj_teden iz instance db
        rezultat = repo.odigraj_teden(izbrani_datum)
        
        return template('odigrane_tekme', rezultat=rezultat)
    
    return template('izberi_datum_form')

# HTML predloga za obrazec za izbiro datuma
@route('/izberi_datum_form')
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