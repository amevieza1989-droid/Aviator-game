from flask import Flask, request, render_template_string, redirect, Response
import sqlite3
from collections import Counter
from datetime import datetime
import os

app = Flask(__name__)
DB = "loto.db"

# Planning officiel LONATO
PLANNING = {
    "LUNDI": {"09:00": "MATINALE", "13:00": "DIAMANT", "18:00": "GOLD"},
    "MARDI": {"09:00": "MATINALE", "13:00": "CASH", "18:00": "BOOM"},
    "MERCREDI": {"09:00": "MATINALE", "13:00": "BENZ", "18:00": "PRESTIGE"},
    "JEUDI": {"09:00": "MATINALE", "13:00": "MILLION", "18:00": "SUPER"},
    "VENDREDI": {"09:00": "MATINALE", "13:00": "KADOO", "18:00": "KING"},
    "SAMEDI": {"09:00": "MATINALE", "13:00": "SAM", "18:00": "BINGO"},
    "DIMANCHE": {"15:00": "DETENTE"},
}

ALL_JEUX = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]

INIT_DATA = [
("VENDREDI","09:00","DETENTE","84-29-45-23-89","14-13-74-17-90","2026-08-02","1"),
("VENDREDI","09:00","DETENTE","32-01-19-03-79","33-30-85-80-71","2026-08-09","2"),
("VENDREDI","09:00","DETENTE","32-88-79-20-19","18-09-10-05-35","2026-08-16","3"),
("VENDREDI","09:00","DETENTE","30-54-36-45-87","56-10-50-62-04","2026-08-23","4"),
("VENDREDI","09:00","DETENTE","69-70-06-13-75","02-44-26-81-28","2026-08-30","5"),
("VENDREDI","09:00","DETENTE","20-55-37-24-22","29-45-84-54-49","2026-09-06","6"),
("VENDREDI","09:00","DETENTE","32-47-81-17-50","03-38-58-82-23","2026-09-13","7"),
("VENDREDI","09:00","DETENTE","55-41-67-23-63","14-04-68-60-20","2026-09-20","8"),
("VENDREDI","09:00","DETENTE","46-78-26-72-10","71-14-65-31-88","2026-09-27","9"),
]

