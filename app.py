from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime
from collections import Counter
import random

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
.card{background:#1a1a1a;padding:12px;margin:8px 0;border-radius:12px;border-left:5px solid gold;text-align:left}
.top{background:gold;color:#111;padding:15px;border-radius:15px}
.btn{background:gold;color:#111;padding:12px 20px;border-radius:25px;text-decoration:none;font-weight:bold;display:inline-block;margin:5px}
.btn2{background:#222;color:gold;border:1px solid gold;padding:12px 20px;border-radius:25px;text-decoration:none;display:inline-block;margin:5px}
</style></head>
<body>
<div class="top"><h2>🏆 LOTO TOGO V9</h2><b>{{count}} tirages - Version Business</b></div>
<a class="btn" href="/admin">🔐 SAISIE</a><a class="btn2" href="/analyse">📊 ANALYSE VIP + WHATSAPP</a>
{% for r in results %}
<div class="card"><b>{{r[1]}} {{r[2]}} - {{r[3]}}</b><br>
{% if r[5]=='' %}5 Numéros: <b style="color:#00ff88">{{r[4]}}</b>
{% else %}H: <b style="color:#00ff88">{{r[4]}}</b><br>B: <b style="color:#ffcc00">{{r[5]}}</b>{% endif %}
<br><small>{{r[6]}}</small></div>
{% endfor %}
</body></html>
"""

ANALYSE_V9 = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}
.top{background:gold;color:#111;padding:15px;border-radius:15px;text-align:center}
.box{background:#151515;padding:14px;margin:12px 0;border-radius:15px;border:1px solid #222}
.badge{display:inline-block;background:#222;border:1px solid gold;color:gold;padding:7px 12px;border-radius:20px;margin:4px;font-weight:bold}
.hot{background:gold;color:#111;border-color:gold}
.cold{background:#300;color:#ff5555;border-color:#ff5555}
.pct{font-size:11px;opacity:0.7}
textarea{width:100%;height:240px;background:#000;color:#0f0;padding:12px;border-radius:10px;border:1px solid #333;font-size:13px}
a{color:gold;text-decoration:none}
h3{margin:5px 0}
</style></head>
<body>
<div class="top"><h2>📊 V9 - ANALYSE BUSINESS</h2><p>{{total}} tirages analysés - Lomé</p></div>
<p><a href="/">← Accueil</a> | <a href="/admin">Saisie →</a></p>

<div class="box">
<h3>🔥 TOP 10 CHAUDS (Togo entier)</h3>
<p style="font-size:12px;color:#aaa">Probabilité de sortie</p>
{% for num, cnt, pct in top_global %}
<span class="badge hot">{{num}} <span class="pct">{{pct}}% ({{cnt}}x)</span></span>
{% endfor %}
</div>

<div class="box">
<h3>🎯 Prédiction par JEU LONATO</h3>
{% for jeu, data in par_jeu.items() %}
<p><b style="color:gold;font-size:16px">{{jeu}}</b> - {{data['total']}} tirages<br>
<span style="color:#00ff88">Chauds:</span> {% for n,c,p in data['tops'] %}<span class="badge">{{n}} {{p}}%</span>{% endfor %}<br>
<span style="color:#ff5555">Retard (à jouer):</span> {% for n in data['retards'] %}<span class="badge cold">{{n}}</span>{% endfor %}
</p>
<hr style="border-color:#222">
{% endfor %}
</div>

<div class="box" style="border:2px solid gold">
<h3>💰 MESSAGE WHATSAPP PRÊT À VENDRE - COPIE/COLLE</h3>
<textarea id="msg">
🔥 LOTO TOGO VIP - ANALYSE DU {{date_jour}}

📊 Basé sur {{total}} tirages officiels LONATO

🏆 TOP 5 Numéros Chauds du moment:
{% for n,c,p in top_global[:5] %}➡️ {{n}} - sorti {{c}} fois ({{p}}%)
{% endfor %}

{% for jeu, data in par_jeu.items() %}
🎯 {{jeu}} ({{data['total']}} tirages):
   Chauds: {% for n,c,p in data['tops'][:3] %}{{n}} {% endfor %}
   À TENTER (retard): {% for n in data['retards'][:2] %}{{n}} {% endfor %}

{% endfor %}
⚠️ Numéros en retard général: {% for n in retard_global[:5] %}{{n}} {% endfor %}

💡 Mon prono pour le prochain tirage: {% for n in prono_jour %}{{n}} {% endfor %}

👉 Abonnement VIP: 500F/jour - 2000F/semaine
📲 Inbox pour recevoir le 2 sûr du jour

#LONATO #LotoTogo #Prono
</textarea>
<br><button onclick="copyMsg()" style="background:gold;color:#111;padding:12px;width:100%;border:none;border-radius:10px;font-weight:bold;margin-top:8px">📋 COPIER LE MESSAGE</button>
</div>

<script>
function copyMsg(){ let t=document.getElementById('msg'); t.select(); document.execCommand('copy'); alert('Message copié! Colle sur WhatsApp'); }
</script>
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
const grille = {'LUNDI':{'09:00':'MATINALE','13:00':'DIAMANT','18:00':'GOLD'},'MARDI':{'09:00':'MATINALE','13:00':'CASH','18:00':'BOOM'},'MERCREDI':{'09:00':'MATINALE','13:00':'BENZ','18:00':'PRESTIGE'},'JEUDI':{'09:00':'MATINALE','13:00':'MILLION','18:00':'SUPER'},'VENDREDI':{'09:00':'MATINALE','13:00':'KADOO','18:00':'KING'},'SAMEDI':{'09:00':'MATINALE','13:00':'SAM','18:00':'BINGO'},'DIMANCHE':{'15:00':'DETENTE'}}
function updateHeures(){ let j=document.getElementById('jour').value; let h=document.getElementById('heure'); if(j=='DIMANCHE'){h.innerHTML='<option value="15:00">15H - DETENTE (10 numéros)</option>';} else {h.innerHTML='<option value="09:00">09H - MATINALE (10 numéros)</option><option value="13:00">13H - 5 numéros</option><option value="18:00">18H - 5 numéros</option>';} updateJeu(); }
function updateJeu(){ let j=document.getElementById('jour').value; let h=document.getElementById('heure').value; document.getElementById('jeu_auto').value=grille[j][h]; let is10=grille[j][h]=='MATINALE'||grille[j][h]=='DETENTE'; document.getElementById('bas_block').style.display=is10?'block':'none'; document.getElementById('label_haut').innerText=is10?'5 Numéros du HAUT':'5 Numéros GAGNANTS (5/90)'; document.querySelectorAll('.b_input').forEach(i=>{i.required=is10; if(!is10)i.value='';}); }
</script>
</head>
<body onload="updateHeures()">
<h2 style="color:gold">🔐 COLLECTE V9</h2>
<form method="POST">
<label>Jour</label><select name="jour" id="jour" onchange="updateHeures()" required><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
<label>Heure</label><select name="heure" id="heure" onchange="updateJeu()" required></select>
<label>Jeu (auto)</label><input name="jeu" id="jeu_auto" readonly>
<label id="label_haut">5 Numéros</label><div class="row"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div>
<div id="bas_block"><label>5 Numéros du BAS</label><div class="row"><input name="b1" class="b_input"><input name="b2" class="b_input"><input name="b3" class="b_input"><input name="b4" class="b_input"><input name="b5" class="b_input"></div></div>
<button type="submit">✅ ENREGISTRER</button>
</form><p><a href="/" style="color:gold">← Accueil</a> | <a href="/analyse" style="color:gold">Analyse VIP →</a></p>
</body></html>
"""

@app.route('/')
def home():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tirages ORDER BY id DESC LIMIT 40")
    results = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM tirages")
    count = cur.fetchone()[0]
    conn.close()
    return render_template_string(HOME, results=results, count=count)

@app.route('/analyse')
def analyse():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT jeu, haut, bas, id FROM tirages ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    if len(rows)<1:
        return "Saisis au moins 2 tirages dans /admin"
    all_nums=[]
    par_jeu_raw={}
    last_seen={}
    for jeu, haut, bas, tid in [(r[0],r[1],r[2],r[3]) for r in rows]:
        haut_list = [x.strip() for x in haut.split('-') if x.strip().isdigit() or x.strip()]
        bas_list = [x.strip() for x in bas.split('-') if x.strip()] if bas else []
        nums = haut_list + bas_list
        for idx, n in enumerate(nums):
            if not n.isdigit(): continue
            n_clean = n.lstrip('0') or '0'
            # garde original pour affichage
            all_nums.append(n)
            par_jeu_raw.setdefault(jeu, []).append(n)
            if n not in last_seen:
                last_seen[n]=tid

    # Global
    total_boules = len(all_nums)
    cnt_global = Counter(all_nums)
    top_global = []
    for num, c in cnt_global.most_common(10):
        pct = round((c/total_boules)*100,1) if total_boules else 0
        top_global.append((num,c,pct))

    # Par jeu
    par_jeu={}
    for jeu, lst in par_jeu_raw.items():
        cnt = Counter(lst)
        total_jeu = len(lst)
        tops=[]
        for num,c in cnt.most_common(3):
            pct = round((c/total_jeu)*100,1)
            tops.append((num,c,pct))
        # retards = moins sortis
        least = cnt.most_common()[:-4:-1]
        retards = [n for n,_ in least]
        # si pas assez, ajoute des numéros jamais sortis
        if len(retards)<3:
            for i in range(1,91):
                s=str(i)
                if s not in cnt:
                    retards.append(s)
                    if len(retards)>=3: break
        par_jeu[jeu]={'tops':tops, 'retards':retards[:3], 'total': len([r for r in rows if r[0]==jeu])}

    retard_global = sorted(last_seen.items(), key=lambda x: x[1]) # plus ancien en premier
    retard_global = [n for n,_ in retard_global[:10]]

    # Prono du jour = mix chaud + retard
    prono_jour=[]
    if top_global:
        prono_jour = [top_global[0][0]]
        if retard_global: prono_jour.append(retard_global[0])
        if len(top_global)>1: prono_jour.append(top_global[1][0])
        # complète aléatoire pour faire 5
        while len(prono_jour)<5:
            r=str(random.randint(1,90))
            if r not in prono_jour: prono_jour.append(r)

    date_jour = datetime.now().strftime("%d/%m/%Y")
    return render_template_string(ANALYSE_V9, top_global=top_global, par_jeu=par_jeu, total=len(rows), retard_global=retard_global, prono_jour=prono_jour, date_jour=date_jour)

@app.route('/admin', methods=['GET','POST'])
def admin():
    conn = sqlite3.connect(DB)
    if request.method=='POST':
        haut=f"{request.form['h1']}-{request.form['h2']}-{request.form['h3']}-{request.form['h4']}-{request.form['h5']}"
        b1=request.form.get('b1','').strip()
        bas=f"{request.form['b1']}-{request.form['b2']}-{request.form['b3']}-{request.form['b4']}-{request.form['b5']}" if b1 else ""
        conn.execute("INSERT INTO tirages (jour, heure, jeu, haut, bas, date_saisie) VALUES (?,?,?,?,?,?)",
                     (request.form['jour'], request.form['heure'], request.form['jeu'], haut, bas, datetime.now().strftime("%d/%m %H:%M")))
        conn.commit()
    conn.close()
    return render_template_string(ADMIN)

if __name__=="__main__":
    app.run()
