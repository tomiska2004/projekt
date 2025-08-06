# app.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DB_NAME = 'coins.db'

# ---------- DATABASE SETUP ----------
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS coins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        country TEXT NOT NULL,
                        century TEXT NOT NULL,
                        quantity INTEGER NOT NULL
                    )''')
        conn.commit()

# ---------- ROUTES ----------
@app.route('/')
def index():
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

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        coins = c.fetchall()
    return render_template('index.html', coins=coins, filters=filters)

@app.route('/admin')
def admin():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM coins")
        coins = c.fetchall()
    return render_template('admin.html', coins=coins)

@app.route('/add', methods=['POST'])
def add_coin():
    name = request.form['name']
    country = request.form['country']
    century = request.form['century']
    quantity = int(request.form['quantity'])
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO coins (name, country, century, quantity) VALUES (?, ?, ?, ?)", (name, country, century, quantity))
        conn.commit()
    return redirect(url_for('admin'))

@app.route('/edit/<int:coin_id>', methods=['POST'])
def edit_coin(coin_id):
    name = request.form['name']
    country = request.form['country']
    century = request.form['century']
    quantity = int(request.form['quantity'])
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("UPDATE coins SET name=?, country=?, century=?, quantity=? WHERE id=?", (name, country, century, quantity, coin_id))
        conn.commit()
    return redirect(url_for('admin'))

@app.route('/delete/<int:coin_id>')
def delete_coin(coin_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM coins WHERE id=?", (coin_id,))
        conn.commit()
    return redirect(url_for('admin'))

@app.route('/update_quantity/<int:coin_id>', methods=['POST'])
def update_quantity(coin_id):
    quantity = int(request.form['quantity'])
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("UPDATE coins SET quantity=? WHERE id=?", (quantity, coin_id))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
