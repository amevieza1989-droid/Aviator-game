from flask import Flask, request, render_template_string, redirect, send_file, jsonify
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os, re, io

app = Flask(__name__)
DB = "loto.db"
JEUX_LISTE = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]
JEUX_10_BOULES = ["MATINALE","DETENTE"]

def get_conn(): return sqlite3.connect(DB)
def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
    conn.commit();conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    th=sum(int(x) for x in haut.split('-') if x.strip().isdigit()) if haut else 0
    tb=sum(int(x) for x in bas.split('-') if x.strip().isdigit()) if bas else 0
    conn=get_conn();c=conn.cursor()
    c.execute('INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y %H:%M'),th,tb))
    conn.commit();conn.close()

def fetch_all(jeu=None):
    conn=get_conn();c=conn.cursor()
    if jeu and jeu!='TOUS':
        c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) DESC, id DESC',(jeu,))
    else:
        c.execute('SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) DESC, id DESC')
    r=c.fetchall();conn.close();return r

# --- PARSEUR V18.3 CORRIGÉ POUR GOOGLE SHEETS ---
def parse_file_pro(content, jeu_force):
    res=[]
    lines = [l.strip() for l in content.splitlines() if l.strip()!='']
    fixed_lines = []
    i=0
    while i < len(lines):
        line = lines[i]
        # Cas 1: ligne finit par / -> la suivante est la machine
        if line.strip().endswith('/') and i+1 < len(lines) and 'WIN' not in lines[i+1].upper():
            line = line + " " + lines[i+1]
            i+=1
        # Cas 2: ligne qui est seulement 5 numéros sans WIN -> rattacher à la précédente qui a /
        elif 'WIN' not in line.upper() and re.search(r'\d', line) and fixed_lines and fixed_lines[-1].strip().endswith('/'):
            fixed_lines[-1] = fixed_lines[-1] + " " + line
            i+=1
            continue
        fixed_lines.append(line)
        i+=1

    for line in fixed_lines:
        if 'WIN' not in line.upper(): continue
        m = re.search(r'(\d{2,4})\s+(\d{1,2})/(\d{1,2})', line)
        if not m: continue
        numero = m.group(1)
        dd = m.group(2).zfill(2); mm = m.group(3).zfill(2)
        yy = "2024" if mm=="12" else "2025"
        date_str = f"{yy}-{mm}-{dd}"
        if '/' not in line: continue
        before, after = line.split('/', 1)
        # WIN: prendre les 5 derniers numéros 1-90 avant le /
        all_before = re.findall(r'\d{1,2}', before)
        win_nums = [n for n in all_before if 1<=int(n)<=90][-5:]
        machine_nums = re.findall(r'\d{1,2}', after)
        machine_nums = [n for n in machine_nums if 1<=int(n)<=90][:5]
        win_nums = [n.zfill(2) for n in win_nums][:5]
        machine_nums = [n.zfill(2) for n in machine_nums][:5]
        if len(win_nums)>=5:
            haut = '-'.join(win_nums[:5])
            if jeu_force in JEUX_10_BOULES:
                if len(machine_nums)>=5:
                    bas = '-'.join(machine_nums[:5])
                    res.append(('LUNDI',"09:00",jeu_force,haut,bas,date_str,numero))
            else:
                res.append(('LUNDI',"09:00",jeu_force,haut,'',date_str,numero))
    return res

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "LOTO IA V18.3",
        "short_name": "LOTO V18.3",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#000000",
        "theme_color": "#FFD700",
        "icons": [{"src": "https://cdn-icons-png.flaticon.com/512/744/744465.png","sizes": "512x512","type": "image/png"}]
    })

@app.route('/sw.js')
def sw():
    js = "self.addEventListener('install', e=>{self.skipWaiting();}); self.addEventListener('fetch', e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))});"
    return (js, 200, {'Content-Type': 'application/javascript'})

