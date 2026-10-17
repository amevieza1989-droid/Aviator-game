from flask import Flask, request, render_template_string, redirect, send_file
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
import os, re, io, random

app = Flask(__name__)
DB = "loto.db"
JEUX_LISTE = ["MATINALE","DIAMANT","GOLD","CASH","BOOM","BENZ","PRESTIGE","MILLION","SUPER","KADOO","KING","SAM","BINGO","DETENTE"]

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
    res=[]
    for line in content.splitlines():
        line=line.strip()
        if not line: continue
        date_str=""; numero=None; line_sans_date=line
        m=re.search(r'(\d{1,4})\s+(\d{2})/(\d{2})',line)
        if m:
            numero=m.group(1); dd=m.group(2); mm=m.group(3)
            yy="2024" if mm=="12" else "2025"; date_str=f"{yy}-{mm}-{dd}"
            line_sans_date=line.replace(m.group(0),' ')
        else:
            m1=re.search(r'(\d{4}-\d{2}-\d{2})',line)
            if m1: date_str=m1.group(1); line_sans_date=line.replace(m1.group(1),' ')
        if not numero:
            nums_tmp=re.findall(r'\b\d{2,4}\b',line)
            if nums_tmp: numero=nums_tmp[-1]
            else: numero=str(len(res)+1)
        nums=re.findall(r'\d+',line_sans_date)
        clean=[n.zfill(2) for n in nums if n.isdigit() and 1<=int(n)<=90]
        if len(clean)>=5:
            haut='-'.join(clean[:5]); bas='-'.join(clean[5:10]) if len(clean)>=10 else ''
            res.append(('LUNDI',"09:00",jeu_force,haut,bas,date_str,numero))
    return res

@app.route('/')
def home():
    total=len(fetch_all())
    rows=fetch_all()
    last=f"#{rows[0][7]} - {rows[0][4]}" if rows else "Aucun"
    return render_template_string(f'<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:12px}}.btn{{display:block;background:#1a1a1a;border:1px solid gold;color:gold;padding:16px;margin:10px 0;border-radius:12px;text-align:center;text-decoration:none;font-weight:bold}}small{{color:#aaa}}</style></head><body><div style="background:gold;color:#111;padding:14px;border-radius:12px;text-align:center;font-weight:bold">LOTO V16 INTELLIGENT 🧠<br>{total} tirages - Dernier: {last}</div><a class="btn" href="/saisir">🎰 SAISIR TIRAGE #717 DU JOUR</a><a class="btn" href="/historique">📜 HISTORIQUE + SAUVE</a><a class="btn" href="/analyse">🧠 ANALYSE INTELLIGENTE + IA</a><a class="btn" href="/export/TXT?jeu=TOUS">💾 BACKUP</a></body></html>')

