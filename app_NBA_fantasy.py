from bottle import Bottle, run, request, static_file, template, redirect
from bottleext import *
import psycopg2, psycopg2.extensions, psycopg2.extras
import hashlib
import Data.auth_public as auth_public
from functools import wraps
from Data.Modeli import *
from Data.Services import AuthService
from database import Repo
import os

repo = Repo()

SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)


conn = psycopg2.connect(database=auth_public.db, host=auth_public.host, user=auth_public.user, password=auth_public.password, port=DB_PORT)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 

def password_hash(s):
    h = hashlib.sha512()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

@get('/')
def osnovna_stran():
    return template('base_screen.html')

def cookie_required(f):
    """
    Dekorator, ki zahteva veljaven piškotek. Če piškotka ni, uporabnika preusmeri na stran za prijavo.
    """
    @wraps(f)
    def decorated( *args, **kwargs):
        cookie = request.get_cookie("username")
        if cookie:
            return f(*args, **kwargs)
        return template('prijava.html')
    return decorated

@get('/prijava') 
def prijava_get():
    return template("prijava.html")

@post('/prijava') 
def prijava_post():
    uporabnisko_ime = request.forms.get('uporabnisko_ime')
    geslo = password_hash(request.forms.get('geslo'))
    
    if uporabnisko_ime is None or geslo is None:
        redirect(url('prijava_get'))
    
    try: 
        cur.execute('SELECT geslo FROM uporabnik WHERE uporabnisko_ime = %s', [uporabnisko_ime])
        hashBaza = cur.fetchone()[0]
        cur.execute('SELECT uporabnik_id FROM uporabnik WHERE uporabnisko_ime = %s', [uporabnisko_ime])
        id_uporabnika = cur.fetchone()[0]
    except:
        hashBaza = None

    if hashBaza is None:
        redirect(url('prijava_get'))
        return

    if geslo != hashBaza:
        redirect(url('prijava_get'))
        return
    
    response.set_cookie("uporabnisko_ime", uporabnisko_ime, path="/")
    redirect(url('profile_get', id_uporabnika=id_uporabnika))

@get('/odjava')
def odjava():
    response.delete_cookie("username")
    response.delete_cookie("password")
    return template('base_screen.html', napaka=None)

@get('/registracija')
def registracija_get():
    return template('login.html')

@post('/registracija')
def registracija_post():
    name = request.forms.name
    username = request.forms.username
    password = password_hash(request.forms.password)
    
    repo.dodaj_uporabnika(uporabnik)
    redirect(url('osnovna_stran'))

# Funkcija za preverjanje uporabniškega imena in gesla
def validate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute('SELECT * FROM uporabnik WHERE uporabnisko_ime = %s AND geslo = %s', (username, hashed_password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# Funkcija za preverjanje ali uporabniško ime že obstaja
def user_exists(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM uporabnik WHERE uporabnisko_ime = %s', (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# Funkcija za registracijo novega uporabnika
def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute('INSERT INTO uporabnik (uporabnisko_ime, geslo) VALUES (%s, %s)', (username, hashed_password))
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()
    cursor.close()
    conn.close()


@app.route('/static/<filename>')
def serve_static(filename):
    return static_file(filename, root='./static')

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)



@app.route('/home')
def home():
    # Fetch player data from the database
    cur.execute("""
        SELECT igralec_id, ime, priimek, pozicija, visina, rojstvo 
        FROM igralec
    """)
    players = cur.fetchall()
    return template('home', players=players)