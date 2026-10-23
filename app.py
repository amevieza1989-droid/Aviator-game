from flask import Flask, request, redirect, url_for, render_template_string, jsonify
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import os, re, io, secrets, random

app = Flask(__name__)
app.secret_key = "V19_3_2_STABLE_BOSS_FINAL"
DB = "/data/loto.db" if os.path.exists("/data") else "loto.db"
JEUX = ["MATINALE", "DETENTE", "DIAMANT", "GOLD", "CASH", "SUPER", "PRESTIGE", "ESSOR"]
ADMIN_PASS = "Boss2026"

# === CORRECTION BOSS: 10 BOULES MATINALE/DETENTE, 5 AUTRES ===
BOULES_CONFIG = {
    "MATINALE": 10,
    "DETENTE": 10,
    "DIAMANT": 5,
    "GOLD": 5,
    "CASH": 5,
    "SUPER": 5,
    "PRESTIGE": 5,
    "ESSOR": 5
}

def get_nb_boules(jeu):
    return BOULES_CONFIG.get(jeu.upper(), 5)

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn=get_conn();c=conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS tirages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jeu TEXT NOT NULL,
            date_tirage TEXT,
            numeros TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS pronos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jeu TEXT NOT NULL,
            numeros TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit();conn.close()
    except Exception as e:
        print("DB init error", e)

init_db()

TEMPLATE = """
<!doctype html>
<html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>LONATO BOSS - {{jeu}} {{nb}} Boules</title>
<style>
body{background:#0a0a0a;color:#ffd700;font-family:Arial;padding:10px;margin:0}
.card{background:#111;border:1px solid #ffd70044;border-radius:12px;padding:12px;margin-bottom:10px}
select,input,button,textarea{width:100%;padding:10px;border-radius:8px;border:1px solid #333;background:#1a1a1a;color:#fff;margin:4px 0}
button{background:#ffd700;color:#000;font-weight:bold;border:none}
.boules{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.boule{width:40px;height:40px;border-radius:50%;background:radial-gradient(circle at 30% 30%, #ffd700, #b8860b);color:#000;display:flex;align-items:center;justify-content:center;font-weight:bold;border:2px solid #fff3}
.boule.b10{background:radial-gradient(circle at 30% 30%, #ff4444, #990000);color:#fff}
.small{font-size:11px;color:#888}
table{width:100%;font-size:12px;border-collapse:collapse}
td,th{border-bottom:1px solid #222;padding:4px}
</style></head><body>
<h2 style=text-align:center>🎯 LONATO BOSS - {{jeu}} ({{nb}} BOULES)</h2>

<div class=card>
<form method=get action="/">
<label>Changer Tirage</label>
<select name=jeu onchange="this.form.submit()">
{% for j in jeux %}<option value="{{j}}" {% if j==jeu %}selected{% endif %}>{{j}} - {{boules_cfg[j]}}B</option>{% endfor %}
</select>
</form>
<div class=small>Regle: MATINALE et DETENTE = 10 boules, les autres = 5 boules</div>
</div>

<div class=card>
<b>HISTORIQUE {{jeu}} ({{hists|length}})</b> <span style="background:#ffd70022;padding:2px 8px;border-radius:20px;font-size:10px">{{nb}} Boules</span>
<form method=post action="/import" enctype=multipart/form-data>
<input type=hidden name=jeu value="{{jeu}}">
<textarea name=text_data rows=2 placeholder="Colle: 48-84-83-34-41 ou pour 10 boules: 12-45-78-90-11-23-34-56-67-89"></textarea>
<div style=display:flex;gap:6px>
<input type=file name=file_data accept=.txt,.csv>
<button type=submit style="background:#00c853;color:#fff">IMPORTER {{jeu}}</button>
</div>
</form>
<table>
{% for h in hists[:20] %}<tr><td>{{h['date_tirage']}}</td><td><b style=color:#ffd700>{{h['numeros']}}</b></td></tr>{% endfor %}
</table>
<form method=post action="/vider" onsubmit="return confirm('Vider {{jeu}}?')"><input type=hidden name=jeu value="{{jeu}}"><button style="background:#222;color:#ff4444;font-size:11px">Vider {{jeu}}</button></form>
</div>

<div class=card>
<b>PRONOSTIC {{jeu}} - {{nb}} BOULES</b>
<div class=boules>
{% for n in prono %}<div class="boule {% if nb==10 %}b10{% endif %}">{{n}}</div>{% endfor %}
</div>
<div style=display:flex;gap:6px>
<a href="/?jeu={{jeu}}&gen=1" style=flex:2><button>GENERER PRONO {{nb}}B</button></a>
<a href="/?jeu={{jeu}}&gen=rand" style=flex:1><button style=background:#222;color:#ffd700;border:1px solid #ffd700">VARIANTE</button></a>
</div>
<div class=small>{{detail}}</div>
</div>

<div class=card><a href="/admin"><button style=background:#222;color:#ffd700>ADMIN</button></a></div>
</body></html>
"""