@app.route('/historique', methods=['GET','POST'])
def historique():
    jeu_filtre=request.args.get('jeu','TOUS'); msg=''
    if request.method=='POST':
        jeu_import=request.form.get('jeu_import','MATINALE'); content_to_parse=None
        pasted=request.form.get('pasted_text','').strip()
        if pasted: content_to_parse=pasted
        else:
            f=request.files.get('file')
            if f and f.filename: content_to_parse=f.read().decode('utf-8', errors='ignore')
        if content_to_parse:
            novos=parse_file_pro(content_to_parse, jeu_import)
            for j,h,je,ht,bs,dt,num in novos: insert_tirage(j,h,je,ht,bs,dt,num)
            msg=f'<div style="background:#25D366;color:#fff;padding:12px;border-radius:10px;font-weight:bold">✅ {len(novos)} importés - IA mise à jour!</div>'
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
    cards=''.join([f'<div style="background:#151515;padding:8px;margin:4px 0;border-radius:8px;border-left:4px solid gold"><b>{format_date(r[6])} #{r[7]}</b> WIN:{r[4]}<br><small>MACHINE:{r[5]}</small></div>' for r in rows[:400]]) or '<div style="color:#888;text-align:center">Base vide</div>'
    return f'<html><body style="background:#000;color:#fff;font-family:Arial;padding:8px"><a href="/" style="color:gold">⬅ ACCUEIL</a><h3 style="color:gold;text-align:center">HISTORIQUE - {jeu_filtre} ({total_rows})</h3><div style="background:#111;border:2px solid gold;padding:10px;border-radius:12px">{msg}<form method="post" enctype="multipart/form-data"><select name="jeu_import" style="width:100%;padding:8px;border-radius:6px;margin-bottom:6px">{"".join([f"<option>{j}</option>" for j in JEUX_LISTE])}</select><textarea name="pasted_text" style="width:100%;height:100px;background:#222;color:#fff;border:1px solid #25D366;border-radius:8px;padding:6px"></textarea><button style="width:100%;background:#25D366;color:#fff;padding:10px;border:none;border-radius:8px;font-weight:bold;margin-top:4px">🚀 IMPORTER</button></form><div style="display:flex;gap:6px;margin-top:8px"><a href="/export/TXT?jeu=TOUS" style="flex:1;background:gold;color:#111;padding:8px;border-radius:6px;text-align:center;text-decoration:none;font-weight:bold">💾 BACKUP</a><a href="/reset" onclick="return confirm(\'Effacer?\')" style="flex:1;background:#ff3333;color:#fff;padding:8px;border-radius:6px;text-align:center;text-decoration:none">🗑️</a></div></div>{filtres}{cards}</body></html>'

