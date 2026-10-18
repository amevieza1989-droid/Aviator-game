from flask import Flask, request, redirect, send_file
import sqlite3, os, re, io
from datetime import datetime

app = Flask(__name__)
DB = "/data/loto.db" if os.path.exists("/data") else "loto.db"
def get_conn(): return sqlite3.connect(DB)
def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT)')
    conn.commit();conn.close()
init_db()

def insert_tirage(j,h,jeu,haut,bas,date,numero):
    conn=get_conn();c=conn.cursor()
    c.execute('DELETE FROM tirages WHERE numero=? AND jeu=?',(numero,jeu))
    c.execute('INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created) VALUES (?,?,?,?,?,?,?,?)',(j,h,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y')))
    conn.commit();conn.close()

def fetch_all(jeu=None):
    conn=get_conn();c=conn.cursor()
    if jeu and jeu!='TOUS': c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) ASC',(jeu,))
    else: c.execute('SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) ASC')
    r=c.fetchall(); conn.close(); return r

def format_date(d):
    if not d: return ""
    try: y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
    except: return d

# === PARSER V24 FIX DATE 2026 ===
def parse_matinale_propre(content, jeu_force):
    raw_lines=content.splitlines()
    merged=[]; i=0
    while i < len(raw_lines):
        l=raw_lines[i].strip()
        if not l: i+=1; continue
        if l.endswith('/') and i+1 < len(raw_lines):
            merged.append(l+' '+raw_lines[i+1].strip()); i+=2
        else:
            merged.append(l); i+=1
    res=[]
    for line in merged:
        if 'WIN:' not in line: continue
        line=line.replace('\ufeff','').strip()
        tokens=line.split()
        if not tokens or not tokens[0].isdigit(): continue
        numero=tokens[0]
        
        # NOUVEAU: cherche JJ/MM/AAAA d'abord!
        m_full=re.search(r'(\d{1,2})/(\d{4})', line)
        if m_full:
            dd,mm,yyyy=m_full.groups()
            date_str=f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
        else:
            # Ancien format JJ/MM sans année -> force 2026
            m_short=re.search(r'(\d{1,2})/(\d{1,2})', line)
            if not m_short: continue
            dd,mm=m_short.groups()
            date_str=f"2026-{mm.zfill(2)}-{dd.zfill(2)}"
        
        try:
            after_win=line.split('WIN:')[1]
            win_part, mach_part= (after_win.split('/',1) if '/' in after_win else (after_win,""))
            win_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', win_part) if 1<=int(x)<=90][:5]
            mach_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', mach_part) if 1<=int(x)<=90][:5]
            if len(win_nums)<5: continue
            haut='-'.join(win_nums); bas='-'.join(mach_nums) if len(mach_nums)==5 else ""
            res.append(('LUNDI','09:00',jeu_force,haut,bas,date_str,numero))
        except: continue
    return res

# --- Le reste de ton app garde identique ---
def auto_seed():
    if len(fetch_all())>0: return
    for fname in ["MATINAL_CORI.txt","MATINAL_CORI.TXT","matinal_cori.txt"]:
        if os.path.exists(fname):
            try:
                with open(fname,'r',encoding='utf-8',errors='ignore') as f: content=f.read()
                data=parse_matinale_propre(content,"MATINALE")
                for j,h,je,ht,bs,dt,num in data: insert_tirage(j,h,je,ht,bs,dt,num)
                break
            except: pass
auto_seed()

@app.route('/')
def home():
    total=len(fetch_all())
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:12px">
    <div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">V24 FIX-DATE - {total} - 2026 OK</div>
    <a href="/historique" style="display:block;background:#222;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none">📜 HISTORIQUE</a>
    <a href="/export" style="display:block;background:#25D366;color:#fff;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold">💾 EXPORTER</a>
    </body></html>'''

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS')
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE'); content=""
        if 'fichier' in request.files and request.files['fichier'].filename!='':
            raw=request.files['fichier'].read()
            try: content=raw.decode('utf-8')
            except: content=raw.decode('latin-1', errors='ignore')
        else: content=request.form.get('pasted_text','')
        novos=parse_matinale_propre(content, jeu_import)
        if novos:
            # Efface tout avant réimport pour être propre
            conn=get_conn();c=conn.cursor();c.execute('DELETE FROM tirages');conn.commit();conn.close()
            for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
        return redirect(f'/historique?jeu={jeu_import}')
    rows=fetch_all(jeu_filtre)
    cards="".join([f'<div style="background:#151515;padding:12px;margin:6px 0;border-radius:10px;border-left:5px solid gold"><b>📅 {format_date(r[6])} - {r[3]} #{r[7]}</b><br>WIN:{r[4]} | MACHINE:{r[5]}</div>' for r in rows[-100:][::-1]])
    return f'''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="background:#000;color:#fff;font-family:Arial;padding:8px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">{jeu_filtre} ({len(rows)})</h3>
    <form method="POST" enctype="multipart/form-data" style="background:#111;padding:10px;border-radius:10px;margin-bottom:10px">
    <select name="jeu_import"><option>MATINALE</option></select><input type="file" name="fichier"><button style="background:gold;width:100%;padding:12px;margin-top:6px;border-radius:8px">IMPORTER V24</button></form>
    {cards}</body></html>'''

@app.route('/export')
def export_page():
    rows=fetch_all("TOUS")
    return f'''<html><body style="background:#000;color:#fff"><a href="/" style="color:gold">⬅</a><h3>Export {len(rows)}</h3><a href="/export/txt">TXT 2026</a></body></html>'''
@app.route('/export/txt')
def export_txt():
    rows=fetch_all("TOUS"); out=[]
    for r in rows:
        if r[6]:
            try: y,m,d=r[6].split('-'); ds=f"{d}/{m}/{y}"
            except: ds=""
        else: ds=""
        if r[5]: out.append(f"{r[7]} {ds} WIN: {r[4]} / {r[5]}")
        else: out.append(f"{r[7]} {ds} WIN: {r[4]}")
    txt="\n".join(out); buf=io.BytesIO(txt.encode('utf-8')); buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="MATINALE_2026.txt", mimetype="text/plain")

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
