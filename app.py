import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

FICHIER_DEPOTS = "depots.json"
NUMERO_MARCHAND = "92 72 70 34"
CODE_ADMIN = "92727034"

def charger_depots():
    if os.path.exists(FICHIER_DEPOTS):
        try:
            with open(FICHIER_DEPOTS, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def sauver_depots(depots):
    with open(FICHIER_DEPOTS, 'w') as f:
        json.dump(depots, f)

@app.route('/api/depot/demande', methods=['POST'])
def demande_depot():
    data = request.json
    depots = charger_depots()
    nouveau = {
        "id": len(depots)+1,
        "montant": data.get('montant'),
        "id_transaction": data.get('id_transaction'),
        "tel_joueur": data.get('telephone', 'Anonyme'),
        "statut": "en_attente",
        "date": datetime.now().strftime("%d/%m %H:%M")
    }
    depots.append(nouveau)
    sauver_depots(depots)
    return jsonify({"success": True, "message": f"Demande de {nouveau['montant']}F reçue."})

@app.route('/api/admin/depots', methods=['GET'])
def liste_depots():
    if request.args.get('code') != CODE_ADMIN:
        return jsonify({"error": "Code invalide"}), 403
    return jsonify(charger_depots())

@app.route('/api/admin/valider', methods=['POST'])
def valider_depot():
    data = request.json
    if data.get('code') != CODE_ADMIN:
        return jsonify({"error": "Code invalide"}), 403
    depots = charger_depots()
    for d in depots:
        if d['id'] == data.get('id_depot'):
            d['statut'] = 'valide'
            sauver_depots(depots)
            return jsonify({"success": True, "montant": d['montant']})
    return jsonify({"error": "Non trouvé"}), 404

ADMIN_HTML = """
<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Admin AviatorTG</title>
<style>body{background:#0a0c1e;color:white;font-family:Arial;padding:20px}
.card{background:#1e1e2e;padding:15px;margin:12px 0;border-radius:10px;border-left:4px solid orange}
button{background:#00d26a;color:white;border:none;padding:12px 20px;border-radius:8px;font-weight:bold}
input{padding:12px;width:90%;border-radius:8px;border:none;margin:10px 0}</style>
</head><body>
<h2>🔥 Panel Admin AviatorTG</h2>
<p>Numéro marchand: 92 72 70 34</p>
<input id='code' placeholder='Code: 92727034' type='password'>
<button onclick='charger()'>Voir les dépôts</button>
<div id='liste'></div>
<script>
async function charger(){
  const code=document.getElementById('code').value;
  const res=await fetch('/api/admin/depots?code='+code);
  const data=await res.json();
  if(data.error){alert(data.error);return;}
  let html='';
  data.slice().reverse().forEach(d=>{
    if(d.statut=='en_attente'){
      html+=`<div class='card'><b>${d.montant}F</b> - ID: ${d.id_transaction}<br>Tel: ${d.tel_joueur} - ${d.date}<br><br><button onclick='valider(${d.id})'>✅ VALIDER ${d.montant}F</button></div>`;
    }else{
      html+=`<div class='card' style='border-color:green;opacity:0.6'><b>${d.montant}F</b> - ${d.id_transaction} - ✅ Validé</div>`;
    }
  });
  document.getElementById('liste').innerHTML=html||'Aucun dépôt';
}
async function valider(id){
  const code=document.getElementById('code').value;
  if(!confirm('Tu as bien reçu l\\'argent ?')) return;
  const res=await fetch('/api/admin/valider',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id_depot:id,code:code})});
  const data=await res.json();
  if(data.success){alert(data.montant+'F validé !'); charger();} else {alert('Erreur');}
}
</script></body></html>
"""
@app.route('/admin')
def admin_page():
    return render_template_string(ADMIN_HTML)
 HTML = r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aviator TOGO PRO</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
body{background:#0a0c1e;color:#fff}
#header{display:flex;justify-content:space-between;padding:12px;background:#15182e}
.logo{font-weight:900;color:#ff3c00}
#balance{color:#00ff88;font-weight:bold}
#game{height:60vh;background:#0f1230;display:flex;align-items:center;justify-content:center}
#multiplier{font-size:60px;font-weight:900;color:#ff3c00}
#controls{padding:15px;background:#15182e}
.btn{width:100%;padding:15px;border:none;border-radius:10px;font-weight:900;font-size:18px;margin:5px 0}
.btn-depot{background:#ff3c00;color:white}
.btn-bet{background:#00d26a;color:white}
</style>
</head>
<body>
<div id="header"><div class="logo">AVIATOR TG</div><div id="balance">1000 F</div></div>
<div id="game"><div id="multiplier">1.00x</div></div>
<div id="controls">
<button class="btn btn-depot" onclick="faireDepot()">💰 DÉPÔT Flooz / Mixx - 1000F=1000F</button>
<button class="btn btn-bet" onclick="parier()">PARIER 100F</button>
</div>
<script>
let solde = 1000;
function majSolde(){ document.getElementById('balance').innerText = solde + ' F'; }
async function faireDepot(){
  const montant = prompt("Montant à déposer (ex: 1000):");
  if(!montant) return;
  const id_trans = prompt(`Parfait.\n1. Envoie ${montant}F au 92 72 70 34 via Mixx ou Flooz\n2. Entre l'ID de transaction:`);
  if(!id_trans) return;
  const tel = prompt("Ton numéro Mixx/Flooz:");
  const res = await fetch('/api/depot/demande', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({montant: montant, id_transaction: id_trans, telephone: tel})
  });
  const data = await res.json();
  alert(data.message + "\\nTu recevras tes " + montant + "F quand l'admin valide.");
}
function parier(){ alert("Solde: "+solde+"F"); }
let mult=1.00;
setInterval(()=>{ mult+=0.01; if(mult>10) mult=1; document.getElementById('multiplier').innerText=mult.toFixed(2)+'x'; },100);
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)