@app.route('/analyse')
def analyse():
    jeu_filtre=request.args.get('jeu','MATINALE'); rows=fetch_all(jeu_filtre)
    if not rows:
        return '<html><body style="background:#000;color:#fff;padding:12px"><a href="/" style="color:gold">⬅ ACCUEIL</a><br>Base vide</body></html>'
    all_nums=[]; paires=Counter(); annonce=defaultdict(Counter)
    prev_win=[]
    for idx, r in enumerate(reversed(rows)): # du plus ancien au plus recent pour annonceur
        win_nums=[x.zfill(2) for x in r[4].split('-') if x.strip().isdigit()]
        all_nums.extend(win_nums)
        # paires
        for i in range(len(win_nums)):
            for j in range(i+1,len(win_nums)):
                paires[tuple(sorted([win_nums[i],win_nums[j]]))]+=1
        # annonceur: quel numero annonce le tirage suivant
        if prev_win:
            for p in prev_win:
                for cur in win_nums:
                    annonce[p][cur]+=1
        prev_win=win_nums
    
    cnt=Counter(all_nums)
    chauds=cnt.most_common(20)
    tous=[str(i).zfill(2) for i in range(1,91)]
    retard=sorted(tous, key=lambda n: cnt.get(n,0))
    
    # Dernier tirage pour annonceur
    last_nums=[x for x in rows[0][4].split('-') if x.strip().isdigit()]
    last_nums=[x.zfill(2) for x in last_nums]
    
    annonce_html=""
    for ln in last_nums[:3]:
        if ln in annonce:
            top_annonce=annonce[ln].most_common(3)
            annonce_html+=f'<div style="background:#111;border:1px solid #555;padding:6px;margin:3px;border-radius:6px"><b>Après {ln} sort souvent:</b> {" ".join([f"{n}({c}x)" for n,c in top_annonce])}</div>'
    
    top_paires=paires.most_common(8)
    paires_html=''.join([f'<span style="display:inline-block;background:#222;border:1px solid gold;color:gold;padding:5px 8px;border-radius:12px;margin:3px;font-size:12px">{a}-{b} ({c}x)</span>' for (a,b),c in top_paires])
    
    chaud_html=''.join([f'<span style="display:inline-block;background:gold;color:#111;padding:5px 10px;border-radius:15px;margin:2px;font-weight:bold;font-size:13px">{n}({c})</span>' for n,c in chauds[:10]])
    retard_html=''.join([f'<span style="display:inline-block;background:#300;color:#ff6b6b;padding:5px 10px;border-radius:15px;margin:2px;border:1px solid #ff6b6b;font-size:13px">{n}({cnt.get(n,0)})</span>' for n in retard[:10]])
    
    # TICKETS INTELLIGENTS
    ticket1=[n for n,c in chauds[:5]]
    # Ticket annonceur basé sur dernier tirage
    ticket_annonce=[]
    for ln in last_nums:
        if ln in annonce and annonce[ln]:
            ticket_annonce.extend([n for n,_ in annonce[ln].most_common(2)])
    ticket_annonce=list(dict.fromkeys(ticket_annonce))[:5]
    if len(ticket_annonce)<5: ticket_annonce+= [n for n,c in chauds[:5] if n not in ticket_annonce]
    ticket_annonce=ticket_annonce[:5]
    
    ticket_paires=[top_paires[0][0][0], top_paires[0][0][1], top_paires[1][0][0], top_paires[1][0][1], chauds[0][0]] if top_paires else ticket1
    ticket_retard=retard[:5]
    
    filtres='<div style="display:flex;flex-wrap:wrap;gap:4px;margin:8px 0">'
    for j in JEUX_LISTE:
        active=jeu_filtre==j
        filtres+=f'<a href="/analyse?jeu={j}" style="background:{"gold" if active else "#222"};color:{"#111" if active else "#fff"};padding:5px 8px;border-radius:15px;text-decoration:none;font-size:10px;font-weight:bold;border:1px solid gold">{j} ({len(fetch_all(j))})</a>'
    filtres+='</div>'
    
    return f'''<html><body style="background:#000;color:#fff;font-family:Arial;padding:6px">
    <a href="/" style="color:gold">⬅ ACCUEIL</a>
    <h3 style="color:gold;text-align:center;border:1px solid gold;padding:6px;border-radius:8px">🧠 IA - {jeu_filtre} - {len(rows)} tirages - Dernier #{rows[0][7]}</h3>
    {filtres}
    <div style="background:#141414;padding:10px;border-radius:10px">
        <div><b>🔥 Chauds (plus sortis):</b><br>{chaud_html}</div>
        <div style="margin-top:8px"><b>❄️ Retard (moins sortis - vont sortir):</b><br>{retard_html}</div>
        <div style="margin-top:8px"><b>🔗 Paires qui sortent ensemble:</b><br>{paires_html}</div>
        <div style="margin-top:8px"><b>🔮 Annonceurs (après dernier tirage { "-".join(last_nums) }):</b><br>{annonce_html or "<small>Pas assez de données</small>"}</div>
        
        <div style="margin-top:12px">
            <div style="background:gold;color:#111;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold">
                🎯 TICKET 1 - CHAUDS<br><span style="font-size:20px">{" - ".join(ticket1)}</span><br><small>Les plus fréquents</small>
            </div>
            <div style="background:#111;border:2px solid #25D366;color:#25D366;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold">
                🧠 TICKET 2 - ANNONCEUR INTELLIGENT<br><span style="font-size:20px;color:#fff">{" - ".join(ticket_annonce)}</span><br><small style="color:#aaa">Basé sur ton dernier tirage #{rows[0][7]} - Ce qui sort après {",".join(last_nums[:2])}</small>
            </div>
            <div style="background:#111;border:2px solid gold;color:gold;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold">
                🔗 TICKET 3 - PAIRES<br><span style="font-size:20px;color:#fff">{" - ".join(ticket_paires)}</span><br><small style="color:#aaa">Les paires qui sortent ensemble</small>
            </div>
            <div style="background:#222;border:2px solid #ff6b6b;color:#ff6b6b;padding:12px;border-radius:10px;margin:6px 0;font-weight:bold">
                ⏰ TICKET 4 - RETARD<br><span style="font-size:20px;color:#fff">{" - ".join(ticket_retard)}</span><br><small style="color:#aaa">Les moins sortis - grosse cote</small>
            </div>
        </div>
        <div style="background:#0a0a0a;border:1px dashed gold;padding:8px;border-radius:8px;margin-top:10px;font-size:11px;color:#aaa">
            💡 IA EXPLIQUE: Le Loto est aléatoire, mais l'IA apprend: si après le 62 le 33 sort souvent, elle te le propose. Ajoute chaque jour le nouveau tirage (#717 aujourd'hui) et l'IA devient plus intelligente!
        </div>
    </div>
    </body></html>'''

