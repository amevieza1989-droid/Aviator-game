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
        else:
            merged.append(l); i+=1
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
            win_part,mach_part=after_win.split('/',1) if '/' in after_win else (after_win,"")
            # V19.2 FIX: extrait uniquement la partie WIN, pas la date
            win_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', win_part) if x.isdigit() and 1<=int(x)<=90][:5]
            mach_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', mach_part) if x.isdigit() and 1<=int(x)<=90][:5]
            if len(win_nums)<5: continue
            haut='-'.join(win_nums)
            bas='-'.join(mach_nums) if jeu_force in JEUX_10_BOULES and len(mach_nums)>=5 else ''
            res.append(('LUNDI',"09:00",jeu_force,haut,bas,date_str,numero))
        except: continue
    return res

def moteur_v19_2(rows, jeu):
    # V19.2: ANALYSE SUR 10 BOULES SI DISPO
    chrono=list(reversed(rows))
    all_nums=[]; paires=Counter(); annonce=defaultdict(Counter); prev=[]
    for r in chrono:
        win=[x.zfill(2) for x in r[4].split('-') if x.strip().isdigit()]
        # V19.2: Si MATINALE/DETENTE, ajoute aussi bas (10 boules)
        if r[3] in JEUX_10_BOULES and r[5]:
            bas=[x.zfill(2) for x in r[5].split('-') if x.strip().isdigit()]
            win_full = win + bas
        else:
            win_full = win
        
        all_nums.extend(win_full)
        for i in range(len(win_full)):
            for j in range(i+1,len(win_full)):
                paires[tuple(sorted([win_full[i],win_full[j]]))]+=1
        if prev:
            for p in prev:
                for cur in win_full: annonce[p][cur]+=1
        prev=win_full

    cnt=Counter(all_nums)
    chauds=[n for n,c in cnt.most_common(20)]
    if len(chauds)<12: chauds=["01","05","12","25","33","47","52","69","70","81","85","90"]
    top_paires=paires.most_common(6)
    
    # Dernier tirage complet
    if rows:
        last_haut=[x.zfill(2) for x in rows[0][4].split('-') if x.strip().isdigit()]
        last_bas=[x.zfill(2) for x in rows[0][5].split('-') if x.strip().isdigit()] if rows[0][3] in JEUX_10_BOULES and rows[0][5] else []
        last = last_haut + last_bas
        last_5 = last_haut  # pour affichage
    else:
        last=[]; last_5=[]

    t_ann=[]
    for ln in last_5:  # on cherche annonceurs après les 5 premiers, mais dans 10B
        if ln in annonce: t_ann.extend([n for n,_ in annonce[ln].most_common(3)])
    t_ann=list(dict.fromkeys(t_ann))[:5]
    if len(t_ann)<5: t_ann+= [n for n in chauds if n not in t_ann][:5-len(t_ann)]
    
    t_pair=[]
    for (a,b),_ in top_paires[:3]: t_pair.extend([a,b])
    t_pair=list(dict.fromkeys(t_pair))
    if len(t_pair)<5: t_pair+= [n for n in chauds if n not in t_pair]
    
    retard=sorted([str(i).zfill(2) for i in range(1,91)], key=lambda n: cnt.get(n,0))[:5]
    
    # V19.2: T3 MIX CHAUDS+ANNONCEURS (plus puissant)
    t_mix=[]
    for a,b in zip(chauds, t_ann):
        if a not in t_mix: t_mix.append(a)
        if b not in t_mix: t_mix.append(b)
        if len(t_mix)>=5: break

    return {"T1":chauds[:5],"T2":t_ann[:5],"T3":t_mix[:5],"T4":retard[:5],"POOL":chauds[:12],"CNT":cnt.most_common(15),"PAIRES":top_paires,"ANN":annonce,"LAST":last_5, "LAST_FULL": last}

