from flask import Flask, request, render_template_string
import sqlite3, os, re
from collections import Counter
from datetime import datetime

app = Flask(__name__)
DB = "loto.db"
JEUX = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]

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
        cur.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY id DESC', (jeu,))
    else:
        cur.execute('SELECT * FROM tirages ORDER BY id DESC')
    r = cur.fetchall()
    conn.close()
    return r

def moteur_v19(rows):
    chrono = list(reversed(rows))
    cnt = Counter()
    for r in chrono[-50:]:
        parts = re.findall(r'\d{1,2}', r[2])
        clean = [p.zfill(2) for p in parts if 1 <= int(p) <= 90]
        cnt.update(clean)
    scores = cnt.most_common(20)
    pool = [n for n,_ in scores]
    if len(pool) < 12:
        pool = ["01","05","12","25","33","47","52","69","70","81","85","90"]
    return {
        "T1": pool[:5],
        "T2": pool[2:7],
        "T3": pool[4:9],
        "T4": pool[1:6],
        "POOL": pool[:12],
        "CNT": scores
    }

BASE = """
<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{background:#000;color:#fff;font-family:sans-serif;padding:10px;margin:0}
a{color:gold;text-decoration:none}
.card{padding:14px;margin:10px 0;border-radius:12px;font-weight:bold;font-size:16px}
.btn{padding:15px;display:block;margin:10px 0;border-radius:10px;text-align:center;font-weight:bold}
</style></head><body>
<a href='/'>⬅ ACCUEIL</a>
%s
</body></html>
"""

@app.route('/')
def home():
    total = len(fetch_all())
    body = f"""
    <h1 style='color:gold;text-align:center;margin-top:20px'>LOTO V19 INTELLIGENT</h1>
    <p style='text-align:center;color:#888'>{total} tirages en base</p>
    <a href='/analyse?jeu=SUPER' class='btn' style='background:gold;color:#000'>ANALYSE SUPER</a>
    <a href='/analyse?jeu=MATINALE' class='btn' style='background:#222;color:#fff;border:1px solid #444'>ANALYSE MATINALE</a>
    <a href='/analyse?jeu=DIAMANT' class='btn' style='background:#222;color:#fff;border:1px solid #444'>ANALYSE DIAMANT</a>
    <a href='/backtest?jeu=SUPER' class='btn' style='background:#25D366;color:#fff'>BACKTEST 2/5</a>
    <a href='/historique' class='btn' style='background:#111;color:gold;border:1px solid gold'>HISTORIQUE + IMPORT</a>
    <div style='text-align:center;margin-top:25px;font-size:12px;color:#555'>https://aviator-game-5iu6.onrender.com</div>
    """
    return render_template_string(BASE % body)

@app.route('/analyse')
def analyse():
    jeu = request.args.get('jeu','SUPER')
    rows = fetch_all(jeu)
    if not rows:
        return render_template_string(BASE % f"<h2 style='color:gold'>Base vide pour {jeu}</h2><p>Va dans HISTORIQUE pour importer des tirages</p>")
    res = moteur_v19(rows)
    body = f"""
    <h2 style='color:gold'>V19 {jeu} - {len(rows)} tirages</h2>
    <div class='card' style='background:gold;color:#000'>T1 CHAUDS (Top Freq): {' - '.join(res['T1'])}</div>
    <div class='card' style='background:#111;border:2px solid #25D366'>T2 EQUILIBRE: {' - '.join(res['T2'])}</div>
    <div class='card' style='background:#111;border:2px solid gold;color:gold'>T3 RETARD: {' - '.join(res['T3'])}</div>
    <div class='card' style='background:#222;border:2px solid #ff6b6b;color:#ff6b6b'>T4 SECURITE: {' - '.join(res['T4'])}</div>
    <div style='margin-top:20px;color:gold'>POOL 12 NUMEROS: {' - '.join(res['POOL'])}</div>
    <div style='margin-top:12px;font-size:12px;color:#888'>Frequences: {res['CNT'][:12]}</div>
    <div style='margin-top:20px'><a href='/backtest?jeu={jeu}' class='btn' style='background:#25D366;color:#fff'>VOIR BACKTEST 2/5</a></div>
    """
    return render_template_string(BASE % body)

