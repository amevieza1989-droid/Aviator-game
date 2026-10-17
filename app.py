from flask import Flask, request, render_template_string, redirect, send_file
import sqlite3
from collections import Counter
from datetime import datetime
import os, re, io, random

app = Flask(__name__)
DB = "loto.db"
JEUX_LISTE = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]
PLANNING = {
    "LUNDI": {"09:00": "MATINALE", "13:00": "DIAMANT", "18:00": "GOLD"},
    "MARDI": {"09:00": "MATINALE", "13:00": "CASH", "18:00": "BOOM"},
    "MERCREDI": {"09:00": "MATINALE", "13:00": "BENZ", "18:00": "PRESTIGE"},
    "JEUDI": {"09:00": "MATINALE", "13:00": "MILLION", "18:00": "SUPER"},
    "VENDREDI": {"09:00": "MATINALE", "13:00": "KADOO", "18:00": "KING"},
    "SAMEDI": {"09:00": "MATINALE", "13:00": "SAM", "18:00": "BINGO"},
    "DIMANCHE": {"15:00": "DETENTE"},
}

def get_conn(): return sqlite3.connect(DB)

def init_db():
    if os.path.exists(DB):
        try: os.remove(DB)
        except: pass
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
    c.execute('DELETE FROM tirages')
    conn.commit();conn.close()

init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    th=sum(int(x) for x in haut.split('-') if x.strip().isdigit()) if haut else 0
    tb=sum(int(x) for x in bas.split('-') if x.strip().isdigit()) if bas else 0
    try:
        if '/' in date and '-' not in date:
            d,m,y=date.split('/')
            date=f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    except: pass
    conn=get_conn();c=conn.cursor()
    c.execute('INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y %H:%M'),th,tb))
    conn.commit();conn.close()

def fetch_all(jeu=None):
    conn=get_conn();c=conn.cursor()
    if jeu and jeu!='TOUS':
        c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) DESC, id DESC',(jeu,))
    else:
        c.execute('SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) DESC, id DESC')
    r=c.fetchall();conn.close();return r

def parse_file_pro(content, jeu_force):
    res=[]
    for line in content.splitlines():
        line=line.strip()
        if not line: continue
        date_str = None
        numero = None
        line_sans_date = line
        
        m = re.search(r'(\d{1,4})\s+(\d{2})/(\d{2})', line)
        if m:
            numero = m.group(1)
            dd = m.group(2); mm = m.group(3)
            yy = "2024" if mm == "12" else "2025"
            date_str = f"{yy}-{mm}-{dd}"
            line_sans_date = line.replace(m.group(0), ' ')
        else:
            m1 = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if m1:
                date_str = m1.group(1)
                line_sans_date = line.replace(m1.group(1), ' ')
            else:
                m2 = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', line)
                if m2:
                    d_raw = m2.group(1)
                    line_sans_date = line.replace(d_raw, ' ')
                    if '/' in d_raw: dd,mm,yy = d_raw.split('/')
                    else: dd,mm,yy = d_raw.split('-')
                    date_str = f"{yy}-{mm.zfill(2)}-{dd.zfill(2)}"
        
        # Si pas de date trouvée = ancien tirage sans date, on met une date neutre
        if not date_str:
            date_str = "2024-12-01"
        
        if not numero:
            # cherche un numero en fin de ligne
            nums_tmp = re.findall(r'\b\d{2,4}\b', line)
            if nums_tmp:
                # le numero est souvent le plus grand ou en fin
                numero = nums_tmp[-1] if int(nums_tmp[-1]) < 1000 else nums_tmp[0]
            else:
                numero = str(len(res)+1)

        nums = re.findall(r'\d+', line_sans_date)
        clean = [n.zfill(2) for n in nums if n.isdigit() and 1 <= int(n) <= 90]
        
        if len(clean) >= 5:
            haut = '-'.join(clean[:5])
            bas = '-'.join(clean[5:10]) if len(clean) >= 10 else ''
            heure = "09:00"
            if jeu_force in ["DIAMANT","CASH","BENZ","MILLION","KADOO","SAM"]: heure="13:00"
            elif jeu_force in ["GOLD","BOOM","PRESTIGE","SUPER","KING","BINGO"]: heure="18:00"
            elif jeu_force=="DETENTE": heure="15:00"
            res.append(('LUNDI',heure,jeu_force,haut,bas,date_str,numero))
    return res

