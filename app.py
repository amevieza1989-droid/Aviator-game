import os
from flask import Flask, request, redirect, render_template_string
from datetime import datetime
from collections import Counter

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_PG=False
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"): DATABASE_URL=DATABASE_URL.replace("postgres://","postgresql://",1)
    try: import psycopg2; USE_PG=True
    except: USE_PG=False

def get_conn():
    if USE_PG:
        import psycopg2; return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3; return sqlite3.connect("loto_togo.db")

def init_db():
    conn=get_conn(); cur=conn.cursor()
    if USE_PG:
        cur.execute('''CREATE TABLE IF NOT EXISTS tirages (id SERIAL PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date_tirage DATE, numero_tirage TEXT, total_haut INT, total_bas INT, date_saisie TEXT)''')
    else:
        cur.execute('''CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date_tirage DATE, numero_tirage TEXT, total_haut INT, total_bas INT, date_saisie TEXT)''')
    conn.commit(); cur.close(); conn.close()
init_db()

def fetch_all():
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT id, jour, heure, jeu, haut, bas, date_tirage, numero_tirage, total_haut, total_bas, date_saisie FROM tirages ORDER BY id DESC")
    r=cur.fetchall(); cur.close(); conn.close(); return r

def insert_tirage(j,h,jeu,haut,bas,dt,nt,ds):
    th=sum(int(x) for x in haut.split('-') if x.strip().isdigit())
    tb=sum(int(x) for x in bas.split('-') if x.strip().isdigit()) if bas else 0
    conn=get_conn(); cur=conn.cursor()
    q="INSERT INTO tirages (jour,heure,jeu,haut,bas,date_tirage,numero_tirage,total_haut,total_bas,date_saisie) VALUES (%s,%s,%s,%s,%s,%s)" if USE_PG else "INSERT INTO tirages (jour,heure,jeu,haut,bas,date_tirage,numero_tirage,total_haut,total_bas,date_saisie) VALUES (?,?,?,?,?,?,?,?,?,?)"
    cur.execute(q,(j,h,jeu,haut,bas,dt,nt,th,tb,ds)); conn.commit(); cur.close(); conn.close()

HOME_HTML="""<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;font-family:Arial;text-align:center;padding:10px}.card{background:#1a1a1a;padding:10px;margin:8px 0;border-radius:12px;border-left:5px solid gold;text-align:left;font-size:12px}.top{background:gold;color:#111;padding:15px;border-radius:15px}.btn{background:gold;color:#111;padding:12px 20px;border-radius:25px;text-decoration:none;font-weight:bold;display:inline-block;margin:5px}</style></head><body><div class="top"><h2>🏆 LOTO TOGO V10.6 PRO</h2><b>{{count}} tirages</b></div><a class="btn" href="/admin">🔐 SAISIE</a><a class="btn" href="/analyse" style="background:#222;color:gold;border:1px solid gold">📊 ANALYSE + WHATSAPP</a>{% for r in rows %}<div class="card"><b>Tr {{r[7]}} - {{r[6]}} | {{r[3]}}</b><br>H: {{r[4]}} [T:{{r[8]}}] | B: {{r[5]}} [T:{{r[9]}}]</div>{% endfor %}</body></html>"""

