from flask import Flask, request, render_template_string, redirect
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os

app = Flask(__name__)
DB = "loto.db"

def get_conn():
    conn = sqlite3.connect(DB)
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tirages
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT,
    total_haut INTEGER, total_bas INTEGER)''')
    conn.commit()
    conn.close()
init_db()

def insert_tirage(jour, heure, jeu, haut, bas, date, numero, created):
    try:
        # calcul totaux
        th = sum([int(x) for x in haut.split('-') if x.strip().isdigit()])
        tb = sum([int(x) for x in bas.split('-') if x.strip().isdigit()])
        conn = get_conn()
        c = conn.cursor()
        # anti-doublon
        c.execute("SELECT id FROM tirages WHERE jeu=? AND numero=?", (jeu, numero))
        if c.fetchone():
            conn.close()
            return False
        c.execute("INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (jour,heure,jeu,haut,bas,date,numero,created,th,tb))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Erreur insert", e)
        return False

def fetch_all():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM tirages ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

HOME_HTML = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}
.btn{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:15px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold;font-size:17px}
.top{background:gold;color:#111;padding:15px;border-radius:15px;text-align:center}
.box{background:#151515;padding:12px;margin:10px 0;border-radius:12px;border:1px solid #333}
</style></head><body>
<div class="top"><h2>🔥 LOTO TOGO V10.8</h2><p>{{nb}} tirages en base</p></div>
<a class="btn" href="/saisir">➕ SAISIR 1 TIRAGE</a>
<a class="btn" href="/import" style="background:#00ff88;color:#111;border-color:#00ff88">📥 IMPORT RAPIDE 50 D'UN COUP</a>
<a class="btn" href="/analyse">📊 ANALYSE + TOTAUX + WHATSAPP</a>
<div class="box"><h3>Derniers tirages</h3>
{% for r in rows[:10] %}
<p><b>{{r[3]}} #{{r[7]}}</b> {{r[6]}} - H:{{r[4]}} ({{r[9]}}) / B:{{r[5]}} ({{r[10]}})</p>
{% endfor %}
</div>
</body></html>
"""

@app.route('/')
def home():
    rows = fetch_all()
    return render_template_string(HOME_HTML, nb=len(rows), rows=rows)

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    if request.method == 'POST':
        jour = request.form.get('jour','LUNDI')
        heure = request.form.get('heure','09:00')
        jeu = request.form.get('jeu','MATINALE')
        haut = request.form.get('haut','')
        bas = request.form.get('bas','')
        date = request.form.get('date', datetime.now().strftime("%Y-%m-%d"))
        numero = request.form.get('numero', '1')
        ok = insert_tirage(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime("%d/%m %H:%M"))
        if not ok:
            return "<h2 style='color:red'>DOUBLON ou ERREUR! Ce tirage existe déjà.</h2><a href='/'>Retour</a>"
        return redirect('/')
    return """
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}input,select{width:100%;padding:12px;margin:6px 0;background:#111;color:#fff;border:1px solid gold;border-radius:10px}button{background:gold;color:#111;padding:15px;width:100%;border:none;border-radius:12px;font-weight:bold}</style></head><body>
    <h2 style="color:gold">➕ Saisir 1 tirage</h2>
    <form method="POST">
    Jour: <select name="jour"><option>LUNDI</option><option>MARDI</option><option>MERCREDI</option><option>JEUDI</option><option>VENDREDI</option><option>SAMEDI</option><option>DIMANCHE</option></select>
    Heure: <input name="heure" value="09:00">
    Jeu: <select name="jeu"><option>MATINALE</option><option>DETENTE</option><option>DIAMANT</option><option>GOLD</option><option>CASH</option><option>BOOM</option></select>
    Numero: <input name="numero" placeholder="ex: 1">
    Date: <input name="date" type="date" value="2026-08-02">
    Haut (ex: 84-29-45-23-89): <input name="haut" required>
    Bas (ex: 14-13-74-17-90): <input name="bas" required>
    <br><br><button type="submit">✅ ENREGISTRER</button>
    </form><p><a href="/" style="color:gold">← Accueil</a></p></body></html>
    """

@app.route('/import', methods=['GET','POST'])
def import_rapide():
    if request.method=='POST':
        texte=request.form['data']
        count=0
        for ligne in texte.splitlines():
            ligne=ligne.strip()
            if not ligne or ';' not in ligne: continue
            try:
                parts=[p.strip() for p in ligne.split(';')]
                if len(parts)!=5: continue
                d,num,jeu,haut,bas=parts
                j='LUNDI'; h='09:00'
                if 'DETENTE' in jeu.upper(): h='10:00'
                if 'DIAMANT' in jeu.upper(): h='11:00'
                ok=insert_tirage(j,h,jeu.strip().upper(),haut.strip(),bas.strip(),d.strip(),num.strip(),datetime.now().strftime("%d/%m %H:%M"))
                if ok: count+=1
            except Exception as e:
                print(e)
                continue
        return f"<h2 style='color:gold'>{count} tirages importés!</h2><a href='/analyse'>Voir analyse →</a><br><br><a href='/import'>Importer encore</a> | <a href='/'>Accueil</a>"
    return """
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:15px}textarea{width:100%;height:350px;background:#111;color:#0f0;padding:10px;border:1px solid gold;border-radius:10px}button{background:#00ff88;color:#111;padding:15px;width:100%;border:none;border-radius:12px;font-weight:bold;font-size:18px}</style></head><body>
    <h2 style="color:gold">📥 IMPORT RAPIDE 200+ TIRAGES</h2>
    <p>Format: <b>DATE;NUMERO;JEU;HAUT;BAS</b><br>Ex: 2026-08-02;1;DETENTE;84-29-45-23-89;14-13-74-17-90</p>
    <form method="POST"><textarea name="data" placeholder="2026-08-02;1;DETENTE;84-29-45-23-89;14-13-74-17-90
2026-08-09;2;DETENTE;32-01-19-03-79;33-30-85-80-71"></textarea><br><br><button type="submit">✅ IMPORTER</button></form>
    <p><a href="/" style="color:gold">← Accueil</a></p>
    <p style="color:#aaa;margin-top:20px">Colle les 9 lignes de Détente que je t'ai données, tu auras 9 tirages d'un coup.</p>
    </body></html>
    """

@app.route('/analyse')
def analyse():
    rows=fetch_all()
    if not rows: return "Pas de tirage <a href='/'>Retour</a>"
    all_nums=[]
    th_list=[]; tb_list=[]
    for r in rows:
        for x in (r[4]+"-"+(r[5] or "")).split("-"):
            if x.strip().isdigit(): all_nums.append(x.strip().zfill(2))
        if r[9]: th_list.append(r[9])
        if r[10]: tb_list.append(r[10])

    cnt=Counter(all_nums)
    total=len(all_nums)
    top=sorted(cnt.items(), key=lambda x:x[1], reverse=True)[:15]
    top_data=[(n,c,round(c/total*100,1)) for n,c in top]
    bottom=sorted(cnt.items(), key=lambda x:x[1])[:5]

    avg_h = int(sum(th_list)/len(th_list)) if th_list else 0
    avg_b = int(sum(tb_list)/len(tb_list)) if tb_list else 0
    min_h = min(th_list) if th_list else 0
    max_h = max(th_list) if th_list else 0
    min_b = min(tb_list) if tb_list else 0
    max_b = max(tb_list) if tb_list else 0

    jeux=defaultdict(list)
    for r in rows: jeux[r[3]].append(r)

    pred_html=""
    for jeu_name, lst in jeux.items():
        nums=[]
        th=[]; tb=[]
        for r in lst:
            for x in (r[4]+"-"+(r[5] or "")).split("-"):
                if x.strip().isdigit(): nums.append(x.strip().zfill(2))
            if r[9]: th.append(r[9])
            if r[10]: tb.append(r[10])
        c=Counter(nums)
        chauds=c.most_common(3)
        retards=sorted(c.items(), key=lambda x:x[1])[:3]
        avg_th = int(sum(th)/len(th)) if th else 0
        avg_tb = int(sum(tb)/len(tb)) if tb else 0
        pred_html+=f"<div class='box'><h3 style='color:gold'>{jeu_name} - {len(lst)} tirages | TOTAL MOY: H:{avg_th} B:{avg_tb}</h3>"
        pred_html+=f"<p><span style='color:#00ff88'>Chauds:</span> "
        for n,cc in chauds:
            p=round(cc/len(nums)*100,1) if nums else 0
            pred_html+=f"<span class='badge hot'>{n} {p}%</span> "
        pred_html+=f"</p><p><span style='color:#ff4444'>Retard:</span> "
        for n,cc in retards:
            pred_html+=f"<span class='badge cold'>{n}</span> "
        pred_html+="</p></div>"

    chauds_msg=" ".join([n for n,c,p in top_data[:5]])
    retards_msg=" ".join([n for n,c in bottom])

    whatsapp_text=f"""🎯 LOTO TOGO V10.8 - PRONO DU JOUR

📊 TOTAL ANALYSIS:
WIN MOY: {avg_h} (Min:{min_h} Max:{max_h})
MACHINE MOY: {avg_b} (Min:{min_b} Max:{max_b})
➡️ Prochain TOTAL estimé: {avg_h}-{avg_h+15}

🔥 A TENTER (retard): {retards_msg}
⚠️ Chauds du moment: {chauds_msg}

💡 Prono 2 Sûr: {top_data[0][0] if top_data else ''} - {bottom[0][0] if bottom else ''}

👉 VIP 500F/jour - 2000F/semaine
📲 Inbox pour le 2 sûr

#LONATO #LotoTogo"""

    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
    body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}
   .top{{background:gold;color:#111;padding:15px;border-radius:15px;text-align:center}}
   .box{{background:#151515;padding:14px;margin:12px 0;border-radius:15px;border:1px solid #333}}
   .badge{{display:inline-block;background:#222;border:1px solid gold;color:gold;padding:7px 12px;border-radius:20px;margin:4px;font-weight:bold}}
   .hot{{background:gold;color:#111}}.cold{{background:#331111;color:#ff8888;border-color:red}}
   .total-box{{background:#1a2a1a;border:2px solid #00ff88}}
   .what{{background:#0a1a0a;border:2px solid gold;border-radius:15px;padding:15px}}
    pre{{background:#111;color:#0f0;padding:12px;border-radius:10px;white-space:pre-wrap;font-size:13px}}
    a{{color:gold}} button{{background:gold;color:#111;padding:14px;width:100%;border:none;border-radius:12px;font-weight:bold}}
    </style></head><body>
    <div class="top"><h2>📊 V10.8 ANALYSE + 2 TOTAUX</h2><p>{len(rows)} tirages | {total} numéros analysés</p></div>
    <p><a href="/">← Accueil</a></p>
    <div class="box total-box"><h3>💰 TOTAL WIN / MACHINE - STATS PRO</h3>
    <p>🔝 <b>WIN (Haut):</b> Moy={avg_h} | Min={min_h} | Max={max_h}</p>
    <p>🔽 <b>MACHINE (Bas):</b> Moy={avg_b} | Min={min_b} | Max={max_b}</p>
    </div>
    <div class="box"><h3>🔥 TOP 15 GLOBAL</h3>
    """ + "".join([f"<span class='badge hot'>{n} {p}% ({c}x)</span>" for n,c,p in top_data]) + f"""
    </div>
    {pred_html}
    <div class="what"><h3>💰 MESSAGE WHATSAPP VIP AVEC TOTAUX</h3>
    <pre id="msg">{whatsapp_text}</pre>
    <button onclick="navigator.clipboard.writeText(document.getElementById('msg').innerText);alert('Copié!')">📋 COPIER LE MESSAGE</button>
    </div>
    </body></html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
