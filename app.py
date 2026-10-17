from flask import Flask, request, redirect, jsonify
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os, re

app = Flask(__name__)
DB = "loto.db"
JEUX_LISTE = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]
JEUX_10_BOULES = ["MATINALE","DETENTE"]

def get_conn(): return sqlite3.connect(DB)
def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT)')
    conn.commit();conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    conn=get_conn();c=conn.cursor()
    c.execute('INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created) VALUES (?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y')))
    conn.commit();conn.close()

def fetch_all(jeu=None):
    conn=get_conn();c=conn.cursor()
    if jeu and jeu!='TOUS':
        c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) DESC',(jeu,))
    else:
        c.execute('SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) DESC')
    r=c.fetchall();conn.close();return r

def format_date(d):
    try: y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
    except: return d or ""

def parse_file_pro(content, jeu_force):
    res=[]; lines=content.strip().splitlines(); num_auto=700
    for line in lines:
        if not line.strip(): continue
        line_clean=line.strip()
        m_date=re.search(r'(\d{1,2})/(\d{1,2})',line_clean)
        dd=m_date.group(1).zfill(2) if m_date else "01"; mm=m_date.group(2).zfill(2) if m_date else "10"
        date_str=f"{'2024' if mm=='12' else '2025'}-{mm}-{dd}"
        m_num=re.search(r'^\s*(\d{2,4})\b',line_clean); numero=m_num.group(1) if m_num else str(num_auto); num_auto+=1
        if '/' in line_clean:
            parts=line_clean.split('/',1)
            win_nums=[x.zfill(2) for x in re.findall(r'\b(\d{1,2})\b',parts[0]) if 1<=int(x)<=90][-5:]
            mach_nums=[x.zfill(2) for x in re.findall(r'\b(\d{1,2})\b',parts[1]) if 1<=int(x)<=90][:5]
        else:
            all_nums=[x.zfill(2) for x in re.findall(r'\b(\d{1,2})\b',line_clean) if 1<=int(x)<=90]
            win_nums=all_nums[-10:][-5:] if len(all_nums)>=5 else []
            mach_nums=all_nums[-5:] if len(all_nums)>=10 else []
            if len(win_nums)<5:
                m_simple=re.findall(r'(\d{2})\D+(\d{2})\D+(\d{2})\D+(\d{2})\D+(\d{2})',line_clean)
                if m_simple: win_nums=[x.zfill(2) for x in m_simple[0] if 1<=int(x)<=90]
        if len(win_nums)>=5 and all(1<=int(x)<=90 for x in win_nums):
            haut='-'.join(win_nums[:5])
            if jeu_force in JEUX_10_BOULES:
                bas='-'.join(mach_nums[:5]) if len(mach_nums)>=5 else ''
                if bas: res.append(('LUNDI','09:00',jeu_force,haut,bas,date_str,numero))
            else:
                res.append(('LUNDI','09:00',jeu_force,haut,'',date_str,numero))
    return res

