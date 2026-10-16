from flask import Flask, request, render_template_string, redirect, send_file
import sqlite3
from datetime import datetime
import os, urllib.parse, re, io

app = Flask(__name__)
DB = "loto.db"

def get_conn(): return sqlite3.connect(DB)

def init_db():
    conn=get_conn()
    c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
    c.execute('SELECT COUNT(*) FROM tirages')
    if c.fetchone()[0]==0:
        data=[("LUNDI","09:00","MATINALE","84-29-45-23-89","14-13-74-17-90","2026-08-02","1"),("MARDI","09:00","MATINALE","32-01-19-03-79","33-30-85-80-71","2026-08-09","2"),("MERCREDI","09:00","MATINALE","32-88-79-20-19","18-09-10-05-35","2026-08-16","3"),("JEUDI","09:00","MATINALE","30-54-36-45-87","56-10-50-62-04","2026-08-23","4"),("VENDREDI","09:00","MATINALE","69-70-06-13-75","02-44-26-81-28","2026-08-30","5"),("SAMEDI","09:00","MATINALE","20-55-37-24-22","29-45-84-54-49","2026-09-06","6"),("LUNDI","09:00","MATINALE","32-47-81-17-50","03-38-58-82-23","2026-09-13","7"),("DIMANCHE","15:00","DETENTE","55-41-67-23-63","14-04-68-60-20","2026-09-20","8"),("DIMANCHE","15:00","DETENTE","46-78-26-72-10","71-14-65-31-88","2026-09-27","9")]
        for j,h,je,ht,bs,dt,num in data:
            th=sum(int(x) for x in ht.split('-'))
            tb=sum(int(x) for x in bs.split('-'))
            c.execute('INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)',(j,h,je,ht,bs,dt,num,datetime.now().strftime('%d/%m %H:%M'),th,tb))
        conn.commit()
    conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    th=sum(int(x) for x in haut.split('-') if x.strip().isdigit())
    tb=sum(int(x) for x in bas.split('-') if x.strip().isdigit()) if bas else 0
    conn=get_conn();c=conn.cursor()
    c.execute('INSERT INTO tirages VALUES (NULL,?,?,?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m %H:%M'),th,tb))
    conn.commit();conn.close()

def fetch_all():
    conn=get_conn();c=conn.cursor()
    c.execute('SELECT * FROM tirages ORDER BY date DESC, id DESC')
    r=c.fetchall();conn.close();return r

def parse_file(content):
    res=[]
    for line in content.splitlines():
        line=line.strip()
        if not line: continue
        dm=re.search(r'\d{4}-\d{2}-\d{2}',line)
        date=dm.group(0) if dm else datetime.now().strftime('%Y-%m-%d')
        nums=re.findall(r'\d+',line)
        clean=[n.zfill(2) for n in nums if 1<=int(n)<=90]
        if len(clean)>=10:
            haut='-'.join(clean[-10:-5])
            bas='-'.join(clean[-5:])
            res.append(('LUNDI','09:00','MATINALE',haut,bas,date,str(len(res)+100)))
    return res

@app.route('/')
def home():
    rows=fetch_all()
    return render_template_string('<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}.btn{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:18px;margin:14px 0;border-radius:14px;text-align:center;text-decoration:none;font-weight:bold}</style></head><body><div style="background:gold;color:#111;padding:18px;border-radius:15px;text-align:center;font-weight:bold">LOTO V13.3 - {{n}} tirages</div><a class="btn" href="/saisir">SAISIR EN CAGE</a><a class="btn" href="/analyse">ANALYSE VENDEUR</a><a class="btn" href="/historique" style="border-color:#25D366;color:#25D366">HISTORIQUE + IMPORT/EXPORT</a></body></html>', n=len(rows))

