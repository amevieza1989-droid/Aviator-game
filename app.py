import os, json
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
.card{background:#1a1c2e;padding:15px;margin:10px 0;border-radius:10px;border-left:4px solid #ff3c00}
button{background:#00d26a;color:white;border:none;padding:12px 20px;border-radius:8px;font-weight:bold;cursor:pointer}
input{padding:12px;width:90%;border-radius:8px;border:none;margin:5px 0}
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
 if(d.error){alert('Mauvais code');return;}
 let h='';
 d.slice().reverse().forEach(x=>{
  if(x.statut=='en_attente'){h+=`<div class=card><b>${x.montant}F</b> - ID:${x.id_transaction}<br>${x.tel} ${x.date}<br><button onclick='v(${x.id})'>VALIDER - Recu Mixx/Flooz ?</button></div>`}
  else{h+=`<div class=card style='border-color:green;opacity:0.6'>${x.montant}F - ${x.id_transaction} ✅ VALIDE</div>`}
 });
 document.getElementById('l').innerHTML=h||'Aucun depot';
}
async function v(id){
 let code=document.getElementById('c').value;
 if(!confirm('Tu as bien recu l argent sur Mixx / Flooz ?'))return;
 let r=await fetch('/api/admin/valider',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id_depot:id,code:code})});
 let j=await r.json();
 alert(j.montant+'F valide !');
 loadDep();
}
</script></body></html>
""")

@app.route("/")
def home():
    return render_template_string("""