ADMIN_HTML="""<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}select,input{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:none}.row{display:flex;gap:8px}.row input{text-align:center;font-weight:bold;font-size:18px;border:2px solid #fff}.row input.dup{border:3px solid red;background:#ffcccc;color:red}button{background:gold;padding:16px;width:100%;border:none;border-radius:12px;font-weight:bold;font-size:18px;margin-top:15px}button:disabled{background:#555;color:#888}label{color:gold;font-weight:bold;margin-top:12px;display:block}#jeu_auto{background:#222;color:gold;font-weight:bold;font-size:22px;text-align:center;border:2px solid gold}#alerte{display:none;background:red;color:#fff;padding:12px;border-radius:10px;text-align:center;font-weight:bold;margin-top:10px}</style><script>
const grille={'LUNDI':{'09:00':'MATINALE','13:00':'DIAMANT','18:00':'GOLD'},'MARDI':{'09:00':'MATINALE','13:00':'CASH','18:00':'BOOM'},'MERCREDI':{'09:00':'MATINALE','13:00':'BENZ','18:00':'PRESTIGE'},'JEUDI':{'09:00':'MATINALE','13:00':'MILLION','18:00':'SUPER'},'VENDREDI':{'09:00':'MATINALE','13:00':'KADOO','18:00':'KING'},'SAMEDI':{'09:00':'MATINALE','13:00':'SAM','18:00':'BINGO'},'DIMANCHE':{'15:00':'DETENTE'}}
function updateHeures(){let j=document.getElementById('jour').value;let h=document.getElementById('heure');if(j=='DIMANCHE'){h.innerHTML='<option value="15:00">15H - DETENTE</option>';}else{h.innerHTML='<option value="09:00">09H - MATINALE</option><option value="13:00">13H - 5/90</option><option value="18:00">18H - 5/90</option>';}updateJeu();}
function updateJeu(){let j=document.getElementById('jour').value;let h=document.getElementById('heure').value;document.getElementById('jeu_auto').value=grille[j][h];}
function calc(){let dup=false;document.querySelectorAll('input[name^=h],input[name^=b]').forEach(i=>i.classList.remove('dup'));let hVals=[],bVals=[];document.querySelectorAll('input[name^=h]').forEach(i=>{if(i.value.trim()){let v=i.value.trim(); if(hVals.includes(v)){i.classList.add('dup');dup=true;} hVals.push(v);}});document.querySelectorAll('input[name^=b]').forEach(i=>{if(i.value.trim()){let v=i.value.trim(); if(bVals.includes(v)||hVals.includes(v)){i.classList.add('dup');dup=true;} bVals.push(v);}});document.querySelectorAll('input[name^=h]').forEach(i=>{if(i.value.trim()&&bVals.includes(i.value.trim())){i.classList.add('dup');dup=true;}});let al=document.getElementById('alerte');let btn=document.getElementById('btnSave');if(dup){al.style.display='block';al.innerText='⛔ ERREUR DOUBLON DETECTE! 23...23 INTERDIT';btn.disabled=true;}else{al.style.display='none';btn.disabled=false;}}
</script></head><body onload="updateHeures()"><h2 style="color:gold">🔐 V10.6 ANTI-DOUBLON</h2><form method="POST" oninput="calc()"><label>Date</label><input type="date" name="date_tirage" required value="{{today}}"><label>N° Tr</label><input type="text" name="numero_tirage" required><label>Jour</label><select name="jour" id="jour" onchange="updateHeures()" required><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select><label>Heure</label><select name="heure" id="heure" onchange="updateJeu()" required></select><label>Jeu</label><input name="jeu" id="jeu_auto" readonly><label>5 Numéros HAUT (WIN)</label><div class="row"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div><div id="bas_block"><label>5 Numéros BAS (MACHINE)</label><div class="row"><input name="b1"><input name="b2"><input name="b3"><input name="b4"><input name="b5"></div></div><div id="alerte"></div><button type="submit" id="btnSave">✅ ENREGISTRER 2 TOTAUX</button></form></body></html>"""

@app.route('/')
def home():
    rows=fetch_all()
    return render_template_string(HOME_HTML, rows=rows[:60], count=len(rows))

@app.route('/admin', methods=['GET','POST'])
def admin_route():
    if request.method=='POST':
        hl=[request.form[f'h{i}'].strip() for i in range(1,6)]
        bl=[request.form.get(f'b{i}','').strip() for i in range(1,6) if request.form.get(f'b{i}','').strip()!='']
        if len(set(hl))!=5 or (bl and len(set(bl))!=len(bl)) or (bl and set(hl)&set(bl)):
            return "<h1 style='color:red'>⛔ DOUBLON</h1><a href='/admin'>Retour</a>",400
        insert_tirage(request.form['jour'],request.form['heure'],request.form['jeu'],"-".join(hl),"-".join(bl) if bl else "",request.form['date_tirage'],request.form['numero_tirage'],datetime.now().strftime("%d/%m %H:%M"))
        return redirect('/admin')
    return render_template_string(ADMIN_HTML, today=datetime.now().strftime("%Y-%m-%d"))

