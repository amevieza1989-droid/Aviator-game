from flask import Flask, request, render_template_string, redirect, send_file
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os, re, io, random

app = Flask(__name__)
DB = "/data/loto.db" if os.path.exists("/data") else "loto.db"
JEUX_LISTE = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]
JEUX_10_BOULES = ["MATINALE","DETENTE"]

def get_conn(): return sqlite3.connect(DB)
def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
    conn.commit();conn.close()
init_db()

def insert_tirage(jour,heure,jeu,haut,bas,date,numero):
    th=sum(int(x) for x in haut.split('-') if x.strip().isdigit()) if haut else 0
    tb=sum(int(x) for x in bas.split('-') if x.strip().isdigit()) if bas else 0
    conn=get_conn();c=conn.cursor()
    c.execute('DELETE FROM tirages WHERE numero=? AND jeu=?',(numero,jeu))
    c.execute('INSERT INTO tirages (jour,heure,jeu,haut,bas,date,numero,created,total_haut,total_bas) VALUES (?,?,?,?,?,?,?,?,?,?)',(jour,heure,jeu,haut,bas,date,numero,datetime.now().strftime('%d/%m/%Y %H:%M'),th,tb))
    conn.commit();conn.close()

def fetch_all(jeu=None):
    conn=get_conn();c=conn.cursor()
    if jeu and jeu!='TOUS':
        c.execute('SELECT * FROM tirages WHERE jeu=? ORDER BY CAST(numero AS INTEGER) DESC, id DESC',(jeu,))
    else:
        c.execute('SELECT * FROM tirages ORDER BY CAST(numero AS INTEGER) DESC, id DESC')
    r=c.fetchall();conn.close();return r

def parse_file_pro(content, jeu_force):
    res=[]; raw_lines=content.splitlines(); merged=[]; i=0
    while i < len(raw_lines):
        l=raw_lines[i].strip()
        if not l: i+=1; continue
        if l.endswith('/') and i+1 < len(raw_lines):
            merged.append(l+' '+raw_lines[i+1].strip()); i+=2
        else: merged.append(l); i+=1
    for line in merged:
        if 'WIN:' not in line: continue
        line=line.replace('\ufeff','').strip()
        numero=None; date_str=""; line_sans_date=line
        m = re.search(r'^(\d+)\s+(\d{2})/(\d{2})/(\d{4})', line)
        if m:
            numero=m.group(1); dd=m.group(2); mm=m.group(3); yyyy=m.group(4)
            date_str=f"{yyyy}-{mm}-{dd}"; line_sans_date=line.replace(m.group(0),' ')
        else:
            m2 = re.search(r'^(\d+)\s+(\d{1,2})/(\d{1,2})\b', line)
            if m2:
                numero=m2.group(1); dd=m2.group(2).zfill(2); mm=m2.group(3).zfill(2)
                date_str=f"2026-{mm}-{dd}"; line_sans_date=line.replace(m2.group(0),' ')
            else:
                m3=re.search(r'(\d{4}-\d{2}-\d{2})',line)
                if m3: date_str=m3.group(1); line_sans_date=line.replace(m3.group(1),' ')
                nums_tmp=re.findall(r'\b\d+\b',line)
                if nums_tmp: numero=nums_tmp[0]
        if not numero: continue
        try:
            after_win=line_sans_date.split('WIN:')[1]
            win_part,mach_part=(after_win.split('/',1) if '/' in after_win else (after_win,""))
            win_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', win_part) if x.isdigit() and 1<=int(x)<=90][:5]
            mach_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', mach_part) if x.isdigit() and 1<=int(x)<=90][:5]
            if len(win_nums)<5: continue
            haut='-'.join(win_nums)
            bas='-'.join(mach_nums) if (jeu_force in JEUX_10_BOULES and len(mach_nums)>=5) else ''
            res.append(('LUNDI',"09:00",jeu_force,haut,bas,date_str,numero))
        except: continue
    return res

def auto_seed():
    if len(fetch_all())>0: return
    for fname in ["MATINAL_CORI.txt","MATINALE_2026_ONLY.txt"]:
        if os.path.exists(fname):
            try:
                with open(fname,'r',encoding='utf-8',errors='ignore') as f: content=f.read()
                data=parse_file_pro(content,"MATINALE")
                for j,h,je,ht,bs,dt,num in data: insert_tirage(j,h,je,ht,bs,dt,num)
                break
            except: pass
