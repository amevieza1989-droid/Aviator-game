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
            th=sum(int(x) for x in ht.split('-') if x.isdigit() and x!="00")
            tb=sum(int(x) for x in bs.split('-') if x.isdigit() and x!="00") if bs else 0
            c.execute("INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",(j,h,je,ht,bs,dt,num,datetime.now().strftime("%d/%m %H:%M"),th,tb))
        conn.commit()
    conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero,created):
    # CORRECTION 01-90 : on ignore 00
    th=sum(int(x.strip()) for x in haut.split('-') if x.strip().isdigit() and x.strip()!="00" and x.strip()!="0")
    tb=sum(int(x.strip()) for x in bas.split('-') if x.strip().isdigit() and x.strip()!="00" and x.strip()!="0") if bas else 0
    conn=get_conn();c=conn.cursor()
    c.execute("INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",(jour,heure,jeu,haut,bas,date,numero,created,th,tb))
    conn.commit();conn.close();return True

def fetch_all():
    conn=get_conn();c=conn.cursor()
    c.execute("SELECT * FROM tirages ORDER BY date DESC, id DESC")
    rows=c.fetchall();conn.close();return rows

@app.route('/')
def home():
    rows=fetch_all()
    html_rows=""
    for r in rows[:30]:
        wa = urllib.parse.quote(f"LONATO {r[1]} {r[2]} {r[3]} #{r[7]} {r[6]} - WIN:{r[4]} {'MACHINE:'+r[5] if r[5] else ''} TOTAL:{r[9]}/{r[10]}")
        html_rows+=f"<div style='background:#151515;padding:10px;margin:6px 0;border-radius:10px;border-left:3px solid gold'><b>{r[1]} {r[2]} {r[3]} #{r[7]}</b> {r[6]}<br>WIN: {r[4]} {'<br>MACHINE: '+r[5] if r[5] else ''}<br><small>TOTAL WIN:{r[9]} | MACHINE:{r[10]}</small><br><a href='https://wa.me/?text={wa}' style='color:#25D366;font-weight:bold;text-decoration:none'>↗ Partager WhatsApp</a></div>"
    return render_template_string(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}}.btn{{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:15px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}}</style></head><body><h2 style='background:gold;color:#111;padding:15px;border-radius:15px;text-align:center'>LOTO V13.1 - 01 à 90 - {len(rows)} tirages</h2><a class='btn' href='/saisir'>SAISIR EN CAGE</a><a class='btn' href='/analyse'>ANALYSE VENDEUR</a>{html_rows}</body></html>")

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method=='POST':
        h = "-".join([request.form.get(f'h{i}','').strip().zfill(2) for i in range(1,6) if request.form.get(f'h{i}','').strip()!='' and request.form.get(f'h{i}','').strip()!='00'])
        b = "-".join([request.form.get(f'b{i}','').strip().zfill(2) for i in range(1,6) if request.form.get(f'b{i}','').strip()!='' and request.form.get(f'b{i}','').strip()!='00'])
        insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'),datetime.now().strftime("%d/%m %H:%M"))
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
 let h=0; for(let i=1;i<=5;i++){let v=document.getElementById('h'+i).value; if(v!='' &&!isNaN(v) && v!='00' && v!='0') h+=parseInt(v);}
 let b=0; for(let i=1;i<=5;i++){let v=document.getElementById('b'+i).value; if(v!='' &&!isNaN(v) && v!='00' && v!='0') b+=parseInt(v);}
 let heure=document.getElementById('heure').value;
 if(heure=='13:00' || heure=='18:00'){ document.getElementById('total').innerText='TOTAL: '+h; }
 else { document.getElementById('total').innerText='TOTAL HAUT (WIN): '+h+' | TOTAL BAS (MACHINE): '+b; }
}
function updateForm(){
 let jour=document.getElementById('jour').value;
 let heureSel=document.getElementById('heure');
 let heure=heureSel.value;
 let jeuBox=document.getElementById('jeu');
 let jeuInput=document.getElementById('jeu_input');
 if(jour=='DIMANCHE'){
   heureSel.innerHTML='<option value="15:00">15H - DETENTE (10 numéros)</option>';
   jeuBox.innerText='DETENTE'; jeuInput.value='DETENTE';
 } else {
   let old=heure;
   heureSel.innerHTML='<option value="09:00">09H - MATINALE (10 numéros)</option><option value="13:00">13H - '+(planning[jour]?planning[jour]['13:00']:'')+' (5 numéros)</option><option value="18:00">18H - '+(planning[jour]?planning[jour]['18:00']:'')+' (5 numéros)</option>';
   if(old && ['09:00','13:00','18:00'].includes(old)) heureSel.value=old;
   heure=heureSel.value;
   if(planning[jour] && planning[jour][heure]){ jeuBox.innerText=planning[jour][heure]; jeuInput.value=planning[jour][heure]; }
 }
 document.getElementById('basDiv').classList.toggle('hidden', heure=='13:00' || heure=='18:00');
 calc();
}
</script>
</head><body>
<label>N° Tr</label><input id="numero_out" placeholder="22" required>
<label>Jour</label><select id="jour" onchange="updateForm()"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
<label>Heure</label><select id="heure" onchange="updateForm()"><option value="09:00">09H - MATINALE (10 numéros)</option><option value="13:00">13H - DIAMANT (5 numéros)</option><option value="18:00">18H - GOLD (5 numéros)</option></select>
<label>Jeu</label><div id="jeu" class="jeu-box">MATINALE</div>
<form id="mainForm" method="POST" oninput="calc()">
<input type="hidden" name="jour" id="jour_input">
<input type="hidden" name="heure" id="heure_input">
<input type="hidden" name="jeu" id="jeu_input" value="MATINALE">
<input type="hidden" name="numero" id="numero_input">
<input type="hidden" name="date" value="2026-10-16">
<label>5 Numéros HAUT (WIN) - 01 à 90</label>
<div class="cage"><input id="h1" name="h1" type="number" min="1" max="90"><input id="h2" name="h2" type="number" min="1" max="90"><input id="h3" name="h3" type="number" min="1" max="90"><input id="h4" name="h4" type="number" min="1" max="90"><input id="h5" name="h5" type="number" min="1" max="90"></div>
<div id="basDiv">
<label>5 Numéros BAS (MACHINE) - 01 à 90</label>
<div class="cage"><input id="b1" name="b1" type="number" min="1" max="90"><input id="b2" name="b2" type="number" min="1" max="90"><input id="b3" name="b3" type="number" min="1" max="90"><input id="b4" name="b4" type="number" min="1" max="90"><input id="b5" name="b5" type="number" min="1" max="90"></div>
</div>
<div id="total" class="total">TOTAL HAUT (WIN): 0 | TOTAL BAS (MACHINE): 0</div>
<button type="submit">✅ ENREGISTRER 2 TOTAUX</button>
</form>
<script>
document.getElementById('mainForm').addEventListener('submit', function(){
 document.getElementById('jour_input').value=document.getElementById('jour').value;
 document.getElementById('heure_input').value=document.getElementById('heure').value;
 document.getElementById('numero_input').value=document.getElementById('numero_out').value;
});
updateForm();
</script>
<a href="/" style="color:gold;display:block;margin-top:10px">Accueil</a>
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
                if x.strip().isdigit():
                    n = x.strip().zfill(2)
                    if n!="00" and n!="0" and int(n)>=1 and int(n)<=90:
                        nums.append(n)
        total=len(nums)
        cnt=Counter(nums)
        chauds=cnt.most_common(6)
        # CORRIGE ICI : 01 à 90 seulement, plus de 00
        all_nums=[str(i).zfill(2) for i in range(1,91)]
        retard=[n for n in all_nums if n not in cnt][:6]
        if len(retard)<3:
            retard+=[n for n,c in cnt.most_common()[-3:] if n not in retard and n!="00"][:3]
        prono=" ".join([c[0] for c in chauds[:2]] + retard[:3])
        wa_text=f"A TENTER (retard): {' '.join(retard[:2])}\n\n⚠️ Numéros en retard général: {' '.join(retard[:5])}\n\n💡 Mon prono pour le prochain tirage: {prono}\n\n👉 Abonnement VIP: 500F/jour - 2000F/semaine\n📲 Inbox pour recevoir le 2 sûr du jour\n\n#LONATO #LotoTogo #Prono"
        wa_encoded=urllib.parse.quote(wa_text)
        chaud_html="".join([f"<span style='display:inline-block;background:#FFD700;color:#111;padding:8px 14px;border-radius:20px;margin:4px;font-weight:bold'>{n} {round(c/total*100,1) if total else 0}% ({c}x)</span>" for n,c in chauds])
        retard_html="".join([f"<span style='display:inline-block;background:#2a0a0a;color:#ff6b6b;padding:8px 14px;border-radius:20px;margin:4px;font-weight:bold;border:1px solid #ff6b6b'>{n}</span>" for n in retard[:3]])
        page+=f"<div style='background:#141414;padding:15px;margin:12px 0;border-radius:15px'><div style='color:gold;font-weight:bold;font-size:18px'>🎯 {jeu_name} - {len(lst)} tirages</div><div style='margin-top:10px;display:flex;flex-wrap:wrap'>{chaud_html}</div><div style='background:#0f0f0f;padding:12px;border-radius:12px;margin-top:10px'><div style='color:#fff'>Chauds</div><div style='margin-top:5px'>{chaud_html}</div><div style='margin-top:10px;color:#ff6b6b'>Retard (à jouer): {retard_html}</div></div><div style='margin-top:12px;background:#000;border:2px solid gold;border-radius:15px;padding:12px'><div style='color:#fff;font-weight:bold'>💰 MESSAGE WHATSAPP PRÊT À VENDRE - COPIE/COLLE</div><textarea id='msg_{jeu_name}' style='width:100%;height:160px;background:#0a0a0a;color:#00ff66;border:none;margin-top:8px;padding:10px'>{wa_text}</textarea><button onclick=\"navigator.clipboard.writeText(document.getElementById('msg_{jeu_name}').value);this.innerText='✅ COPIÉ!'\" style='width:100%;background:gold;color:#111;padding:12px;border:none;border-radius:12px;font-weight:bold;margin-top:8px'>📋 COPIER LE MESSAGE</button><a href='https://wa.me/?text={wa_encoded}' style='display:block;text-align:center;background:#25D366;color:#fff;padding:12px;border-radius:12px;text-decoration:none;font-weight:bold;margin-top:6px'>↗ ENVOYER SUR WHATSAPP</a></div></div>"
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'></head><body style='background:#000;color:#fff;font-family:Arial;padding:8px'><a href='/' style='color:gold'>⬅ Accueil</a><h2 style='color:gold;text-align:center'>ANALYSE VENDEUR V13.1 - 01 à 90</h2>{page}</body></html>"

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
