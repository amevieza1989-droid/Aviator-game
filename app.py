import os
from flask import Flask, request, redirect, render_template_string
from datetime import datetime
from collections import Counter
import random

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_PG = False
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    try:
        import psycopg2
        USE_PG = True
    except:
        USE_PG = False

def get_conn():
    if USE_PG:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        return sqlite3.connect("loto_togo.db")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    if USE_PG:
        cur.execute('''CREATE TABLE IF NOT EXISTS tirages
        (id SERIAL PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date_tirage DATE, numero_tirage TEXT, total INT, date_saisie TEXT)''')
        # Migration si ancienne table
        cur.execute("ALTER TABLE tirages ADD COLUMN IF NOT EXISTS date_tirage DATE")
        cur.execute("ALTER TABLE tirages ADD COLUMN IF NOT EXISTS numero_tirage TEXT")
        cur.execute("ALTER TABLE tirages ADD COLUMN IF NOT EXISTS total INT")
    else:
        cur.execute('''CREATE TABLE IF NOT EXISTS tirages
        (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date_tirage DATE, numero_tirage TEXT, total INT, date_saisie TEXT)''')
        for col in ["date_tirage DATE", "numero_tirage TEXT", "total INT"]:
            try:
                cur.execute(f"ALTER TABLE tirages ADD COLUMN {col}")
            except:
                pass
    conn.commit()
    cur.close()
    conn.close()

init_db()

def calc_total(haut, bas):
    all_nums = (haut + "-" + bas).split("-")
    s = 0
    for x in all_nums:
        if x.strip().isdigit():
            s += int(x.strip())
    return s