auto_seed()

# === MOTEUR V19 INTELLIGENT 2/5 ===
def moteur_intelligent_v19(rows):
    if not rows: return {}
    chrono = list(reversed(rows))
    all_nums_recent_40 = []
    for r in chrono[-40:]: all_nums_recent_40.extend([x.zfill(2) for x in r[4].split('-')])
    cnt40 = Counter(all_nums_recent_40)
    cnt_total = Counter()
    for r in chrono: cnt_total.update([x.zfill(2) for x in r[4].split('-')])
    last_seen = {}
    for idx, r in enumerate(chrono):
        for n in r[4].split('-'): last_seen[n.zfill(2)] = idx
    paires = Counter()
    for r in chrono:
        nums = [x.zfill(2) for x in r[4].split('-')]
        for i in range(len(nums)):
            for j in range(i+1, len(nums)): paires[tuple(sorted([nums[i], nums[j]]))] += 1
    annonce = defaultdict(Counter)
    prev = []
    for r in chrono:
        cur = [x.zfill(2) for x in r[4].split('-')]
        if prev:
            for p in prev:
                for c in cur: annonce[p][c]+=1
        prev = cur
    scores = {}
    for i in range(1,91):
        n = str(i).zfill(2); s = 0
        s += cnt40.get(n,0) * 3
        s += cnt_total.get(n,0) * 0.5
        if n in last_seen:
            retard = len(chrono) - last_seen[n]
            if retard > 15: s += retard * 0.8
        pair_score = sum(c for (a,b),c in paires.items() if n in (a,b))
        s += pair_score * 0.1
        scores[n] = s
    pool_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    pool = [n for n,_ in pool_sorted[:14]]
    last_draw = [x.zfill(2) for x in rows[0][4].split('-')]
    annonce_pool = []
    for ln in last_draw:
        if ln in annonce: annonce_pool.extend([n for n,_ in annonce[ln].most_common(2)])
    annonce_pool = list(dict.fromkeys(annonce_pool))[:5]
    t1 = [n for n,_ in pool_sorted[:5]]
    t2 = (annonce_pool[:2] + [n for n in pool if n not in annonce_pool][:3])[:5]
    best_pairs = paires.most_common(3); t3_set = []
    for (a,b),_ in best_pairs:
        if a not in t3_set: t3_set.append(a)
        if b not in t3_set: t3_set.append(b)
    t3 = (t3_set + [n for n in pool if n not in t3_set])[:5]
    retard_sorted = sorted([str(i).zfill(2) for i in range(1,91)], key=lambda x: cnt_total.get(x,0))
    t4 = (retard_sorted[:2] + [n for n,_ in pool_sorted[:5] if n not in retard_sorted[:2]])[:5]
    def clean(t): return list(dict.fromkeys(t))[:5]
    return {
        "TICKET 1 - CHAUDS (40 derniers)": clean(t1),
        "TICKET 2 - ANNONCEUR (Markov)": clean(t2),
        "TICKET 3 - PAIRES FORTES": clean(t3),
        "TICKET 4 - RETARD + CHAUD": clean(t4),
        "POOL_12": pool[:12],
        "scores": scores,
        "paires": paires.most_common(10),
        "annonce": annonce,
        "cnt40": cnt40.most_common(12),
        "retard": retard_sorted[:10]
    }
    @app.route('/')
