from flask import Flask, request, render_template_string, redirect, jsonify
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
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
    conn.commit();conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    conn=get_conn();c=conn.cursor()
    c.execute('INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y %H:%M'),sum(int(x) for x in haut.split('-') if x.isdigit()),sum(int(x) for x in bas.split('-') if x.isdigit()) if bas else 0))
    conn.commit();conn.close()

def fetch_all(jeu=None):
    conn=get_conn();c=conn.cursor()
    c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) DESC' if jeu and jeu!='TOUS' else 'SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) DESC', (jeu,) if jeu and jeu!='TOUS' else ())
    r=c.fetchall();conn.close();return r

# --- V18.4 PARSEUR ULTRA ---
def parse_file_pro(content, jeu_force):
    res=[]
    # Nettoyer et tout mettre sur une seule ligne logique par tirage
    # On cherche le motif: NUMERO DATE ... 5 num ... / ... 5 num
    # Remplace les sauts de ligne entre WIN et MACHINE par espace
    txt = content.replace('\r','\n')
    # Si ligne seule avec 5 numéros genre "05-81-60-45-71", on la colle à la précédente
    txt = re.sub(r'\n\s*(\d{2}[- ]\d{2}[- ]\d{2}[- ]\d{2}[- ]\d{2})\s*\n', r' / \1\n', txt)
    
    # Trouve tous les tirages avec regex ultra tolérante
    pattern = r'(\d{2,4})\s+(\d{1,2})/(\d{1,2})[^\d]*(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})'
    for m in re.finditer(pattern, txt, re.IGNORECASE | re.DOTALL):
        numero, dd, mm = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
        date_str = f"{'2024' if mm=='12' else '2025'}-{mm}-{dd}"
        win = [m.group(4).zfill(2), m.group(5).zfill(2), m.group(6).zfill(2), m.group(7).zfill(2), m.group(8).zfill(2)]
        mach = [m.group(9).zfill(2), m.group(10).zfill(2), m.group(11).zfill(2), m.group(12).zfill(2), m.group(13).zfill(2)]
        # Vérifier 1-90
        if not all(1<=int(x)<=90 for x in win+mach): continue
        haut = '-'.join(win)
        bas = '-'.join(mach) if jeu_force in JEUX_10_BOULES else ''
        if jeu_force in JEUX_10_BOULES and not bas: continue
        res.append(('LUNDI','09:00',jeu_force,haut,bas,date_str,numero))
    return res

@app.route('/manifest.json')
def manifest(): return jsonify({"name":"LOTO V18.4","short_name":"LOTO V18.4","start_url":"/","display":"standalone","background_color":"#000","theme_color":"#FFD700","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/744/744465.png","sizes":"512x512","type":"image/png"}]})
@app.route('/sw.js')
def sw(): return ("self.addEventListener('install',e=>self.skipWaiting());",200,{'Content-Type':'application/javascript'})