@app.route('/')
def home():
    total=len(fetch_all())
    return render_template_string(f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}}.btn{{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}}</style></head><body><div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">LOTO V14.3 PROPRE - {total} tirages</div><a class="btn" href="/saisir">🎰 SAISIR EN CAGE</a><a class="btn" href="/historique">📜 HISTORIQUE + COLLER TEXTE</a><a class="btn" href="/analyse">📊 ANALYSE + TICKETS</a></body></html>')

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS')
    msg=''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE')
        content_to_parse = None
        pasted = request.form.get('pasted_text','').strip()
        if pasted:
            content_to_parse = pasted
        else:
            f=request.files.get('file')
            if f and f.filename:
                content_to_parse = f.read().decode('utf-8', errors='ignore')
        
        if content_to_parse:
            novos=parse_file_pro(content_to_parse, jeu_import)
            for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
            msg=f'<div style="background:#25D366;color:#fff;padding:12px;border-radius:10px;font-weight:bold">✅ {len(novos)} tirages importés en {jeu_import} - Trié par N° de tirage</div>'
        else:
            msg='<div style="background:#ff3333;color:#fff;padding:10px;border-radius:10px">❌ Colle du texte ou choisis un fichier</div>'

    rows=fetch_all(jeu_filtre)
    total_rows = len(rows)
    filtres='<div style="display:flex;flex-wrap:wrap;gap:5px;margin:10px 0">'
    for j in ["TOUS"]+JEUX_LISTE:
        cnt=len(fetch_all() if j=="TOUS" else fetch_all(j))
        active=jeu_filtre==j
        filtres+=f'<a href="/historique?jeu={j}" style="background:{"gold" if active else "#222"};color:{"#111" if active else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:12px;font-weight:bold;border:1px solid gold">{j} ({cnt})</a>'
    filtres+='</div>'
    def format_date(d):
        try:
            y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
        except: return d
    cards=''.join([f'<div style="background:#151515;padding:10px;margin:5px 0;border-radius:8px;border-left:4px solid gold"><b>{format_date(r[6])} - {r[3]} #{r[7]}</b><br>WIN:{r[4]} | MACHINE:{r[5]}<br><small style="color:#888">Ajouté le {r[8]}</small></div>' for r in rows[:400]]) or '<div style="text-align:center;color:#888;margin:20px">Base vide</div>'
    
    return f'''<html><body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a>
    <h3 style="color:gold;text-align:center;border:1px solid gold;padding:8px;border-radius:10px">HISTORIQUE - {jeu_filtre} ({total_rows})</h3>
    <div style="background:#111;border:2px solid gold;padding:12px;border-radius:12px">{msg}
        <form method="post" enctype="multipart/form-data">
            <label style="color:gold;font-weight:bold;font-size:13px">JEU:</label>
            <select name="jeu_import" style="width:100%;padding:10px;border-radius:6px;margin-bottom:8px">{"".join([f"<option value={j}>{j}</option>" for j in JEUX_LISTE])}</select>
            
            <label style="color:#25D366;font-weight:bold;font-size:14px">METHODE 1 - COLLER TEXTE (RECOMMANDÉ):</label>
            <textarea name="pasted_text" placeholder="Ex: 450 08/12 05-12-23-45-67" style="width:100%;height:120px;background:#222;color:#fff;border:1px solid #25D366;border-radius:8px;padding:8px;margin-top:4px"></textarea>
            <button style="width:100%;background:#25D366;color:#fff;padding:12px;border:none;border-radius:8px;font-weight:bold;margin-top:6px">🚀 IMPORTER LE TEXTE COLLÉ</button>
            
            <div style="text-align:center;color:#666;margin:10px 0">--- OU ---</div>
            
            <label style="color:#888;font-size:12px">METHODE 2 - FICHIER:</label>
            <input type="file" name="file" accept=".txt,.csv" style="width:100%;padding:8px;background:#222;color:#fff;border-radius:6px;margin-top:4px">
            <button style="width:100%;background:#333;color:#fff;padding:8px;border:none;border-radius:8px;margin-top:4px">Importer fichier</button>
        </form>
        <a href="/reset" onclick="return confirm('⚠️ Effacer TOUT ?')" style="display:block;background:#ff3333;color:#fff;padding:10px;border-radius:8px;text-align:center;text-decoration:none;margin-top:12px;font-weight:bold">🗑️ EFFACER TOUT L HISTORIQUE</a>
    </div>{filtres}{cards}</body></html>'''

