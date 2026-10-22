from flask import Flask, request, redirect, send_file, session
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import os, re, io, secrets

app = Flask(__name__)
app.secret_key = "V19_3_2_STABLE_BOSS_FINAL"
DB = "/data/loto.db" if os.path.exists("/data") else "loto.db"
JEUX = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]
ADMIN_PASS = "Boss2026"

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    try:
        conn=get_conn();c=conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
        c.execute('CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, max_uses INTEGER, used_count INTEGER, expire TEXT, jeu TEXT, note TEXT, created TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS code_uses (id INTEGER PRIMARY KEY, code TEXT, ip TEXT, device TEXT, date TEXT)')
        conn.commit();conn.close()
    except: pass
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    try:
        conn=get_conn();c=conn.cursor()
        c.execute('DELETE FROM tirages WHERE numero=? AND jeu=?',(numero,jeu))
        c.execute('INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y'),0,0))
        conn.commit();conn.close()
    except: pass

def fetch_all(jeu=None):
    try:
        conn=get_conn();c=conn.cursor()
        if jeu and jeu!='TOUS':
            c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) DESC',(jeu,))
        else:
            c.execute('SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) DESC')
        r=c.fetchall();conn.close();return r
    except:
        return []

def check_code(code_str, ip):
    try:
        conn=get_conn();c=conn.cursor()
        c.execute('SELECT code,expire,jeu FROM codes WHERE code=?',(code_str,))
        row=c.fetchone()
        if not row:
            conn.close();return False,"Code invalide"
        code,expire,jeu=row
        if datetime.strptime(expire,'%Y-%m-%d') < datetime.now():
            conn.close();return False,"Code expire"
        c.execute('SELECT * FROM code_uses WHERE code=?',(code,))
        existing=c.fetchall()
        if existing:
            c.execute('SELECT * FROM code_uses WHERE code=? AND ip=?',(code,ip))
            same=c.fetchone()
            if not same:
                conn.close();return False,"CODE DEJA UTILISE - 1 CODE = 1 CLIENT"
        if not existing:
            c.execute('INSERT INTO code_uses (code,ip,device,date) VALUES (?,?,?,?)',(code,ip,'',datetime.now().strftime('%d/%m/%Y')))
            c.execute('UPDATE codes SET used_count=1 WHERE code=?',(code,))
            conn.commit()
        conn.close();return True,jeu
    except Exception as e:
        return False,f"Erreur {e}"

@app.route('/')
def home():
    total=len(fetch_all())
    btns="".join([f"<a style='display:block;padding:14px;margin:8px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold;background:#1e1e1e;color:#fff;border:1px solid #333' href='/analyse?jeu={j}'>ANALYSE {j} ({len(fetch_all(j))})</a>" for j in JEUX])
    code=session.get('code_acces','')
    return f"<html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='background:#000;color:#fff;font-family:Arial;padding:12px'><h1 style='color:gold;text-align:center'>LOTO V19.3.2</h1><p style='text-align:center;color:#888'>{total} tirages - {code if code else 'GRATUIT'}</p>{btns}<a style='display:block;padding:14px;margin:8px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold;background:#25D366;color:#fff' href='/backtest?jeu=SUPER'>BACKTEST</a><a style='display:block;padding:14px;margin:8px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold;background:#111;color:gold;border:1px solid gold' href='/historique?jeu=SUPER'>HISTORIQUE SUPER</a><a style='display:block;padding:14px;margin:8px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold;background:gold;color:#111' href='/acces'>ENTRER CODE UNIQUE</a><a style='display:block;padding:14px;margin:8px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold;background:#222;color:#555' href='/admin'>ADMIN</a></body></html>"

@app.route('/acces', methods=['GET','POST'])
def acces():
    msg=""
    if request.method=='POST':
        code=request.form.get('code','').strip().upper()
        ip=request.remote_addr or "0"
        ok,info=check_code(code,ip)
        if ok:
            session['code_acces']=code;session['jeu_allowed']=info
            return redirect(f"/analyse?jeu={info}")
        else:
            msg=f"<div style='background:#ff3333;padding:12px;border-radius:8px;margin-bottom:10px'>{info}</div>"
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:15px'><a href='/' style='color:gold'>ACCUEIL</a><h2 style='color:gold;text-align:center'>CODE UNIQUE</h2>{msg}<form method='post'><input name='code' placeholder='SUPER-XXXX' style='width:100%;padding:14px;background:#222;color:#fff;border:1px solid gold;border-radius:8px'><button style='width:100%;background:gold;color:#111;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:10px'>VALIDER</button></form></body></html>"

