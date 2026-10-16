from flask import Flask, render_template_string, request, redirect, url_for, send_file
import json, os, re
from datetime import datetime
import io

app = Flask(__name__)
DATA_FILE = "tirages.json"

def load_tirages():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return [
        {"jour":"DIMANCHE","heure":"15:00","type":"DETENTE","numero":9,"date":"2026-09-27","win":[46,78,26,72,10],"machine":[71,14,65,31,88]},
        {"jour":"DIMANCHE","heure":"15:00","type":"DETENTE","numero":8,"date":"2026-09-20","win":[55,41,67,23,63],"machine":[14,4,68,60,20]},
        {"jour":"LUNDI","heure":"09:00","type":"MATINALE","numero":7,"date":"2026-09-13","win":[32,47,81,17,50],"machine":[3,38,58,82,23]},
        {"jour":"SAMEDI","heure":"09:00","type":"MATINALE","numero":6,"date":"2026-09-06","win":[20,55,37,24,22],"machine":[29,45,84,54,49]},
    ]

def save_tirages(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_txt(content):
    tirages = []
    lines = content.splitlines()
    current = {}
    for line in lines:
        line = line.strip()
        if not line:
            if current.get("win"):
                tirages.append(current)
                current = {}
            continue
        if "|" in line or ";" in line:
            sep = "|" if "|" in line else ";"
            parts = [p.strip() for p in line.split(sep)]
            nums = re.findall(r'\d+', line)
            if len(nums) >= 10:
                win = list(map(int, nums[-10:-5]))
                mach = list(map(int, nums[-5:]))
                tirages.append({"jour":"LUNDI","heure":"09:00","type":"MATINALE","numero":0,"date":parts[0] if len(parts[0])>5 else datetime.now().strftime("%Y-%m-%d"),"win":win,"machine":mach})
                continue
        if "WIN" in line.upper():
            nums = list(map(int, re.findall(r'\d+', line)))
            if len(nums)>=5:
                current["win"] = nums[-5:]
        if "MACHINE" in line.upper():
            nums = list(map(int, re.findall(r'\d+', line)))
            if len(nums)>=5:
                current["machine"] = nums[-5:]
                if "win" in current:
                    current.setdefault("jour","LUNDI")
                    current.setdefault("heure","09:00")
                    current.setdefault("type","MATINALE")
                    current.setdefault("numero",len(tirages)+1)
                    current.setdefault("date",datetime.now().strftime("%Y-%m-%d"))
                    tirages.append(current)
                    current = {}
    if current.get("win") and current.get("machine"):
        tirages.append(current)
    return tirages

TEMPLATE_BASE = """
<style>
body{background:#0a0a0a;color:white;font-family:Arial;padding:10px}
.btn{padding:12px;border-radius:10px;border:2px solid #FFD700;color:#FFD700;text-align:center;margin:8px 0;display:block;text-decoration:none;font-weight:bold}
.btn-yellow{background:#FFD700;color:black}
.btn-green{border-color:#00FF88;color:#00FF88}
.card{border-left:4px solid #FFD700;background:#1a1a1a;padding:10px;margin:10px 0;border-radius:8px}
.badge{background:#00FF88;color:black;padding:5px 10px;border-radius:5px;border:none;margin-top:5px}
</style>
"""

@app.route('/')
def accueil():
    return render_template_string(TEMPLATE_BASE + """
    <a class="btn btn-yellow">LOTO V13.3 - 01 à 90 - Import/Export</a>
    <a href="/saisir" class="btn">🎰 SAISIR EN CAGE</a>
    <a href="/analyse" class="btn">📊 ANALYSE VENDEUR</a>
    <a href="/historique" class="btn btn-green">📜 HISTORIQUE DES TIRAGES</a>
    """)

@app.route('/historique', methods=['GET','POST'])
def historique():
    tirages = load_tirages()
    message = ""
    if request.method == 'POST':
        f = request.files.get('file')
        if f and f.filename:
            try:
                content = f.read().decode('utf-8', errors='ignore')
                nouveaux = parse_txt(content)
                for n in nouveaux:
                    n["total_win"] = sum(n.get("win",[]))
                    n["total_machine"] = sum(n.get("machine",[]))
                    tirages.append(n)
                save_tirages(tirages)
                message = f"<div style='background:#00FF88;color:black;padding:10px;border-radius:8px'>✅ {len(nouveaux)} tirages importés! (Fichier: {f.filename})</div>"
            except Exception as e:
                message = f"<div style='background:red;color:white;padding:10px'>Erreur: {e}</div>"
    try:
        tirages_sorted = sorted(tirages, key=lambda x: x.get("date",""), reverse=True)
    except:
        tirages_sorted = tirages
    html_cards = ""
    for t in tirages_sorted:
        win_str = "-".join([f"{x:02d}" for x in t.get("win",[])])
        mach_str = "-".join([f"{x:02d}" for x in t.get("machine",[])])
        total_win = t.get("total_win", sum(t.get("win",[])))
        total_mach = t.get("total_machine", sum(t.get("machine",[])))
        html_cards += f"""
        <div class="card">
        <b>{t.get('jour','')} {t.get('heure','')} {t.get('type','')} #{t.get('numero','')} - {t.get('date','')}</b><br>
        WIN: {win_str}<br>
        MACHINE: {mach_str}<br>
        TOTAL WIN:{total_win} | MACHINE:{total_mach}<br>
        <button class="badge">📋 Partager WhatsApp</button>
        </div>
        """
    return render_template_string(TEMPLATE_BASE + """
    <a href="/" class="btn" style="border-color:cyan;color:cyan">⬅️ ACCUEIL</a>
    <div class="btn btn-yellow">📜 HISTORIQUE - {{count}} TIRAGES</div>
    <div style="background:#1a1a1a;padding:12px;border-radius:10px;border:2px dashed #FFD700;margin:10px 0">
    <h3 style="color:#FFD700;margin:0 0 8px 0">📥 IMPORT MASSIF</h3>
    """ + message + """
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".txt,.csv" style="color:white;margin:8px 0" required>
        <button type="submit" style="background:#FFD700;color:black;padding:10px;width:100%;border-radius:8px;font-weight:bold;border:none">Importer MATINAL_RESULTS.txt</button>
    </form>
    </div>
    <div style="display:flex;gap:8px">
        <a href="/export/txt" class="btn" style="flex:1;border-color:#00FF88;color:#00FF88">📤 Exporter TXT</a>
        <a href="/export/json" class="btn" style="flex:1;border-color:cyan;color:cyan">📤 Exporter JSON</a>
    </div>
    {{cards|safe}}
    """, count=len(tirages_sorted), cards=html_cards)

@app.route('/export/<fmt>')
def export_file(fmt):
    tirages = load_tirages()
    if fmt == "json":
        return send_file(DATA_FILE, as_attachment=True) if os.path.exists(DATA_FILE) else (json.dumps(tirages), 200, {'Content-Type':'application/json'})
    else:
        output = io.StringIO()
        for t in tirages:
            win = "-".join([f"{x:02d}" for x in t.get("win",[])])
            mach = "-".join([f"{x:02d}" for x in t.get("machine",[])])
            output.write(f"{t.get('date','')} | WIN: {win} | MACHINE: {mach}\\n")
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(mem, as_attachment=True, download_name="EXPORT_LOTO_V13.3.txt", mimetype="text/plain")

@app.route('/saisir')
def saisir():
    return render_template_string(TEMPLATE_BASE + """<a href="/" class="btn">⬅️ Retour</a><div class="btn">SAISIR EN CAGE</div>""")

@app.route('/analyse')
def analyse():
    return render_template_string(TEMPLATE_BASE + """<a href="/" class="btn">⬅️ Retour</a><div class="btn">ANALYSE VENDEUR</div>""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
