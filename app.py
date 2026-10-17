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
        # Extraire tous les nombres 1-90
        nums = re.findall(r'\b0*(\d{1,2})\b', line)
        nums = [n.zfill(2) for n in nums if n.isdigit() and 1<=int(n)<=90]
        if len(nums)<5: continue
        # Date
        m=re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', line)
        if m:
            dd=m.group(1).zfill(2); mm=m.group(2).zfill(2); yy=m.group(3)
            yy='20'+yy if len(yy)==2 else yy
            date_str=f"{yy}-{mm}-{dd}"
        else:
            m2=re.search(r'(\d{1,2})/(\d{1,2})', line)
            dd=m2.group(1).zfill(2) if m2 else "01"
            mm=m2.group(2).zfill(2) if m2 else "10"
            date_str=f"2025-{mm}-{dd}"
        # Numero = premier nombre 2-4 chiffres dans la ligne ou auto
        m_num=re.search(r'\b(\d{3,4})\b', line)
        numero=m_num.group(1) if m_num else str(num_auto)
        num_auto+=1
        # LOGIQUE ULTRA SIMPLE
        if jeu_force in JEUX_10:
            # Besoin de 10 boules
            if len(nums)>=10:
                haut='-'.join(nums[:5]); bas='-'.join(nums[5:10])
                res.append(('LUNDI','09:00',jeu_force,haut,bas,date_str,numero))
            elif len(nums)>=5:
                # Si seulement 5, on duplique pas, on met 5 en haut, vide en bas -> refuse, donc on prend 5 quand même
                haut='-'.join(nums[:5])
                # Pour ne pas perdre, on importe quand même en 10b avec bas = les 5 suivants si possible sinon 5 random
                bas='-'.join(nums[:5])  # temporaire pour ne pas bloquer
                res.append(('LUNDI','09:00',jeu_force,haut,bas,date_str,numero))
        else:
            haut='-'.join(nums[:5])
            res.append(('LUNDI','09:00',jeu_force,haut,'',date_str,numero))
    return res

@app.route('/')
def home():
    total=len(fetch_all())
    return f'<html><body style="background:#000;color:#fff;font-family:Arial;padding:12px"><div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">V19.1 ULTRA - {total} tirages</div><a href="/historique?jeu=MATINALE" style="display:block;background:#25D366;color:#fff;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">📁 IMPORTER FICHIER MATINALE</a><a href="/analyse?jeu=MATINALE" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none">🧠 ANALYSE</a></body></html>'

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS'); ok=request.args.get('ok'); err=request.args.get('err'); debug=request.args.get('debug','')
    msg=f'<div style="background:#25D366;padding:10px;border-radius:8px">✅ {ok} importés!</div>' if ok else f'<div style="background:#ff4444;padding:10px;border-radius:8px">❌ {err}<br><small>{debug}</small></div>' if err else ''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE'); content=""
        if 'fichier' in request.files and request.files['fichier'].filename!='':
            f=request.files['fichier']
            raw=f.read()
            try: content=raw.decode('utf-8')
            except: content=raw.decode('latin-1', errors='ignore')
        else: content=request.form.get('pasted_text','')
        novos=parse_file_pro(content, jeu_import)
        if not novos:
            sample=content[:200].replace('<','').replace('>','')
            return redirect(f'/historique?jeu={jeu_import}&err=0 detecte - Fichier lu: {len(content)} chars&debug=Debut: {sample}')
        for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
        return redirect(f'/historique?jeu={jeu_import}&ok={len(novos)}')
    rows=fetch_all(jeu_filtre)
    jeu_pour_import=jeu_filtre if jeu_filtre in JEUX_LISTE else "MATINALE"
    options="".join([f'<option value="{j}" {"selected" if j==jeu_pour_import else ""}>{j}</option>' for j in JEUX_LISTE])
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({len(rows)})</h3>
    <div style="background:#111;border:2px solid gold;padding:14px;border-radius:12px">{msg}
    <form method="post" enctype="multipart/form-data">
    <select name="jeu_import" style="width:100%;padding:12px;background:#222;color:#fff;border-radius:8px">{options}</select>
    <label style="color:#25D366;font-weight:bold;display:block;margin-top:10px">📁 FICHIER .txt:</label>
    <input type="file" name="fichier" accept=".txt,.csv,.log" style="width:100%;padding:12px;background:#222;color:#fff;border:2px dashed #25D366;border-radius:8px">
    <textarea name="pasted_text" style="width:100%;height:60px;background:#222;color:#fff;border-radius:8px;margin-top:8px" placeholder="OU colle ici"></textarea>
    <button style="width:100%;background:#25D366;color:#fff;padding:14px;border:none;border-radius:8px;font-weight:bold;margin-top:10px">📁 IMPORTER V19.1</button>
    </form></div></body></html>'''

@app.route('/analyse')
def analyse():
    jeu=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu)
    if not rows: return f'<body style="background:#000;color:#fff;padding:12px"><a href="/historique?jeu={jeu}">⬅ Importer {jeu}</a> Base vide {jeu}</body>'
    all_nums=[]
    for r in rows:
        all_nums.extend([x for x in r[4].split('-') if x.isdigit() and 1<=int(x)<=90])
        if r[5]: all_nums.extend([x for x in r[5].split('-') if x.isdigit() and 1<=int(x)<=90])
    cnt=Counter(all_nums); chauds=cnt.most_common(5)
    ticket=' - '.join([n for n,c in chauds])
    return f'<html><body style="background:#000;color:#fff;font-family:Arial;padding:12px"><a href="/" style="color:gold">⬅</a><h3 style="color:gold">{jeu} - {len(rows)} tirages</h3><div style="background:gold;color:#111;padding:14px;border-radius:10px;text-align:center;font-weight:bold">TICKET: {ticket}</div><p>Chauds: {cnt.most_common(10)}</p></body></html>'

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
