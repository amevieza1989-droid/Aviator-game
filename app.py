from flask import Flask, request, render_template_string, redirect, send_file
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os, urllib.parse, re, io

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
    c.execute('SELECT COUNT(*) FROM tirages')
    if c.fetchone()[0]==0:
        for j,h,je,ht,bs,dt,num in INIT_DATA:
            th=sum(int(x) for x in ht.split('-') if x.isdigit())
            tb=sum(int(x) for x in bs.split('-') if x.isdigit()) if bs else 0
            c.execute('INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)',(j,h,je,ht,bs,dt,num,datetime.now().strftime('%d/%m %H:%M'),th,tb))
        conn.commit()
    conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    th=sum(int(x.strip()) for x in haut.split('-') if x.strip().isdigit())
    tb=sum(int(x.strip()) for x in bas.split('-') if x.strip().isdigit()) if bas else 0
    conn=get_conn();c=conn.cursor()
    c.execute('INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m %H:%M'),th,tb))
    conn.commit();conn.close()

def fetch_all():
    conn=get_conn();c=conn.cursor()
    c.execute('SELECT * FROM tirages ORDER BY date DESC, id DESC')
    r=c.fetchall();conn.close();return r

def parse_file(content):
    res=[]
    for line in content.splitlines():
        line=line.strip()
        if not line: continue
        dm=re.search(r'\d{4}-\d{2}-\d{2}',line)
        date=dm.group(0) if dm else datetime.now().strftime('%Y-%m-%d')
        nums=re.findall(r'\d+',line)
        clean=[n.zfill(2) for n in nums if 1<=int(n)<=90]
        if len(clean)>=10:
            haut='-'.join(clean[-10:-5])
            bas='-'.join(clean[-5:])
            res.append(('LUNDI','09:00','MATINALE',haut,bas,date,str(len(res)+100)))
    return res

@app.route('/')
def home():
    rows=fetch_all()
    return render_template_string('<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}.btn{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:18px;margin:14px 0;border-radius:14px;text-align:center;text-decoration:none;font-weight:bold}.header{background:gold;color:#111;padding:18px;border-radius:15px;text-align:center;font-weight:bold}</style></head><body><div class="header">LOTO V13.3 - {{n}} tirages - Tous Jeux</div><a class="btn" href="/saisir">🎰 SAISIR EN CAGE</a><a class="btn" href="/analyse">📊 ANALYSE VENDEUR</a><a class="btn" href="/historique" style="border-color:#25D366;color:#25D366">📜 HISTORIQUE + IMPORT/EXPORT</a></body></html>', n=len(rows))

@app.route('/historique', methods=['GET','POST'])
def historique():
    msg=''
    if request.method=='POST':
        f=request.files.get('file')
        if f and f.filename:
            content=f.read().decode('utf-8', errors='ignore')
            novos=parse_file(content)
            for j,h,je,ht,bs,dt,num in novos:
                insert_tirage(j,h,je,ht,bs,dt,num)
            msg=f'<div style="background:#25D366;color:#fff;padding:12px;border-radius:10px">OK {len(novos)} importes</div>'
    rows=fetch_all()
    cards=''
    for r in rows:
        cards+=f'<div style="background:#151515;padding:12px;margin:8px 0;border-radius:12px;border-left:4px solid gold"><b>{r[1]} {r[2]} {r[3]} #{r[7]}</b> - {r[6]}<br>WIN:{r[4]}<br>MACHINE:{r[5]}</div>'
    return render_template_string('<html><body style="background:#000;color:#fff;font-family:Arial;padding:10px"><a href="/" style="color:gold">ACCUEIL</a><h2 style="color:gold;text-align:center;border:2px solid gold;padding:12px;border-radius:12px">HISTORIQUE - {{n}}</h2><div style="background:#111;border:2px dashed gold;padding:14px;border-radius:14px">{{msg|safe}}<form method="post" enctype="multipart/form-data"><input type="file" name="file" accept=".txt,.csv" style="width:100%;padding:10px;background:#222;color:#fff;border-radius:8px" required><button type="submit" style="width:100%;background:gold;color:#111;padding:12px;border:none;border-radius:10px;font-weight:bold">IMPORTER MATINAL_RESULTS.txt</button></form><a href="/export/txt" style="display:block;text-align:center;background:#111;border:1px solid #25D366;color:#25D366;padding:8px;border-radius:8px;text-decoration:none;margin-top:6px">Export TXT</a></div>{{cards|safe}}</body></html>', n=len(rows), msg=msg, cards=cards)

