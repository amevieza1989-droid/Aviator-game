from flask import Flask, request, redirect, jsonify
import sqlite3
from collections import Counter
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
    try:
        y,m,dd=d.split('-')
        return f"{dd}/{m}/{y}"
    except:
        return d or "Sans date"

def parse_file_pro(content, jeu_force):
    res=[]
    txt = content.replace('\r','\n')
    txt = re.sub(r'\n\s*(\d{2}[- ]\d{2}[- ]\d{2}[- ]\d{2}[- ]\d{2})\s*\n', r' / \1\n', txt)
    is_10b = jeu_force in JEUX_10_BOULES
    if is_10b:
        pattern = r'(\d{2,4})\s+(\d{1,2})/(\d{1,2})[^\d]*(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})'
        for m in re.finditer(pattern, txt, re.IGNORECASE | re.DOTALL):
            numero, dd, mm = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
            date_str = f"{'2024' if mm=='12' else '2025'}-{mm}-{dd}"
            win = [m.group(i).zfill(2) for i in range(4,9)]
            mach = [m.group(i).zfill(2) for i in range(9,14)]
            if not all(1<=int(x)<=90 for x in win+mach): continue
            res.append(('LUNDI','09:00',jeu_force,'-'.join(win),'-'.join(mach),date_str,numero))
    else:
        pattern = r'(\d{2,4})\s+(\d{1,2})/(\d{1,2})[^\d]*(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})\D+(\d{1,2})'
        for m in re.finditer(pattern, txt, re.IGNORECASE | re.DOTALL):
            numero, dd, mm = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
            date_str = f"{'2024' if mm=='12' else '2025'}-{mm}-{dd}"
            win = [m.group(i).zfill(2) for i in range(4,9)]
            if not all(1<=int(x)<=90 for x in win): continue
            res.append(('LUNDI','09:00',jeu_force,'-'.join(win),'',date_str,numero))
    return res

@app.route('/')
def home():
    total=len(fetch_all())
    return f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:12px"><div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">V18.6 DATE OK - {total} tirages</div><a href="/historique" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">📜 HISTORIQUE AVEC DATE</a><a href="/saisir" style="display:block;background:gold;color:#111;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">🎰 SAISIR</a></body></html>'

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS')
    ok=request.args.get('ok'); err=request.args.get('err')
    msg=f'<div style="background:#25D366;padding:10px;border-radius:8px;margin-bottom:8px">✅ {ok} importés en {jeu_filtre}!</div>' if ok else f'<div style="background:#ff4444;padding:10px;border-radius:8px;margin-bottom:8px">❌ {err}</div>' if err else ''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE')
        txt=request.form.get('pasted_text','')
        novos=parse_file_pro(txt, jeu_import)
        if not novos:
            return redirect(f'/historique?jeu={jeu_import}&err=0 detecte - Verifie format')
        for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
        return redirect(f'/historique?jeu={jeu_import}&ok={len(novos)}')
    
    rows=fetch_all(jeu_filtre)
    jeu_pour_import = jeu_filtre if jeu_filtre in JEUX_LISTE else "MATINALE"
    options = "".join([f'<option value="{j}" {"selected" if j==jeu_pour_import else ""}>{j} - {10 if j in JEUX_10_BOULES else 5}b</option>' for j in JEUX_LISTE])
    filtres=''.join([f'<a href="/historique?jeu={j}" style="background:{"gold" if jeu_filtre==j else "#222"};color:{"#111" if jeu_filtre==j else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;margin:2px;display:inline-block;border:1px solid gold">{j} ({len(fetch_all() if j=="TOUS" else fetch_all(j))})</a>' for j in ["TOUS"]+JEUX_LISTE])
    
    # --- HISTORIQUE AVEC DATE BIEN VISIBLE ---
    cards_html = ""
    for r in rows[:500]:
        # r = id, jour, heure, jeu, haut, bas, date, numero, created
        date_aff = format_date(r[6])
        if r[5]: # 10 boules
            cards_html += f'<div style="background:#151515;padding:12px;margin:6px 0;border-radius:10px;border-left:5px solid #25D366"><div style="color:#25D366;font-weight:bold;font-size:14px">📅 {date_aff} - {r[3]} #{r[7]}</div><div style="margin-top:4px"><span style="color:gold">WIN:</span> {r[4]}<br><span style="color:#25D366">MACHINE:</span> {r[5]} ✅ 10b</div></div>'
        else:
            cards_html += f'<div style="background:#151515;padding:12px;margin:6px 0;border-radius:10px;border-left:5px solid gold"><div style="color:gold;font-weight:bold;font-size:14px">📅 {date_aff} - {r[3]} #{r[7]}</div><div style="margin-top:4px">NUM: {r[4]} (5b)</div></div>'
    if not cards_html:
        cards_html = '<div style="color:#888;text-align:center;padding:30px">Base vide - Importe ton fichier</div>'

    return f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px"><a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({len(rows)})</h3><div style="background:#111;border:2px solid gold;padding:10px;border-radius:12px">{msg}<form method="post"><select name="jeu_import" style="width:100%;padding:10px;background:#222;color:#fff;border-radius:6px">{options}</select><textarea name="pasted_text" style="width:100%;height:100px;background:#222;color:#fff;border:1px solid #25D366;border-radius:8px;margin-top:6px;padding:8px" placeholder="703 01/10 WIN: 18-13-79-01-32 / 02-46-24-72-41"></textarea><button style="width:100%;background:#25D366;color:#fff;padding:12px;border:none;border-radius:8px;font-weight:bold;margin-top:6px">🚀 IMPORTER V18.6</button></form></div><div style="margin:12px 0">{filtres}</div>{cards_html}</body></html>'

