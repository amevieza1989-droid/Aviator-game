from flask import Flask, request, render_template_string, redirect
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os, urllib.parse

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

def get_conn(): return sqlite3.connect(DB)
def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
    conn.commit()
    c.execute("SELECT COUNT(*) FROM tirages")
    if c.fetchone()[0]==0:
        for j,h,je,ht,bs,dt,num in INIT_DATA:
            th=sum(int(x) for x in ht.split('-') if x.isdigit())
            tb=sum(int(x) for x in bs.split('-') if x.isdigit()) if bs else 0
            c.execute("INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",(j,h,je,ht,bs,dt,num,datetime.now().strftime("%d/%m %H:%M"),th,tb))
        conn.commit()
    conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero,created):
    haut=haut.strip(); bas=(bas or "").strip()
    th=sum(int(x.strip()) for x in haut.split('-') if x.strip().isdigit())
    tb=sum(int(x.strip()) for x in bas.split('-') if x.strip().isdigit()) if bas else 0
    conn=get_conn();c=conn.cursor()
    c.execute("SELECT id FROM tirages WHERE jeu=? AND numero=? AND date=?",(jeu,numero,date))
    if c.fetchone(): conn.close(); return False
    c.execute("INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",(jour,heure,jeu,haut,bas,date,numero,created,th,tb))
    conn.commit();conn.close();return True

def fetch_all():
    conn=get_conn();c=conn.cursor()
    c.execute("SELECT * FROM tirages ORDER BY date DESC, id DESC")
    rows=c.fetchall();conn.close();return rows

@app.route('/')
def home():
    rows=fetch_all()
    rows_html=""
    for r in rows[:30]:
        is5 = r[2] in ["13:00","18:00"]
        wa = urllib.parse.quote(f"LONATO {r[3]} {r[6]} - {r[4]} {r[5] if r[5] else ''}")
        rows_html+=f"<div style='background:#151515;padding:10px;margin:6px 0;border-radius:10px;border-left:3px solid gold'><b>{r[1]} {r[2]} {r[3]} #{r[7]}</b> {r[6]}<br>H:{r[4]} { 'B:'+r[5] if r[5] else ''}<br><a href='https://wa.me/?text={wa}' style='color:#25D366;font-weight:bold'>↗ WhatsApp</a></div>"
    return render_template_string(f"""
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}}.btn{{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:15px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}}</style></head><body>
<h2 style="background:gold;color:#111;padding:15px;border-radius:15px;text-align:center">LOTO V12 - {len(rows)} tirages</h2>
<a class="btn" href="/saisir">SAISIR 1 TIRAGE</a><a class="btn" href="/analyse">ANALYSE VENDEUR COMME SCREENSHOT</a>
{rows_html}
</body></html>
""")

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method=='POST':
        insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),request.form.get('haut'),request.form.get('bas'),request.form.get('date'),request.form.get('numero'),datetime.now().strftime("%d/%m %H:%M"))
        return redirect('/')
    return """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}input,select{width:100%;padding:12px;margin:6px 0;background:#111;color:#fff;border:1px solid gold;border-radius:10px}button{background:gold;color:#111;padding:15px;width:100%;border:none;border-radius:12px;font-weight:bold}.hidden{display:none}</style>
<script>
const planning={"LUNDI":{"09:00":"MATINALE","13:00":"DIAMANT","18:00":"GOLD"},"MARDI":{"09:00":"MATINALE","13:00":"CASH","18:00":"BOOM"},"MERCREDI":{"09:00":"MATINALE","13:00":"BENZ","18:00":"PRESTIGE"},"JEUDI":{"09:00":"MATINALE","13:00":"MILLION","18:00":"SUPER"},"VENDREDI":{"09:00":"MATINALE","13:00":"KADOO","18:00":"KING"},"SAMEDI":{"09:00":"MATINALE","13:00":"SAM","18:00":"BINGO"},"DIMANCHE":{"15:00":"DETENTE"}};
function updateForm(){
 let j=document.getElementById('jour').value; let h=document.getElementById('heure').value; let s=document.getElementById('jeu');
 if(planning[j]&&planning[j][h]){s.value=planning[j][h];}
 let basDiv=document.getElementById('basDiv');
 if(h=='13:00' || h=='18:00'){basDiv.classList.add('hidden'); document.getElementById('bas').required=false;}
 else {basDiv.classList.remove('hidden'); document.getElementById('bas').required=true;}
}
</script></head><body>
<h2 style="color:gold">SAISIR V12</h2>
<form method="POST">
Jour:<select id="jour" name="jour" onchange="updateForm()"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
Heure:<select id="heure" name="heure" onchange="updateForm()"><option>09:00</option><option>13:00</option><option>15:00</option><option>18:00</option></select>
Jeu:<select id="jeu" name="jeu"><option>MATINALE</option><option>DIAMANT</option><option>GOLD</option><option>CASH</option><option>BOOM</option><option>BENZ</option><option>PRESTIGE</option><option>MILLION</option><option>SUPER</option><option>KADOO</option><option>KING</option><option>SAM</option><option>BINGO</option><option>DETENTE</option></select>
Numero:<input name="numero" required>Date:<input name="date" type="date" value="2026-10-16" required>
Haut:<input name="haut" required><div id="basDiv">Bas:<input id="bas" name="bas"></div><br><button>ENREGISTRER</button>
</form><a href="/" style="color:gold">Accueil</a><script>updateForm();</script></body></html>
"""