def home():
    total=len(fetch_all())
    return render_template_string(f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}}.btn{{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}}</style></head><body><div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">LOTO V19 INTELLIGENT - {total} tirages<br>2/5 GARANTI SYSTEM</div><a class="btn" href="/saisir">🎰 SAISIR</a><a class="btn" href="/historique">📜 HISTORIQUE</a><a class="btn" href="/analyse">🧠 ANALYSE IA V19</a><a class="btn" href="/backtest" style="border-color:#25D366;color:#25D366">📊 BACKTEST 2/5</a></body></html>')

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS'); msg=''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE'); content_to_parse=None
        pasted=request.form.get('pasted_text','').strip()
        if pasted: content_to_parse=pasted
        else:
            f=request.files.get('file') or request.files.get('fichier')
            if f and f.filename: content_to_parse=f.read().decode('utf-8', errors='ignore')
        if content_to_parse:
            novos=parse_file_pro(content_to_parse, jeu_import)
            if novos:
                conn=get_conn();c=conn.cursor();c.execute('DELETE FROM tirages WHERE jeu=?',(jeu_import,));conn.commit();conn.close()
                for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
                msg=f'<div style="background:#25D366;color:#fff;padding:12px;border-radius:10px;font-weight:bold;margin-bottom:10px">✅ {len(novos)} importés! {jeu_import}</div>'
    rows=fetch_all(jeu_filtre); total_rows=len(rows)
    def format_date(d):
        if not d or d.strip()=="": return "ANCIEN"
        try: y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
        except: return d
    filtres='<div style="display:flex;flex-wrap:wrap;gap:5px;margin:10px 0">'
    for j in ["TOUS"]+JEUX_LISTE:
        cnt=len(fetch_all() if j=="TOUS" else fetch_all(j))
        active=jeu_filtre==j
        filtres+=f'<a href="/historique?jeu={j}" style="background:{"gold" if active else "#222"};color:{"#111" if active else "#fff"};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;font-weight:bold;border:1px solid gold">{j} ({cnt})</a>'
    filtres+='</div>'
    cards=''.join([f'<div style="background:#151515;padding:8px;margin:4px 0;border-radius:8px;border-left:4px solid gold"><b>{format_date(r[6])} {r[3]} #{r[7]}</b> {r[4]}<br><small>{"10b" if r[5] else "5b"}</small></div>' for r in rows[:500]]) or '<div style="color:#888;text-align:center;padding:20px">Base vide</div>'
    return f'''<html><body style="background:#000;color:#fff;font-family:Arial;padding:8px"><a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({total_rows})</h3><div style="background:#111;border:2px solid gold;padding:12px;border-radius:12px">{msg}<form method="post" enctype="multipart/form-data"><select name="jeu_import" style="width:100%;padding:12px;border-radius:8px;margin-bottom:10px;background:#222;color:#fff;border:1px solid gold">{"".join([f"<option value='{j}'>{j}</option>" for j in JEUX_LISTE])}</select><input type="file" name="file" style="width:100%;background:#222;color:#fff;padding:10px;border-radius:6px"><textarea name="pasted_text" style="width:100%;height:80px;background:#222;color:#fff;border:1px solid #444;border-radius:8px;padding:8px;margin-top:8px"></textarea><button type="submit" style="width:100%;background:#25D366;color:#fff;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:10px">📥 IMPORTER</button></form></div>{filtres}{cards}</body></html>'''