def get_conn(): return sqlite3.connect(DB)
def init_db():
    conn=get_conn(); c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY AUTOINCREMENT, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)''')
    conn.commit()
    c.execute("SELECT COUNT(*) FROM tirages")
    if c.fetchone()[0]==0:
        for jour,heure,jeu,haut,bas,date,numero in INIT_DATA:
            th=sum([int(x) for x in haut.split('-') if x.isdigit()]); tb=sum([int(x) for x in bas.split('-') if x.isdigit()])
            c.execute("INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)",(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime("%d/%m %H:%M"),th,tb))
        conn.commit()
    conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero,created):
    try:
        th=sum([int(x) for x in haut.split('-') if x.strip().isdigit()]); tb=sum([int(x) for x in bas.split('-') if x.strip().isdigit()])
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT id FROM tirages WHERE jeu=? AND numero=? AND date=?",(jeu,numero,date))
        if c.fetchone(): conn.close(); return False
        c.execute("INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)",(jour,heure,jeu,haut,bas,date,numero,created,th,tb))
        conn.commit(); conn.close(); return True
    except: return False

def fetch_all():
    conn=get_conn(); c=conn.cursor(); c.execute("SELECT * FROM tirages ORDER BY date DESC, id DESC"); rows=c.fetchall(); conn.close(); return rows

HOME_HTML = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}.btn{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:15px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}.top{background:gold;color:#111;padding:15px;border-radius:15px;text-align:center}.box{background:#151515;padding:12px;margin:10px 0;border-radius:12px;border:1px solid #333}.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}</style></head><body>
<div class="top"><h2>🔥 LOTO TOGO V11 - PLANNING OFFICIEL</h2><p>{{nb}} tirages | 14 jeux</p></div>
<a class="btn" href="/saisir">➕ SAISIR 1 TIRAGE (auto-détecte le jeu)</a>
<a class="btn" href="/import" style="background:#00ff88;color:#111;border-color:#00ff88">📥 IMPORT RAPIDE</a>
<a class="btn" href="/analyse">📊 ANALYSE PAR JEU + TOTAUX</a>
<div class="box"><h3 style="color:gold">📅 Planning LONATO</h3>
<p><b>Lun-Sam 9h:</b> MATINALE</p><p><b>Lun:</b> 13h DIAMANT / 18h GOLD</p><p><b>Mar:</b> 13h CASH / 18h BOOM</p><p><b>Mer:</b> 13h BENZ / 18h PRESTIGE</p><p><b>Jeu:</b> 13h MILLION / 18h SUPER</p><p><b>Ven:</b> 13h KADOO / 18h KING</p><p><b>Sam:</b> 13h SAM / 18h BINGO</p><p><b>Dim:</b> 15h DETENTE</p>
</div>
<div class="box"><h3>Derniers tirages</h3>
{% for r in rows[:20] %}<p><b>{{r[1]}} {{r[2]}} {{r[3]}} #{{r[7]}}</b> {{r[6]}} - H:{{r[4]}} ({{r[9]}}) / B:{{r[5]}} ({{r[10]}})</p>{% endfor %}</div>
</body></html>
"""
@app.route('/')
def home(): rows=fetch_all(); return render_template_string(HOME_HTML, nb=len(rows), rows=rows)

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method=='POST':
        jour=request.form.get('jour'); heure=request.form.get('heure'); jeu=request.form.get('jeu')
        ok=insert_tirage(jour,heure,jeu,request.form.get('haut'),request.form.get('bas'),request.form.get('date'),request.form.get('numero'),datetime.now().strftime("%d/%m %H:%M"))
        if not ok: return "<h2 style='color:red'>DOUBLON</h2><a href='/'>Retour</a>"
        return redirect('/')
    return """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}input,select{width:100%;padding:12px;margin:6px 0;background:#111;color:#fff;border:1px solid gold;border-radius:10px}button{background:gold;color:#111;padding:15px;width:100%;border:none;border-radius:12px;font-weight:bold}#jeu{border-color:#00ff88;background:#0a1a0a;color:#00ff88;font-weight:bold}</style>
<script>
const planning = {
"LUNDI":{"09:00":"MATINALE","13:00":"DIAMANT","18:00":"GOLD"},
"MARDI":{"09:00":"MATINALE","13:00":"CASH","18:00":"BOOM"},
"MERCREDI":{"09:00":"MATINALE","13:00":"BENZ","18:00":"PRESTIGE"},
"JEUDI":{"09:00":"MATINALE","13:00":"MILLION","18:00":"SUPER"},
"VENDREDI":{"09:00":"MATINALE","13:00":"KADOO","18:00":"KING"},
"SAMEDI":{"09:00":"MATINALE","13:00":"SAM","18:00":"BINGO"},
"DIMANCHE":{"15:00":"DETENTE"}
};
function updateJeu(){
  let jour=document.getElementById('jour').value;
  let heure=document.getElementById('heure').value;
  let jeuSel=document.getElementById('jeu');
  if(planning[jour] && planning[jour][heure]){ jeuSel.value=planning[jour][heure]; }
}
</script>
</head><body>
<h2 style="color:gold">➕ Saisir 1 tirage - V11 Auto</h2>
<form method="POST">
Jour:<select id="jour" name="jour" onchange="updateJeu()"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
Heure:<select id="heure" name="heure" onchange="updateJeu()"><option>09:00</option><option>13:00</option><option>15:00</option><option>18:00</option></select>
Jeu (auto):<select id="jeu" name="jeu"><option>MATINALE</option><option>DIAMANT</option><option>GOLD</option><option>CASH</option><option>BOOM</option><option>BENZ</option><option>PRESTIGE</option><option>MILLION</option><option>SUPER</option><option>KADOO</option><option>KING</option><option>SAM</option><option>BINGO</option><option>DETENTE</option></select>
Numero:<input name="numero" placeholder="ex: 10">Date:<input name="date" type="date" value="2026-10-15">
Haut (ex: 84-29-45-23-89):<input name="haut" required>Bas (ex: 14-13-74-17-90):<input name="bas" required>
<br><br><button type="submit">✅ ENREGISTRER</button></form>
<p><a href="/" style="color:gold">← Accueil</a></p>
<script>updateJeu();</script>
</body></html>
"""

@app.route('/import', methods=['GET','POST'])
def imp():
    if request.method=='POST':
        txt=request.form['data']; c=0
        for l in txt.splitlines():
            if ';' not in l: continue
            try: d,num,jeu,haut,bas=[p.strip() for p in l.split(';')];
                if insert_tirage("LUNDI","09:00",jeu.upper(),haut,bas,d,num,datetime.now().strftime("%d/%m %H:%M")): c+=1
            except: continue
        return f"<h2>{c} importés</h2><a href='/'>Accueil</a>"
    return """<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;padding:15px}textarea{width:100%;height:350px;background:#111;color:#0f0;border:1px solid gold}button{background:#00ff88;color:#111;padding:15px;width:100%;border:none;border-radius:12px;font-weight:bold}</style></head><body>
    <h2>📥 IMPORT</h2><form method="POST"><textarea name="data"></textarea><br><br><button>IMPORTER</button></form></body></html>"""

@app.route('/analyse')
def analyse():
    rows=fetch_all()
    if not rows: return "Vide <a href='/'>Retour</a>"
    from collections import Counter, defaultdict
    jeux=defaultdict(list)
    for r in rows: jeux[r[3]].append(r)
    html=""
    for jeu_name,lst in jeux.items():
        nums=[]; th=[]
        for r in lst:
            for x in (r[4]+"-"+(r[5] or "")).split("-"):
                if x.strip().isdigit(): nums.append(x.strip().zfill(2))
            if r[9]: th.append(r[9])
        cnt=Counter(nums); top=cnt.most_common(5); avg=int(sum(th)/len(th)) if th else 0
        html+=f"<div style='background:#151515;padding:12px;margin:10px 0;border-radius:12px;border:1px solid #333'><h3 style='color:gold'>{jeu_name} - {len(lst)} tirages | TOTAL MOY {avg}</h3><p>"
        for n,c in top: html+=f"<span style='background:gold;color:#111;padding:5px 10px;border-radius:20px;margin:3px;display:inline-block'>{n} x{c}</span> "
        html+="</p></div>"
    return f"<html><body style='background:#0a0a0a;color:#fff;font-family:Arial;padding:10px'><h2 style='background:gold;color:#111;padding:15px;border-radius:15px;text-align:center'>ANALYSE PAR JEU - {len(rows)} tirages</h2><a href='/' style='color:gold'>← Accueil</a>{html}</body></html>"

if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
