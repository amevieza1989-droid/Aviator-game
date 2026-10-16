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
    return render_template_string(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}}.btn{{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:15px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}}</style></head><body><h2 style='background:gold;color:#111;padding:15px;border-radius:15px;text-align:center'>LOTO V12.1 CAGE - {len(rows)} tirages</h2><a class='btn' href='/saisir'>SAISIR EN CAGE</a><a class='btn' href='/analyse'>ANALYSE VENDEUR</a></body></html>")

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method=='POST':
        # Récupère les 10 cases
        h1=request.form.get('h1','');h2=request.form.get('h2','');h3=request.form.get('h3','');h4=request.form.get('h4','');h5=request.form.get('h5','')
        b1=request.form.get('b1','');b2=request.form.get('b2','');b3=request.form.get('b3','');b4=request.form.get('b4','');b5=request.form.get('b5','')
        haut="-".join([x for x in [h1,h2,h3,h4,h5] if x.strip()!=''])
        bas="-".join([x for x in [b1,b2,b3,b4,b5] if x.strip()!=''])
        insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),haut,bas,request.form.get('date'),request.form.get('numero'),datetime.now().strftime("%d/%m %H:%M"))
        return redirect('/')
    return """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}
select,input{width:100%;padding:12px;margin:5px 0;background:#fff;color:#111;border-radius:10px;border:none;font-weight:bold;font-size:16px}
.cage{display:flex;gap:6px;margin:8px 0}
.cage input{width:18%;text-align:center;padding:12px 2px;background:#fff;color:#111;border-radius:10px;font-size:18px;font-weight:bold;border:2px solid #fff}
label{color:gold;font-weight:bold;margin-top:12px;display:block}
.jeu-box{background:#0a0a0a;border:2px solid gold;color:gold;text-align:center;padding:14px;border-radius:12px;font-weight:bold;font-size:20px;margin:8px 0}
.total{color:gold;text-align:center;font-weight:bold;margin:12px 0;font-size:16px}
button{background:gold;color:#111;padding:15px;width:100%;border:none;border-radius:12px;font-weight:bold;font-size:16px}
.hidden{display:none}
</style>
<script>
const planning={"LUNDI":{"09:00":"MATINALE","13:00":"DIAMANT","18:00":"GOLD"},"MARDI":{"09:00":"MATINALE","13:00":"CASH","18:00":"BOOM"},"MERCREDI":{"09:00":"MATINALE","13:00":"BENZ","18:00":"PRESTIGE"},"JEUDI":{"09:00":"MATINALE","13:00":"MILLION","18:00":"SUPER"},"VENDREDI":{"09:00":"MATINALE","13:00":"KADOO","18:00":"KING"},"SAMEDI":{"09:00":"MATINALE","13:00":"SAM","18:00":"BINGO"},"DIMANCHE":{"15:00":"DETENTE"}};
function calc(){
 let h=0; for(let i=1;i<=5;i++){let v=document.getElementById('h'+i).value; if(v!='' &&!isNaN(v)) h+=parseInt(v);}
 let b=0; for(let i=1;i<=5;i++){let v=document.getElementById('b'+i).value; if(v!='' &&!isNaN(v)) b+=parseInt(v);}
 let heure=document.getElementById('heure').value;
 if(heure=='13:00' || heure=='18:00'){ document.getElementById('total').innerText='TOTAL: '+h; }
 else { document.getElementById('total').innerText='TOTAL HAUT (WIN): '+h+' | TOTAL BAS (MACHINE): '+b; }
}
function updateForm(){
 let j=document.getElementById('jour').value; let h=document.getElementById('heure').value;
 let jeuSel=document.getElementById('jeu'); let labelHeure=document.getElementById('labelHeure');
 if(planning[j]&&planning[j][h]){jeuSel.innerText=planning[j][h]; document.getElementById('jeu_input').value=planning[j][h];}
 if(j=='DIMANCHE'){ labelHeure.options.length=0; let opt=document.createElement('option'); opt.value='15:00'; opt.text='15H - DETENTE (10 numéros)'; labelHeure.add(opt); }
 else {
   labelHeure.options.length=0;
   let o1=document.createElement('option'); o1.value='09:00'; o1.text='09H - MATINALE (10 numéros)'; labelHeure.add(o1);
   let o2=document.createElement('option'); o2.value='13:00'; o2.text='13H - '+ (planning[j]&&planning[j]['13:00']?planning[j]['13:00']:'') +' (5 numéros)'; labelHeure.add(o2);
   let o3=document.createElement('option'); o3.value='18:00'; o3.text='18H - '+ (planning[j]&&planning[j]['18:00']?planning[j]['18:00']:'') +' (5 numéros)'; labelHeure.add(o3);
   labelHeure.value=h;
 }
 let basDiv=document.getElementById('basDiv');
 if(h=='13:00' || h=='18:00'){basDiv.classList.add('hidden');}
 else {basDiv.classList.remove('hidden');}
 calc();
}
</script>
</head><body>
<label>N° Tr</label><input name="numero" form="mainForm" placeholder="22" required>
<label>Jour</label><select id="jour" onchange="updateForm()"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
<label>Heure</label><select id="heure" onchange="updateForm()"></select>
<label>Jeu</label><div id="jeu" class="jeu-box">MATINALE</div>
<input type="hidden" id="jeu_input" name="jeu" form="mainForm" value="MATINALE">
<form id="mainForm" method="POST" oninput="calc()">
<input type="hidden" name="jour" id="jour_input">
<input type="hidden" name="heure" id="heure_input">
<input type="hidden" name="date" value="2026-10-16">

<label>5 Numéros HAUT (WIN)</label>
<div class="cage"><input id="h1" name="h1" type="number" min="0" max="90"><input id="h2" name="h2" type="number"><input id="h3" name="h3" type="number"><input id="h4" name="h4" type="number"><input id="h5" name="h5" type="number"></div>
<div id="basDiv">
<label>5 Numéros BAS (MACHINE)</label>
<div class="cage"><input id="b1" name="b1" type="number"><input id="b2" name="b2" type="number"><input id="b3" name="b3" type="number"><input id="b4" name="b4" type="number"><input id="b5" name="b5" type="number"></div>
</div>
<div id="total" class="total">TOTAL HAUT (WIN): 0 | TOTAL BAS (MACHINE): 0</div>
<button type="submit">✅ ENREGISTRER 2 TOTAUX</button>
</form>
<script>
document.getElementById('mainForm').addEventListener('submit', function(){
 document.getElementById('jour_input').value=document.getElementById('jour').value;
 document.getElementById('heure_input').value=document.getElementById('heure').value;
});
updateForm();
</script>
<a href="/" style="color:gold">Accueil</a>
</body></html>
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
        chauds=cnt.most_common(6)
        all_nums=[str(i).zfill(2) for i in range(0,91)]
        retard=[n for n in all_nums if n not in cnt][:5]
        if len(retard)<3: retard+= [n for n,c in cnt.most_common()[-3:] if n not in retard]
        prono=" ".join([c[0] for c in chauds[:2]] + retard[:3])
        wa_text=f"A TENTER (retard): {' '.join(retard[:2])}\n\n⚠️ Numéros en retard général: {' '.join(retard)}\n\n💡 Mon prono pour le prochain tirage: {prono}\n\n👉 Abonnement VIP: 500F/jour - 2000F/semaine\n📲 Inbox pour recevoir le 2 sûr du jour\n\n#LONATO #LotoTogo #Prono"
        wa_encoded=urllib.parse.quote(wa_text)
        chaud_html="".join([f"<span style='display:inline-block;background:#FFD700;color:#111;padding:8px 14px;border-radius:20px;margin:4px;font-weight:bold'>{n} {round(c/total*100,1) if total else 0}% ({c}x)</span>" for n,c in chauds])
        retard_html="".join([f"<span style='display:inline-block;background:#2a0a0a;color:#ff6b6b;padding:8px 14px;border-radius:20px;margin:4px;font-weight:bold;border:1px solid #ff6b6b'>{n}</span>" for n in retard[:3]])
        page+=f"<div style='background:#141414;padding:15px;margin:12px 0;border-radius:15px'><div style='display:flex;flex-wrap:wrap'>{chaud_html}</div><div style='background:#0f0f0f;padding:12px;border-radius:12px;margin-top:10px'><div style='color:#fff;font-weight:bold'>🎯 Prédiction par JEU LONATO</div><div style='color:gold;font-weight:bold'>{jeu_name} - {len(lst)} tirages</div><div style='margin-top:8px'><span style='color:#00ff88'>Chauds:</span> {chaud_html[:200]}</div><div style='margin-top:8px'><span style='color:#ff6b6b'>Retard (à jouer):</span> {retard_html}</div></div><div style='margin-top:12px;background:#000;border:2px solid gold;border-radius:15px;padding:12px'><div style='color:#fff;font-weight:bold'>💰 MESSAGE WHATSAPP PRÊT À VENDRE - COPIE/COLLE</div><textarea id='msg_{jeu_name}' style='width:100%;height:150px;background:#0a0a0a;color:#00ff66;border:none;margin-top:8px'>{wa_text}</textarea><button onclick=\"navigator.clipboard.writeText(document.getElementById('msg_{jeu_name}').value)\" style='width:100%;background:gold;color:#111;padding:12px;border:none;border-radius:12px;font-weight:bold;margin-top:8px'>📋 COPIER LE MESSAGE</button><a href='https://wa.me/?text={wa_encoded}' style='display:block;text-align:center;background:#25D366;color:#fff;padding:12px;border-radius:12px;text-decoration:none;font-weight:bold;margin-top:6px'>↗ ENVOYER SUR WHATSAPP</a></div></div>"
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:8px'><a href='/' style='color:gold'>⬅ Accueil</a><h2 style='color:gold;text-align:center'>ANALYSE VENDEUR V12.1</h2>{page}</body></html>"

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