@app.route('/analyse')
def analyse():
    jeu_filtre=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu_filtre)
    if not rows: return '<html><body style="background:#000;color:#fff;padding:12px"><a href="/" style="color:gold">⬅</a><br>Base vide</body></html>'
    res = moteur_intelligent_v19(rows)
    chaud_html=''.join([f'<span style="display:inline-block;background:gold;color:#111;padding:5px 10px;border-radius:15px;margin:2px;font-weight:bold">{n}({c})</span>' for n,c in res["cnt40"][:10]])
    retard_html=''.join([f'<span style="display:inline-block;background:#300;color:#ff6b6b;padding:5px 10px;border-radius:15px;margin:2px;border:1px solid #ff6b6b">{n}</span>' for n in res["retard"][:10]])
    paires_html=''.join([f'<span style="display:inline-block;background:#222;border:1px solid gold;color:gold;padding:5px 8px;border-radius:12px;margin:3px">{a}-{b}({c}x)</span>' for (a,b),c in res["paires"][:8]])
    last_nums=[x.zfill(2) for x in rows[0][4].split('-')]
    t1=" - ".join(res["TICKET 1 - CHAUDS (40 derniers)"]); t2=" - ".join(res["TICKET 2 - ANNONCEUR (Markov)"]); t3=" - ".join(res["TICKET 3 - PAIRES FORTES"]); t4=" - ".join(res["TICKET 4 - RETARD + CHAUD"])
    filtres='<div style="display:flex;flex-wrap:wrap;gap:4px;margin:8px 0">'
    for j in JEUX_LISTE:
        active=jeu_filtre==j
        filtres+=f'<a href="/analyse?jeu={j}" style="background:{"gold" if active else "#222"};color:{"#111" if active else "#fff"};padding:5px 8px;border-radius:15px;text-decoration:none;font-size:10px;font-weight:bold;border:1px solid gold">{j}({len(fetch_all(j))})</a>'
    filtres+='</div>'
    return f'''<html><body style="background:#000;color:#fff;font-family:Arial;padding:6px"><a href="/" style="color:gold">⬅ ACCUEIL</a> | <a href="/backtest?jeu={jeu_filtre}" style="color:#25D366">📊 BACKTEST</a><h3 style="color:gold;text-align:center;border:1px solid gold;padding:6px;border-radius:8px">🧠 V19 - {jeu_filtre} - {len(rows)} tirages</h3>{filtres}<div style="background:#141414;padding:10px;border-radius:10px"><div><b>🔥 Chauds 40:</b><br>{chaud_html}</div><div style="margin-top:8px"><b>❄️ Retard:</b><br>{retard_html}</div><div style="margin-top:8px"><b>🔗 Paires:</b><br>{paires_html}</div><div style="margin-top:8px"><b>🎯 POOL 12:</b><br><span style="color:gold;font-weight:bold">{" - ".join(res["POOL_12"])}</span></div><div style="margin-top:12px"><div style="background:gold;color:#111;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold">🎯 TICKET 1 - CHAUDS<br><span style="font-size:20px">{t1}</span></div><div style="background:#111;border:2px solid #25D366;color:#25D366;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold">🧠 TICKET 2 - ANNONCEUR<br><span style="font-size:20px;color:#fff">{t2}</span><br><small>{"-".join(last_nums)}</small></div><div style="background:#111;border:2px solid gold;color:gold;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold">🔗 TICKET 3 - PAIRES<br><span style="font-size:20px;color:#fff">{t3}</span></div><div style="background:#222;border:2px solid #ff6b6b;color:#ff6b6b;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold">⏰ TICKET 4 - RETARD<br><span style="font-size:20px;color:#fff">{t4}</span></div></div></div></body></html>'''

@app.route('/predict/<jeu>')
def predict_route(jeu):
    jeu=jeu.upper(); rows=fetch_all(jeu)
    if not rows: return {"error":"pas de données pour "+jeu}
    res=moteur_intelligent_v19(rows)
    return {"jeu": jeu, "tickets": {"t1": res["TICKET 1 - CHAUDS (40 derniers)"], "t2": res["TICKET 2 - ANNONCEUR (Markov)"], "t3": res["TICKET 3 - PAIRES FORTES"], "t4": res["TICKET 4 - RETARD + CHAUD"]}, "pool_12": res["POOL_12"]}

@app.route('/backtest')
def backtest():
    jeu=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu)
    if len(rows)<50: return f"Pas assez de données {len(rows)}"
    chrono=list(reversed(rows)); wins2=0; wins3=0; total=len(chrono)-40
    for i in range(40, len(chrono)):
        past=chrono[:i]; futur=set([x.zfill(2) for x in chrono[i][4].split('-')])
        res=moteur_intelligent_v19(past)
        tickets=[res["TICKET 1 - CHAUDS (40 derniers)"], res["TICKET 2 - ANNONCEUR (Markov)"], res["TICKET 3 - PAIRES FORTES"], res["TICKET 4 - RETARD + CHAUD"]]
        best=max(len(futur.intersection(set(t))) for t in tickets)
        if best>=2: wins2+=1
        if best>=3: wins3+=1
    pct2 = wins2/total*100 if total else 0; pct3 = wins3/total*100 if total else 0
    return f'''<html><body style="background:#000;color:#fff;font-family:Arial;padding:12px"><a href="/" style="color:gold">⬅ ACCUEIL</a><h2 style="color:gold">📊 BACKTEST {jeu} - {total} tirages</h2><div style="background:#111;border:2px solid #25D366;padding:16px;border-radius:12px;text-align:center"><div style="font-size:28px;color:#25D366;font-weight:bold">{pct2:.1f}%</div><div>2/5 parmi 4 tickets</div><div style="font-size:22px;color:gold;margin-top:12px">{pct3:.1f}%</div><div>3/5</div><div style="margin-top:12px;color:#888">{wins2}/{total}</div></div></body></html>'''

