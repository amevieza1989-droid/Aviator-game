from flask import Flask, request, redirect, send_file, session
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import os, re, io, secrets

app = Flask(__name__)
app.secret_key = "V19_3_1_UNIQUE_CODE_BOSS_2026"
DB = "/data/loto.db" if os.path.exists("/data") else "loto.db"
JEUX_LISTE = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]
JEUX_10_BOULES = ["MATINALE","DETENTE"]
ADMIN_PASS = "Boss2026"

def get_conn(): return sqlite3.connect(DB)
def init_db():
    conn=get_conn();c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tirages (id INTEGER PRIMARY KEY, jour TEXT, heure TEXT, jeu TEXT, haut TEXT, bas TEXT, date TEXT, numero TEXT, created TEXT, total_haut INTEGER, total_bas INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, max_uses INTEGER, used_count INTEGER, expire TEXT, jeu TEXT, note TEXT, created TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS code_uses (id INTEGER PRIMARY KEY, code TEXT, ip TEXT, device TEXT, date TEXT)')
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
            win_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', win_part) if x.isdigit() and 1<=int(x)<=90][:5]
            mach_nums=[x.zfill(2) for x in re.findall(r'\d{1,2}', mach_part) if x.isdigit() and 1<=int(x)<=90][:5]
            if len(win_nums)<5: continue
            haut='-'.join(win_nums)
            bas='-'.join(mach_nums) if jeu_force in JEUX_10_BOULES and len(mach_nums)>=5 else ''
            res.append(('LUNDI',"09:00",jeu_force,haut,bas,date_str,numero))
        except: continue
    return res

def moteur_v19_intelligent(rows):
    chrono=list(reversed(rows))
    all_nums=[]; paires=Counter(); annonce=defaultdict(Counter); prev=[]
    for r in chrono:
        win=[x.zfill(2) for x in r[4].split('-') if x.strip().isdigit()]
        all_nums.extend(win)
        for i in range(len(win)):
            for j in range(i+1,len(win)):
                paires[tuple(sorted([win[i],win[j]]))]+=1
        if prev:
            for p in prev:
                for cur in win: annonce[p][cur]+=1
        prev=win
    cnt=Counter(all_nums)
    chauds=[n for n,c in cnt.most_common(20)]
    if len(chauds)<12: chauds=["01","05","12","25","33","47","52","69","70","81","85","90"]
    top_paires=paires.most_common(6)
    last=[x.zfill(2) for x in rows[0][4].split('-') if x.strip().isdigit()] if rows else []
    t_ann=[]
    for ln in last:
        if ln in annonce: t_ann.extend([n for n,_ in annonce[ln].most_common(2)])
    t_ann=list(dict.fromkeys(t_ann))[:5]
    if len(t_ann)<5: t_ann+= [n for n in chauds if n not in t_ann][:5-len(t_ann)]
    t_pair=[]
    for (a,b),_ in top_paires[:2]: t_pair.extend([a,b])
    t_pair=list(dict.fromkeys(t_pair))
    if len(t_pair)<5: t_pair+= [n for n in chauds if n not in t_pair]
    retard=sorted([str(i).zfill(2) for i in range(1,91)], key=lambda n: cnt.get(n,0))[:5]
    return {"T1":chauds[:5],"T2":t_ann[:5],"T3":t_pair[:5],"T4":retard[:5],"POOL":chauds[:12],"CNT":cnt.most_common(15),"PAIRES":top_paires,"ANN":annonce,"LAST":last}

def check_code_valid(code_str, ip):
    conn=get_conn();c=conn.cursor()
    c.execute('SELECT code,max_uses,used_count,expire,jeu FROM codes WHERE code=?',(code_str,))
    row=c.fetchone()
    if not row:
        conn.close();return False,"Code invalide - Contacte Boss"
    code,max_u,used,expire,jeu=row
    if datetime.strptime(expire,'%Y-%m-%d') < datetime.now():
        conn.close();return False,f"Code expire le {expire}"
    c.execute('SELECT * FROM code_uses WHERE code=?',(code,))
    existing=c.fetchall()
    # Si deja utilise par une autre IP, bloque
    if existing:
        c.execute('SELECT * FROM code_uses WHERE code=? AND ip=?',(code,ip))
        same_ip=c.fetchone()
        if not same_ip:
            conn.close();return False,f"CODE DEJA UTILISE par un autre client ({used}/1). 1 CODE = 1 CLIENT"
    if not existing:
        c.execute('INSERT INTO code_uses (code,ip,device,date) VALUES (?,?,?,?)',(code,ip,request.headers.get('User-Agent','')[:80],datetime.now().strftime('%d/%m/%Y %H:%M')))
        c.execute('UPDATE codes SET used_count=1 WHERE code=?',(code,))
        conn.commit()
    conn.close();return True,jeu

@app.route('/')
def home():
    total=len(fetch_all())
    btns=""
    for j in JEUX_LISTE:
        c=len(fetch_all(j))
        bg="#1e1e1e"; border="gold" if j=="SUPER" else "#333"; color="gold" if j=="SUPER" else "#fff"
        if c>0: bg="#2a2a2a"
        btns+=f"<a class='btn' style='background:{bg};color:{color};border:1px solid {border}' href='/analyse?jeu={j}'>ANALYSE {j} ({c})</a>"
    acces = session.get('code_acces','')
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'><style>body{{background:#000;color:#fff;font-family:Arial;padding:12px;margin:0}}.btn{{display:block;padding:14px;margin:8px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold;font-size:13px}}</style></head><body><h1 style='color:gold;text-align:center'>LOTO V19.3.1 - 1 CODE 1 CLIENT</h1><p style='text-align:center;color:#888'>{total} tirages - Acces: {acces if acces else 'GRATUIT'}</p>{btns}<a class='btn' style='background:#25D366;color:#fff' href='/backtest?jeu=SUPER'>BACKTEST SUPER</a><a class='btn' style='background:#111;color:gold;border:1px solid gold' href='/historique?jeu=TOUS'>📜 HISTORIQUE</a><a class='btn' style='background:gold;color:#111' href='/acces'>🔑 ENTRER MON CODE UNIQUE</a><a class='btn' style='background:#222;color:#555;border:1px solid #333;font-size:10px' href='/admin'>ADMIN BOSS</a></body></html>"

@app.route('/acces', methods=['GET','POST'])
def acces_page():
    msg=""
    if request.method=='POST':
        code=request.form.get('code','').strip().upper()
        ip=request.remote_addr or "unknown"
        valid,info=check_code_valid(code,ip)
        if valid:
            session['code_acces']=code
            session['jeu_allowed']=info
            session.permanent=True
            return redirect(f"/analyse?jeu={info if info!='TOUS' else 'SUPER'}")
        else:
            msg=f"<div style='background:#ff3333;padding:12px;border-radius:8px;margin-bottom:10px;font-weight:bold'>❌ {info}</div>"
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:15px'><a href='/' style='color:gold'>⬅ ACCUEIL</a><h2 style='color:gold;text-align:center'>🔑 CODE UNIQUE - 1 CLIENT</h2>{msg}<div style='background:#111;border:2px solid gold;padding:15px;border-radius:12px'><form method='post'><input name='code' placeholder='Ex: SUPER-A1B2C3' style='width:100%;padding:14px;border-radius:8px;background:#222;color:#fff;border:1px solid gold;font-size:16px;text-transform:uppercase'><button style='width:100%;background:gold;color:#111;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:10px'>DEVERROUILLER</button></form><div style='margin-top:15px;color:#888;font-size:12px'>⚠️ 1 CODE = 1 SEUL TELEPHONE<br>Si tu partages ton code, il ne marchera plus pour toi.<br><br>Paye Mixx by Yas / Flooz puis reçois ton code perso sur WhatsApp</div></div></body></html>"

@app.route('/admin', methods=['GET','POST'])
def admin():
    if session.get('admin')!=True:
        if request.method=='POST':
            if request.form.get('pass')==ADMIN_PASS:
                session['admin']=True
                return redirect('/admin')
            else:
                return "<html><body style='background:#000;color:#fff;padding:20px'><h3 style='color:#ff3333'>Mauvais pass</h3><a href='/admin' style='color:gold'>Reessayer</a></body></html>"
        return "<html><body style='background:#000;color:#fff;font-family:Arial;padding:20px'><h3 style='color:gold'>ADMIN BOSS</h3><form method='post'><input type='password' name='pass' placeholder='Mot de passe Boss2026' style='width:100%;padding:12px;background:#222;color:#fff;border:1px solid gold;border-radius:8px'><button style='width:100%;background:gold;color:#111;padding:12px;margin-top:10px;border:none;border-radius:8px;font-weight:bold'>ENTRER</button></form></body></html>"
    msg=""
    if request.method=='POST' and 'generer' in request.form:
        jeu=request.form.get('jeu','SUPER'); duree=int(request.form.get('duree','30')); note=request.form.get('note','Client')
        code=f"{jeu}-{secrets.token_hex(3).upper()}"
        expire=(datetime.now()+timedelta(days=duree)).strftime('%Y-%m-%d')
        conn=get_conn();c=conn.cursor()
        c.execute('INSERT INTO codes (code,max_uses,used_count,expire,jeu,note,created) VALUES (?,?,?,?,?,?,?)',(code,1,0,expire,jeu,note,datetime.now().strftime('%d/%m/%Y')))
        conn.commit();conn.close()
        msg=f"<div style='background:#25D366;color:#fff;padding:14px;border-radius:10px;margin-bottom:10px;font-weight:bold'>✅ CODE UNIQUE CREE:<br><br><span style='font-size:22px;letter-spacing:2px'>{code}</span><br><br>1 CODE = 1 CLIENT<br>Expire {expire} - Jeu {jeu}<br><br>COPIE ET ENVOIE AU CLIENT</div>"
    conn=get_conn();c=conn.cursor()
    c.execute('SELECT code,max_uses,used_count,expire,jeu,note,created FROM codes ORDER BY id DESC LIMIT 50')
    codes=c.fetchall()
    c.execute('SELECT code,ip,date FROM code_uses ORDER BY id DESC LIMIT 20')
    uses=c.fetchall()
    conn.close()
    liste="".join([f"<div style='background:#151515;padding:8px;margin:4px 0;border-radius:6px;border-left:4px solid {'#25D366' if u==1 else 'gold'};font-size:12px'><b>{co}</b> - {'✅ UTILISE' if u==1 else '🟡 DISPONIBLE'} - Exp {ex} - {je}<br><small>{no} - Cree {cr}</small> <a href='/admin/del/{co}' style='color:#ff3333;float:right'>SUPPR</a></div>" for co,m,u,ex,je,no,cr in codes])
    uses_html="".join([f"<div style='font-size:11px;color:#888;background:#0a0a0a;padding:4px;margin:2px;border-radius:4px'>{co} - IP {ip} - {d}</div>" for co,ip,d in uses])
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:10px'><a href='/' style='color:gold'>⬅ ACCUEIL</a><h3 style='color:gold'>ADMIN - 1 CODE = 1 CLIENT</h3>{msg}<div style='background:#111;border:2px solid gold;padding:12px;border-radius:12px'><form method='post'><label style='color:gold;font-size:12px'>JEU AUTORISE</label><select name='jeu' style='width:100%;padding:12px;background:#222;color:#fff;border:1px solid gold;border-radius:6px;margin-bottom:8px'>{''.join([f'<option>{j}</option>' for j in JEUX_LISTE+['TOUS'])])}</select><label style='color:gold;font-size:12px'>DUREE (jours)</label><input name='duree' value='30' type='number' style='width:100%;padding:10px;background:#222;color:#fff;border:1px solid #555;border-radius:6px;margin-bottom:8px'><label style='color:gold;font-size:12px'>NOM CLIENT + PAIEMENT</label><input name='note' placeholder='Ex: Koffi - 5000F Flooz 22/10' style='width:100%;padding:10px;background:#222;color:#fff;border:1px solid #555;border-radius:6px;margin-bottom:8px'><button name='generer' value='1' style='width:100%;background:gold;color:#111;padding:16px;border:none;border-radius:10px;font-weight:bold'>🎫 GENERER CODE UNIQUE (1 CLIENT MAX)</button></form></div><h4 style='color:gold;margin-top:15px'>Codes generes ({len(codes)}) - VERT=Utilise</h4>{liste}<h4 style='color:#25D366;margin-top:15px'>Dernières utilisations</h4>{uses_html}<a href='/admin/logout' style='display:block;background:#ff3333;color:#fff;padding:10px;text-align:center;border-radius:8px;margin-top:15px;text-decoration:none'>Deconnexion</a></body></html>"

@app.route('/admin/del/<code>')
def admin_del(code):
    if session.get('admin')!=True: return redirect('/admin')
    conn=get_conn();c=conn.cursor();c.execute('DELETE FROM codes WHERE code=?',(code,));c.execute('DELETE FROM code_uses WHERE code=?',(code,));conn.commit();conn.close()
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin',None); return redirect('/')

@app.route('/analyse')
def analyse():
    jeu=request.args.get('jeu','MATINALE')
    code_acces=session.get('code_acces')
    jeu_allowed=session.get('jeu_allowed','TOUS')
    if not code_acces:
        if jeu!="MATINALE" and len(fetch_all(jeu))>5:
            return redirect('/acces')
    rows=fetch_all(jeu)
    if not rows: return f"<html><body style='background:#000;color:#fff;padding:12px'><a href='/' style='color:gold'>⬅ ACCUEIL</a><h3>Base vide {jeu}</h3><a href='/historique?jeu={jeu}' style='color:#25D366'>IMPORTER</a></body></html>"
    res=moteur_v19_intelligent(rows)
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
    vip_badge=f"<div style='background:#25D366;color:#fff;padding:6px;text-align:center;border-radius:20px;font-size:11px;margin-bottom:8px'>✅ VIP: {code_acces} - Expire 30j - 1 CLIENT</div>" if code_acces else "<div style='background:#222;color:#888;padding:6px;text-align:center;border-radius:20px;font-size:11px;margin-bottom:8px'>Mode GRATUIT - CODE REQUIS</div>"
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:8px'><a href='/' style='color:gold'>⬅ ACCUEIL</a>{vip_badge}<h3 style='color:gold;text-align:center;border:1px solid gold;padding:8px;border-radius:10px'>V19.3.1 - {jeu} - {len(rows)} - #{rows[0][7]}</h3>{filtres}<div style='background:#141414;padding:10px;border-radius:10px'><div><b>🔥 Chauds:</b><br>{chaud_html}</div><div style='margin-top:8px'><b>🔗 Paires:</b><br>{paires_html}</div><div style='margin-top:8px'><b>🔮 Apres {'-'.join(res['LAST'])}:</b><br>{ann_html or '<small>Pas assez</small>'}</div><div style='margin-top:12px'><div style='background:gold;color:#111;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold'>🎯 T1 CHAUDS<br><span style='font-size:22px'>{' - '.join(res['T1'])}</span></div><div style='background:#111;border:2px solid #25D366;color:#25D366;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold'>🧠 T2 ANNONCEUR<br><span style='font-size:22px;color:#fff'>{' - '.join(res['T2'])}</span></div><div style='background:#111;border:2px solid gold;color:gold;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold'>🔗 T3 PAIRES<br><span style='font-size:22px;color:#fff'>{' - '.join(res['T3'])}</span></div><div style='background:#222;border:2px solid #ff6b6b;color:#ff6b6b;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold'>⏰ T4 RETARD<br><span style='font-size:22px;color:#fff'>{' - '.join(res['T4'])}</span></div><div style='margin-top:10px;color:gold'>POOL 12: {' - '.join(res['POOL'])}</div></div><div style='margin-top:15px'><a href='/backtest?jeu={jeu}' style='display:block;background:#25D366;color:#fff;padding:14px;border-radius:10px;text-align:center;text-decoration:none;font-weight:bold'>BACKTEST 2/5</a></div></div></body></html>"

@app.route('/backtest')
def backtest():
    jeu=request.args.get('jeu','SUPER'); rows=fetch_all(jeu)
    if len(rows)<40: return f"<html><body style='background:#000;color:#fff;padding:12px'><a href='/' style='color:gold'>ACCUEIL</a><h3>Besoin 40, tu as {len(rows)}</h3></body></html>"
    chrono=list(reversed(rows)); wins=0; total=len(chrono)-30
    for i in range(30, len(chrono)):
        past=chrono[:i]
        futur=set([x.zfill(2) for x in chrono[i][4].split('-') if x.strip().isdigit()])
        res=moteur_v19_intelligent(past)
        best=max(len(futur.intersection(set(t))) for t in [res['T1'],res['T2'],res['T3'],res['T4']])
        if best>=2: wins+=1
    pct=wins/total*100 if total else 0
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:12px;text-align:center'><a href='/' style='color:gold;float:left'>⬅ ACCUEIL</a><h2 style='color:gold'>BACKTEST {jeu} V19.3.1</h2><div style='font-size:56px;color:#25D366;font-weight:bold'>{pct:.1f}%</div><div>{wins}/{total}</div><a href='/analyse?jeu={jeu}' style='display:block;background:gold;color:#111;padding:14px;border-radius:10px;margin-top:20px;text-decoration:none;font-weight:bold'>RETOUR</a></body></html>"

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
                return redirect(f'/historique?jeu={jeu_import}')
    rows=fetch_all(jeu_filtre)
    def fmt(d):
        if not d: return "ANCIEN"
        try: y,m,dd=d.split('-'); return f"{dd}/{m}/{y}"
        except: return d
    opts="".join([f"<option value='{j}' {'selected' if (jeu_filtre==j or (jeu_filtre=='TOUS' and j=='MATINALE')) else ''}>{j}</option>" for j in JEUX_LISTE])
    filtres='<div style="display:flex;flex-wrap:wrap;gap:5px;margin:10px 0">'
    for j in ["TOUS"]+JEUX_LISTE:
        cnt=len(fetch_all() if j=="TOUS" else fetch_all(j))
        active=jeu_filtre==j
        filtres+=f"<a href='/historique?jeu={j}' style=\"background:{'gold' if active else '#222'};color:{'#111' if active else '#fff'};padding:6px 10px;border-radius:20px;text-decoration:none;font-size:11px;font-weight:bold;border:1px solid gold\">{j} ({cnt})</a>"
    filtres+='</div>'
    cards=''.join([f"<div style='background:#151515;padding:8px;margin:4px 0;border-radius:8px;border-left:4px solid {'#25D366' if r[3] in JEUX_10_BOULES else 'gold'}'><b>{fmt(r[6])} {r[3]} #{r[7]}</b> {r[4]} { '/ '+r[5] if r[5] else ''}</div>" for r in rows[:400]]) or '<div style="color:#888;text-align:center;padding:20px">Base vide</div>'
    return f"<html><body style='background:#000;color:#fff;font-family:Arial;padding:8px'><a href='/' style='color:gold'>⬅ ACCUEIL</a><h3 style='color:gold;text-align:center'>HISTORIQUE V19.3.1 - {jeu_filtre} ({len(rows)})</h3><div style='background:#111;border:2px solid gold;padding:12px;border-radius:12px'>{msg}<form method='post' enctype='multipart/form-data'><select name='jeu_import' style='width:100%;padding:12px;border-radius:8px;margin-bottom:10px;background:#222;color:#fff;border:1px solid gold'>{opts}</select><input type='file' name='file' style='width:100%;background:#222;color:#fff;padding:10px;border-radius:6px' accept='.txt'><textarea name='pasted_text' placeholder='170 22/10/2026 WIN: 48-84-85-34-41' style='width:100%;height:80px;background:#222;color:#fff;border:1px solid #444;border-radius:8px;padding:8px;margin-top:8px'></textarea><button style='width:100%;background:#25D366;color:#fff;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:10px'>📥 IMPORTER</button></form></div>{filtres}{cards}</body></html>"

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
    return send_file(mem, as_attachment=True, download_name=f'BACKUP_{jeu}_{len(rows)}_V19_3_1.txt', mimetype='text/plain')

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