@app.route('/analyse')
def analyse():
    jeu_filtre=request.args.get('jeu','MATINALE')
    rows=fetch_all(jeu_filtre)
    nums=[]
    for r in rows:
        for x in (r[4]+"-"+(r[5] or "")).split('-'):
            if x.strip().isdigit(): nums.append(x.strip().zfill(2))
    cnt=Counter(nums)
    chauds=cnt.most_common(20)
    tous=[str(i).zfill(2) for i in range(1,91)]
    retard=sorted(tous, key=lambda n: cnt.get(n,0))[:15]
    filtres='<div style="display:flex;flex-wrap:wrap;gap:5px;margin:10px 0">'
    for j in JEUX_LISTE:
        active=jeu_filtre==j
        filtres+=f'<a href="/analyse?jeu={j}" style="background:{"gold" if active else "#222"};color:{"#111" if active else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:12px;font-weight:bold;border:1px solid gold">{j} ({len(fetch_all(j))})</a>'
    filtres+='</div>'
    chaud_html=''.join([f'<span style="display:inline-block;background:gold;color:#111;padding:6px 12px;border-radius:20px;margin:3px;font-weight:bold">{n} ({c}x)</span>' for n,c in chauds[:8]]) or '<span style="color:#888">Aucun</span>'
    retard_html=''.join([f'<span style="display:inline-block;background:#300;color:#ff6b6b;padding:6px 12px;border-radius:20px;margin:3px;border:1px solid #ff6b6b">{n} ({cnt.get(n,0)}x)</span>' for n in retard[:8]])
    if len(chauds)>=5:
        ticket1 = [n for n,c in chauds[:5]]
        ticket2 = [chauds[0][0], chauds[1][0], retard[0], retard[1], chauds[2][0]]
        ticket3 = [n for n in retard[:5]]
        random.seed(len(rows)); ticket4 = random.sample([n for n,c in chauds[:15]], 5)
    else:
        ticket1=ticket2=ticket3=ticket4=["01","02","03","04","05"]
    tickets_html=f'''
    <div style="margin-top:15px">
        <div style="background:linear-gradient(45deg,#FFD700,#FFA500);color:#111;padding:14px;border-radius:12px;margin:10px 0;font-weight:bold;border:2px solid #fff">
            🎯 TICKET 1 - CHAUDS<br><span style="font-size:24px;letter-spacing:2px">{' - '.join(ticket1)}</span>
        </div>
        <div style="background:#111;border:2px solid gold;color:gold;padding:14px;border-radius:12px;margin:10px 0;font-weight:bold">
            🔥 TICKET 2 - MIX<br><span style="font-size:24px;color:#fff">{' - '.join(ticket2)}</span>
        </div>
        <div style="background:#222;border:2px solid #ff6b6b;color:#ff6b6b;padding:14px;border-radius:12px;margin:10px 0;font-weight:bold">
            ⏰ TICKET 3 - RETARD<br><span style="font-size:24px;color:#fff">{' - '.join(ticket3)}</span>
        </div>
        <div style="background:#0a3d0a;border:2px solid #25D366;color:#25D366;padding:14px;border-radius:12px;margin:10px 0;font-weight:bold">
            🎲 TICKET 4 - ALEA<br><span style="font-size:24px;color:#fff">{' - '.join(ticket4)}</span>
        </div>
    </div>
    '''
    return f'<html><body style="background:#000;color:#fff;font-family:Arial;padding:8px"><a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center;border:1px solid gold;padding:8px;border-radius:10px">ANALYSE - {jeu_filtre} - {len(rows)} tirages</h3>{filtres}<div style="background:#141414;padding:12px;border-radius:12px"><div><b>Chauds:</b><br>{chaud_html}</div><div style="margin-top:12px"><b>Retard:</b><br>{retard_html}</div>{tickets_html}</div></body></html>'

