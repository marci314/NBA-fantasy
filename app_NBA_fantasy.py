from bottle import Bottle, run, request, static_file, template, redirect
from bottleext import *
import psycopg2
import hashlib

import os
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

app = Bottle()

## Funkcija za povezavo z bazo
def get_db_connection():
    return psycopg2.connect(
        dbname='sem2024_marcelb',  
        user = 'javnost',
        password = 'javnogeslo',
        host='baza.fmf.uni-lj.si'
    )

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

@app.route('/')
def login_page():
    # Preveri, če je uporabnik že prijavljen preko piškotka
    username = request.get_cookie("username")
    if username:
        return template('<b>Pozdravljeni, {{username}}!</b>', username=username)
    else:
        return static_file('login.html', root='./views')

@app.route('/handle_form', method='POST')
def handle_form():
    username = request.forms.get('username')
    password = request.forms.get('password')
    action = request.forms.get('action')

    if not username or not password:
        return template('<b>Napaka: Uporabniško ime in geslo sta obvezna.</b>')

    if action == 'login':
        user = validate_user(username, password)
        if user:
            response.set_cookie("username", username, path='/')
            return template('<b>Pozdravljeni, {{username}}!</b>', username=username)
        else:
            return template('<b>Napaka: Uporabniško ime in geslo se ne ujemata.</b>')
    elif action == 'register':
        if user_exists(username):
            return template('<b>Napaka: Uporabniško ime že obstaja.</b>')
        else:
            register_user(username, password)
            return template('<b>Registracija uspešna. Sedaj se lahko prijavite.</b>')

@app.route('/static/<filename>')
def serve_static(filename):
    return static_file(filename, root='./static')

if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)