@app.route('/backtest')
def backtest():
    jeu = request.args.get('jeu','SUPER')
    rows = fetch_all(jeu)
    if len(rows) < 50:
        return render_template_string(BASE % f"<h3>Pas assez de donnees: {len(rows)}/50 pour backtest</h3>")
    chrono = list(reversed(rows))
    wins = 0
    total = len(chrono) - 40
    for i in range(40, len(chrono)):
        past = chrono[:i]
        futur_nums = [x.zfill(2) for x in re.findall(r'\d{{1,2}}', chrono[i][2]) if 1 <= int(x) <= 90]
        futur = set(futur_nums)
        res = moteur_v19(past)
        best = max(len(futur.intersection(set(t))) for t in [res['T1'],res['T2'],res['T3'],res['T4']])
        if best >= 2:
            wins += 1
    pct = wins/total*100 if total else 0
    body = f"""
    <h2 style='color:gold;text-align:center'>BACKTEST {jeu}</h2>
    <div style='font-size:52px;color:#25D366;font-weight:bold;text-align:center'>{pct:.1f}%</div>
    <div style='text-align:center'>Reussite 2/5 avec 4 tickets</div>
    <div style='text-align:center;margin-top:10px;color:#888'>{wins} / {total} tirages testes</div>
    <div style='margin-top:20px'><a href='/analyse?jeu={jeu}' class='btn' style='background:gold;color:#000'>RETOUR ANALYSE</a></div>
    """
    return render_template_string(BASE % body)

@app.route('/historique', methods=['GET','POST'])
def hist():
    msg = ""
    if request.method == 'POST':
        jeu = request.form.get('jeu_import','SUPER')
        txt = request.form.get('pasted_text','')
        if txt:
            nums = [x.zfill(2) for x in re.findall(r'\d{1,2}', txt) if 1 <= int(x) <= 90][:5]
            if len(nums) >= 5:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute('INSERT INTO tirages (jeu,haut,numero) VALUES (?,?,?)', (jeu, '-'.join(nums), '-'.join(nums)))
                conn.commit()
                conn.close()
                msg = f"<div style='background:#25D366;color:#fff;padding:10px;border-radius:8px'>Ajoute: {'-'.join(nums)}</div>"
            else:
                msg = "<div style='background:#ff6b6b;color:#fff;padding:10px;border-radius:8px'>5 numeros requis (1-90)</div>"
    rows = fetch_all()
    rows_html = "".join([f"<div style='border-bottom:1px solid #222;padding:6px;font-size:13px'>{r[0]} | {r[1]} | {r[2]}</div>" for r in rows[:200]])
    body = f"""
    <h3 style='color:gold'>HISTORIQUE ({len(rows)} tirages)</h3>
    {msg}
    <form method='post' style='margin-top:10px'>
    <select name='jeu_import' style='width:100%;padding:12px;background:#222;color:#fff;border-radius:8px'>
    <option>SUPER</option><option>MATINALE</option><option>DIAMANT</option><option>GOLD</option>
    </select>
    <textarea name='pasted_text' placeholder='Ex: 69-32-52-12-63 ou 69 32 52 12 63' style='width:100%;height:90px;background:#222;color:#fff;margin-top:8px;border-radius:8px;padding:10px'></textarea>
    <button style='width:100%;background:#25D366;color:#fff;padding:14px;margin-top:8px;border:none;border-radius:10px;font-weight:bold'>IMPORTER</button>
    </form>
    <div style='margin-top:15px;max-height:400px;overflow:auto;background:#111;border-radius:8px;padding:5px'>{rows_html}</div>
    """
    return render_template_string(BASE % body)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