@app.route('/analyse')
def analyse():
    rows=fetch_all()
    jeux=defaultdict(list)
    for r in rows: jeux[r[3]].append(r)
    page=""
    for jeu_name,lst in jeux.items():
        nums=[]
        for r in lst:
            for x in (r[4]+"-"+(r[5] or "")).split("-"):
                if x.strip().isdigit(): nums.append(x.strip().zfill(2))
        total=len(nums)
        cnt=Counter(nums)
        # Chauds = les plus fréquents
        chauds=cnt.most_common(6)
        # Retard = les moins fréquents + jamais sortis
        all_nums=[str(i).zfill(2) for i in range(0,91)]
        retard=[]
        for n in all_nums:
            if n not in cnt: retard.append(n)
        # Si pas assez de jamais sortis, prends les moins joués
        if len(retard)<3:
            for n,c in cnt.most_common()[-3:]:
                if n not in retard: retard.append(n)
        retard=retard[:6]

        # Blocs HTML comme ton screenshot
        chaud_html=""
        for n,c in chauds:
            pct= round(c/total*100,1) if total>0 else 0
            chaud_html+=f"<span style='display:inline-block;background:#FFD700;color:#111;padding:8px 14px;border-radius:20px;margin:4px;font-weight:bold;border:2px solid #111'>{n} {pct}% ({c}x)</span>"
        retard_html=""
        for n in retard[:3]:
            retard_html+=f"<span style='display:inline-block;background:#2a0a0a;color:#ff6b6b;padding:8px 14px;border-radius:20px;margin:4px;font-weight:bold;border:1px solid #ff6b6b'>{n}</span>"

        # Prono = 2 chauds + 2 retards + 1 au milieu
        prono_nums=[]
        if len(chauds)>=2: prono_nums+=[chauds[0][0], chauds[1][0]]
        if len(retard)>=2: prono_nums+=[retard[0], retard[1]]
        if len(chauds)>=3: prono_nums.append(chauds[2][0])
        prono_str=" ".join(prono_nums[:5])

        wa_text=f"""A TENTER (retard): {' '.join(retard[:2])}

⚠️ Numéros en retard général: {' '.join(retard[:5])}

💡 Mon prono pour le prochain tirage: {prono_str}

👉 Abonnement VIP: 500F/jour - 2000F/semaine
📲 Inbox pour recevoir le 2 sûr du jour

#LONATO #LotoTogo #Prono"""

        wa_encoded=urllib.parse.quote(wa_text)

        page+=f"""
<div style='background:#141414;padding:15px;margin:12px 0;border-radius:15px;border:1px solid #222'>
<div style='display:flex;flex-wrap:wrap'>{chaud_html}</div>
<br>
<div style='background:#0f0f0f;padding:12px;border-radius:12px'>
<div style='color:#fff;font-weight:bold;margin-bottom:8px'>🎯 Prédiction par JEU LONATO</div>
<div style='color:gold;font-weight:bold;font-size:18px'>{jeu_name} - {len(lst)} tirages</div>
<div style='margin-top:10px'><span style='color:#00ff88'>Chauds:</span> {''.join([f"<span style='background:#111;border:1px solid gold;color:gold;padding:6px 12px;border-radius:20px;margin:3px;display:inline-block'>{n} {round(c/total*100,1) if total else 0}%</span>" for n,c in chauds[:3]])}
</div>
<div style='margin-top:10px'><span style='color:#ff6b6b'>Retard (à jouer):</span> {retard_html}</div>
</div>

<div style='margin-top:15px;background:#000;border:2px solid gold;border-radius:15px;padding:12px'>
<div style='color:#fff;font-weight:bold'>💰 MESSAGE WHATSAPP PRÊT À VENDRE - COPIE/COLLE</div>
<textarea id='msg_{jeu_name}' style='width:100%;height:160px;background:#0a0a0a;color:#00ff66;border:none;margin-top:8px;padding:10px;font-family:monospace'>{wa_text}</textarea>
<button onclick="navigator.clipboard.writeText(document.getElementById('msg_{jeu_name}').value); alert('Copié!')" style='width:100%;background:gold;color:#111;padding:12px;border:none;border-radius:12px;font-weight:bold;margin-top:8px'>📋 COPIER LE MESSAGE</button>
<a href='https://wa.me/?text={wa_encoded}' style='display:block;text-align:center;background:#25D366;color:#fff;padding:12px;border-radius:12px;text-decoration:none;font-weight:bold;margin-top:6px'>↗ ENVOYER SUR WHATSAPP</a>
</div>
</div>
"""
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'></head><body style='background:#000;color:#fff;font-family:Arial;padding:8px'><a href='/' style='color:gold'>⬅ Accueil</a><h2 style='color:gold;text-align:center'>ANALYSE VENDEUR V12</h2>{page}</body></html>"

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