@app.route('/admin', methods=['GET','POST'])
def admin():
    if session.get('admin')!=True:
        if request.method=='POST':
            if request.form.get('pass')==ADMIN_PASS:
                session['admin']=True
                return redirect('/admin')
            else:
                return "<html><body style='background:#000;color:#fff;padding:20px'><h3 style='color:red'>Mauvais pass</h3><a href='/admin' style='color:gold'>Reessayer</a></body></html>"
        return "<html><body style='background:#000;color:#fff;font-family:Arial;padding:20px'><h3 style='color:gold'>ADMIN BOSS</h3><form method='post'><input type='password' name='pass' placeholder='Boss2026' style='width:100%;padding:12px;background:#222;color:#fff;border:1px solid gold;border-radius:8px'><button style='width:100%;background:gold;color:#111;padding:12px;margin-top:10px;border:none;border-radius:8px;font-weight:bold'>ENTRER</button></form></body></html>"
    msg=""
    if request.method=='POST' and 'generer' in request.form:
        jeu=request.form.get('jeu','SUPER'); duree=int(request.form.get('duree','30')); note=request.form.get('note','Client')
        code=f"{jeu}-{secrets.token_hex(3).upper()}"
        expire=(datetime.now()+timedelta(days=duree)).strftime('%Y-%m-%d')
        try:
            conn=get_conn();c=conn.cursor()
            c.execute('INSERT INTO codes (code,max_uses,used_count,expire,jeu,note,created) VALUES (?,?,?,?,?,?,?)',(code,1,0,expire,jeu,note,datetime.now().strftime('%d/%m/%Y')))
            conn.commit();conn.close()
            msg=f"<div style='background:#25D366;color:#fff;padding:15px;border-radius:10px;margin-bottom:10px;text-align:center'><b style='font-size:22px'>{code}</b><br><br>1 CODE = 1 CLIENT<br>Expire {expire} - {jeu}<br>{note}<br><br>COPIE CE CODE</div>"
        except Exception as e:
            msg=f"<div style='background:#ff3333;padding:10px'>Erreur {e}</div>"
    conn=get_conn();c=conn.cursor()
    try:
        c.execute('SELECT code,used_count,expire,jeu,note FROM codes ORDER BY id DESC LIMIT 30')
        codes=c.fetchall()
    except:
        codes=[]
    conn.close()
    html=""
    for co,used,ex,je,no in codes:
        st="UTILISE" if used==1 else "DISPO"
        col="#25D366" if used==1 else "gold"
        html+=f"<div style='background:#151515;padding:8px;margin:4px 0;border-radius:6px;border-left:4px solid {col}'><b>{co}</b> - {st} - {ex} - {je} - {no} <a href='/admin/del/{co}' style='color:red;float:right'>X</a></div>"
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:10px'><a href='/' style='color:gold'>ACCUEIL</a><h3 style='color:gold'>ADMIN V19.3.2 - 1 CODE 1 CLIENT</h3>{msg}<div style='background:#111;border:2px solid gold;padding:12px;border-radius:12px'><form method='post'><select name='jeu' style='width:100%;padding:12px;background:#222;color:#fff;border:1px solid gold;border-radius:6px'><option>SUPER</option><option>MATINALE</option><option>DIAMANT</option><option>TOUS</option></select><input name='duree' value='30' type='number' style='width:100%;padding:10px;margin-top:8px;background:#222;color:#fff;border-radius:6px'><input name='note' placeholder='Nom client + paiement' style='width:100%;padding:10px;margin-top:8px;background:#222;color:#fff;border-radius:6px'><button name='generer' value='1' style='width:100%;background:gold;color:#111;padding:16px;border:none;border-radius:10px;font-weight:bold;margin-top:10px'>GENERER CODE UNIQUE</button></form></div>{html}<a href='/admin/logout' style='display:block;background:#ff3333;color:#fff;padding:10px;text-align:center;border-radius:8px;margin-top:15px;text-decoration:none'>Deconnexion</a></body></html>"