@app.route('/analyse')
def analyse():
    rows=fetch_all()
    if not rows:
        return "Pas de tirage"
    # GLOBAL
    all_nums=[]
    for r in rows:
        for x in (r[4]+"-"+(r[5] or "")).split("-"):
            if x.strip().isdigit(): all_nums.append(x.strip())
    cnt=Counter(all_nums)
    total=len(all_nums)
    top=sorted(cnt.items(), key=lambda x:x[1], reverse=True)[:15]
    top_data=[(n,c,round(c/total*100,1)) for n,c in top]
    bottom=sorted(cnt.items(), key=lambda x:x[1])[:5] # retard

    # Par JEU
    from collections import defaultdict
    jeux=defaultdict(list)
    for r in rows:
        jeux[r[3]].append(r)
    pred_html=""
    for jeu_name, lst in jeux.items():
        nums=[]
        for r in lst:
            for x in (r[4]+"-"+(r[5] or "")).split("-"):
                if x.strip().isdigit(): nums.append(x.strip())
        c=Counter(nums)
        chauds=c.most_common(3)
        retards=sorted(c.items(), key=lambda x:x[1])[:3]
        pred_html+=f"<div class='box'><h3 style='color:gold'>{jeu_name} - {len(lst)} tirages</h3><p><span style='color:#00ff88'>Chauds:</span> "
        for n,cc in chauds:
            p=round(cc/len(nums)*100,1) if nums else 0
            pred_html+=f"<span class='badge hot'>{n} {p}%</span> "
        pred_html+=f"</p><p><span style='color:#ff4444'>Retard (à jouer):</span> "
        for n,cc in retards:
            pred_html+=f"<span class='badge' style='background:#331111;color:#ff8888;border-color:red'>{n}</span> "
        pred_html+="</p></div>"

    # Message WhatsApp
    chauds_msg=" ".join([n for n,c,p in top_data[:5]])
    retards_msg=" ".join([n for n,c in bottom])
    whatsapp_text=f"""🎯 LOTO TOGO - PRONO DU JOUR
A TENTER (retard): {retards_msg}

⚠️ Numéros en retard général: {chauds_msg}

💡 Mon prono pour le prochain tirage: {top_data[0][0] if top_data else ''} {top_data[1][0] if len(top_data)>1 else ''} {top_data[2][0] if len(top_data)>2 else ''} {bottom[0][0] if bottom else ''} {bottom[1][0] if len(bottom)>1 else ''}

👉 Abonnement VIP: 500F/jour - 2000F/semaine
📲 Inbox pour recevoir le 2 sûr du jour

#LONATO #LotoTogo #Prono"""

    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
    body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}
   .top{{background:gold;color:#111;padding:15px;border-radius:15px;text-align:center}}
   .box{{background:#151515;padding:14px;margin:12px 0;border-radius:15px;border:1px solid #333}}
   .badge{{display:inline-block;background:#222;border:1px solid gold;color:gold;padding:7px 12px;border-radius:20px;margin:4px;font-weight:bold}}
   .hot{{background:gold;color:#111}}
   .what{{background:#0a1a0a;border:2px solid gold;border-radius:15px;padding:15px}}
    pre{{background:#111;color:#0f0;padding:12px;border-radius:10px;white-space:pre-wrap;font-size:13px}}
    a{{color:gold}}
    </style></head><body>
    <div class="top"><h2>📊 V10.6 ANALYSE PRO + WHATSAPP</h2><p>{len(rows)} tirages | Base à vie</p></div>
    <p><a href="/">← Accueil</a> | <a href="/admin">Saisie</a></p>

    <div class="box"><h3>🔥 TOP 15 GLOBAL</h3>
    """ + "".join([f"<span class='badge hot'>{n} {p}% ({c}x)</span>" for n,c,p in top_data]) + f"""
    </div>
    <div class="box"><h3>🎯 Prédiction par JEU LONATO</h3></div>
    {pred_html}
    <div class="what"><h3>💰 MESSAGE WHATSAPP PRÊT À VENDRE - COPIE/COLLE</h3>
    <pre id="msg">{whatsapp_text}</pre>
    <button onclick="navigator.clipboard.writeText(document.getElementById('msg').innerText);alert('Copié!')" style="background:gold;color:#111;padding:14px;width:100%;border:none;border-radius:12px;font-weight:bold;font-size:16px">📋 COPIER LE MESSAGE</button>
    </div>
    <div class="box"><h3>📊 HISTORIQUE 2 TOTAUX</h3>
    """ + "".join([f"<p style='font-size:11px'>Tr {r[7]} - {r[6]} - {r[3]} H:{r[8]} B:{r[9]} - {r[4]} | {r[5]}</p>" for r in rows[:30]]) + """
    </div></body></html>
    """)

if __name__=="__main__":
    app.run()