@app.route('/')
def home():
    total=len(fetch_all())
    btns=""
    for j in JEUX_LISTE:
        c=len(fetch_all(j))
        bg="#1a1a1a"
        border="gold" if j=="SUPER" else "#333"
        color="gold" if j=="SUPER" else "#fff"
        if c>0: bg="#222"
        btns+=f"<a class='btn' style='background:{bg};color:{color};border:1px solid {border}' href='/analyse?jeu={j}'>ANALYSE {j} ({c})</a>"
    html=f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>body{{background:#000;color:#fff;font-family:Arial;padding:12px;margin:0}}.btn{{display:block;padding:14px;margin:8px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold;font-size:13px}}</style>
    </head><body>
    <h1 style='color:gold;text-align:center;margin-top:10px'>LOTO V19.2 - 10B ANALYSE / 5B JEU</h1>
    <p style='text-align:center;color:#888'>{total} tirages - V19.2 Intelligent</p>
    {btns}
    <a class='btn' style='background:#25D366;color:#fff;margin-top:12px' href='/backtest?jeu=MATINALE'>BACKTEST 2/5 - MATINALE</a>
    <a class='btn' style='background:#111;color:gold;border:1px solid gold' href='/historique'>📜 HISTORIQUE + IMPORT</a>
    <div style='text-align:center;margin-top:15px;font-size:10px;color:#444'>V19.2 - 10B Analyse - https://aviator-game-5iu6.onrender.com</div>
    </body></html>
    """
    return html

@app.route('/analyse')
def analyse():
    jeu=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu)
    if not rows: return f"<html><body style='background:#000;color:#fff;padding:12px'><a href='/' style='color:gold'>⬅ ACCUEIL</a><h3>Base vide {jeu} - Importe d'abord</h3></body></html>"
    res=moteur_v19_2(rows, jeu)
    chaud_html=''.join([f"<span style='display:inline-block;background:gold;color:#111;padding:5px 10px;border-radius:15px;margin:2px;font-weight:bold'>{n}({c})</span>" for n,c in res['CNT'][:10]])
    paires_html=''.join([f"<span style='display:inline-block;background:#222;border:1px solid gold;color:gold;padding:5px 8px;border-radius:12px;margin:3px;font-size:12px'>{a}-{b} ({cc}x)</span>" for (a,b),cc in res['PAIRES'][:6]])
    ann_html=""
    for ln in res['LAST'][:3]:
        if ln in res['ANN']:
            top=res['ANN'][ln].most_common(3)
            ann_html+=f"<div style='background:#111;border:1px solid #555;padding:6px;margin:3px;border-radius:6px'><b>Apres {ln}:</b> {' '.join([f'{n}({c}x)' for n,c in top])}</div>"
    filtres='<div style="display:flex;flex-wrap:wrap;gap:4px;margin:8px 0">'
    for j in JEUX_LISTE:
        active=jeu==j
        filtres+=f"<a href='/analyse?jeu={j}' style=\"background:{'gold' if active else '#222'};color:{'#111' if active else '#fff'};padding:5px 8px;border-radius:15px;text-decoration:none;font-size:10px;font-weight:bold;border:1px solid gold\">{j} ({len(fetch_all(j))})</a>"
    filtres+='</div>'
    mode = "10B ANALYSE" if jeu in JEUX_10_BOULES else "5B"
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:8px'><a href='/' style='color:gold'>⬅ ACCUEIL</a><h3 style='color:gold;text-align:center;border:1px solid gold;padding:8px;border-radius:10px'>V19.2 - {jeu} - {mode} - {len(rows)} tirages - #{rows[0][7]}</h3>{filtres}<div style='background:#141414;padding:10px;border-radius:10px'><div><b>🔥 Chauds ({mode}):</b><br>{chaud_html}</div><div style='margin-top:8px'><b>🔗 Paires (10B):</b><br>{paires_html}</div><div style='margin-top:8px'><b>🔮 Annonceurs apres {'-'.join(res['LAST'])}:</b><br>{ann_html or '<small>Pas assez</small>'}<br><small style=color:#888>Full dernier: {'-'.join(res['LAST_FULL'])}</small></div><div style='margin-top:12px'><div style='background:gold;color:#111;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold'>🎯 T1 CHAUDS (5B sortie / 10B analyse)<br><span style='font-size:22px'>{' - '.join(res['T1'])}</span></div><div style='background:#111;border:2px solid #25D366;color:#25D366;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold'>🧠 T2 ANNONCEUR (10B)<br><span style='font-size:22px;color:#fff'>{' - '.join(res['T2'])}</span></div><div style='background:#111;border:2px solid gold;color:gold;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold'>🔗 T3 MIX CHAUDS+ANNONCEURS<br><span style='font-size:22px;color:#fff'>{' - '.join(res['T3'])}</span></div><div style='background:#222;border:2px solid #ff6b6b;color:#ff6b6b;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold'>⏰ T4 RETARD<br><span style='font-size:22px;color:#fff'>{' - '.join(res['T4'])}</span></div><div style='margin-top:10px;color:gold'>POOL 12: {' - '.join(res['POOL'])}</div></div><div style='margin-top:15px'><a href='/backtest?jeu={jeu}' style='display:block;background:#25D366;color:#fff;padding:14px;border-radius:10px;text-align:center;text-decoration:none;font-weight:bold'>TESTER BACKTEST 2/5</a></div></div></body></html>"

@app.route('/backtest')
def backtest():
    jeu=request.args.get('jeu','SUPER'); rows=fetch_all(jeu)
    if len(rows)<40: return f"<html><body style='background:#000;color:#fff;padding:12px'><a href='/' style='color:gold'>ACCUEIL</a><h3>Besoin 40 tirages, tu as {len(rows)}</h3></body></html>"
    chrono=list(reversed(rows)); wins=0; total=len(chrono)-30
    for i in range(30, len(chrono)):
        past=chrono[:i]
        # futur en 10B si possible
        futur_haut=set([x.zfill(2) for x in chrono[i][4].split('-') if x.strip().isdigit()])
        futur_bas=set([x.zfill(2) for x in chrono[i][5].split('-') if x.strip().isdigit()]) if chrono[i][3] in JEUX_10_BOULES and chrono[i][5] else set()
        futur = futur_haut | futur_bas
        if not futur: futur = futur_haut
        res=moteur_v19_2(past, jeu)
        best=max(len(futur.intersection(set(t))) for t in [res['T1'],res['T2'],res['T3'],res['T4']])
        if best>=2: wins+=1
    pct=wins/total*100 if total else 0
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:12px;text-align:center'><a href='/' style='color:gold;float:left'>⬅ ACCUEIL</a><h2 style='color:gold'>BACKTEST {jeu} V19.2 - 10B</h2><div style='font-size:56px;color:#25D366;font-weight:bold'>{pct:.1f}%</div><div>Reussite 2/5 avec 4 tickets IA (sur 10B)</div><div style='color:#888;margin-top:8px'>{wins}/{total}</div><a href='/analyse?jeu={jeu}' style='display:block;background:gold;color:#111;padding:14px;border-radius:10px;margin-top:20px;text-decoration:none;font-weight:bold'>RETOUR ANALYSE</a></body></html>"

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS'); msg=''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE'); content=None
        pasted=request.form.get('pasted_text','').strip()
        if pasted: content=pasted
        else:
            f=request.files.get('file') or request.files.get('fichier')
            if f and f.filename: content=f.read().decode('utf-8', errors='ignore')
        if content:
            novos=parse_file_pro(content, jeu_import)
            if novos:
                conn=get_conn();c=conn.cursor();c.execute('DELETE FROM tirages WHERE jeu=?',(jeu_import,));conn.commit();conn.close()
                for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
                msg=f"<div style='background:#25D366;color:#fff;padding:12px;border-radius:10px;font-weight:bold;margin-bottom:10px'>✅ {len(novos)} importes V19.2! {jeu_import} - {len([x for x in novos if x[4]])} avec bas</div>"
    rows=fetch_all(jeu_filtre)
    def fmt(d):
        if not d: return "ANCIEN"
        try: y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
        except: return d
    filtres='<div style="display:flex;flex-wrap:wrap;gap:5px;margin:10px 0">'
    for j in ["TOUS"]+JEUX_LISTE:
        cnt=len(fetch_all() if j=="TOUS" else fetch_all(j))
        active=jeu_filtre==j
        filtres+=f"<a href='/historique?jeu={j}' style=\"background:{'gold' if active else '#222'};color:{'#111' if active else '#fff'};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;font-weight:bold;border:1px solid gold\">{j} ({cnt})</a>"
    filtres+='</div>'
    cards=''.join([f"<div style='background:#151515;padding:8px;margin:4px 0;border-radius:8px;border-left:4px solid {'#25D366' if r[3] in JEUX_10_BOULES else 'gold'}'><b>{fmt(r[6])} {r[3]} #{r[7]}</b> {r[4]} { '/ '+r[5] if r[5] else ''}</div>" for r in rows[:400]]) or '<div style="color:#888;text-align:center">Base vide</div>'
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:8px'><a href='/' style='color:gold'>⬅ ACCUEIL</a><h3 style='color:gold;text-align:center'>HISTORIQUE V19.2 - {jeu_filtre} ({len(rows)}) - 10B FIX</h3><div style='background:#111;border:2px solid gold;padding:12px;border-radius:12px'>{msg}<form method='post' enctype='multipart/form-data'><select name='jeu_import' style='width:100%;padding:12px;border-radius:8px;margin-bottom:10px;background:#222;color:#fff;border:1px solid gold'>{' '.join([f'<option>{j}</option>' for j in JEUX_LISTE])}</select><input type='file' name='file' style='width:100%;background:#222;color:#fff;padding:10px;border-radius:6px' accept='.txt'><textarea name='pasted_text' placeholder='Colle: 170 22/10/2026 WIN: 48-84-85-34-41 / 12-34-56-78-90 (pour MATINALE)' style='width:100%;height:80px;background:#222;color:#fff;border:1px solid #444;border-radius:8px;padding:8px;margin-top:8px'></textarea><button style='width:100%;background:#25D366;color:#fff;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:10px'>📥 IMPORTER V19.2</button></form><div style='display:flex;gap:6px;margin-top:12px'><a href='/export/TXT?jeu=TOUS' style='flex:1;background:gold;color:#111;padding:10px;border-radius:8px;text-align:center;text-decoration:none;font-weight:bold'>💾 BACKUP</a><a href='/reset' onclick=\"return confirm('Effacer?')\" style='flex:1;background:#ff3333;color:#fff;padding:10px;border-radius:8px;text-align:center;text-decoration:none'>🗑️ VIDER</a></div></div>{filtres}{cards}</body></html>"

@app.route('/reset')
def reset():
    conn=get_conn();c=conn.cursor();c.execute('DELETE FROM tirages');conn.commit();conn.close()
    return redirect('/historique?jeu=TOUS')

@app.route('/export/<fmt>')
def export_file(fmt):
    jeu=request.args.get('jeu','TOUS'); rows=fetch_all(jeu)
    out=io.StringIO()
    for r in rows:
        if r[6]:
            try: y,m,d=r[6].split('-'); ds=f"{d}/{m}/{y}"
            except: ds=r[6]
        else: ds="01/01/2026"
        out.write(f"{r[7]} {ds} WIN: {r[4]} / {r[5]}\n" if r[5] else f"{r[7]} {ds} WIN: {r[4]}\n")
    mem=io.BytesIO(out.getvalue().encode('utf-8'))
    return send_file(mem, as_attachment=True, download_name=f'BACKUP_{jeu}_{len(rows)}_V19_2.txt', mimetype='text/plain')

@app.route('/saisir', methods=['GET','POST'])
def saisir():
    return f"<html><body style='background:#000;color:#fff;padding:12px'><h3 style='color:gold;text-align:center'>V19.2 - Utilise Historique+Import</h3><a href='/' style='color:gold'>⬅ ACCUEIL</a><p style='color:#888'>Format: 170 22/10/2026 WIN: 48-84-85-34-41 / 12-34-56-78-90 pour MATINALE</p></body></html>"

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
