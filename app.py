from flask import Flask, request, render_template_string, redirect
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os

app = Flask(__name__)
DB = "loto.db"

PLANNING = {
    "LUNDI": {"09:00": "MATINALE", "13:00": "DIAMANT", "18:00": "GOLD"},
    "MARDI": {"09:00": "MATINALE", "13:00": "CASH", "18:00": "BOOM"},
    "MERCREDI": {"09:00": "MATINALE", "13:00": "BENZ", "18:00": "PRESTIGE"},
    "JEUDI": {"09:00": "MATINALE", "13:00": "MILLION", "18:00": "SUPER"},
    "VENDREDI": {"09:00": "MATINALE", "13:00": "KADOO", "18:00": "KING"},
    "SAMEDI": {"09:00": "MATINALE", "13:00": "SAM", "18:00": "BINGO"},
    "DIMANCHE": {"15:00": "DETENTE"},
}

INIT_DATA = [
("LUNDI","09:00","MATINALE","84-29-45-23-89","14-13-74-17-90","2026-08-02","1"),
("MARDI","09:00","MATINALE","32-01-19-03-79","33-30-85-80-71","2026-08-09","2"),
("MERCREDI","09:00","MATINALE","32-88-79-20-19","18-09-10-05-35","2026-08-16","3"),
("JEUDI","09:00","MATINALE","30-54-36-45-87","56-10-50-62-04","2026-08-23","4"),
("VENDREDI","09:00","MATINALE","69-70-06-13-75","02-44-26-81-28","2026-08-30","5"),
("SAMEDI","09:00","MATINALE","20-55-37-24-22","29-45-84-54-49","2026-09-06","6"),
("LUNDI","09:00","MATINALE","32-47-81-17-50","03-38-58-82-23","2026-09-13","7"),
("DIMANCHE","15:00","DETENTE","55-41-67-23-63","14-04-68-60-20","2026-09-20","8"),
("DIMANCHE","15:00","DETENTE","46-78-26-72-10","71-14-65-31-88","2026-09-27","9"),
]

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY AUTOINCREMENT, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)''')
    conn.commit()
    c.execute("SELECT COUNT(*) FROM tirages")
    if c.fetchone()[0] == 0:
        for jour,heure,jeu,haut,bas,date,numero in INIT_DATA:
            th = sum([int(x) for x in haut.split('-') if x.isdigit()])
            tb = sum([int(x) for x in bas.split('-') if x.isdigit()])
            c.execute("INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)",(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime("%d/%m %H:%M"),th,tb))
        conn.commit()
    conn.close()

init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero,created):
    haut = haut.strip()
    bas = bas.strip()
    th = 0
    tb = 0
    for x in haut.split('-'):
        if x.strip().isdigit():
            th += int(x.strip())
    for x in bas.split('-'):
        if x.strip().isdigit():
            tb += int(x.strip())
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM tirages WHERE jeu=? AND numero=? AND date=?",(jeu,numero,date))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)",(jour,heure,jeu,haut,bas,date,numero,created,th,tb))
    conn.commit()
    conn.close()
    return True

def fetch_all():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM tirages ORDER BY date DESC, id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

@app.route('/')
def home():
    rows = fetch_all()
    html = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}.btn{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:15px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}</style></head><body>
<h2 style="background:gold;color:#111;padding:15px;border-radius:15px;text-align:center">LOTO TOGO V11.2 - {{nb}} tirages</h2>
<a class="btn" href="/saisir">SAISIR 1 TIRAGE</a>
<a class="btn" href="/analyse">ANALYSE PAR JEU</a>
{% for r in rows[:30] %}<p><b>{{r[1]}} {{r[2]}} {{r[3]}} #{{r[7]}}</b> {{r[6]}} - H:{{r[4]}} ({{r[9]}}) B:{{r[5]}} ({{r[10]}})</p>{% endfor %}
</body></html>
"""
    return render_template_string(html, nb=len(rows), rows=rows)

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method == 'POST':
        ok = insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),request.form.get('haut'),request.form.get('bas'),request.form.get('date'),request.form.get('numero'),datetime.now().strftime("%d/%m %H:%M"))
        if not ok:
            return "<h2>DOUBLON</h2><a href='/'>Retour</a>"
        return redirect('/')
    return """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}input,select{width:100%;padding:12px;margin:6px 0;background:#111;color:#fff;border:1px solid gold;border-radius:10px}button{background:gold;color:#111;padding:15px;width:100%;border:none;border-radius:12px;font-weight:bold}</style>
<script>
const planning={"LUNDI":{"09:00":"MATINALE","13:00":"DIAMANT","18:00":"GOLD"},"MARDI":{"09:00":"MATINALE","13:00":"CASH","18:00":"BOOM"},"MERCREDI":{"09:00":"MATINALE","13:00":"BENZ","18:00":"PRESTIGE"},"JEUDI":{"09:00":"MATINALE","13:00":"MILLION","18:00":"SUPER"},"VENDREDI":{"09:00":"MATINALE","13:00":"KADOO","18:00":"KING"},"SAMEDI":{"09:00":"MATINALE","13:00":"SAM","18:00":"BINGO"},"DIMANCHE":{"15:00":"DETENTE"}};
function updateJeu(){let j=document.getElementById('jour').value;let h=document.getElementById('heure').value;let s=document.getElementById('jeu');if(planning[j]&&planning[j][h]){s.value=planning[j][h];}}
</script></head><body>
<h2 style="color:gold">SAISIR V11.2 AUTO</h2>
<form method="POST">
Jour:<select id="jour" name="jour" onchange="updateJeu()"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
Heure:<select id="heure" name="heure" onchange="updateJeu()"><option>09:00</option><option>13:00</option><option>15:00</option><option>18:00</option></select>
Jeu:<select id="jeu" name="jeu"><option>MATINALE</option><option>DIAMANT</option><option>GOLD</option><option>CASH</option><option>BOOM</option><option>BENZ</option><option>PRESTIGE</option><option>MILLION</option><option>SUPER</option><option>KADOO</option><option>KING</option><option>SAM</option><option>BINGO</option><option>DETENTE</option></select>
Numero:<input name="numero"><input name="date" type="date" value="2026-10-16">Haut:<input name="haut" required>Bas:<input name="bas" required><br><br><button>ENREGISTRER</button>
</form><a href="/" style="color:gold">Accueil</a><script>updateJeu();</script></body></html>
"""

@app.route('/analyse')
def analyse():
    rows = fetch_all()
    jeux = defaultdict(list)
    for r in rows:
        jeux[r[3]].append(r)
    html = ""
    for jeu_name,lst in jeux.items():
        nums = []
        for r in lst:
            for x in (r[4]+"-"+(r[5] or "")).split("-"):
                if x.strip().isdigit():
                    nums.append(x.strip().zfill(2))
        cnt = Counter(nums)
        top = cnt.most_common(5)
        html += f"<div style='background:#151515;padding:12px;margin:8px 0;border-radius:12px'><h3 style='color:gold'>{jeu_name} - {len(lst)} tirages</h3><p>"
        for n,c in top:
            html += f"<span style='background:gold;color:#111;padding:4px 8px;border-radius:10px;margin:2px'>{n} x{c}</span> "
        html += "</p></div>"
    return f"<html><body style='background:#0a0a0a;color:#fff;padding:10px'><a href='/' style='color:gold'>Accueil</a>{html}</body></html>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