@app.route('/reset')
def reset():
    init_db()
    return redirect('/historique?jeu=TOUS')

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    today=datetime.now().strftime('%Y-%m-%d')
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6) if request.form.get(f'h{i}','')])
        b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','')])
        insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect(f'/historique?jeu={request.form.get("jeu")}')
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}select,input{{width:100%;padding:12px;margin:4px 0;border-radius:6px;border:1px solid #333}}label{{color:gold;font-weight:bold;font-size:12px}}.jeu-box{{background:#111;border:2px solid gold;color:gold;text-align:center;padding:10px;border-radius:8px;font-weight:bold}}.cage{{display:flex;gap:3px}}.cage input{{width:18%;text-align:center;font-weight:bold}}</style>
<script>const planning={{"LUNDI":{{"09:00":"MATINALE","13:00":"DIAMANT","18:00":"GOLD"}},"MARDI":{{"09:00":"MATINALE","13:00":"CASH","18:00":"BOOM"}},"MERCREDI":{{"09:00":"MATINALE","13:00":"BENZ","18:00":"PRESTIGE"}},"JEUDI":{{"09:00":"MATINALE","13:00":"MILLION","18:00":"SUPER"}},"VENDREDI":{{"09:00":"MATINALE","13:00":"KADOO","18:00":"KING"}},"SAMEDI":{{"09:00":"MATINALE","13:00":"SAM","18:00":"BINGO"}},"DIMANCHE":{{"15:00":"DETENTE"}}}};
function updateForm(){{let jour=document.getElementById('jour').value;let heureSel=document.getElementById('heure');let heure=heureSel.value;let jeuBox=document.getElementById('jeu');let jeuInput=document.getElementById('jeu_input');if(jour=='DIMANCHE'){{heureSel.innerHTML='<option value="15:00">15H - DETENTE</option>';jeuBox.innerText='DETENTE';jeuInput.value='DETENTE';}}else{{heureSel.innerHTML='<option value="09:00">09H - MATINALE</option><option value="13:00">13H - '+planning[jour]['13:00']+'</option><option value="18:00">18H - '+planning[jour]['18:00']+'</option>';if(['09:00','13:00','18:00'].includes(heure))heureSel.value=heure;heure=heureSel.value;jeuBox.innerText=planning[jour][heure];jeuInput.value=planning[jour][heure];}}let is5=heure=='13:00'||heure=='18:00';document.getElementById('basDiv').style.display=is5?'none':'block';}}
</script></head><body><h3 style="color:gold;text-align:center">SAISIR PRO</h3><label>N° TIRAGE</label><input id="numero_out" type="number" min="1" max="1000" value="703" required><label>JOUR</label><select id="jour" onchange="updateForm()"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select><label>HEURE</label><select id="heure" onchange="updateForm()"><option value="09:00">09H</option><option value="13:00">13H</option><option value="18:00">18H</option></select><label>📅 DATE DU TIRAGE</label><input type="date" id="date_out" value="{today}" required><label>JEU AUTO</label><div id="jeu" class="jeu-box">MATINALE</div><form id="mainForm" method="POST"><input type="hidden" name="jour" id="jour_input"><input type="hidden" name="heure" id="heure_input"><input type="hidden" name="jeu" id="jeu_input" value="MATINALE"><input type="hidden" name="numero" id="numero_input"><input type="hidden" name="date" id="date_input"><div style="margin:10px 0"><label>WIN (5)</label><div class="cage"><input name="h1" placeholder="01" required><input name="h2" placeholder="02" required><input name="h3" placeholder="03" required><input name="h4" placeholder="04" required><input name="h5" placeholder="05" required></div></div><div id="basDiv"><label>MACHINE (5) - MATINALE</label><div class="cage"><input name="b1" placeholder="06"><input name="b2" placeholder="07"><input name="b3" placeholder="08"><input name="b4" placeholder="09"><input name="b5" placeholder="10"></div></div><button style="width:100%;background:gold;color:#111;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:12px">✅ ENREGISTRER</button></form><script>document.getElementById('mainForm').addEventListener('submit', function(){{document.getElementById('jour_input').value=document.getElementById('jour').value;document.getElementById('heure_input').value=document.getElementById('heure').value;document.getElementById('numero_input').value=document.getElementById('numero_out').value;document.getElementById('date_input').value=document.getElementById('date_out').value;}});updateForm();</script><a href="/" style="color:gold;display:block;text-align:center;margin-top:12px">⬅ Retour</a></body></html>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
