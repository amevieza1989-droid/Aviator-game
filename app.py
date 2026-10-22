from flask import Flask, request, render_template_string, redirect, send_file
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os, re, io

app = Flask(__name__)
DB = "/data/loto.db" if os.path.exists("/data") else "loto.db"
JEUX_LISTE = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]
JEUX_10_BOULES = ["MATINALE","DETENTE"]

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
    conn.commit();conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    conn=get_conn();c=conn.cursor()
    c.execute('DELETE FROM tirages WHERE numero=? AND jeu=?',(numero,jeu))
    c.execute('INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y %H:%M'),0,0))
    conn.commit();conn.close()

def fetch_all(jeu=None):
    conn=get_conn();c=conn.cursor()
    if jeu and jeu!='TOUS':
        c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) DESC, id DESC',(jeu,))
    else:
        c.execute('SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) DESC, id DESC')
    r=c.fetchall();conn.close();return r

def parse_file_pro(content, jeu_force):
    res=[]; lines=content.splitlines()
    for line in lines:
        if 'WIN:' not in line: continue
        try:
            nums=re.findall(r'\d{1,2}', line.split('WIN:')[1])
            win_nums=[x.zfill(2) for x in nums if 1<=int(x)<=90][:5]
            if len(win_nums)<5: continue
            numero=re.findall(r'^\s*(\d+)', line)
            num=numero[0] if numero else "1"
            res.append(('LUNDI',"09:00",jeu_force,'-'.join(win_nums),'',"2026-01-01",num))
        except: continue
    return res

def moteur_intelligent_v19(rows):
    if not rows: return {}
    chrono=list(reversed(rows))
    cnt40=Counter()
    for r in chrono[-40:]: cnt40.update([x.zfill(2) for x in r[4].split('-')])
    cnt_total=Counter()
    for r in chrono: cnt_total.update([x.zfill(2) for x in r[4].split('-')])
    paires=Counter()
    for r in chrono:
        nums=[x.zfill(2) for x in r[4].split('-')]
        for i in range(len(nums)):
            for j in range(i+1,len(nums)): paires[tuple(sorted([nums[i],nums[j]]))]+=1
    annonce=defaultdict(Counter); prev=[]
    for r in chrono:
        cur=[x.zfill(2) for x in r[4].split('-')]
        if prev:
            for p in prev:
                for c in cur: annonce[p][c]+=1
        prev=cur
    scores={}
    for i in range(1,91):
        n=str(i).zfill(2); s=cnt40.get(n,0)*3+cnt_total.get(n,0)*0.5
        s+=sum(c for (a,b),c in paires.items() if n in (a,b))*0.1
        scores[n]=s
    pool_sorted=sorted(scores.items(), key=lambda x:x[1], reverse=True)
    pool=[n for n,_ in pool_sorted[:14]]
    last_draw=[x.zfill(2) for x in rows[0][4].split('-')]
    annonce_pool=[]
    for ln in last_draw:
        if ln in annonce: annonce_pool.extend([n for n,_ in annonce[ln].most_common(2)])
    annonce_pool=list(dict.fromkeys(annonce_pool))[:5]
    t1=[n for n,_ in pool_sorted[:5]]
    t2=(annonce_pool[:2]+[n for n in pool if n not in annonce_pool][:3])[:5]
    bp=paires.most_common(3); t3_set=[]
    for (a,b),_ in bp:
        if a not in t3_set: t3_set.append(a)
        if b not in t3_set: t3_set.append(b)
    t3=(t3_set+[n for n in pool if n not in t3_set])[:5]
    retard_sorted=sorted([str(i).zfill(2) for i in range(1,91)], key=lambda x:cnt_total.get(x,0))
    t4=(retard_sorted[:2]+[n for n,_ in pool_sorted[:5] if n not in retard_sorted[:2]])[:5]
    def clean(t): return list(dict.fromkeys(t))[:5]
    return {"T1":clean(t1),"T2":clean(t2),"T3":clean(t3),"T4":clean(t4),"POOL":pool[:12],"cnt40":cnt40.most_common(10),"retard":retard_sorted[:10],"paires":paires.most_common(8)}
    @app.route('/')
