import os
from flask import Flask, request, redirect, render_template_string
from datetime import datetime
from collections import Counter

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
    conn=get_conn(); cur=conn.cursor()
    if USE_PG:
        cur.execute('''CREATE TABLE IF NOT EXISTS tirages (id SERIAL PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date_tirage DATE, numero_tirage TEXT, total_haut INT, total_bas INT, date_saisie TEXT)''')
        cur.execute("ALTER TABLE tirages ADD COLUMN IF NOT EXISTS date_tirage DATE")
        cur.execute("ALTER TABLE tirages ADD COLUMN IF NOT EXISTS numero_tirage TEXT")
        cur.execute("ALTER TABLE tirages ADD COLUMN IF NOT EXISTS total_haut INT")
        cur.execute("ALTER TABLE tirages ADD COLUMN IF NOT EXISTS total_bas INT")
    else:
        cur.execute('''CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date_tirage DATE, numero_tirage TEXT, total_haut INT, total_bas INT, date_saisie TEXT)''')
        for col in ["date_tirage DATE","numero_tirage TEXT","total_haut INT","total_bas INT"]:
            try: cur.execute(f"ALTER TABLE tirages ADD COLUMN {col}")
            except: pass
    conn.commit(); cur.close(); conn.close()
init_db()

def calc_totaux(haut, bas):
    h = sum(int(x) for x in haut.split('-') if x.strip().isdigit())
    b = sum(int(x) for x in bas.split('-') if x.strip().isdigit()) if bas else 0
    return h, b

def fetch_all():
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT id, jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total_haut, total_bas, date_saisie FROM tirages ORDER BY date_tirage DESC, id DESC")
    rows=cur.fetchall(); cur.close(); conn.close(); return rows

