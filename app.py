import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

FICHIER = "depots.json"
CODE = "92727034"

def load():
    if os.path.exists(FICHIER):
        try:
            with open(FICHIER, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save(d):
    with open(FICHIER, "w") as f:
        json.dump(d, f)

@app.route("/api/depot/demande", methods=["POST"])
def depot():
    data = request.json
    all_dep = load()
    all_dep.append({
        "id": len(all_dep)+1,
        "montant": data.get("montant"),
        "id_transaction": data.get("id_transaction"),
        "tel": data.get("telephone", "-"),
        "statut": "en_attente",
        "date": datetime.now().strftime("%d/%m %H:%M")
    })
    save(all_dep)
    return jsonify({"success": True})

@app.route("/api/admin/depots")
def list_dep():
    if request.args.get("code") != CODE:
        return jsonify({"error": "code"}), 403
    return jsonify(load())

@app.route("/api/admin/valider", methods=["POST"])
def val():
    data = request.json
    if data.get("code") != CODE:
        return jsonify({"error": "code"}), 403
    deps = load()
    for x in deps:
        if x["id"] == data.get("id_depot"):
            x["statut"] = "valide"
            save(deps)
            return jsonify({"success": True, "montant": x["montant"]})
    return jsonify({"error": "not found"}), 404

@app.route("/admin")
def admin():
    return render_template_string("""
<html><head><meta name='viewport' content='width=device-width'><style>
body{background:#0a0c1e;color:white;font-family:Arial;padding:20px}
.card{background:#1e1e2e;padding:15px;margin:10px 0;border-radius:10px;border-left:4px solid orange}
button{background:#00d26a;color:white;border:none;padding:10px 20px;border-radius:8px}
input{padding:10px;width:90%;border-radius:8px;border:none}
</style></head><body>
<h2>Panel Admin - 92 72 70 34</h2>
<input id='c' placeholder='Code 92727034' type='password'>
<button onclick='loadDep()'>Voir depots</button>
<div id='l'></div>
<script>
async function loadDep(){
 let code=document.getElementById('c').value;
 let r=await fetch('/api/admin/depots?code='+code);
 let d=await r.json();
 let h='';
 d.reverse().forEach(x=>{
  if(x.statut=='en_attente'){h+=`<div class=card><b>${x.montant}F</b> ID:${x.id_transaction}<br>${x.tel} ${x.date}<br><button onclick='v(${x.id})'>VALIDER</button></div>`}
  else{h+=`<div class=card style='border-color:green;opacity:0.6'>${x.montant}F - ${x.id_transaction} OK</div>`}
 });
 document.getElementById('l').innerHTML=h;
}
async function v(id){
 let code=document.getElementById('c').value;
 if(!confirm('Recu sur Mixx/Flooz ?'))return;
 let r=await fetch('/api/admin/valider',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id_depot:id,code:code})});
 let j=await r.json();
 alert(j.montant+'F valide');
 loadDep();
}
</script></body></html>
""")

@app.route("/")
def home():
    return render_template_string("""
<html><head><meta name='viewport' content='width=device-width'><style>
body{background:#0a0c1e;color:white;font-family:Arial;text-align:center;padding:20px}
button{width:90%;padding:15px;margin:10px;border:none;border-radius:10px;font-weight:bold;font-size:18px}
.depot{background:#ff3c00;color:white}
.bet{background:#00d26a;color:white}
.mult{font-size:60px;color:#ff3c00;margin:40px 0}
</style></head><body>
<h1>AVIATOR TG</h1>
<div>1000 F</div>
<div class='mult' id='m'>1.00x</div>
<button class='depot' onclick='depotF()'>DEPOT Flooz/Mixx 1000F=1000F</button>
<button class='bet'>PARIER 100F</button>
<script>
async function depotF(){
 let mo=prompt('Montant:');
 if(!mo)return;
 let idt=prompt('Envoie '+mo+'F au 92 72 70 34 puis entre ID:');
 if(!idt)return;
 let tel=prompt('Ton numero:');
 let r=await fetch('/api/depot/demande',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({montant:mo,id_transaction:idt,telephone:tel})});
 alert('Demande envoyee! Tu recevras '+mo+'F apres validation.');
}
let x=1;setInterval(()=>{x+=0.01;if(x>10)x=1;document.getElementById('m').innerText=x.toFixed(2)+'x'},100);
</script></body></html>
""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