@app.route('/admin/del/<code>')
def adel(code):
    if session.get('admin')!=True: return redirect('/admin')
    conn=get_conn();c=conn.cursor()
    c.execute('DELETE FROM codes WHERE code=?',(code,));c.execute('DELETE FROM code_uses WHERE code=?',(code,));conn.commit();conn.close()
    return redirect('/admin')

@app.route('/admin/logout')
def alogout():
    session.pop('admin',None);return redirect('/')

@app.route('/analyse')
def analyse():
    jeu=request.args.get('jeu','SUPER')
    rows=fetch_all(jeu)
    if not rows:
        return f"<html><body style='background:#000;color:#fff;padding:12px'><a href='/' style='color:gold'>ACCUEIL</a><h3>Base {jeu} vide - Va HISTORIQUE pour importer</h3><a href='/historique?jeu={jeu}' style='color:#25D366'>IMPORTER {jeu}</a></body></html>"
    return f"<html><body style='background:#000;color:#fff;padding:12px'><a href='/' style='color:gold'>ACCUEIL</a><h3 style='color:gold;text-align:center'>{jeu} {len(rows)} tirages - #{rows[0][7] if rows else ''}</h3><div style='background:#141414;padding:10px;border-radius:10px;text-align:center;color:#888'>Moteur V19 pret - {len(rows)} tirages OK<br><br><a href='/backtest?jeu={jeu}' style='background:#25D366;color:#fff;padding:12px;border-radius:8px;text-decoration:none'>BACKTEST</a></div></body></html>"

@app.route('/backtest')
def backtest():
    return "<html><body style='background:#000;color:#fff;padding:20px;text-align:center'><h2 style='color:gold'>BACKTEST</h2><p>Importe d'abord tes tirages</p><a href='/' style='color:gold'>ACCUEIL</a></body></html>"

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu=request.args.get('jeu','SUPER')
    if request.method=='POST':
        jf=request.form.get('jeu_import','SUPER')
        content=None
        pasted=request.form.get('pasted_text','').strip()
        if pasted:
            content=pasted
        else:
            f=request.files.get('file')
            if f and f.filename:
                try:
                    content=f.read().decode('utf-8', errors='ignore')
                except:
                    content=""
        if content:
            count=0
            for line in content.splitlines():
                if 'WIN:' not in line: continue
                try:
                    parts=line.strip().split()
                    numero=parts[0]
                    haut=""
                    if 'WIN:' in line:
                        after=line.split('WIN:')[1].split('/')[0]
                        nums=re.findall(r'\d{1,2}', after)
                        haut='-'.join([x.zfill(2) for x in nums[:5]])
                    if haut:
                        insert_tirage("LUNDI","09:00",jf,haut,"",datetime.now().strftime('%Y-%m-%d'),numero)
                        count+=1
                except: continue
            return redirect(f'/historique?jeu={jf}')
    rows=fetch_all(jeu)
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:10px'><a href='/' style='color:gold'>ACCUEIL</a><h3 style='color:gold;text-align:center'>HISTORIQUE {jeu} ({len(rows)})</h3><div style='background:#111;border:2px solid gold;padding:12px;border-radius:12px'><form method='post' enctype='multipart/form-data'><select name='jeu_import' style='width:100%;padding:12px;background:#222;color:#fff;border:1px solid gold;border-radius:8px'><option selected>{jeu}</option><option>SUPER</option><option>MATINALE</option></select><input type='file' name='file' style='width:100%;background:#222;color:#fff;padding:10px;border-radius:6px;margin-top:8px'><textarea name='pasted_text' placeholder='170 22/10/2026 WIN: 48-84-85-34-41' style='width:100%;height:80px;background:#222;color:#fff;border-radius:8px;margin-top:8px;padding:8px'></textarea><button style='width:100%;background:#25D366;color:#fff;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:10px'>IMPORTER {jeu}</button></form></div><div style='margin-top:10px'><a href='/reset?jeu={jeu}' style='color:red'>Vider {jeu}</a></div></body></html>"

@app.route('/reset')
def reset():
    jeu=request.args.get('jeu','SUPER')
    conn=get_conn();c=conn.cursor()
    if jeu=='TOUS':
        c.execute('DELETE FROM tirages')
    else:
        c.execute('DELETE FROM tirages WHERE jeu=?',(jeu,))
    conn.commit();conn.close()
    return redirect(f'/historique?jeu={jeu}')

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