def home():
    total=len(fetch_all())
    return render_template_string(f'<html><body style="background:#000;color:#fff;padding:12px"><h2 style="color:gold;text-align:center">LOTO V19 FIX - {total} tirages</h2><a href="/historique" style="display:block;background:#222;border:1px solid gold;color:gold;padding:14px;margin:8px;border-radius:10px;text-align:center;text-decoration:none">HISTORIQUE</a><a href="/analyse?jeu=SUPER" style="display:block;background:gold;color:#111;padding:14px;margin:8px;border-radius:10px;text-align:center;text-decoration:none;font-weight:bold">ANALYSE SUPER</a><a href="/backtest?jeu=SUPER" style="display:block;background:#111;border:1px solid #25D366;color:#25D366;padding:14px;margin:8px;border-radius:10px;text-align:center;text-decoration:none">BACKTEST</a></body></html>')

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS')
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE')
        txt=request.form.get('pasted_text','')
        if txt:
            novos=parse_file_pro(txt, jeu_import)
            if novos:
                conn=get_conn();c=conn.cursor();c.execute('DELETE FROM tirages WHERE jeu=?',(jeu_import,));conn.commit();conn.close()
                for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
    rows=fetch_all(jeu_filtre)
    return f'<html><body style="background:#000;color:#fff;padding:8px"><a href="/" style="color:gold">ACCUEIL</a><h3 style="color:gold">HISTORIQUE {jeu_filtre} ({len(rows)})</h3><form method="post"><select name="jeu_import"><option>MATINALE</option><option>SUPER</option><option>DIAMANT</option></select><textarea name="pasted_text" style="width:100%;height:100px;background:#222;color:#fff"></textarea><button style="width:100%;background:#25D366;color:#fff;padding:12px">IMPORTER</button></form></body></html>'

@app.route('/analyse')
def analyse():
    jeu_filtre=request.args.get('jeu','SUPER'); rows=fetch_all(jeu_filtre)
    if not rows: return 'Base vide'
    res=moteur_intelligent_v19(rows)
    return f'<html><body style="background:#000;color:#fff;padding:8px"><a href="/" style="color:gold">ACCUEIL</a><h3 style="color:gold">V19 {jeu_filtre} {len(rows)} tirages</h3><div style="background:gold;color:#111;padding:12px;border-radius:10px;margin:6px">T1 CHAUDS: {" - ".join(res["T1"])}</div><div style="background:#111;border:2px solid #25D366;color:#25D366;padding:12px;border-radius:10px;margin:6px">T2 ANNONCEUR: {" - ".join(res["T2"])}</div><div style="background:#111;border:2px solid gold;color:gold;padding:12px;border-radius:10px;margin:6px">T3 PAIRES: {" - ".join(res["T3"])}</div><div style="background:#222;border:2px solid #ff6b6b;color:#ff6b6b;padding:12px;border-radius:10px;margin:6px">T4 RETARD: {" - ".join(res["T4"])}</div><div style="margin-top:10px;color:gold">POOL 12: {" - ".join(res["POOL"])}</div></body></html>'

@app.route('/backtest')
def backtest():
    jeu=request.args.get('jeu','SUPER'); rows=fetch_all(jeu)
    if len(rows)<50: return f'Pas assez {len(rows)}'
    chrono=list(reversed(rows)); wins2=0; total=len(chrono)-40
    for i in range(40,len(chrono)):
        past=chrono[:i]; futur=set([x.zfill(2) for x in chrono[i][4].split('-')])
        res=moteur_intelligent_v19(past)
        best=max(len(futur.intersection(set(t))) for t in [res["T1"],res["T2"],res["T3"],res["T4"]])
        if best>=2: wins2+=1
    pct=wins2/total*100 if total else 0
    return f'<html><body style="background:#000;color:#fff;padding:12px"><h2 style="color:gold">BACKTEST {jeu}</h2><div style="font-size:32px;color:#25D366">{pct:.1f}% 2/5</div><div>{wins2}/{total}</div></body></html>'

@app.route('/reset')
def reset():
    conn=get_conn();c=conn.cursor();c.execute('DELETE FROM tirages');conn.commit();conn.close()
    return redirect('/')

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