@app.route('/reset')
def reset():
    conn=get_conn();c=conn.cursor();c.execute('DELETE FROM tirages');conn.commit();conn.close()
    return redirect('/historique?jeu=TOUS')

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    today=datetime.now().strftime('%Y-%m-%d')
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6)])
        b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','')])
        insert_tirage('LUNDI','09:00',request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect(f'/historique?jeu={request.form.get("jeu")}')
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}input,select{{width:100%;padding:14px;margin:6px 0;border-radius:8px;border:1px solid #444;background:#1a1a1a;color:#fff;font-size:16px}}label{{color:gold;font-weight:bold;font-size:13px;margin-top:10px;display:block}}.cage{{display:flex;gap:6px}}.cage input{{width:18%;text-align:center;font-weight:bold;font-size:18px;border:2px solid gold}}.hidden{{display:none}}button{{width:100%;background:gold;color:#111;padding:16px;border:none;border-radius:12px;font-weight:bold;margin-top:16px}}</style>
    <script>const JEUX_10=["MATINALE","DETENTE"];function updateForm(){{let jeu=document.getElementById('jeu').value;let md=document.getElementById('machineDiv');let lw=document.getElementById('labelWin');let info=document.getElementById('infoJeu');if(JEUX_10.includes(jeu)){{md.classList.remove('hidden');lw.innerText="WIN (5) - "+jeu+" = 10 BOULES";info.innerText=jeu+" = 10 BOULES";info.style.background="#25D366";}}else{{md.classList.add('hidden');lw.innerText="NUM (5) - "+jeu+" = 5 BOULES";info.innerText=jeu+" = 5 BOULES";info.style.background="gold";info.style.color="#111";}}document.getElementById('jeu_input').value=jeu;}}</script></head><body>
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h2 style="color:gold;text-align:center">🎰 SAISIR V18.6</h2>
    <div id="infoJeu" style="background:gold;color:#111;padding:10px;border-radius:8px;text-align:center;font-weight:bold">BENZ = 5 BOULES</div>
    <label>N°</label><input id="numero_out" type="number" value="718"><label>DATE</label><input type="date" id="date_out" value="{today}">
    <label>JEU</label><select id="jeu" onchange="updateForm()"><option value="MATINALE">MATINALE - 10 BOULES</option><option value="DETENTE">DETENTE - 10 BOULES</option><option value="BENZ" selected>BENZ - 5 BOULES</option><option value="GOLD">GOLD - 5 BOULES</option><option value="DIAMANT">DIAMANT</option><option value="CASH">CASH</option><option value="BOOM">BOOM</option><option value="PRESTIGE">PRESTIGE</option><option value="MILLION">MILLION</option><option value="SUPER">SUPER</option><option value="KADOO">KADOO</option><option value="KING">KING</option><option value="SAM">SAM</option><option value="BINGO">BINGO</option></select>
    <form id="mainForm" method="POST"><input type="hidden" name="jour" value="LUNDI"><input type="hidden" name="heure" value="09:00"><input type="hidden" name="jeu" id="jeu_input" value="BENZ"><input type="hidden" name="numero" id="numero_input"><input type="hidden" name="date" id="date_input">
    <label id="labelWin">NUM (5)</label><div class="cage"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div>
    <div id="machineDiv" class="hidden"><label style="color:#25D366">MACHINE (5)</label><div class="cage"><input name="b1"><input name="b2"><input name="b3"><input name="b4"><input name="b5"></div></div>
    <button>ENREGISTRER</button></form>
    <script>document.getElementById('mainForm').addEventListener('submit',function(){{document.getElementById('numero_input').value=document.getElementById('numero_out').value;document.getElementById('date_input').value=document.getElementById('date_out').value;}});updateForm();</script>
    </body></html>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