@app.route('/export/<fmt>')
def export_file(fmt):
    rows=fetch_all()
    out=io.StringIO()
    for r in rows: out.write(f'{r[6]} | {r[1]} {r[2]} {r[3]} #{r[7]} | WIN:{r[4]} | MACHINE:{r[5]}\n')
    mem=io.BytesIO(out.getvalue().encode('utf-8'))
    return send_file(mem, as_attachment=True, download_name='EXPORT.txt', mimetype='text/plain')

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').strip().zfill(2) for i in range(1,6) if request.form.get(f'h{i}','').strip() not in ['','00','0']])
        b='-'.join([request.form.get(f'b{i}','').strip().zfill(2) for i in range(1,6) if request.form.get(f'b{i}','').strip() not in ['','00','0']])
        insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect('/historique')
    # ICI C'EST TON VRAI CODE D'ORIGINE QUI CHANGE BENZ, PRESTIGE, etc.
    return """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}
select,input{width:100%;padding:14px;margin:6px 0;background:#fff;color:#111;border-radius:10px;border:none;font-weight:bold;font-size:16px}
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
 document.getElementById('total').innerText=(heure=='13:00'||heure=='18:00')?'TOTAL: '+h:'TOTAL HAUT (WIN): '+h+' | TOTAL BAS (MACHINE): '+b;
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
<h3 style="color:gold">SAISIR EN CAGE - V13.3 Tous Jeux</h3>
<label>N° Tr</label><input id="numero_out" placeholder="22" required>
<label>Jour</label><select id="jour" onchange="updateForm()"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
<label>Heure</label><select id="heure" onchange="updateForm()"><option value="09:00">09H - MATINALE</option><option value="13:00">13H - DIAMANT</option><option value="18:00">18H - GOLD</option></select>
<label>Jeu</label><div id="jeu" class="jeu-box">MATINALE</div>
<form id="mainForm" method="POST" oninput="calc()">
<input type="hidden" name="jour" id="jour_input">
<input type="hidden" name="heure" id="heure_input">
<input type="hidden" name="jeu" id="jeu_input" value="MATINALE">
<input type="hidden" name="numero" id="numero_input">
<input type="hidden" name="date" value="2026-10-16">
<label>5 Numéros HAUT (WIN)</label>
<div class="cage"><input id="h1" name="h1" type="number" min="1" max="90"><input id="h2" name="h2" type="number" min="1" max="90"><input id="h3" name="h3" type="number" min="1" max="90"><input id="h4" name="h4" type="number" min="1" max="90"><input id="h5" name="h5" type="number" min="1" max="90"></div>
<div id="basDiv">
<label>5 Numéros BAS (MACHINE)</label>
<div class="cage"><input id="b1" name="b1" type="number" min="1" max="90"><input id="b2" name="b2" type="number" min="1" max="90"><input id="b3" name="b3" type="number" min="1" max="90"><input id="b4" name="b4" type="number" min="1" max="90"><input id="b5" name="b5" type="number" min="1" max="90"></div>
</div>
<div id="total" class="total">TOTAL HAUT (WIN): 0 | TOTAL BAS (MACHINE): 0</div>
<button type="submit">✅ ENREGISTRER</button>
</form>
<script>
document.getElementById('mainForm').addEventListener('submit', function(){
 document.getElementById('jour_input').value=document.getElementById('jour').value;
 document.getElementById('heure_input').value=document.getElementById('heure').value;
 document.getElementById('numero_input').value=document.getElementById('numero_out').value;
});
updateForm();
</script>
<a href="/" style="color:gold;display:block;margin-top:15px;text-align:center">⬅ Retour Accueil</a>
</body></html>
"""

@app.route('/analyse')
def analyse():
    rows=fetch_all()
    return render_template_string('<html><body style="background:#000;color:#fff;font-family:Arial;padding:10px"><a href="/" style="color:gold">ACCUEIL</a><h2 style="color:gold">ANALYSE - {{n}} tirages</h2></body></html>', n=len(rows))

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
