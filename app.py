from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "loto_togo.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS tirages
    (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, numeros TEXT, date_saisie TEXT)''')
    conn.close()
init_db()

HOME = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:15px}
.card{background:#1a1a1a;padding:12px;margin:8px 0;border-radius:10px;border-left:4px solid gold;text-align:left}
.top{background:linear-gradient(45deg,gold,#ffcc00);color:#111;padding:15px;border-radius:15px}
.btn{background:gold;color:#111;padding:14px 30px;border-radius:25px;text-decoration:none;font-weight:bold;display:inline-block;margin:10px}
.heure{color:gold;font-weight:bold}
</style></head>
<body>
<div class="top"><h1>🏆 LOTO TOGO PRO V4</h1><p>Serveur OK ✅ | {{count}} tirages</p></div>
<a class="btn" href="/admin">🔐 ADMIN - SAISIR RESULTAT</a>
<h3>📊 Résultats Togo - Lundi à Dimanche</h3>
{% for r in results %}
<div class="card"><span class="heure">{{r[2]}}</span> - {{r[1]}} | <b>{{r[3]}}</b><br>
<b style="font-size:18px;color:gold">{{r[4]}}</b><br><small>{{r[5]}}</small></div>
{% else %}<p>Aucun résultat. Clique ADMIN pour commencer.</p>{% endfor %}
</body></html>
"""

ADMIN = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}
input,select{width:100%;padding:14px;margin:8px 0;border-radius:10px;border:none;font-size:16px}
button{background:gold;padding:16px;width:100%;border:none;border-radius:12px;font-weight:bold;font-size:18px;margin-top:10px}
label{color:gold;font-weight:bold;margin-top:10px;display:block}
</style></head>
<body>
<h2 style="color:gold">🔐 COLLECTE TOGO</h2>
<form method="POST">
<label>Jour</label>
<select name="jour" required>
<option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option>
<option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option>
</select>
<label>Heure du tirage</label>
<select name="heure" required>
<option value="09:00">09H - Matin</option>
<option value="13:00">13H - Midi</option>
<option value="18:00">18H - Soir</option>
</select>
<label>Nom du Jeu LONATO</label>
<select name="jeu" required>
<option>DIAMANT</option><option>BENZ</option><option>KADOO</option>
<option>SAM</option><option>MATINAL</option><option>EVENEMENT SPECIAL</option>
</select>
<label>5 Numéros gagnants</label>
<input name="numeros" placeholder="Ex: 33 - 49 - 21 - 46 - 86" required>
<button type="submit">✅ ENREGISTRER</button>
</form>
<p><a href="/" style="color:gold">← Retour</a></p>
<h3>Historique</h3>
{% for r in results %}
<div style="background:#1a1a1a;padding:8px;margin:5px;border-radius:5px;font-size:13px">
{{r[1]}} {{r[2]}} | {{r[3]}} | {{r[4]}} <a href="/delete/{{r[0]}}" style="color:red;float:right">Supprimer</a></div>
{% endfor %}
</body></html>
"""

@app.route('/')
def home():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tirages ORDER BY id DESC LIMIT 30")
    results = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM tirages")
    count = cur.fetchone()[0]
    conn.close()
    return render_template_string(HOME, results=results, count=count)

@app.route('/admin', methods=['GET','POST'])
def admin():
    conn = sqlite3.connect(DB)
    if request.method == 'POST':
        conn.execute("INSERT INTO tirages (jour, heure, jeu, numeros, date_saisie) VALUES (?,?,?,?,?)",
                     (request.form['jour'], request.form['heure'], request.form['jeu'],
                      request.form['numeros'], datetime.now().strftime("%d/%m %H:%M")))
        conn.commit()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tirages ORDER BY id DESC")
    results = cur.fetchall()
    conn.close()
    return render_template_string(ADMIN, results=results)

@app.route('/delete/<id>')
def delete(id):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM tirages WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == "__main__":
    app.run()