@app.route('/reset')
def reset():
    conn=get_conn();c=conn.cursor(); c.execute('DELETE FROM tirages'); conn.commit(); conn.close()
    return redirect('/historique?jeu=TOUS')

@app.route('/export/<fmt>')
def export_file(fmt):
    jeu=request.args.get('jeu','TOUS'); rows=fetch_all(jeu)
    out=io.StringIO()
    for r in rows: out.write(f'{r[7]} {r[6]} WIN:{r[4]} MACHINE:{r[5]}\n')
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
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{background:#0a0a0a;color:#fff;font-family:Arial;padding:10px}}select,input{{width:100%;padding:12px;margin:4px 0;border-radius:6px;border:1px solid #333}}label{{color:gold;font-weight:bold;font-size:12px}}.jeu-box{{background:#111;border:2px solid gold;color:gold;text-align:center;padding:10px;border-radius:8px;font-weight:bold}}.cage{{display:flex;gap:3px}}.cage input{{width:18%;text-align:center;font-weight:bold}}</style></head><body><h3 style="color:gold;text-align:center">🧠 SAISIR - IA VA APPRENDRE</h3><label>N° TIRAGE (ex: 717)</label><input id="numero_out" type="number" min="1" max="2000" value="717" required><label>DATE</label><input type="date" id="date_out" value="{today}" required><label>JEU</label><select id="jeu" class="jeu-box"><option>MATINALE</option><option>DIAMANT</option><option>GOLD</option><option>CASH</option><option>BOOM</option><option>BENZ</option><option>PRESTIGE</option><option>MILLION</option><option>SUPER</option><option>KADOO</option><option>KING</option><option>SAM</option><option>BINGO</option><option>DETENTE</option></select><form id="mainForm" method="POST"><input type="hidden" name="jour" value="LUNDI"><input type="hidden" name="heure" value="09:00"><input type="hidden" name="jeu" id="jeu_input" value="MATINALE"><input type="hidden" name="numero" id="numero_input"><input type="hidden" name="date" id="date_input"><div style="margin:10px 0"><label>WIN (5) - EX: 62 55 33 51 81</label><div class="cage"><input name="h1" placeholder="62" required><input name="h2" placeholder="55" required><input name="h3" placeholder="33" required><input name="h4" placeholder="51" required><input name="h5" placeholder="81" required></div></div><div><label>MACHINE (5) - EX: 38 61 52 26 14</label><div class="cage"><input name="b1" placeholder="38"><input name="b2" placeholder="61"><input name="b3" placeholder="52"><input name="b4" placeholder="26"><input name="b5" placeholder="14"></div></div><button style="width:100%;background:gold;color:#111;padding:14px;border:none;border-radius:10px;font-weight:bold;margin-top:12px">🧠 ENREGISTRER ET FAIRE APPRENDRE L IA</button></form><script>document.getElementById('mainForm').addEventListener('submit', function(){{document.getElementById('jeu_input').value=document.getElementById('jeu').value;document.getElementById('numero_input').value=document.getElementById('numero_out').value;document.getElementById('date_input').value=document.getElementById('date_out').value;}});</script><a href="/" style="color:gold;display:block;text-align:center;margin-top:12px">⬅ Retour</a></body></html>"""

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