def fetch_all():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total, date_saisie FROM tirages ORDER BY date_tirage DESC, CAST(numero_tirage AS INTEGER) DESC, id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def insert_tirage(jour, heure, jeu, haut, bas, date_tirage, numero_tirage, date_s):
    total = calc_total(haut, bas)
    conn = get_conn()
    cur = conn.cursor()
    if USE_PG:
        cur.execute("INSERT INTO tirages (jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total, date_saisie) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total, date_s))
    else:
        cur.execute("INSERT INTO tirages (jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total, date_saisie) VALUES (?,?,?,?,?,?,?,?,?)", (jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total, date_s))
    conn.commit()
    cur.close()
    conn.close()

HOME = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:10px}
.card{background:#1a1a1a;padding:10px;margin:8px 0;border-radius:12px;border-left:5px solid gold;text-align:left;font-size:13px}
.top{background:gold;color:#111;padding:15px;border-radius:15px}
.btn{background:gold;color:#111;padding:12px 20px;border-radius:25px;text-decoration:none;font-weight:bold;display:inline-block;margin:5px}
.btn2{background:#222;color:gold;border:1px solid gold;padding:12px 20px;border-radius:25px;text-decoration:none;display:inline-block;margin:5px}
.badge{background:#222;border:1px solid #555;color:#ffcc00;padding:3px 8px;border-radius:12px;font-size:11px}
</style></head>
<body>
<div class="top"><h2>🏆 LOTO TOGO V10.2 - ARCHIVE 2005</h2><b>{{count}} tirages</b> {% if pg %}✅ BASE À VIE{% endif %}</div>
<a class="btn" href="/admin">🔐 SAISIE N° + TOTAL</a><a class="btn2" href="/analyse">📊 ANALYSE</a>
{% for r in results %}
<div class="card">
<b>{{r[6]}} | Tr N°{{r[7]}} | {{r[1]}} {{r[2]}} - {{r[3]}}</b><br>
{% if not r[5] or r[5]=='' %}5/90: <b style="color:#00ff88">{{r[4]}}</b>
{% else %}H: <b style="color:#00ff88">{{r[4]}}</b> | B: <b style="color:#ffcc00">{{r[5]}}</b>{% endif %}
<span class="badge">TOTAL: {{r[8]}}</span>
<br><small>{{r[9]}}</small></div>
{% endfor %}
</body></html>
"""

ADMIN = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}
select,input{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:none}
.row{display:flex;gap:8px}.row input{text-align:center;font-weight:bold;font-size:18px}
button{background:gold;padding:16px;width:100%;border:none;border-radius:12px;font-weight:bold;font-size:18px;margin-top:15px}
label{color:gold;font-weight:bold;margin-top:12px;display:block}
#jeu_auto{background:#222;color:gold;font-weight:bold;font-size:22px;text-align:center;border:2px solid gold}
</style>
<script>
const grille={'LUNDI':{'09:00':'MATINALE','13:00':'DIAMANT','18:00':'GOLD'},'MARDI':{'09:00':'MATINALE','13:00':'CASH','18:00':'BOOM'},'MERCREDI':{'09:00':'MATINALE','13:00':'BENZ','18:00':'PRESTIGE'},'JEUDI':{'09:00':'MATINALE','13:00':'MILLION','18:00':'SUPER'},'VENDREDI':{'09:00':'MATINALE','13:00':'KADOO','18:00':'KING'},'SAMEDI':{'09:00':'MATINALE','13:00':'SAM','18:00':'BINGO'},'DIMANCHE':{'15:00':'DETENTE'}}
function updateHeures(){let j=document.getElementById('jour').value;let h=document.getElementById('heure');if(j=='DIMANCHE'){h.innerHTML='<option value="15:00">15H - DETENTE (10 numéros)</option>';}else{h.innerHTML='<option value="09:00">09H - MATINALE (10 numéros)</option><option value="13:00">13H - 5 numéros</option><option value="18:00">18H - 5 numéros</option>';}updateJeu();}
function updateJeu(){let j=document.getElementById('jour').value;let h=document.getElementById('heure').value;document.getElementById('jeu_auto').value=grille[j][h];let is10=grille[j][h]=='MATINALE'||grille[j][h]=='DETENTE';document.getElementById('bas_block').style.display=is10?'block':'none';document.querySelectorAll('.b_input').forEach(i=>{i.required=is10;if(!is10)i.value='';});}
function calc(){let vals=[];document.querySelectorAll('input[name^=h],input[name^=b]').forEach(i=>{if(i.value &&!isNaN(i.value)) vals.push(parseInt(i.value))});let sum=vals.reduce((a,b)=>a+b,0);document.getElementById('total_live').innerText=sum?('TOTAL AUTO: '+sum):'';}
</script></head>
<body onload="updateHeures()">
<h2 style="color:gold">🔐 COLLECTE V10.2 - COMME 2005</h2>
<form method="POST" oninput="calc()">
<label>📅 Date du tirage (ex: 0301 = 03 Janv)</label><input type="date" name="date_tirage" required value="{{today}}">
<label>🔢 N° Tr (ex: 203 - comme sur ta photo)</label><input type="text" name="numero_tirage" placeholder="203" required>
<label>Jour</label><select name="jour" id="jour" onchange="updateHeures()" required><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
<label>Heure</label><select name="heure" id="heure" onchange="updateJeu()" required></select>
<label>Jeu (auto)</label><input name="jeu" id="jeu_auto" readonly>
<label>5 Numéros Gagnants (ex: 22-12-44-63-13)</label><div class="row"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div>
<div id="bas_block"><label>5 Numéros du BAS (pour MATINALE)</label><div class="row"><input name="b1" class="b_input"><input name="b2" class="b_input"><input name="b3" class="b_input"><input name="b4" class="b_input"><input name="b5" class="b_input"></div></div>
<div id="total_live" style="color:gold;font-weight:bold;text-align:center;margin-top:10px;font-size:20px"></div>
<button type="submit">✅ ENREGISTRER N° + TOTAL AUTO</button>
</form><p><a href="/" style="color:gold">← Accueil</a> | <a href="/analyse" style="color:gold">Analyse →</a></p></body></html>
"""

@app.route('/')
def home():
    rows = fetch_all()
    return render_template_string(HOME, results=rows[:60], count=len(rows), pg=USE_PG)

@app.route('/admin', methods=['GET','POST'])
def admin_route():
    if request.method=='POST':
        haut=f"{request.form['h1']}-{request.form['h2']}-{request.form['h3']}-{request.form['h4']}-{request.form['h5']}"
        b1=request.form.get('b1','').strip()
        bas=f"{request.form['b1']}-{request.form['b2']}-{request.form['b3']}-{request.form['b4']}-{request.form['b5']}" if b1 else ""
        insert_tirage(request.form['jour'], request.form['heure'], request.form['jeu'], haut, bas, request.form['date_tirage'], request.form['numero_tirage'], datetime.now().strftime("%d/%m %H:%M"))
        return redirect('/admin')
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template_string(ADMIN, today=today)

@app.route('/analyse')
def analyse():
    rows = fetch_all()
    if not rows:
        return "Saisis 1 tirage"
    all_nums=[]
    totals=[]
    for r in rows:
        nums=(r[4]+"-"+(r[5] or "")).split("-")
        for n in nums:
            if n.strip().isdigit():
                all_nums.append(n.strip())
        if r[8]:
            totals.append(r[8])
    cnt=Counter(all_nums)
    top10=[(n,c,round(c/len(all_nums)*100,1)) for n,c in cnt.most_common(10)] if all_nums else []
    avg_total = int(sum(totals)/len(totals)) if totals else 0
    return render_template_string("""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}.top{background:gold;color:#111;padding:15px;border-radius:15px;text-align:center}.box{background:#151515;padding:14px;margin:12px 0;border-radius:15px}.badge{display:inline-block;background:#222;border:1px solid gold;color:gold;padding:7px 12px;border-radius:20px;margin:4px;font-weight:bold}.hot{background:gold;color:#111}a{color:gold}</style></head>
    <body><div class="top"><h2>📊 V10.2 TOTAL ANALYSE</h2><p>{{count}} tirages | TOTAL Moyen: {{avg}} | Comme archive 2005</p></div><p><a href="/">← Accueil</a> | <a href="/admin">Saisie →</a></p>
    <div class="box"><h3>🔥 TOP 10 CHAUDS</h3>{% for n,c,p in top10 %}<span class="badge hot">{{n}} {{p}}% ({{c}}x)</span>{% endfor %}</div>
    <div class="box"><h3>📊 Liste avec TOTAL (comme ta photo)</h3>
    {% for r in rows[:30] %}<p><b>Tr {{r[7]}} - {{r[6]}} TOTAL {{r[8]}}</b> : {{r[4]}} {% if r[5] %}| {{r[5]}}{% endif %}</p>{% endfor %}
    </div></body></html>
    """, count=len(rows), avg=avg_total, top10=top10, rows=rows)

if __name__=="__main__":
    app.run()
