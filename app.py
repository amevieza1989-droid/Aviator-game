import os, json, time, random, threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
FICHIER="depots.json"; CODE="92727034"

etat={"multiplier":1.0,"crash":2.5,"playing":True,"start":time.time(),"history":[4.99,19.67,1.04,10.32,15.46,11.32,13.87]}
lock=threading.Lock()

def gen_crash():
    r=random.random()
    if r<0.5: return 1+random.random()*1.5
    if r<0.85: return 1.5+random.random()*4
    if r<0.97: return 5+random.random()*10
    return 10+random.random()*90

def boucle():
    while True:
        with lock:
            if etat["playing"]:
                elapsed=time.time()-etat["start"]
                etat["multiplier"]=1 + elapsed*0.2 + (elapsed**1.8)*0.08
                if etat["multiplier"]>=etat["crash"]:
                    etat["history"]=[round(etat["crash"],2)]+etat["history"][:19]
                    etat["playing"]=False; etat["end_time"]=time.time()
            else:
                if time.time()-etat.get("end_time",0)>3:
                    etat["crash"]=gen_crash(); etat["multiplier"]=1.0; etat["start"]=time.time(); etat["playing"]=True
        time.sleep(0.08)
threading.Thread(target=boucle,daemon=True).start()

def load(): return json.load(open(FICHIER)) if os.path.exists(FICHIER) else []
def save(d): json.dump(d, open(FICHIER,"w"))

@app.route("/api/state")
def state():
    with lock: return jsonify(etat)

@app.route("/api/depot/demande", methods=["POST"])
def depot():
    data=request.json; all_dep=load()
    all_dep.append({"id":len(all_dep)+1,"montant":data.get("montant"),"id_transaction":data.get("id_transaction"),"tel":data.get("telephone"),"statut":"en_attente","date":datetime.now().strftime("%d/%m %H:%M")})
    save(all_dep); return jsonify({"success":True})

@app.route("/api/admin/depots")
def list_dep():
    if request.args.get("code")!=CODE: return jsonify({"error":"code"}),403
    return jsonify(load())

@app.route("/api/admin/valider", methods=["POST"])
def val():
    data=request.json
    if data.get("code")!=CODE: return jsonify({"error":"code"}),403
    deps=load()
    for x in deps:
        if x["id"]==data.get("id_depot"): x["statut"]="valide"; save(deps); return jsonify({"success":True})
    return jsonify({"error":"not found"}),404

@app.route("/admin")
def admin():
    return render_template_string("""
<html><head><meta name='viewport' content='width=device-width'><style>body{background:#0a0c1e;color:white;font-family:Arial;padding:20px}.card{background:#1a1c2e;padding:15px;margin:10px 0;border-radius:10px;border-left:4px solid #ff3c00}button{background:#00d26a;color:white;border:none;padding:12px 20px;border-radius:8px;font-weight:bold}</style></head><body>
<h2>Admin 92727034</h2><input id='c' type='password' placeholder='Code'><button onclick='loadDep()'>Voir</button><div id='l'></div>
<script>
async function loadDep(){let code=document.getElementById('c').value;let r=await fetch('/api/admin/depots?code='+code);let d=await r.json();let h='';d.slice().reverse().forEach(x=>{if(x.statut=='en_attente')h+=`<div class=card><b>${x.montant}F</b> ${x.id_transaction}<br><button onclick='v(${x.id})'>VALIDER</button></div>`});document.getElementById('l').innerHTML=h;}
async function v(id){let code=document.getElementById('c').value;await fetch('/api/admin/valider',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id_depot:id,code:code})});loadDep();}
</script></body></html>""")

