from flask import Flask, request
import sqlite3, os
from collections import Counter
from datetime import datetime

app = Flask(__name__)
DB = "loto.db"

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jeu TEXT, haut TEXT, numero TEXT)')
    conn.commit()
    conn.close()

init_db()

def fetch_all(jeu=None):
    conn = get_conn()
    cur = conn.cursor()
    if jeu and jeu != "TOUS":
        cur.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY id DESC',(jeu,))
    else:
        cur.execute('SELECT * FROM tirages ORDER BY id DESC')
    r = cur.fetchall()
    conn.close()
    return r

def moteur(rows):
    from collections import Counter
    c = Counter()
    for r in rows[-40:]:
        c.update(r[2].split('-'))
    pool = [n for n,_ in c.most_common(12)]
    if len(pool) < 5:
        pool = ["01","05","12","25","33","47","52","69","70","81","85","90"]
    return {"T1":pool[:5],"T2":pool[2:7],"T3":pool[4:9],"T4":pool[1:6],"POOL":pool}

@app.route('/')
def home():
    total = len(fetch_all())
    return f'<h1 style="color:gold">LOTO V19 FIX OK - {total} tirages</h1><a href="/analyse?jeu=SUPER">ANALYSE</a> | <a href="/backtest?jeu=SUPER">BACKTEST</a> | <a href="/historique">HISTORIQUE</a>'

@app.route('/analyse')
def analyse():
    jeu = request.args.get('jeu','SUPER')
    rows = fetch_all(jeu)
    if not rows:
        return 'Base vide'
    res = moteur(rows)
    return f'T1: {"-".join(res["T1"])}<br>T2: {"-".join(res["T2"])}<br>T3: {"-".join(res["T3"])}<br>T4: {"-".join(res["T4"])}<br>POOL: {"-".join(res["POOL"])}'

@app.route('/backtest')
def backtest():
    jeu = request.args.get('jeu','SUPER')
    rows = fetch_all(jeu)
    if len(rows) < 40:
        return f'Pas assez {len(rows)}'
    chrono = list(reversed(rows))
    wins = 0
    total = len(chrono)-40
    for i in range(40,len(chrono)):
        past = chrono[:i]
        futur = set(chrono[i][2].split('-'))
        res = moteur(past)
        best = max(len(futur.intersection(set(t))) for t in [res["T1"],res["T2"],res["T3"],res["T4"]])
        if best >= 2:
            wins += 1
    pct = wins/total*100 if total else 0
    return f'BACKTEST {jeu}: {pct:.1f}% 2/5 ({wins}/{total})'

@app.route('/historique', methods=['GET','POST'])
def hist():
    if request.method == 'POST':
        txt = request.form.get('pasted_text','')
        if txt:
            import re
            nums = [x.zfill(2) for x in re.findall(r"\d{1,2}", txt) if 1 <= int(x) <= 90][:5]
            if len(nums) >=5:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute('INSERT INTO tirages (jeu,haut,numero) VALUES (?,?,?)',('SUPER','-'.join(nums),'1'))
                conn.commit()
                conn.close()
    return '<form method="post"><textarea name="pasted_text"></textarea><button>IMPORTER</button></form>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
