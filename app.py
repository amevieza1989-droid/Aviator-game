from flask import Flask, request, redirect, render_template_string
import sqlite3
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
DB = "loto.db"

# Crée la base si elle n'existe pas
def init_db():
    conn = sqlite3.connect(DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS tirages
    (id INTEGER PRIMARY KEY, pays TEXT, loterie TEXT, numeros TEXT, date TEXT)''')
    conn.close()
init_db()

# PAGE D'ACCUEIL - Ce que tes clients voient
HOME_HTML = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#111;color:#fff;font-family:Arial;text-align:center;padding:20px}
.card{background:#222;padding:15px;margin:10px;border-radius:10px;border-left:4px solid gold}
.btn{background:gold;color:#111;padding:12px 25px;border-radius:20px;text-decoration:none;font-weight:bold}
</style></head>
<body>
<h1 style="color:gold">🏆 LOTO STATS PRO V4 LIVE</h1>
<p>Serveur OK ✅ - {{count}} tirages enregistrés</p>
<a class="btn" href="/admin">ADMIN COLLECTE</a>
<h3>Derniers Résultats</h3>
{% for r in results %}
<div class="card"><b>{{r[1]}} - {{r[2]}}</b><br>{{r[3]}}<br><small>{{r[4]}}</small></div>
{% endfor %}
</body></html>
"""

# PAGE ADMIN - Là où TOI tu collectes
ADMIN_HTML = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#111;color:#fff;font-family:Arial;padding:20px}
input,select{width:100%;padding:12px;margin:8px 0;border-radius:8px;border:none}
button{background:gold;padding:15px;width:100%;border:none;border-radius:10px;font-weight:bold;font-size:16px}
</style></head>
<body>
<h2 style="color:gold">🔐 ADMIN COLLECTE</h2>
<p>Ajoute ici les résultats que tu reçois sur WhatsApp</p>
<form method="POST">
<select name="pays" required>
<option value="TOGO">TOGO - LONATO</option>
<option value="BENIN">BENIN - LNB</option>
<option value="GHANA">GHANA - NLA</option>
<option value="CI">COTE D'IVOIRE - LONACI</option>
</select>
<select name="loterie" required>
<option>DIAMANT</option><option>BENZ</option><option>KADOO</option>
<option>SAM</option><option>MATINAL</option><option>LONACI 5/90</option>
<option>GHANA Monday Special</option><option>GHANA Friday Bonanza</option>
</select>
<input name="numeros" placeholder="Ex: 33 - 49 - 21 - 46 - 86" required>
<button type="submit">ENREGISTRER LE TIRAGE</button>
</form>
<p><a href="/" style="color:gold">← Retour accueil</a></p>
<h3>Historique</h3>
{% for r in results %}
<div style="background:#222;padding:10px;margin:5px;border-radius:5px">{{r[1]}} | {{r[2]}} | {{r[3]}} | {{r[4]}}
<a href="/delete/{{r[0]}}" style="color:red">X</a></div>
{% endfor %}
</body></html>
"""

@app.route('/')
def home():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tirages ORDER BY id DESC LIMIT 20")
    results = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM tirages")
    count = cur.fetchone()[0]
    conn.close()
    return render_template_string(HOME_HTML, results=results, count=count)

@app.route('/admin', methods=['GET','POST'])
def admin():
    conn = sqlite3.connect(DB)
    if request.method == 'POST':
        pays = request.form['pays']
        loterie = request.form['loterie']
        numeros = request.form['numeros']
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        conn.execute("INSERT INTO tirages (pays, loterie, numeros, date) VALUES (?,?,?,?)",
                     (pays, loterie, numeros, date))
        conn.commit()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tirages ORDER BY id DESC")
    results = cur.fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, results=results)

@app.route('/delete/<id>')
def delete(id):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM tirages WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

# Fonction pour futur scraping automatique
def scrape_togo():
    try:
        r = requests.get("https://www.loterie-togo.com", timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup.title.text
    except:
        return None

if __name__ == "__main__":
    app.run()