def parse_numeros(text, nb):
    nums = list(map(int, re.findall(r'\d+', text)))
    nums = [n for n in nums if 1 <= n <= 90]
    return nums[:nb]

@app.route("/", methods=["GET"])
def index():
    jeu = request.args.get("jeu", "SUPER").upper()
    if jeu not in JEUX: jeu = "SUPER"
    nb = get_nb_boules(jeu)
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM tirages WHERE jeu=? ORDER BY id DESC", (jeu,))
    hists = c.fetchall()
    conn.close()
    gen = request.args.get("gen")
    prono = []
    detail = ""
    if gen == "rand" or len(hists)==0:
        pool=[]
        while len(pool)<nb:
            n=random.randint(1,90)
            if n not in pool: pool.append(n)
        prono=sorted(pool)
        detail=f"Variante aleatoire - {nb} boules"
    else:
        freq=Counter()
        for h in hists:
            for x in re.findall(r'\d+', h["numeros"]):
                try: freq[int(x)]+=1
                except: pass
        if len(freq)>=nb:
            top=[k for k,v in freq.most_common(nb*3)]
            random.shuffle(top)
            prono=sorted(top[:nb])
            detail=f"Base sur {len(hists)} tirages - frequence {nb}B"
        else:
            pool=[]
            while len(pool)<nb:
                n=random.randint(1,90)
                if n not in pool: pool.append(n)
            prono=sorted(pool)
            detail=f"Random (pas assez hist) - {nb}B"
    return render_template_string(TEMPLATE, jeu=jeu, nb=nb, jeux=JEUX, boules_cfg=BOULES_CONFIG, hists=hists, prono=prono, detail=detail)

@app.route("/import", methods=["POST"])
def do_import():
    jeu = request.form.get("jeu","SUPER").upper()
    nb = get_nb_boules(jeu)
    text_data = request.form.get("text_data","")
    file = request.files.get("file_data")
    content = text_data
    if file and file.filename:
        content += "\n" + file.read().decode(errors="ignore")
    lines = content.strip().split("\n")
    conn=get_conn();c=conn.cursor()
    for line in lines:
        if not line.strip(): continue
        nums = parse_numeros(line, nb)
        if len(nums) < nb: continue
        numeros_str = "-".join(map(str, nums[:nb]))
        date_t = datetime.now().strftime("%d/%m %H:%M")
        c.execute("INSERT INTO tirages (jeu, date_tirage, numeros) VALUES (?,?,?)", (jeu, date_t, numeros_str))
    conn.commit();conn.close()
    return redirect(url_for("index", jeu=jeu))

@app.route("/vider", methods=["POST"])
def vider():
    jeu=request.form.get("jeu","SUPER").upper()
    conn=get_conn();c=conn.cursor()
    c.execute("DELETE FROM tirages WHERE jeu=?", (jeu,))
    conn.commit();conn.close()
    return redirect(url_for("index", jeu=jeu))

@app.route("/admin", methods=["GET","POST"])
def admin():
    if request.method=="POST":
        if request.form.get("pass")==ADMIN_PASS:
            return "OK ADMIN - DB: "+DB
        return "Mauvais pass", 403
    return '<form method=post><input name=pass type=password placeholder=Pass><button>Login</button></form>'

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