def insert_tirage(jour, heure, jeu, haut, bas, date_tirage, numero_tirage, date_s):
    th, tb = calc_totaux(haut, bas)
    conn=get_conn(); cur=conn.cursor()
    if USE_PG:
        cur.execute("INSERT INTO tirages (jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total_haut, total_bas, date_saisie) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (jour, heure, jeu, haut, bas, date_tirage, numero_tirage, th, tb, date_s))
    else:
        cur.execute("INSERT INTO tirages (jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total_haut, total_bas, date_saisie) VALUES (?,?,?,?,?,?,?,?,?,?)", (jour, heure, jeu, haut, bas, date_tirage, numero_tirage, th, tb, date_s))
    conn.commit(); cur.close(); conn.close()

HOME = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:10px}.card{background:#1a1a1a;padding:10px;margin:8px 0;border-radius:12px;border-left:5px solid gold;text-align:left;font-size:12px}.top{background:gold;color:#111;padding:15px;border-radius:15px}.btn{background:gold;color:#111;padding:12px 20px;border-radius:25px;text-decoration:none;font-weight:bold;display:inline-block;margin:5px}</style></head>
<body><div class="top"><h2>🏆 LOTO TOGO V10.4 - ANTI-DOUBLON</h2><b>{{count}} tirages</b> {% if pg %}✅ BASE A VIE{% endif %}</div><a class="btn" href="/admin">🔐 SAISIE</a><a class="btn" href="/analyse" style="background:#222;color:gold;border:1px solid gold">📊 ANALYSE</a>{% for r in results %}<div class="card"><b>{{r[6]}} | Tr N°{{r[7]}} | {{r[3]}}</b><br>Haut: <b style="color:#00ff88">{{r[4]}}</b> <span style="background:#00ff88;color:#111;padding:2px 6px;border-radius:10px;font-weight:bold">T:{{r[8]}}</span><br>{% if r[5] %}Bas: <b style="color:#ffcc00">{{r[5]}}</b> <span style="background:#ffcc00;color:#111;padding:2px 6px;border-radius:10px;font-weight:bold">T:{{r[9]}}</span>{% endif %}</div>{% endfor %}</body></html>
"""

ADMIN = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}select,input{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:none}
.row{display:flex;gap:8px}.row input{text-align:center;font-weight:bold;font-size:18px;border:2px solid #fff}
.row input.dup{border:3px solid red;background:#ffcccc;color:red}
button{background:gold;padding:16px;width:100%;border:none;border-radius:12px;font-weight:bold;font-size:18px;margin-top:15px}
button:disabled{background:#555;color:#888}
label{color:gold;font-weight:bold;margin-top:12px;display:block}
#jeu_auto{background:#222;color:gold;font-weight:bold;font-size:22px;text-align:center;border:2px solid gold}
#alerte{display:none;background:red;color:#fff;padding:12px;border-radius:10px;text-align:center;font-weight:bold;margin-top:10px}
#total_live{color:gold;font-weight:bold;text-align:center;margin-top:10px;font-size:15px}
</style><script>
const grille={'LUNDI':{'09:00':'MATINALE','13:00':'DIAMANT','18:00':'GOLD'},'MARDI':{'09:00':'MATINALE','13:00':'CASH','18:00':'BOOM'},'MERCREDI':{'09:00':'MATINALE','13:00':'BENZ','18:00':'PRESTIGE'},'JEUDI':{'09:00':'MATINALE','13:00':'MILLION','18:00':'SUPER'},'VENDREDI':{'09:00':'MATINALE','13:00':'KADOO','18:00':'KING'},'SAMEDI':{'09:00':'MATINALE','13:00':'SAM','18:00':'BINGO'},'DIMANCHE':{'15:00':'DETENTE'}}
function updateHeures(){let j=document.getElementById('jour').value;let h=document.getElementById('heure');if(j=='DIMANCHE'){h.innerHTML='<option value="15:00">15H - DETENTE (10 numéros)</option>';}else{h.innerHTML='<option value="09:00">09H - MATINALE (10 numéros)</option><option value="13:00">13H - 5 numéros</option><option value="18:00">18H - 5 numéros</option>';}updateJeu();}
function updateJeu(){let j=document.getElementById('jour').value;let h=document.getElementById('heure').value;document.getElementById('jeu_auto').value=grille[j][h];let is10=grille[j][h]=='MATINALE'||grille[j][h]=='DETENTE';document.getElementById('bas_block').style.display=is10?'block':'none';}
function calc(){
  let dup=false; document.querySelectorAll('input[name^=h],input[name^=b]').forEach(i=>i.classList.remove('dup'));
  let hVals=[], bVals=[];
  document.querySelectorAll('input[name^=h]').forEach(i=>{if(i.value.trim()){let v=i.value.trim(); if(hVals.includes(v)){i.classList.add('dup'); dup=true;} hVals.push(v);}});
  document.querySelectorAll('input[name^=b]').forEach(i=>{if(i.value.trim()){let v=i.value.trim(); if(bVals.includes(v)||hVals.includes(v)){i.classList.add('dup'); dup=true;} bVals.push(v);}});
  document.querySelectorAll('input[name^=h]').forEach(i=>{if(i.value.trim() && bVals.includes(i.value.trim())){i.classList.add('dup'); dup=true;}});
  let hSum=hVals.filter(v=>!isNaN(v)&&v!=='').reduce((a,b)=>a+parseInt(b),0);
  let bSum=bVals.filter(v=>!isNaN(v)&&v!=='').reduce((a,b)=>a+parseInt(b),0);
  document.getElementById('total_live').innerHTML=dup?'':`TOTAL HAUT (WIN): ${hSum} | TOTAL BAS (MACHINE): ${bSum}`;
  let alerte=document.getElementById('alerte'); let btn=document.getElementById('btnSave');
  if(dup){alerte.style.display='block'; alerte.innerText='⛔ ERREUR DOUBLON DETECTE! Ex: 23...23 INTERDIT EN HAUT, EN BAS OU ENTRE HAUT ET BAS'; btn.disabled=true;}
  else{alerte.style.display='none'; btn.disabled=false;}
}
</script></head><body onload="updateHeures()">
<h2 style="color:gold">🔐 V10.4 - ANTI-DOUBLON 23...23</h2>
<form method="POST" oninput="calc()">
<label>Date</label><input type="date" name="date_tirage" required value="{{today}}">
<label>N° Tr</label><input type="text" name="numero_tirage" placeholder="22" required>
<label>Jour</label><select name="jour" id="jour" onchange="updateHeures()" required><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
<label>Heure</label><select name="heure" id="heure" onchange="updateJeu()" required></select>
<label>Jeu</label><input name="jeu" id="jeu_auto" readonly>
<label>5 Numéros HAUT (WIN)</label><div class="row"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div>
<div id="bas_block"><label>5 Numéros BAS (MACHINE)</label><div class="row"><input name="b1"><input name="b2"><input name="b3"><input name="b4"><input name="b5"></div></div>
<div id="total_live"></div><div id="alerte"></div>
<button type="submit" id="btnSave">✅ ENREGISTRER 2 TOTAUX</button>
</form><p><a href="/" style="color:gold">← Accueil</a></p></body></html>
"""

@app.route('/')
def home():
    rows=fetch_all()
    return render_template_string(HOME, results=rows[:60], count=len(rows), pg=USE_PG)

@app.route('/admin', methods=['GET','POST'])
def admin_route():
    if request.method=='POST':
        haut_list=[request.form[f'h{i}'].strip() for i in range(1,6)]
        bas_list=[request.form.get(f'b{i}','').strip() for i in range(1,6) if request.form.get(f'b{i}','').strip()!='']
        if len(set(haut_list))!=len(haut_list):
            return "<h1 style='color:red;text-align:center;padding:30px'>⛔ DOUBLON DANS HAUT: 23...23 INTERDIT<br><br><a href='/admin'>Retour</a></h1>",400
        if bas_list and len(set(bas_list))!=len(bas_list):
            return "<h1 style='color:red;text-align:center;padding:30px'>⛔ DOUBLON DANS BAS: 23...23 INTERDIT<br><br><a href='/admin'>Retour</a></h1>",400
        if bas_list and set(haut_list) & set(bas_list):
            return f"<h1 style='color:red;text-align:center;padding:30px'>⛔ DOUBLON HAUT/BAS: {set(haut_list) & set(bas_list)} existe déjà<br><br><a href='/admin'>Retour</a></h1>",400
        haut="-".join(haut_list)
        bas="-".join(bas_list) if bas_list else ""
        insert_tirage(request.form['jour'], request.form['heure'], request.form['jeu'], haut, bas, request.form['date_tirage'], request.form['numero_tirage'], datetime.now().strftime("%d/%m %H:%M"))
        return redirect('/admin')
    return render_template_string(ADMIN, today=datetime.now().strftime("%Y-%m-%d"))

@app.route('/analyse')
def analyse():
    rows=fetch_all()
    html=f"<html><body style='background:#0a0a0a;color:#fff;font-family:Arial;padding:15px'><h2 style='color:gold'>📊 V10.4 ANTI-DOUBLON - {len(rows)} tirages</h2><a href='/' style='color:gold'>← Accueil</a><br><br>"
    for r in rows[:30]:
        html+=f"Tr {r[7]} - {r[6]} - H:{r[8]} B:{r[9]} - {r[4]} | {r[5]}<br>"
    html+="</body></html>"
    return html

if __name__=="__main__":
    app.run()
