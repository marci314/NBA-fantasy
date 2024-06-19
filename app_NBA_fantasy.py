from Presentation.bottleext import *
import psycopg2, psycopg2.extras
import os
from functools import wraps
from Services.auth_service import AuthService
from Data.database import *
from Data.auth_public import host, dbname, user, password
import hashlib


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

@route('/')
def domaca_stran():
    return template('domaca_stran')

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
        return redirect('/home')
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

    if auth_service.ali_obstaja_uporabnik(uporabnisko_ime):
        return template('registracija.html', napaka="Uporabniško ime že obstaja.")
    
    try:
        auth_service.dodaj_uporabnika(uporabnisko_ime, geslo)
        return redirect('/prijava')
    except Exception as e:
        return template('registracija.html', napaka=f"Napaka pri ustvarjanju računa: {str(e)}")

# Domov - prikaz igralcev
@route('/home')
@cookie_required
def home():
    cur.execute("""
        SELECT igralec_id, ime, priimek, pozicija, visina, rojstvo 
        FROM igralec
    """)
    players = cur.fetchall()
    return template('homescreen.html', players=players)

# Moja ekipa - prikaz ekipe
@route('/moja_ekipa/<ime_ekipe>')
@cookie_required
def moja_ekipa(ime_ekipe):
    ekipa = repo.pokazi_ekipo(ime_ekipe)
    if not ekipa:
        return "Ekipa ni najdena."
    return template('moja_ekipa.html', ekipa=ekipa)

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