@app.route('/')
def home():
    total=len(fetch_all())
    return render_template_string(f'''
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="manifest" href="/manifest.json"><meta name="theme-color" content="#FFD700">
    <style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}}.btn{{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}}</style>
    <script>if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js')}}</script>
    </head><body>
    <div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">LOTO V18.3 PROPRE<br>{total} tirages</div>
    <a class="btn" href="/saisir">🎰 SAISIR</a><a class="btn" href="/historique">📜 HISTORIQUE</a><a class="btn" href="/analyse">🧠 ANALYSE</a>
    </body></html>''')

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS')
    ok=request.args.get('ok')
    err=request.args.get('err')
    msg=''
    if ok: msg=f'<div style="background:#25D366;color:#fff;padding:12px;border-radius:10px;font-weight:bold">✅ {ok} importés en {jeu_filtre}!</div>'
    if err: msg=f'<div style="background:#ff4444;color:#fff;padding:12px;border-radius:10px;font-weight:bold">❌ {err}</div>'
    
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE')
        pasted=request.form.get('pasted_text','').strip()
        content_to_parse=pasted
        if not content_to_parse:
            f=request.files.get('file')
            if f and f.filename: content_to_parse=f.read().decode('utf-8', errors='ignore')
        if content_to_parse:
            novos=parse_file_pro(content_to_parse, jeu_import)
            if len(novos)==0:
                return redirect(f'/historique?jeu={jeu_import}&err=Aucun tirage detecte - Verifie format: 714 14/10 WIN: 51-07-13-50-12 / 05-81-60-45-71')
            for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
            return redirect(f'/historique?jeu={jeu_import}&ok={len(novos)}')
        else:
            return redirect(f'/historique?jeu={jeu_filtre}&err=Colle d abord tes resultats')

    rows=fetch_all(jeu_filtre); total_rows=len(rows)
    def format_date(d):
        try: y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
        except: return d
    
    # CORRECTION FILTRE: le select suit le filtre actuel
    jeu_pour_import = jeu_filtre if jeu_filtre in JEUX_LISTE else "MATINALE"
    options_html = "".join([f'<option value="{j}" {"selected" if j==jeu_pour_import else ""}>{j} - {10 if j in JEUX_10_BOULES else 5}b</option>' for j in JEUX_LISTE])

    filtres='<div style="display:flex;flex-wrap:wrap;gap:5px;margin:10px 0">'
    for j in ["TOUS"]+JEUX_LISTE:
        cnt=len(fetch_all() if j=="TOUS" else fetch_all(j))
        active=jeu_filtre==j
        filtres+=f'<a href="/historique?jeu={j}" style="background:{"gold" if active else "#222"};color:{"#111" if active else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;font-weight:bold;border:1px solid gold">{j} ({cnt})</a>'
    filtres+='</div>'
    
    cards=''.join([f'<div style="background:#151515;padding:8px;margin:4px 0;border-radius:8px;border-left:4px solid {"#25D366" if r[5] else "gold"}"><b>{format_date(r[6])} {r[3]} #{r[7]}</b><br>{"WIN:"+r[4]+" | MACHINE:"+r[5]+" ✅ 10b" if r[5] else "NUM:"+r[4]} </div>' for r in rows[:500]]) or '<div style="color:#888;text-align:center;padding:20px">Base vide - Colle ton fichier ci-dessus</div>'

    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="manifest" href="/manifest.json"></head>
    <body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({total_rows})</h3>
    <div style="background:#111;border:2px solid gold;padding:10px;border-radius:12px">{msg}
    <form method="post"><select name="jeu_import" style="width:100%;padding:10px;border-radius:6px;margin-bottom:6px;background:#222;color:#fff">{options_html}</select>
    <textarea name="pasted_text" placeholder="Colle ici: 703 01/10 WIN: 18-13-79-01-32 / 02-46-24-72-41 (meme si MACHINE a la ligne)" style="width:100%;height:130px;background:#222;color:#fff;border:1px solid #25D366;border-radius:8px;padding:8px"></textarea>
    <button style="width:100%;background:#25D366;color:#fff;padding:12px;border:none;border-radius:8px;font-weight:bold;margin-top:6px">🚀 IMPORTER V18.3</button></form></div>
    {filtres}{cards}</body></html>'''

@app.route('/analyse')
def analyse():
    jeu_filtre=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu_filtre)
    if not rows: return f'<html><body style="background:#000;color:#fff;padding:12px"><a href="/historique?jeu={jeu_filtre}" style="color:gold">⬅ Va importer {jeu_filtre} d abord</a><br><br>Base vide pour {jeu_filtre}</body></html>'
    all_nums=[]; paires=Counter(); annonce=defaultdict(Counter); prev_win=[]
    for r in reversed(rows):
        win_nums=[x.zfill(2) for x in r[4].split('-') if x.strip().isdigit()]
        all_nums.extend(win_nums)
        for i in range(len(win_nums)):
            for j in range(i+1,len(win_nums)): paires[tuple(sorted([win_nums[i],win_nums[j]]))]+=1
        if prev_win:
            for p in prev_win:
                for cur in win_nums: annonce[p][cur]+=1
        prev_win=win_nums
    cnt=Counter(all_nums); chauds=cnt.most_common(20)
    tous=[str(i).zfill(2) for i in range(1,91)]
    retard=sorted(tous, key=lambda n: cnt.get(n,0))
    last_nums=[x.zfill(2) for x in rows[0][4].split('-') if x.strip().isdigit()]
    ticket1=[n for n,c in chauds[:5]]
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="manifest" href="/manifest.json"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">🧠 {jeu_filtre} - {len(rows)} tirages</h3>
    <div style="background:gold;color:#111;padding:12px;border-radius:10px;margin:10px 0;font-weight:bold;text-align:center;font-size:18px">🎯 {" - ".join(ticket1)}</div>
    <a href="/analyse?jeu={jeu_filtre}" style="background:#222;color:gold;padding:8px;border-radius:6px;text-decoration:none">🔄 Actualiser</a>
    <div style="margin-top:10px"><a href="/historique?jeu={jeu_filtre}" style="color:#25D366">📜 Voir historique {jeu_filtre}</a></div>
    </body></html>'''