@app.route('/')
def home():
    total=len(fetch_all())
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:12px">
    <div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">V19.0 FICHIER - {total} tirages</div>
    <a href="/historique" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">📁 IMPORTER FICHIER</a>
    <a href="/saisir" style="display:block;background:gold;color:#111;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">🎰 SAISIR</a>
    <a href="/analyse?jeu=MATINALE" style="display:block;background:#222;border:1px solid #25D366;color:#25D366;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">🧠 ANALYSEUR + IA</a>
    </body></html>'''

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS'); ok=request.args.get('ok'); err=request.args.get('err')
    msg=f'<div style="background:#25D366;padding:10px;border-radius:8px">✅ {ok} importés en {jeu_filtre}!</div>' if ok else f'<div style="background:#ff4444;padding:10px;border-radius:8px">❌ {err}</div>' if err else ''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE')
        content=""
        # 1. FICHIER uploadé (priorité)
        if 'fichier' in request.files and request.files['fichier'].filename!='':
            f=request.files['fichier']
            try: content=f.read().decode('utf-8', errors='ignore')
            except: content=f.read().decode('latin-1', errors='ignore')
        else:
            # 2. Fallback copier-coller
            content=request.form.get('pasted_text','')
        novos=parse_file_pro(content, jeu_import)
        if not novos: return redirect(f'/historique?jeu={jeu_import}&err=0 detecte - Fichier vide ou format non reconnu')
        for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
        return redirect(f'/historique?jeu={jeu_import}&ok={len(novos)}')
    rows=fetch_all(jeu_filtre)
    jeu_pour_import=jeu_filtre if jeu_filtre in JEUX_LISTE else "MATINALE"
    options="".join([f'<option value="{j}" {"selected" if j==jeu_pour_import else ""}>{j} - {10 if j in JEUX_10_BOULES else 5}b</option>' for j in JEUX_LISTE])
    filtres=''.join([f'<a href="/historique?jeu={j}" style="background:{"gold" if jeu_filtre==j else "#222"};color:{"#111" if jeu_filtre==j else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;margin:2px;display:inline-block;border:1px solid gold">{j} ({len(fetch_all() if j=="TOUS" else fetch_all(j))})</a>' for j in ["TOUS"]+JEUX_LISTE])
    cards="".join([f'<div style="background:#151515;padding:12px;margin:6px 0;border-radius:10px;border-left:5px solid {"#25D366" if r[5] else "gold"}"><b>📅 {format_date(r[6])} - {r[3]} #{r[7]}</b><br>{"WIN:"+r[4]+" | MACHINE:"+r[5] if r[5] else "NUM:"+r[4]}</div>' for r in rows[:500]]) or '<div style="color:#888;text-align:center;padding:30px">Base vide</div>'
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({len(rows)})</h3>
    <div style="background:#111;border:2px solid gold;padding:14px;border-radius:12px">{msg}
    <form method="post" enctype="multipart/form-data">
    <label style="color:gold;font-weight:bold">Jeu à importer:</label>
    <select name="jeu_import" style="width:100%;padding:12px;background:#222;color:#fff;border-radius:8px;margin:6px 0">{options}</select>
    <label style="color:#25D366;font-weight:bold;margin-top:10px;display:block">📁 Choisir FICHIER .txt (Recommandé):</label>
    <input type="file" name="fichier" accept=".txt,.csv" style="width:100%;padding:12px;background:#222;color:#fff;border:2px dashed #25D366;border-radius:8px;margin:6px 0">
    <div style="text-align:center;color:#888;margin:8px 0">--- OU ---</div>
    <label style="color:#888">Copier-coller (si pas de fichier):</label>
    <textarea name="pasted_text" style="width:100%;height:70px;background:#222;color:#fff;border:1px solid #444;border-radius:8px;padding:8px" placeholder="78-89-43-76-32"></textarea>
    <button style="width:100%;background:#25D366;color:#fff;padding:14px;border:none;border-radius:8px;font-weight:bold;margin-top:10px;font-size:16px">📁 IMPORTER FICHIER V19.0</button>
    </form></div><div style="margin:12px 0">{filtres}</div>{cards}</body></html>'''

