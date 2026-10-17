from flask import Flask, request, redirect
import sqlite3, os, re
from collections import Counter, defaultdict
from datetime import datetime

app = Flask(__name__)
DB = "loto.db"
JEUX_LISTE = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]
JEUX_10 = ["MATINALE","DETENTE"]

def get_conn(): return sqlite3.connect(DB)
def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT)')
    conn.commit();conn.close()
init_db()
def insert_tirage(j,h,jeu,haut,bas,date,numero):
    conn=get_conn();c=conn.cursor()
    c.execute('INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created) VALUES (?,?,?,?,?,?,?,?)',(j,h,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y')))
    conn.commit();conn.close()
def fetch_all(jeu=None):
    conn=get_conn();c=conn.cursor()
    c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) DESC' if jeu and jeu!='TOUS' else 'SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) DESC', (jeu,) if jeu and jeu!='TOUS' else ())
    r=c.fetchall();conn.close();return r
def format_date(d):
    try: y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
    except: return d or ""
def parse_file_pro(content, jeu_force):
    res=[]; num_auto=1
    for line in content.splitlines():
        if not line.strip(): continue
        nums = re.findall(r'\b0*(\d{1,2})\b', line)
        nums = [n.zfill(2) for n in nums if n.isdigit() and 1<=int(n)<=90]
        if len(nums)<5: continue
        m=re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', line)
        if m: dd=m.group(1).zfill(2); mm=m.group(2).zfill(2); yy=m.group(3); yy='20'+yy if len(yy)==2 else yy; date_str=f"{yy}-{mm}-{dd}"
        else: m2=re.search(r'(\d{1,2})/(\d{1,2})', line); dd=m2.group(1).zfill(2) if m2 else "01"; mm=m2.group(2).zfill(2) if m2 else "10"; date_str=f"2025-{mm}-{dd}"
        m_num=re.search(r'\b(\d{3,4})\b', line); numero=m_num.group(1) if m_num else str(num_auto); num_auto+=1
        if jeu_force in JEUX_10:
            if len(nums)>=10: haut='-'.join(nums[:5]); bas='-'.join(nums[5:10]); res.append(('LUNDI','09:00',jeu_force,haut,bas,date_str,numero))
            elif len(nums)>=5: haut='-'.join(nums[:5]); bas='-'.join(nums[:5]); res.append(('LUNDI','09:00',jeu_force,haut,bas,date_str,numero))
        else: haut='-'.join(nums[:5]); res.append(('LUNDI','09:00',jeu_force,haut,'',date_str,numero))
    return res

@app.route('/')
def home():
    total=len(fetch_all())
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:12px">
    <div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">V19.2 COMPLET - {total} tirages</div>
    <a href="/historique" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">📜 HISTORIQUE AVEC DATE</a>
    <a href="/saisir" style="display:block;background:gold;color:#111;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">🎰 SAISIR</a>
    <a href="/analyse?jeu=MATINALE" style="display:block;background:#222;border:1px solid #25D366;color:#25D366;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">🧠 ANALYSEUR + IA</a>
    </body></html>'''

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS'); ok=request.args.get('ok'); err=request.args.get('err'); debug=request.args.get('debug','')
    msg=f'<div style="background:#25D366;padding:10px;border-radius:8px">✅ {ok} importés en {jeu_filtre}!</div>' if ok else f'<div style="background:#ff4444;padding:10px;border-radius:8px">❌ {err}<br><small>{debug}</small></div>' if err else ''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE'); content=""
        if 'fichier' in request.files and request.files['fichier'].filename!='':
            f=request.files['fichier']; raw=f.read()
            try: content=raw.decode('utf-8')
            except: content=raw.decode('latin-1', errors='ignore')
        else: content=request.form.get('pasted_text','')
        novos=parse_file_pro(content, jeu_import)
        if not novos:
            sample=content[:200].replace('<','').replace('>','')
            return redirect(f'/historique?jeu={jeu_import}&err=0 detecte - Lu {len(content)} chars&debug={sample}')
        for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
        return redirect(f'/historique?jeu={jeu_import}&ok={len(novos)}')
    rows=fetch_all(jeu_filtre); jeu_pour_import=jeu_filtre if jeu_filtre in JEUX_LISTE else "MATINALE"
    options="".join([f'<option value="{j}" {"selected" if j==jeu_pour_import else ""}>{j} - {10 if j in JEUX_10 else 5}b</option>' for j in JEUX_LISTE])
    filtres=''.join([f'<a href="/historique?jeu={j}" style="background:{"gold" if jeu_filtre==j else "#222"};color:{"#111" if jeu_filtre==j else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;margin:2px;display:inline-block;border:1px solid gold">{j} ({len(fetch_all() if j=="TOUS" else fetch_all(j))})</a>' for j in ["TOUS"]+JEUX_LISTE])
    cards="".join([f'<div style="background:#151515;padding:12px;margin:6px 0;border-radius:10px;border-left:5px solid {"#25D366" if r[5] else "gold"}"><b>📅 {format_date(r[6])} - {r[3]} #{r[7]}</b><br>{"WIN:"+r[4]+" | MACHINE:"+r[5] if r[5] else "NUM:"+r[4]}</div>' for r in rows[:500]]) or '<div style="color:#888;text-align:center;padding:30px">Base vide - Importe fichier</div>'
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({len(rows)})</h3>
    <div style="background:#111;border:2px solid gold;padding:14px;border-radius:12px">{msg}
    <form method="post" enctype="multipart/form-data">
    <select name="jeu_import" style="width:100%;padding:12px;background:#222;color:#fff;border-radius:8px">{options}</select>
    <label style="color:#25D366;font-weight:bold;display:block;margin-top:10px">📁 Choisir FICHIER .txt:</label>
    <input type="file" name="fichier" style="width:100%;padding:12px;background:#222;color:#fff;border:2px dashed #25D366;border-radius:8px">
    <textarea name="pasted_text" style="width:100%;height:50px;background:#222;color:#fff;border-radius:8px;margin-top:8px" placeholder="OU colle 78-89-43-76-32"></textarea>
    <button style="width:100%;background:#25D366;color:#fff;padding:14px;border:none;border-radius:8px;font-weight:bold;margin-top:10px">📁 IMPORTER V19.2</button>
    </form></div><div style="margin:12px 0">{filtres}</div>{cards}</body></html>'''

