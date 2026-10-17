from flask import Flask, request, redirect
import sqlite3, os, re
from collections import Counter
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
    if not d or d.strip()=="": return ""
    try: y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
    except: return d

def parse_file_pro(content, jeu_force):
    res=[]
    for line in content.splitlines():
        if not line.strip(): continue
        orig=line
        m_num=re.search(r'#\s*(\d+)', orig)
        if not m_num: m_num=re.search(r'^\s*(\d{2,4})\b', orig)
        numero=m_num.group(1) if m_num else ""
        win_nums=[]; mach_nums=[]
        m_win=re.search(r'WIN\s*[:\-]\s*([0-9\-]+)', orig, re.I)
        m_mach=re.search(r'MACHINE\s*[:\-]\s*([0-9\-]+)', orig, re.I)
        if m_win: win_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', m_win.group(1)) if 1<=int(x)<=90][:5]
        if m_mach: mach_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', m_mach.group(1)) if 1<=int(x)<=90][:5]
        if not win_nums:
            all_nums=[x.zfill(2) for x in re.findall(r'\b\d{1,2}\b', orig) if 1<=int(x)<=90]
            if len(all_nums)>=10 and jeu_force in JEUX_10: win_nums=all_nums[:5]; mach_nums=all_nums[5:10]
            elif len(all_nums)>=5: win_nums=all_nums[:5]
        if len(win_nums)<5: continue
        # VRAIE DATE SEULEMENT 2020-2026, mois 1-12, jour 1-31
        date_str=""
        m_date=re.search(r'(\d{1,2})[/-](\d{1,2})[/-](20\d{2})', orig)
        if m_date:
            dd=int(m_date.group(1)); mm=int(m_date.group(2)); yy=int(m_date.group(3))
            if 1<=dd<=31 and 1<=mm<=12 and 2020<=yy<=2026:
                date_str=f"{yy}-{str(mm).zfill(2)}-{str(dd).zfill(2)}"
        haut='-'.join(win_nums[:5]); bas='-'.join(mach_nums[:5]) if mach_nums else ""
        res.append(('LUNDI','09:00',jeu_force,haut,bas,date_str,numero))
    return res

@app.route('/')
def home():
    total=len(fetch_all())
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:12px">
    <div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">V20.1 SAISIR COMPLET - {total} tirages</div>
    <a href="/historique" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">📜 HISTORIQUE</a>
    <a href="/saisir" style="display:block;background:gold;color:#111;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">🎰 SAISIR - 14 JEUX</a>
    <a href="/analyse?jeu=MATINALE" style="display:block;background:#222;border:1px solid #25D366;color:#25D366;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">🧠 ANALYSE</a>
    </body></html>'''

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS'); ok=request.args.get('ok'); err=request.args.get('err')
    msg=f'<div style="background:#25D366;padding:10px;border-radius:8px">✅ {ok} importés!</div>' if ok else f'<div style="background:#ff4444;padding:10px;border-radius:8px">❌ {err}</div>' if err else ''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE'); content=""
        if 'fichier' in request.files and request.files['fichier'].filename!='':
            f=request.files['fichier']; raw=f.read()
            try: content=raw.decode('utf-8')
            except: content=raw.decode('latin-1', errors='ignore')
        else: content=request.form.get('pasted_text','')
        novos=parse_file_pro(content, jeu_import)
        if not novos: return redirect(f'/historique?jeu={jeu_import}&err=0 detecte')
        for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
        return redirect(f'/historique?jeu={jeu_import}&ok={len(novos)}')
    rows=fetch_all(jeu_filtre); jeu_pour_import=jeu_filtre if jeu_filtre in JEUX_LISTE else "MATINALE"
    options="".join([f'<option value="{j}" {"selected" if j==jeu_pour_import else ""}>{j} - {10 if j in JEUX_10 else 5}b</option>' for j in JEUX_LISTE])
    filtres=''.join([f'<a href="/historique?jeu={j}" style="background:{"gold" if jeu_filtre==j else "#222"};color:{"#111" if jeu_filtre==j else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;margin:2px;display:inline-block;border:1px solid gold">{j} ({len(fetch_all() if j=="TOUS" else fetch_all(j))})</a>' for j in ["TOUS"]+JEUX_LISTE])
    cards=""
    for r in rows[:500]:
        date_affiche=format_date(r[6])
        titre = f"{date_affiche} - {r[3]} #{r[7]}" if date_affiche else f"{r[3]} #{r[7]}"
        cards+=f'<div style="background:#151515;padding:12px;margin:6px 0;border-radius:10px;border-left:5px solid gold"><b>📅 {titre}</b><br>WIN:{r[4]} | MACHINE:{r[5] if r[5] else "-"}</div>'
    if not cards: cards='<div style="color:#888;text-align:center;padding:30px">Base vide</div>'
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({len(rows)})</h3>
    <div style="background:#111;border:2px solid gold;padding:14px;border-radius:12px">{msg}
    <form method="post" enctype="multipart/form-data">
    <select name="jeu_import" style="width:100%;padding:12px;background:#222;color:#fff;border-radius:8px">{options}</select>
    <input type="file" name="fichier" style="width:100%;padding:12px;background:#222;color:#fff;border:2px dashed #25D366;border-radius:8px;margin:8px 0">
    <button style="width:100%;background:#25D366;color:#fff;padding:14px;border:none;border-radius:8px;font-weight:bold">📁 IMPORTER V20.1</button>
    </form></div><div style="margin:12px 0">{filtres}</div>{cards}</body></html>'''