@app.route('/analyse')
def analyse():
    jeu=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu)
    if not rows: return f'<html><body style="background:#000;color:#fff;padding:12px"><a href="/historique?jeu={jeu}">⬅ Importer {jeu}</a><br>Base vide</body></html>'
    all_nums=[]; paires=Counter(); annonce=defaultdict(Counter); prev_win=[]
    for r in reversed(rows):
        win_nums=[x for x in r[4].split('-') if x.isdigit() and 1<=int(x)<=90]
        mach_nums=[x for x in (r[5].split('-') if r[5] else []) if x.isdigit() and 1<=int(x)<=90]
        combined=win_nums+mach_nums
        all_nums.extend(combined if jeu in JEUX_10_BOULES else win_nums)
        check=win_nums if jeu not in JEUX_10_BOULES else combined
        for i in range(len(check)):
            for j in range(i+1,len(check)): paires[tuple(sorted([check[i],check[j]]))]+=1
        if prev_win:
            for p in prev_win:
                for cur in win_nums:
                    if p!=cur: annonce[p][cur]+=1
        prev_win=win_nums
    cnt=Counter([n for n in all_nums if 1<=int(n)<=90])
    for bad in ['91','92','93','94','95','00']:
        if bad in cnt: del cnt[bad]
    chauds=cnt.most_common(15); froids=sorted(cnt.items(), key=lambda x:x[1])[:10]; top_paires=paires.most_common(10)
    last_nums=[x for x in rows[0][4].split('-') if x.isdigit() and 1<=int(x)<=90]
    ticket1=[n for n,c in chauds[:5]]; ticket2=[]
    for p in last_nums[:2]:
        if p in annonce: ticket2.extend([n for n,c in annonce[p].most_common(3) if 1<=int(n)<=90])
    ticket2=list(dict.fromkeys(ticket2))[:5]
    if len(ticket2)<5: ticket2=[n for n,c in chauds[5:10]]
    ticket1=[x for x in ticket1 if 1<=int(x)<=90][:5]; ticket2=[x for x in ticket2 if 1<=int(x)<=90][:5]
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a> <a href="/historique?jeu={jeu}" style="color:#25D366;float:right">📜 Historique</a>
    <h3 style="color:gold;text-align:center">🧠 {jeu} - {len(rows)} - {format_date(rows[0][6])}</h3>
    <div style="background:gold;color:#111;padding:14px;border-radius:10px;text-align:center;font-weight:bold;font-size:18px">🎯 TICKET 1: {" - ".join(ticket1)}</div>
    <div style="background:#25D366;color:#fff;padding:14px;border-radius:10px;text-align:center;font-weight:bold;font-size:18px;margin-top:8px">🔥 TICKET 2: {" - ".join(ticket2)}</div>
    <div style="background:#151515;padding:12px;border-radius:10px;margin-top:12px"><b style="color:gold">🔥 Chauds:</b> {", ".join([f"{n}({c})" for n,c in chauds[:12]])}<br><br><b style="color:#888">❄️ Froids:</b> {", ".join([f"{n}({c})" for n,c in froids[:8]])}<br><br><b style="color:#25D366">🔗 Paires:</b><br>{"<br>".join([f"{a}-{b}:{c}" for (a,b),c in top_paires[:8]])} </div>
    <div style="text-align:center;margin-top:12px"><a href="/analyse?jeu={jeu}" style="background:#222;color:gold;padding:10px 20px;border-radius:8px;text-decoration:none;border:1px solid gold">🔄 Actualiser</a></div></body></html>'''

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    today=datetime.now().strftime('%Y-%m-%d')
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6)])
        b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','')])
        if all(1<=int(x)<=90 for x in h.split('-') if x): insert_tirage('LUNDI','09:00',request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect(f'/historique?jeu={request.form.get("jeu")}')
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}input,select{{width:100%;padding:14px;margin:6px 0;border-radius:8px;border:1px solid #444;background:#1a1a1a;color:#fff}}label{{color:gold;font-weight:bold}}.cage{{display:flex;gap:6px}}.cage input{{width:18%;text-align:center;font-weight:bold;border:2px solid gold}}.hidden{{display:none}}button{{width:100%;background:gold;color:#111;padding:16px;border:none;border-radius:12px;font-weight:bold;margin-top:16px}}</style>
    <script>const J10=["MATINALE","DETENTE"];function upd(){{let j=document.getElementById('jeu').value;let md=document.getElementById('machineDiv');if(J10.includes(j))md.classList.remove('hidden');else md.classList.add('hidden');document.getElementById('jeu_input').value=j;}}</script></head><body>
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h2 style="color:gold;text-align:center">🎰 SAISIR V19.0</h2>
    <label>N°</label><input id="numero_out" type="number" value="718"><label>DATE</label><input type="date" id="date_out" value="{today}">
    <label>JEU</label><select id="jeu" onchange="upd()"><option value="MATINALE">MATINALE - 10b</option><option value="DETENTE">DETENTE - 10b</option><option value="BENZ" selected>BENZ - 5b</option><option value="DIAMANT">DIAMANT - 5b</option><option value="GOLD">GOLD</option></select>
    <form id="mainForm" method="POST"><input type="hidden" name="jeu" id="jeu_input" value="BENZ"><input type="hidden" name="numero" id="numero_input"><input type="hidden" name="date" id="date_input"><input type="hidden" name="jour" value="LUNDI"><input type="hidden" name="heure" value="09:00">
    <label>WIN (5)</label><div class="cage"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div>
    <div id="machineDiv" class="hidden"><label style="color:#25D366">MACHINE (5)</label><div class="cage"><input name="b1"><input name="b2"><input name="b3"><input name="b4"><input name="b5"></div></div>
    <button>ENREGISTRER</button></form>
    <script>document.getElementById('mainForm').addEventListener('submit',function(){{document.getElementById('numero_input').value=document.getElementById('numero_out').value;document.getElementById('date_input').value=document.getElementById('date_out').value;}});upd();</script></body></html>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
