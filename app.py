# app.py
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key'

MAIN_DB = 'main.db'
SUPERADMIN_EMAIL = 'nandor@gmail.com'

# ---------- MAIN DB SETUP ----------
def init_main_db():
    with sqlite3.connect(MAIN_DB) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )''')
        conn.commit()

# ---------- USER DB SETUP ----------
def init_user_db(email):
    email = email.strip().lower()

    db_name = f'user_{email}.db'
    if not os.path.exists(db_name):
        with sqlite3.connect(db_name) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS coins (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            country TEXT NOT NULL,
                            century TEXT NOT NULL,
                            quantity INTEGER NOT NULL
                        )''')
            conn.commit()
    return db_name

def get_user_db():
    if 'email' not in session:
        return None
    return init_user_db(session['email'])


def get_useremail_db():
    if 'user_id' not in session:
        return None
    return init_user_db(session['email'])
# ---------- AUTH ROUTES ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect(MAIN_DB) as conn:
            c = conn.cursor()
            c.execute("SELECT id, password FROM users WHERE email = ?", (email,))
            user = c.fetchone()
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['email'] = email
                return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    try:
        with sqlite3.connect(MAIN_DB) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            user_id = c.lastrowid
            session['user_id'] = user_id
            session['email'] = email
            init_user_db(user_id)
            return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        return render_template('login.html', error='User already exists')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- APP ROUTES ----------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_user_db()
    filters = {
        'country': request.args.get('country', ''),
        'century': request.args.get('century', ''),
        'quantity': request.args.get('quantity', '')
    }
    query = "SELECT * FROM coins WHERE 1=1"
    params = []

    if filters['country']:
        query += " AND country = ?"
        params.append(filters['country'])
    if filters['century']:
        query += " AND century = ?"
        params.append(filters['century'])
    if filters['quantity']:
        query += " AND quantity = ?"
        params.append(filters['quantity'])

    with sqlite3.connect(db) as conn:
        c = conn.cursor()
        c.execute(query, params)
        coins = c.fetchall()
    return render_template('index.html', coins=coins, filters=filters)

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_user_db()
    with sqlite3.connect(db) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM coins")
        coins = c.fetchall()
    return render_template('admin.html', coins=coins)

@app.route('/add', methods=['POST'])
def add_coin():
    db = get_user_db()
    name = request.form['name']
    country = request.form['country']
    century = request.form['century']
    quantity = int(request.form['quantity'])
    with sqlite3.connect(db) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO coins (name, country, century, quantity) VALUES (?, ?, ?, ?)", (name, country, century, quantity))
        conn.commit()
    return redirect(url_for('admin'))

@app.route('/edit/<int:coin_id>', methods=['POST'])
def edit_coin(coin_id):
    db = get_user_db()
    name = request.form['name']
    country = request.form['country']
    century = request.form['century']
    quantity = int(request.form['quantity'])
    with sqlite3.connect(db) as conn:
        c = conn.cursor()
        c.execute("UPDATE coins SET name=?, country=?, century=?, quantity=? WHERE id=?", (name, country, century, quantity, coin_id))
        conn.commit()
    return redirect(url_for('admin'))

@app.route('/delete/<int:coin_id>')
def delete_coin(coin_id):
    db = get_user_db()
    with sqlite3.connect(db) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM coins WHERE id=?", (coin_id,))
        conn.commit()
    return redirect(url_for('admin'))

@app.route('/update_quantity/<int:coin_id>', methods=['POST'])
def update_quantity(coin_id):
    db = get_user_db()
    quantity = int(request.form['quantity'])
    with sqlite3.connect(db) as conn:
        c = conn.cursor()
        c.execute("UPDATE coins SET quantity=? WHERE id=?", (quantity, coin_id))
        conn.commit()
    return redirect(url_for('index'))


# ---------- SUPERADMIN PANEL ----------
@app.route('/superadmin')
def superadmin():
    if 'email' not in session or session['email'] != SUPERADMIN_EMAIL:
        return "Unauthorized", 403

    db_files = [f for f in os.listdir('.') if f.endswith('.db')]
    return render_template('superadmin.html', db_files=db_files)

@app.route('/download/<filename>')
def download_db(filename):
    if 'email' not in session or session['email'] != SUPERADMIN_EMAIL:
        return "Unauthorized", 403
    if not filename.startswith("user_") or not filename.endswith(".db"):
        return "Invalid file", 400
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    init_main_db()
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port)