@app.route('/historique', methods=['GET','POST'])
def historique():
    msg=''
    if request.method=='POST':
        f=request.files.get('file')
        if f and f.filename:
            content=f.read().decode('utf-8', errors='ignore')
            novos=parse_file(content)
            for j,h,je,ht,bs,dt,num in novos:
                insert_tirage(j,h,je,ht,bs,dt,num)
            msg=f'<div style="background:#25D366;color:#fff;padding:12px;border-radius:10px;margin:10px 0">OK {len(novos)} importes depuis {f.filename}</div>'
    rows=fetch_all()
    cards=''
    for r in rows:
        cards+=f'<div style="background:#151515;padding:12px;margin:8px 0;border-radius:12px;border-left:4px solid gold"><b>{r[1]} {r[2]} {r[3]} #{r[7]}</b> - {r[6]}<br>WIN: {r[4]}<br>MACHINE: {r[5]}</div>'
    return render_template_string('<html><body style="background:#000;color:#fff;font-family:Arial;padding:10px"><a href="/" style="color:gold">ACCUEIL</a><h2 style="color:gold;text-align:center;border:2px solid gold;padding:12px;border-radius:12px">HISTORIQUE - {{n}} TIRAGES</h2><div style="background:#111;border:2px dashed gold;padding:14px;border-radius:14px"><b style="color:gold">IMPORT MASSIF</b>{{msg|safe}}<form method="post" enctype="multipart/form-data"><input type="file" name="file" accept=".txt,.csv" style="width:100%;padding:10px;background:#222;color:#fff;border-radius:8px" required><button type="submit" style="width:100%;background:gold;color:#111;padding:12px;border:none;border-radius:10px;font-weight:bold;margin-top:6px">IMPORTER MATINAL_RESULTS.txt</button></form><div style="display:flex;gap:6px;margin-top:8px"><a href="/export/txt" style="flex:1;text-align:center;background:#111;border:1px solid #25D366;color:#25D366;padding:8px;border-radius:8px;text-decoration:none">Export TXT</a><a href="/export/csv" style="flex:1;text-align:center;background:#111;border:1px solid cyan;color:cyan;padding:8px;border-radius:8px;text-decoration:none">Export CSV</a></div></div>{{cards|safe}}</body></html>', n=len(rows), msg=msg, cards=cards)

@app.route('/export/<fmt>')
def export_file(fmt):
    rows=fetch_all()
    out=io.StringIO()
    if fmt=='csv':
        for r in rows: out.write(f'{r[6]},{r[1]},{r[2]},{r[3]},{r[7]},{r[4]},{r[5]}\n')
        mem=io.BytesIO(out.getvalue().encode('utf-8'))
        return send_file(mem, as_attachment=True, download_name='EXPORT.csv', mimetype='text/csv')
    else:
        for r in rows: out.write(f'{r[6]} | WIN:{r[4]} | MACHINE:{r[5]}\n')
        mem=io.BytesIO(out.getvalue().encode('utf-8'))
        return send_file(mem, as_attachment=True, download_name='EXPORT.txt', mimetype='text/plain')

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6) if request.form.get(f'h{i}','') not in ['','00','0']])
        b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','') not in ['','00','0']])
        insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect('/historique')
    return '''<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#000;color:#fff;font-family:Arial;padding:10px}input,select{width:100%;padding:12px;margin:5px 0;border-radius:8px}</style></head><body><h3 style="color:gold">SAISIR EN CAGE</h3><form method="POST"><input name="numero" placeholder="Numero"><select name="jour"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select><select name="heure"><option>09:00</option><option>13:00</option><option>18:00</option><option>15:00</option></select><input name="jeu" value="MATINALE"><input name="date" type="date"><div style="display:flex;gap:4px"><input name="h1" placeholder="W1"><input name="h2" placeholder="W2"><input name="h3" placeholder="W3"><input name="h4" placeholder="W4"><input name="h5" placeholder="W5"></div><div style="display:flex;gap:4px"><input name="b1" placeholder="M1"><input name="b2" placeholder="M2"><input name="b3" placeholder="M3"><input name="b4" placeholder="M4"><input name="b5" placeholder="M5"></div><button style="width:100%;background:gold;padding:12px;border:none;border-radius:10px;font-weight:bold">ENREGISTRER</button></form><a href="/" style="color:gold">Retour</a></body></html>'''

@app.route('/analyse')
def analyse():
    rows=fetch_all()
    return render_template_string('<html><body style="background:#000;color:#fff;font-family:Arial;padding:10px"><a href="/" style="color:gold">ACCUEIL</a><h2 style="color:gold">ANALYSE - {{n}} tirages</h2><div>Analyse vendeur active</div></body></html>', n=len(rows))

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