@app.route('/analyse')
def analyse():
    jeu=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu)
    if not rows: return f'<body style="background:#000;color:#fff;padding:12px"><a href="/historique?jeu={jeu}">⬅ Importer {jeu}</a> Base vide</body>'
    all_nums=[]
    for r in rows:
        all_nums.extend([x for x in r[4].split('-') if x.isdigit() and 1<=int(x)<=90])
        if r[5]: all_nums.extend([x for x in r[5].split('-') if x.isdigit() and 1<=int(x)<=90])
    cnt=Counter(all_nums); chauds=cnt.most_common(5); ticket=' - '.join([n for n,c in chauds])
    return f'<html><body style="background:#000;color:#fff;font-family:Arial;padding:12px"><a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold">{jeu} - {len(rows)}</h3><div style="background:gold;color:#111;padding:14px;border-radius:10px;text-align:center;font-weight:bold">TICKET: {ticket}</div><p>Chauds: {cnt.most_common(12)}</p><a href="/analyse?jeu={jeu}" style="background:#222;color:gold;padding:10px 20px;border-radius:8px;text-decoration:none;border:1px solid gold">🔄</a></body></html>'

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    today=datetime.now().strftime('%Y-%m-%d')
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6)]); b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','')])
        if all(1<=int(x)<=90 for x in h.split('-') if x): insert_tirage('LUNDI','09:00',request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect(f'/historique?jeu={request.form.get("jeu")}')
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}input,select{{width:100%;padding:14px;margin:6px 0;border-radius:8px;border:1px solid #444;background:#1a1a1a;color:#fff}}label{{color:gold;font-weight:bold}}.cage{{display:flex;gap:6px}}.cage input{{width:18%;text-align:center;font-weight:bold;border:2px solid gold}}.hidden{{display:none}}button{{width:100%;background:gold;color:#111;padding:16px;border:none;border-radius:12px;font-weight:bold;margin-top:16px}}</style>
    <script>const J10=["MATINALE","DETENTE"];function upd(){{let j=document.getElementById('jeu').value;let md=document.getElementById('machineDiv');if(J10.includes(j))md.classList.remove('hidden');else md.classList.add('hidden');document.getElementById('jeu_input').value=j;}}</script></head><body>
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h2 style="color:gold;text-align:center">🎰 SAISIR V19.2</h2>
    <label>N°</label><input id="numero_out" type="number" value="718"><label>DATE</label><input type="date" id="date_out" value="{today}">
    <label>JEU</label><select id="jeu" onchange="upd()"><option value="MATINALE">MATINALE - 10b</option><option value="DETENTE">DETENTE - 10b</option><option value="BENZ" selected>BENZ - 5b</option><option value="DIAMANT">DIAMANT - 5b</option></select>
    <form id="mainForm" method="POST"><input type="hidden" name="jeu" id="jeu_input" value="BENZ"><input type="hidden" name="numero" id="numero_input"><input type="hidden" name="date" id="date_input"><input type="hidden" name="jour" value="LUNDI"><input type="hidden" name="heure" value="09:00">
    <label>WIN (5)</label><div class="cage"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div>
    <div id="machineDiv" class="hidden"><label style="color:#25D366">MACHINE (5)</label><div class="cage"><input name="b1"><input name="b2"><input name="b3"><input name="b4"><input name="b5"></div></div>
    <button>ENREGISTRER</button></form>
    <script>document.getElementById('mainForm').addEventListener('submit',function(){{document.getElementById('numero_input').value=document.getElementById('numero_out').value;document.getElementById('date_input').value=document.getElementById('date_out').value;}});upd();</script></body></html>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