@app.route("/")
def home():
    return render_template_string("""
<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#0e1624;color:white;font-family:Arial;overflow:hidden}
.top{height:32px;background:#1a2332;display:flex;gap:8px;padding:0 10px;align-items:center;overflow-x:auto}.top span{padding:2px 8px;border-radius:10px}
.main{display:flex;height:calc(100vh - 32px - 200px)}.left{width:30%;background:#111c2e;overflow-y:auto;padding:5px;font-size:11px}.row{display:flex;justify-content:space-between;padding:6px;border-bottom:1px solid #1a2332}
.center{flex:1;position:relative;background:radial-gradient(ellipse at bottom,#1a2a44,#0e1624);display:flex;align-items:center;justify-content:center}
canvas{position:absolute;inset:0;width:100%;height:100%}.mult{font-size:56px;font-weight:bold;z-index:2}
.controls{background:#1a2332;height:200px;padding:8px;display:flex;gap:8px}.betbox{flex:1;background:#222d44;border-radius:12px;padding:8px;display:flex;flex-direction:column}
.betbox label{font-size:11px;opacity:0.7}.betbox input{width:100%;padding:10px;background:#0e1624;border:1px solid #333;color:white;border-radius:8px;text-align:center;font-size:16px;margin:3px 0}
.row2{display:flex;gap:6px}.row2>div{flex:1}
.btn{width:100%;padding:12px;border:none;border-radius:10px;font-weight:bold;font-size:14px;cursor:pointer;margin-top:4px}.orange{background:#ff7a00;color:white}.green{background:#00d26a;color:white}.red{background:#ff3c00}
.auto-toggle{display:flex;align-items:center;gap:6px;font-size:11px;margin:4px 0}.switch{width:34px;height:18px;background:#333;border-radius:10px;position:relative;cursor:pointer}.switch.on{background:#00d26a}.switch i{position:absolute;top:2px;left:2px;width:14px;height:14px;background:white;border-radius:50%;transition:0.2s}.switch.on i{left:18px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.8);display:none;align-items:center;justify-content:center;z-index:99}.modal .box{background:#1a2332;padding:20px;border-radius:12px;width:90%;max-width:360px}.modal input{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:none}
</style></head><body>
<div class="top" id="history"></div><div class="main"><div class="left" id="players"></div><div class="center"><canvas id="c"></canvas><div class="mult" id="mult">1.00x</div></div></div>

<div class="controls">
<div class="betbox">
<div style="display:flex;justify-content:space-between;font-size:12px"><span>Solde: <b id="solde">1000F</b></span><span onclick="openDepot()" style="color:#ff7a00">+ DEPOT</span></div>
<div class="row2"><div><label>Mise</label><input id="mise1" value="100" type="number"></div><div><label>Auto Cashout</label><input id="auto1" value="2.00" type="number" step="0.1"></div></div>
<div class="auto-toggle" onclick="toggleAuto(1)"><div class="switch on" id="sw1"><i></i></div> Auto Cashout</div>
<button class="btn orange" id="btn1" onclick="parier(1)">PLACER UN PARI</button>
</div>

<div class="betbox">
<div style="font-size:12px">Pari 2</div>
<div class="row2"><div><label>Mise</label><input id="mise2" value="100" type="number"></div><div><label>Auto Cashout</label><input id="auto2" value="3.00" type="number" step="0.1"></div></div>
<div class="auto-toggle" onclick="toggleAuto(2)"><div class="switch on" id="sw2"><i></i></div> Auto Cashout</div>
<button class="btn green" id="btn2" onclick="parier(2)">PLACER UN PARI</button>
</div>
</div>

<div class="modal" id="modalDepot"><div class="box"><h3>Depot</h3><input id="depMontant" type="number" placeholder="Montant"><input id="depTel" placeholder="Numero"><input id="depId" placeholder="ID transaction"><button class="btn green" onclick="envoyerDepot()">J'AI ENVOYE</button><button class="btn" style="background:#333;margin-top:8px" onclick="closeDepot()">ANNULER</button></div></div>

<script>
let solde=1000,bet1=0,bet2=0,autoOn1=true,autoOn2=true,curMult=1,playing=true;
let canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
function resize(){canvas.width=canvas.clientWidth;canvas.height=canvas.clientHeight}window.onresize=resize;resize();

function toggleAuto(n){if(n==1){autoOn1=!autoOn1;document.getElementById('sw1').className='switch '+(autoOn1?'on':'');}else{autoOn2=!autoOn2;document.getElementById('sw2').className='switch '+(autoOn2?'on':'');}}

async function poll(){
 let r=await fetch('/api/state');let e=await r.json();curMult=e.multiplier;playing=e.playing;
 document.getElementById('mult').innerText=curMult.toFixed(2)+'x';
 document.getElementById('mult').style.color=e.playing?(curMult>=2?'#00ff88':'white'):'#ff3c00';
 document.getElementById('history').innerHTML=e.history.map(v=>`<span style="background:${v<2?'#2a2a5a':v<5?'#2a4a2a':'#4a2a1a'};color:${v<2?'#9aa0ff':v<5?'#7aff7a':'#ff9a5a'}">${v.toFixed(2)}x</span>`).join('');
 ctx.clearRect(0,0,canvas.width,canvas.height);ctx.beginPath();ctx.strokeStyle='#ff3c00';ctx.lineWidth=3;
 let progress=e.playing?Math.min(curMult/10,1):1;
 for(let x=0;x<canvas.width*progress;x++){let t=x/canvas.width*5;let y=canvas.height - Math.pow(t,2.2)*60 - t*10;if(y<0)break;if(x==0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.stroke();

 if(!playing){document.getElementById('btn1').innerText='PLACER UN PARI';document.getElementById('btn1').className='btn orange';document.getElementById('btn2').innerText='PLACER UN PARI';document.getElementById('btn2').className='btn green';if(bet1>0||bet2>0){bet1=0;bet2=0;}}
 else{
   if(bet1>0){
     let gain=(bet1*curMult).toFixed(0);document.getElementById('btn1').innerText='CASHOUT '+gain+'F';document.getElementById('btn1').className='btn red';
     if(autoOn1){let target=parseFloat(document.getElementById('auto1').value);if(curMult>=target){solde+=bet1*curMult;document.getElementById('solde').innerText=Math.floor(solde)+'F';bet1=0;document.getElementById('btn1').innerText='GAIN '+gain+'F';}}
   }
   if(bet2>0){
     let gain=(bet2*curMult).toFixed(0);document.getElementById('btn2').innerText='CASHOUT '+gain+'F';document.getElementById('btn2').className='btn red';
     if(autoOn2){let target=parseFloat(document.getElementById('auto2').value);if(curMult>=target){solde+=bet2*curMult;document.getElementById('solde').innerText=Math.floor(solde)+'F';bet2=0;document.getElementById('btn2').innerText='GAIN '+gain+'F';}}
   }
 }
}
setInterval(poll,100);

function parier(n){
 let mise=parseInt(document.getElementById('mise'+n).value);
 if(!playing){alert('Attends le prochain tour');return;}
 if(n==1&&bet1==0){if(solde<mise){alert('Solde insuffisant -> DEPOT');return;}solde-=mise;bet1=mise;document.getElementById('solde').innerText=solde+'F';}
 else if(n==1&&bet1>0){solde+=bet1*curMult;bet1=0;document.getElementById('solde').innerText=Math.floor(solde)+'F';document.getElementById('btn1').innerText='PLACER UN PARI';document.getElementById('btn1').className='btn orange';}
 if(n==2&&bet2==0){if(solde<mise){alert('Solde');return;}solde-=mise;bet2=mise;document.getElementById('solde').innerText=solde+'F';}
 else if(n==2&&bet2>0){solde+=bet2*curMult;bet2=0;document.getElementById('solde').innerText=Math.floor(solde)+'F';document.getElementById('btn2').innerText='PLACER UN PARI';document.getElementById('btn2').className='btn green';}
}
function openDepot(){document.getElementById('modalDepot').style.display='flex';}
function closeDepot(){document.getElementById('modalDepot').style.display='none';}
async function envoyerDepot(){let m=document.getElementById('depMontant').value;let t=document.getElementById('depTel').value;let id=document.getElementById('depId').value;if(!m||!t||!id){alert('Remplis tout');return;}await fetch('/api/depot/demande',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({montant:m,telephone:t,id_transaction:id})});alert('Envoye');closeDepot();}
</script></body></html>""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