@app.route('/reset')
def reset():
    conn=get_conn();c=conn.cursor(); c.execute('DELETE FROM tirages'); conn.commit(); conn.close()
    return redirect('/historique?jeu=TOUS')

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    today=datetime.now().strftime('%Y-%m-%d')
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6) if request.form.get(f'h{i}','')])
        b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','')])
        insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect(f'/analyse?jeu={request.form.get("jeu")}')
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="manifest" href="/manifest.json">
    <style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}select,input{{width:100%;padding:12px;margin:4px 0;border-radius:6px;border:1px solid #333}}label{{color:gold;font-weight:bold;font-size:12px}}.cage{{display:flex;gap:3px}}.cage input{{width:18%;text-align:center;font-weight:bold}}.hidden{{display:none}}</style>
    <script>
    const JEUX_10=["MATINALE","DETENTE"];
    function updateForm(){{
        let jeu=document.getElementById('jeu').value;
        let machineDiv=document.getElementById('machineDiv');
        let labelWin=document.getElementById('labelWin');
        let info=document.getElementById('infoJeu');
        if (JEUX_10.includes(jeu)) {{
            machineDiv.classList.remove('hidden');
            labelWin.innerText="WIN (5) - "+jeu+" = 10 BOULES";
            info.innerText=jeu+" = 10 BOULES";
            info.style.background="#25D366";
        }} else {{
            machineDiv.classList.add('hidden');
            labelWin.innerText="NUM (5) - "+jeu+" = 5 BOULES";
            info.innerText=jeu+" = 5 BOULES SEULEMENT";
            info.style.background="gold"; info.style.color="#111";
        }}
        document.getElementById('jeu_input').value=jeu;
    }}
    if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js')}}
    </script></head><body>
    <h3 style="color:gold;text-align:center">SAISIR V18.3</h3>
    <div id="infoJeu" style="background:gold;color:#111;padding:8px;border-radius:8px;text-align:center;font-weight:bold;margin-bottom:8px">BENZ = 5 BOULES</div>
    <label>N°</label><input id="numero_out" type="number" value="718" required><label>DATE</label><input type="date" id="date_out" value="{today}" required>
    <label>JEU</label><select id="jeu" onchange="updateForm()" style="background:#111;border:2px solid gold;color:gold;font-weight:bold">
        <option value="MATINALE">MATINALE - 10 BOULES</option><option value="DETENTE">DETENTE - 10 BOULES</option>
        <option value="DIAMANT">DIAMANT - 5 BOULES</option><option value="GOLD">GOLD - 5 BOULES</option>
        <option value="CASH">CASH - 5 BOULES</option><option value="BOOM">BOOM - 5 BOULES</option>
        <option value="BENZ" selected>BENZ - 5 BOULES</option><option value="PRESTIGE">PRESTIGE - 5 BOULES</option>
        <option value="MILLION">MILLION - 5 BOULES</option><option value="SUPER">SUPER - 5 BOULES</option>
        <option value="KADOO">KADOO - 5 BOULES</option><option value="KING">KING - 5 BOULES</option>
        <option value="SAM">SAM - 5 BOULES</option><option value="BINGO">BINGO - 5 BOULES</option>
    </select>
    <form id="mainForm" method="POST">
    <input type="hidden" name="jour" value="LUNDI"><input type="hidden" name="heure" value="09:00"><input type="hidden" name="jeu" id="jeu_input" value="BENZ"><input type="hidden" name="numero" id="numero_input"><input type="hidden" name="date" id="date_input">
    <div style="margin:10px 0"><label id="labelWin">NUM (5)</label><div class="cage"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div></div>
    <div id="machineDiv" class="hidden"><label style="color:#25D366">MACHINE (5) - MATINALE/DETENTE</label><div class="cage"><input name="b1"><input name="b2"><input name="b3"><input name="b4"><input name="b5"></div></div>
    <button style="width:100%;background:gold;color:#111;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:12px">ENREGISTRER</button>
    </form>
    <script>document.getElementById('mainForm').addEventListener('submit', function(){{document.getElementById('numero_input').value=document.getElementById('numero_out').value;document.getElementById('date_input').value=document.getElementById('date_out').value;}}); updateForm();</script>
    <a href="/" style="color:gold;display:block;text-align:center;margin-top:12px">⬅ Retour</a></body></html>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