<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#0e1624;color:white;font-family:Arial;overflow:hidden}
.top{height:32px;background:#1a2332;display:flex;align-items:center;gap:8px;padding:0 10px;font-size:12px;overflow-x:auto;white-space:nowrap}
.top span{padding:2px 8px;border-radius:10px}
.main{display:flex;height:calc(100vh - 32px - 180px)}
.left{width:30%;background:#111c2e;border-right:1px solid #222;overflow-y:auto;padding:5px;font-size:11px}
.row{display:flex;justify-content:space-between;padding:6px;border-bottom:1px solid #1a2332}
.center{flex:1;position:relative;background:radial-gradient(ellipse at bottom,#1a2a44,#0e1624);display:flex;align-items:center;justify-content:center}
canvas{position:absolute;inset:0;width:100%;height:100%}
.mult{font-size:56px;font-weight:bold;z-index:2}
.controls{background:#1a2332;height:180px;padding:10px;display:flex;gap:10px}
.betbox{flex:1;background:#222d44;border-radius:12px;padding:10px}
.betbox input{width:100%;padding:12px;background:#0e1624;border:1px solid #333;color:white;border-radius:8px;text-align:center;font-size:18px;margin:6px 0}
.btn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:bold;font-size:16px;cursor:pointer}
.orange{background:#ff7a00;color:white}
.green{background:#00d26a;color:white}
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.8);display:none;align-items:center;justify-content:center;z-index:99}
.modal .box{background:#1a2332;padding:20px;border-radius:12px;width:90%;max-width:360px}
.modal input{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:none}
</style></head><body>
<div class="top" id="history"></div>
<div class="main">
<div class="left" id="players"></div>
<div class="center"><canvas id="c"></canvas><div class="mult" id="mult">1.00x</div></div>
</div>
<div class="controls">
<div class="betbox">
<div style="display:flex;justify-content:space-between;font-size:12px"><span>Solde: <b id="solde">1000F</b></span><span onclick="openDepot()" style="color:#ff7a00;cursor:pointer">+ DEPOT</span></div>
<input id="mise1" value="100"><button class="btn orange" id="btn1" onclick="parier(1)">PLACER UN PARI</button>
</div>
<div class="betbox">
<div style="font-size:12px">Auto Cashout</div>
<input id="mise2" value="100"><button class="btn green" id="btn2" onclick="parier(2)">PLACER UN PARI</button>
</div>
</div>

<div class="modal" id="modalDepot">
<div class="box">
<h3>Depot Wave/CFA</h3><p style="font-size:12px;opacity:0.7;margin:6px 0">Envoie au 92 72 70 34 (Flooz/Mixx)</p>
<input id="depMontant" type="number" placeholder="Montant ex: 2000">
<input id="depTel" placeholder="Ton numero">
<input id="depId" placeholder="ID transaction apres envoi">
<button class="btn green" onclick="envoyerDepot()">J'AI ENVOYE</button>
<button class="btn" style="background:#333;margin-top:8px" onclick="closeDepot()">ANNULER</button>
</div>
</div>

<script>
let solde=1000;
let crash=0,m=1,playing=false,bet1=0,bet2=0;
let canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
function resize(){canvas.width=canvas.clientWidth;canvas.height=canvas.clientHeight}window.onresize=resize;resize();
let hist=[2.34,1.12,5.67,1.05,12.81,3.44,1.99];
function drawHistory(){
 let h=document.getElementById('history');
 h.innerHTML=hist.map(v=>`<span style="background:${v<2?'#2a2a5a':v<5?'#2a4a2a':'#4a2a1a'};color:${v<2?'#9aa0ff':v<5?'#7aff7a':'#ff9a5a'}">${v.toFixed(2)}x</span>`).join('');
}
drawHistory();
let playersList=["Momo*12","Aviateur*77","TG*92","Boss*34","Lomé*01","Koffi*","Aya*"];
function drawPlayers(){
 let p=document.getElementById('players');
 let rows=playersList.map(n=>{let mise=Math.floor(Math.random()*900+100);let mult=(Math.random()*5+1.1).toFixed(2);return `<div class=row><span>${n}</span><span>${mise}F</span><span style="color:#00d26a">${mult}x</span></div>`}).join('');
 p.innerHTML=rows;
}
setInterval(drawPlayers,2000);drawPlayers();

function gameLoop(){
 if(!playing){
   m=1; crash=Math.random()<0.1? (1+Math.random()*0.9) : (1+Math.random()*20);
   if(Math.random()<0.05) crash=50+Math.random()*50;
   playing=true;
 }
 m+=0.02+m*0.008;
 document.getElementById('mult').innerText=m.toFixed(2)+'x';
 document.getElementById('mult').style.color=m>=2?'#00ff88':m>=10?'#ffaa00':'white';
 // draw curve
 ctx.clearRect(0,0,canvas.width,canvas.height);
 ctx.beginPath();ctx.strokeStyle='#ff3c00';ctx.lineWidth=3;
 for(let x=0;x<canvas.width;x++){let t=x/canvas.width*5;let y=canvas.height - Math.pow(t,2.2)*60 - t*10; if(y<0)break; if(x==0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.stroke();
 ctx.lineTo(canvas.width,canvas.height);ctx.lineTo(0,canvas.height);ctx.closePath();ctx.fillStyle='rgba(255,60,0,0.15)';ctx.fill();
 if(m>=crash){
   document.getElementById('mult').innerText=crash.toFixed(2)+'x';document.getElementById('mult').style.color='#ff3c00';
   playing=false; hist.unshift(crash); if(hist.length>20)hist.pop(); drawHistory();
   bet1=0;bet2=0; document.getElementById('btn1').innerText='PLACER UN PARI';document.getElementById('btn2').innerText='PLACER UN PARI';
   setTimeout(()=>{document.getElementById('mult').innerText='1.00x';},1500);
 }
}
setInterval(gameLoop,80);

function parier(n){
 let mise=parseInt(document.getElementById('mise'+n).value);
 if(n==1 && bet1==0){if(solde<mise){alert('Solde insuffisant, fais un depot');return;} solde-=mise;bet1=mise;document.getElementById('btn1').innerText='CASHOUT '+(mise*m).toFixed(0)+'F';document.getElementById('solde').innerText=solde+'F';}
 else if(n==1 && bet1>0){let gain=bet1*m;solde+=gain;bet1=0;document.getElementById('btn1').innerText='PLACER UN PARI';document.getElementById('solde').innerText=solde+'F';}
 if(n==2 && bet2==0){if(solde<mise){alert('Solde insuffisant');return;} solde-=mise;bet2=mise;document.getElementById('btn2').innerText='CASHOUT';document.getElementById('solde').innerText=solde+'F';}
 else if(n==2 && bet2>0){let gain=bet2*m;solde+=gain;bet2=0;document.getElementById('btn2').innerText='PLACER UN PARI';document.getElementById('solde').innerText=solde+'F';}
}

function openDepot(){document.getElementById('modalDepot').style.display='flex';}
function closeDepot(){document.getElementById('modalDepot').style.display='none';}
async function envoyerDepot(){
 let montant=document.getElementById('depMontant').value;
 let tel=document.getElementById('depTel').value;
 let idt=document.getElementById('depId').value;
 if(!montant||!tel||!idt){alert('Remplis tout: montant, numero, ID transaction');return;}
 let r=await fetch('/api/depot/demande',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({montant:montant,telephone:tel,id_transaction:idt})});
 let j=await r.json();
 alert('Demande envoyee ! Tu recevras '+montant+'F des que je valide sur /admin');
 closeDepot();
}
</script></body></html>
""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
