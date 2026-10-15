from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "loto_togo.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS tirages
    (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date_saisie TEXT)''')
    conn.close()
init_db()

HOME = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:10px}
.card{background:#1a1a1a;padding:12px;margin:10px 0;border-radius:12px;border-left:5px solid gold;text-align:left}
.top{background:gold;color:#111;padding:12px;border-radius:12px}
.btn{background:gold;color:#111;padding:14px 30px;border-radius:25px;text-decoration:none;font-weight:bold;display:inline-block;margin:10px}
.haut{color:#00ff88;font-weight:bold}.bas{color:#ffcc00}
</style></head>
<body>
<div class="top"><h2>🏆 LOTO TOGO PRO V5</h2><p>{{count}} tirages enregistrés</p></div>
<a class="btn" href="/admin">🔐 ADMIN SAISIE</a>
<h3>Derniers tirages Togo</h3>
{% for r in results %}
<div class="card">
<b>{{r[1]}} - {{r[2]}} - {{r[3]}}</b><br>
<span class="haut">HAUT (5): {{r[4]}}</span><br>
<span class="bas">BAS (5): {{r[5]}}</span><br>
<small>{{r[6]}}</small>
</div>
{% endfor %}
</body></html>
"""

ADMIN = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}
select,input{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:none}
.row{display:flex;gap:8px}.row input{text-align:center;font-weight:bold;font-size:18px}
button{background:gold;padding:16px;width:100%;border:none;border-radius:12px;font-weight:bold;font-size:18px;margin-top:15px}
label{color:gold;font-weight:bold;margin-top:10px;display:block}
</style>
<script>
function checkDimanche(){
 let jour = document.getElementById('jour').value;
 let heure = document.getElementById('heure');
 if(jour=='DIMANCHE'){
   heure.innerHTML='<option value="15:00">15H - Dimanche Unique</option>';
 } else {
   heure.innerHTML='<option value="09:00">09H - Matin</option><option value="13:00">13H - Midi</option><option value="18:00">18H - Soir</option>';
 }
}
</script>
</head>
<body onload="checkDimanche()">
<h2 style="color:gold">🔐 COLLECTE TOGO - 10 BOULES</h2>
<form method="POST">
<label>Jour</label>
<select name="jour" id="jour" onchange="checkDimanche()" required>
<option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option>
<option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option>
</select>
<label>Heure</label>
<select name="heure" id="heure" required></select>
<label>Jeu LONATO</label>
<select name="jeu" required>
<option>DIAMANT</option><option>BENZ</option><option>KADOO</option><option>SAM</option><option>SPECIAL DIMANCHE</option>
</select>
<label>5 Numéros du HAUT (gagnants)</label>
<div class="row">
<input name="h1" placeholder="H1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required>
</div>
<label>5 Numéros du BAS (machine)</label>
<div class="row">
<input name="b1" placeholder="B1" required><input name="b2" required><input name="b3" required><input name="b4" required><input name="b5" required>
</div>
<button type="submit">✅ ENREGISTRER 10 BOULES</button>
</form>
<p><a href="/" style="color:gold">← Retour accueil</a></p>
<h3>Historique</h3>
{% for r in results %}
<div style="background:#1a1a1a;padding:8px;margin:5px;border-radius:6px;font-size:12px">
{{r[1]}} {{r[2]}} {{r[3]}}<br>H:{{r[4]}} | B:{{r[5]}} <a href="/delete/{{r[0]}}" style="color:red;float:right">X</a>
</div>
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
        haut = f"{request.form['h1']}-{request.form['h2']}-{request.form['h3']}-{request.form['h4']}-{request.form['h5']}"
        bas = f"{request.form['b1']}-{request.form['b2']}-{request.form['b3']}-{request.form['b4']}-{request.form['b5']}"
        conn.execute("INSERT INTO tirages (jour, heure, jeu, haut, bas, date_saisie) VALUES (?,?,?,?,?,?)",
                     (request.form['jour'], request.form['heure'], request.form['jeu'], haut, bas, datetime.now().strftime("%d/%m %H:%M")))
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