@app.route('/reset')
def reset():
    conn=get_conn();c=conn.cursor(); c.execute('DELETE FROM tirages'); conn.commit(); conn.close()
    return redirect('/historique?jeu=TOUS')

@app.route('/export/<fmt>')
def export_file(fmt):
    jeu=request.args.get('jeu','TOUS'); rows=fetch_all(jeu); out=io.StringIO()
    for r in rows:
        ds=r[6] if r[6] else "2026-01-01"
        if r[5]: out.write(f'{r[7]} {ds} WIN: {r[4]} / {r[5]}\n')
        else: out.write(f'{r[7]} {ds} WIN: {r[4]}\n')
    mem=io.BytesIO(out.getvalue().encode('utf-8'))
    return send_file(mem, as_attachment=True, download_name=f'BACKUP_{jeu}_{len(rows)}.txt', mimetype='text/plain')

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    today=datetime.now().strftime('%Y-%m-%d')
    if request.method=='POST':
        h='-'.join([request.form.get(f'h{i}','').zfill(2) for i in range(1,6) if request.form.get(f'h{i}','')])
        b='-'.join([request.form.get(f'b{i}','').zfill(2) for i in range(1,6) if request.form.get(f'b{i}','')])
        insert_tirage(request.form.get('jour'),request.form.get('heure'),request.form.get('jeu'),h,b,request.form.get('date'),request.form.get('numero'))
        return redirect(f'/analyse?jeu={request.form.get("jeu")}')
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}select,input{{width:100%;padding:12px;margin:4px 0;border-radius:6px;border:1px solid #333}}label{{color:gold;font-weight:bold;font-size:12px}}.cage{{display:flex;gap:3px}}.cage input{{width:18%;text-align:center;font-weight:bold}}.hidden{{display:none}}</style>
<script>const JEUX_10=["MATINALE","DETENTE"];function updateForm(){{let jeu=document.getElementById('jeu').value;let md=document.getElementById('machineDiv');let lw=document.getElementById('labelWin');if(JEUX_10.includes(jeu)){{md.classList.remove('hidden');lw.innerText="WIN (5) - 10b";}}else{{md.classList.add('hidden');lw.innerText="NUMEROS (5) - "+jeu;}}document.getElementById('jeu_input').value=jeu;}}</script></head><body><h3 style="color:gold;text-align:center">V19 SAISIR</h3><label>N° TIRAGE</label><input id="numero_out" type="number" value="717"><label>DATE</label><input type="date" id="date_out" value="{today}"><label>JEU</label><select id="jeu" onchange="updateForm()" style="background:#111;border:2px solid gold;color:gold;font-weight:bold"><option>MATINALE</option><option>DETENTE</option><option>DIAMANT</option><option>GOLD</option><option>CASH</option><option>BOOM</option><option selected>BENZ</option><option>PRESTIGE</option><option>MILLION</option><option>SUPER</option><option>KADOO</option><option>KING</option><option>SAM</option><option>BINGO</option></select><form id="mainForm" method="POST"><input type="hidden" name="jour" value="LUNDI"><input type="hidden" name="heure" value="09:00"><input type="hidden" name="jeu" id="jeu_input" value="BENZ"><input type="hidden" name="numero" id="numero_input"><input type="hidden" name="date" id="date_input"><div style="margin:10px 0"><label id="labelWin">NUMEROS (5)</label><div class="cage"><input name="h1" required><input name="h2" required><input name="h3" required><input name="h4" required><input name="h5" required></div></div><div id="machineDiv" class="hidden"><label style="color:#25D366">MACHINE (5)</label><div class="cage"><input name="b1"><input name="b2"><input name="b3"><input name="b4"><input name="b5"></div></div><button style="width:100%;background:gold;color:#111;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:12px">ENREGISTRER</button></form><script>document.getElementById('mainForm').addEventListener('submit', function(){{document.getElementById('numero_input').value=document.getElementById('numero_out').value;document.getElementById('date_input').value=document.getElementById('date_out').value;}}); updateForm();</script><a href="/" style="color:gold;display:block;text-align:center;margin-top:12px">⬅ Retour</a></body></html>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