@app.route('/analyse')
def analyse():
    jeu=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu)
    if not rows: return f'<body style="background:#000;color:#fff;padding:12px"><a href="/historique?jeu={jeu}">⬅ Importer</a> Base vide</body>'
    all_nums=[]
    for r in rows:
        all_nums.extend([x for x in r[4].split('-') if x.isdigit()])
        if r[5]: all_nums.extend([x for x in r[5].split('-') if x.isdigit()])
    cnt=Counter(all_nums); chauds=cnt.most_common(5); ticket=' - '.join([n for n,c in chauds])
    return f'<html><body style="background:#000;color:#fff;font-family:Arial;padding:12px"><a href="/" style="color:gold">⬅</a><h3 style="color:gold">{jeu} - {len(rows)}</h3><div style="background:gold;color:#111;padding:14px;border-radius:10px;text-align:center;font-weight:bold">TICKET: {ticket}</div></body></html>'

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    today=datetime.now().strftime('%Y-%m-%d')
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6)]); b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','')])
        if all(1<=int(x)<=90 for x in h.split('-') if x): insert_tirage('LUNDI','09:00',request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect(f'/historique?jeu={request.form.get("jeu")}')
    # ICI LES 14 JEUX COMPLETS
    options_saisir="".join([f'<option value="{j}">{j} - {10 if j in JEUX_10 else 5}b</option>' for j in JEUX_LISTE])
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}input,select{{width:100%;padding:14px;margin:6px 0;border-radius:8px;border:1px solid #444;background:#1a1a1a;color:#fff;font-size:16px}}label{{color:gold;font-weight:bold}}.cage{{display:flex;gap:6px}}.cage input{{width:18%;text-align:center;font-weight:bold;border:2px solid gold}}.hidden{{display:none}}button{{width:100%;background:gold;color:#111;padding:16px;border:none;border-radius:12px;font-weight:bold;margin-top:16px}}</style>
    <script>const J10=["MATINALE","DETENTE"];function upd(){{let j=document.getElementById('jeu').value;let md=document.getElementById('machineDiv');if(J10.includes(j))md.classList.remove('hidden');else md.classList.add('hidden');document.getElementById('jeu_input').value=j;}}</script></head><body>
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h2 style="color:gold;text-align:center">🎰 SAISIR V20.1 - 14 JEUX</h2>
    <label>N° TIRAGE</label><input id="numero_out" type="number" value="718"><label>DATE (vraie date)</label><input type="date" id="date_out" value="{today}">
    <label>JEU (14 jeux)</label><select id="jeu" onchange="upd()">{options_saisir}</select>
    <form id="mainForm" method="POST"><input type="hidden" name="jeu" id="jeu_input" value="MATINALE"><input type="hidden" name="numero" id="numero_input"><input type="hidden" name="date" id="date_input"><input type="hidden" name="jour" value="LUNDI"><input type="hidden" name="heure" value="09:00">
    <label>WIN (5 numéros)</label><div class="cage"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div>
    <div id="machineDiv"><label style="color:#25D366">MACHINE (5 pour MATINALE/DETENTE)</label><div class="cage"><input name="b1"><input name="b2"><input name="b3"><input name="b4"><input name="b5"></div></div>
    <button>ENREGISTRER</button></form>
    <script>document.getElementById('mainForm').addEventListener('submit',function(){{document.getElementById('numero_input').value=document.getElementById('numero_out').value;document.getElementById('date_input').value=document.getElementById('date_out').value;}});upd();</script>
    </body></html>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