@app.route('/')
def home():
    total=len(fetch_all())
    return f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="manifest" href="/manifest.json"></head><body style="background:#000;color:#fff;font-family:Arial;padding:12px"><div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">V18.4 ULTRA - {total} tirages</div><a href="/historique" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">📜 HISTORIQUE - IMPORTER ICI</a><a href="/saisir" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none">🎰 SAISIR</a><a href="/analyse?jeu=MATINALE" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none">🧠 ANALYSE</a></body></html>'

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS')
    ok=request.args.get('ok'); err=request.args.get('err')
    msg=f'<div style="background:#25D366;padding:10px;border-radius:8px;margin-bottom:8px">✅ {ok} importés!</div>' if ok else f'<div style="background:#ff4444;padding:10px;border-radius:8px;margin-bottom:8px">❌ {err}</div>' if err else ''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE')
        txt=request.form.get('pasted_text','')
        if not txt.strip():
            f=request.files.get('file')
            if f: txt=f.read().decode('utf-8', errors='ignore')
        novos=parse_file_pro(txt, jeu_import)
        if not novos:
            return redirect(f'/historique?jeu={jeu_import}&err=0 detecte - J ai lu {len(txt)} caracteres. Colle un exemple: 714 14/10 WIN: 51-07-13-50-12 / 05-81-60-45-71')
        for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
        return redirect(f'/historique?jeu={jeu_import}&ok={len(novos)}')
    
    rows=fetch_all(jeu_filtre)
    jeu_pour_import = jeu_filtre if jeu_filtre in JEUX_LISTE else "MATINALE"
    options = "".join([f'<option value="{j}" {"selected" if j==jeu_pour_import else ""}>{j} - {10 if j in JEUX_10_BOULES else 5}b</option>' for j in JEUX_LISTE])
    filtres=''.join([f'<a href="/historique?jeu={j}" style="background:{"gold" if jeu_filtre==j else "#222"};color:{"#111" if jeu_filtre==j else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;margin:2px;display:inline-block;border:1px solid gold">{j} ({len(fetch_all() if j=="TOUS" else fetch_all(j))})</a>' for j in ["TOUS"]+JEUX_LISTE])
    cards=''.join([f'<div style="background:#151515;padding:8px;margin:4px 0;border-radius:8px;border-left:4px solid {"#25D366" if r[5] else "gold"}">{r[7]} - {r[3]}<br>WIN:{r[4]} | MACHINE:{r[5]} ✅</div>' if r[5] else f'<div style="background:#151515;padding:8px;margin:4px 0;border-radius:8px">{r[7]} - {r[3]} NUM:{r[4]}</div>' for r in rows[:300]]) or '<div style="color:#888;text-align:center;padding:20px">Base vide</div>'
    return f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px"><a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({len(rows)})</h3><div style="background:#111;border:2px solid gold;padding:10px;border-radius:12px">{msg}<form method="post"><select name="jeu_import" style="width:100%;padding:10px;background:#222;color:#fff;border-radius:6px">{options}</select><textarea name="pasted_text" style="width:100%;height:140px;background:#222;color:#fff;border:1px solid #25D366;border-radius:8px;margin-top:6px;padding:8px" placeholder="Colle ici meme si coupé:&#10;714 14/10 WIN: 51-07-13-50-12 /&#10;05-81-60-45-71"></textarea><button style="width:100%;background:#25D366;color:#fff;padding:12px;border:none;border-radius:8px;font-weight:bold;margin-top:6px">🚀 IMPORTER V18.4</button></form></div><div style="margin:10px 0">{filtres}</div>{cards}</body></html>'

@app.route('/analyse')
def analyse():
    jeu=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu)
    if not rows: return f'<html><body style="background:#000;color:#fff;padding:12px"><a href="/historique?jeu={jeu}" style="color:gold">⬅ Importer {jeu}</a><br>Base vide</body></html>'
    from collections import Counter
    c=Counter(); 
    for r in rows: c.update(r[4].split('-'))
    chauds=[n for n,_ in c.most_common(5)]
    return f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;padding:12px"><a href="/" style="color:gold">⬅</a><h3 style="color:gold;text-align:center">{jeu} - {len(rows)} tirages</h3><div style="background:gold;color:#111;padding:14px;border-radius:10px;text-align:center;font-size:20px;font-weight:bold">{" - ".join(chauds)}</div><br><a href="/historique?jeu={jeu}" style="color:#25D366">📜 Voir historique</a></body></html>'

@app.route('/reset')
def reset():
    conn=get_conn();c=conn.cursor();c.execute('DELETE FROM tirages');conn.commit();conn.close()
    return redirect('/historique?jeu=TOUS')

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6)])
        b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','')])
        insert_tirage('LUNDI','09:00',request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect(f'/historique?jeu={request.form.get("jeu")}')
    return f'<html><body style="background:#000;color:#fff;padding:12px"><h3 style="color:gold">SAISIR V18.4</h3><form method="POST"><input name="numero" placeholder="Numero 718" style="width:100%;padding:10px;margin:4px 0"><input name="date" type="date" style="width:100%;padding:10px"><select name="jeu" style="width:100%;padding:10px"><option>MATINALE</option><option>BENZ</option></select><div style="display:flex;gap:4px;margin:10px 0">{"".join([f"<input name=h{i} placeholder={i} style=width:18%>" for i in range(1,6)])}</div><div style="display:flex;gap:4px">{"".join([f"<input name=b{i} placeholder=M{i} style=width:18%>" for i in range(1,6)])}</div><button style="width:100%;background:gold;padding:12px;margin-top:10px;font-weight:bold">ENREGISTRER</button></form></body></html>'

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
