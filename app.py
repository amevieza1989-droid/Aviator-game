import os, json, time, random, threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
FICHIER="depots.json"; CODE="92727034"

etat={"phase":"waiting","multiplier":1.0,"crash":2.0,"countdown":7.0,"elapsed":0,"history":[2.21,2.31,2.77,1.57,3.15,2.19,1.02],"wait_start":time.time()}
lock=threading.Lock()

def gen_crash():
    r=random.random()
    if r<0.55: return 1+random.random()*1.8
    if r<0.85: return 2+random.random()*3
    if r<0.96: return 5+random.random()*8
    return 10+random.random()*40

def boucle():
    while True:
        with lock:
            now=time.time()
            if etat["phase"]=="flying":
                elapsed=now-etat["start"]
                etat["elapsed"]=elapsed
                etat["multiplier"]=1 + elapsed*0.26 + pow(elapsed,1.8)*0.06
                if etat["multiplier"]>=etat["crash"]:
                    etat["history"]=[round(etat["crash"],2)]+etat["history"][:30]
                    etat["phase"]="crashed"; etat["crash_time"]=now
            elif etat["phase"]=="crashed":
                if now-etat["crash_time"]>1.2:
                    etat["phase"]="waiting"; etat["wait_start"]=now
            elif etat["phase"]=="waiting":
                etat["countdown"]=max(0,7-(now-etat["wait_start"]))
                if now-etat["wait_start"]>=7:
                    etat["crash"]=gen_crash(); etat["phase"]="flying"; etat["start"]=now; etat["multiplier"]=1.0; etat["elapsed"]=0
        time.sleep(0.05)
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

@app.route("/")
def home():
    return render_template_string("""
<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0e1624;color:white;font-family:Arial;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
.top{height:34px;min-height:34px;background:#1a2332;display:flex;gap:6px;padding:0 8px;align-items:center;overflow-x:auto}
.top span{padding:3px 8px;border-radius:10px;font-size:12px}
.main{flex:1;display:flex;overflow:hidden;min-height:0;position:relative}
.left{display:none}
.center{flex:1;position:relative;background:radial-gradient(ellipse at bottom,#1a2a44,#0e1624);overflow:hidden}
canvas{position:absolute;inset:0;width:100%;height:100%}
.mult{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:54px;font-weight:900;text-align:center;z-index:3;line-height:1.1}
.mult small{display:block;font-size:16px;font-weight:400;opacity:0.8;margin-top:6px}
#plane{position:absolute;z-index:4;font-size:32px;will-change:left,top;transform:translate(-50%,-50%)}
.controls{height:250px;min-height:250px;background:#0f172a;padding:8px;display:flex;gap:8px;border-top:2px solid #ff7a00}
.betbox{flex:1;background:#1e2a44;border-radius:12px;padding:8px;display:flex;flex-direction:column;justify-content:space-between;border:1px solid #2a3a5a}
.solde-badge{background:#0a2540;border:1px solid #00d26a;padding:4px 10px;border-radius:20px;font-size:13px;font-weight:bold;color:#00ff88}
.betbox label{font-size:10px;opacity:0.6}.row2{display:flex;gap:6px}.row2>div{flex:1}
.betbox input{width:100%;padding:10px;background:#0e1624;border:1px solid #333;color:white;border-radius:8px;text-align:center;font-size:15px;margin:2px 0}
.btn{width:100%;padding:12px;border:none;border-radius:10px;font-weight:bold;font-size:13px;cursor:pointer;margin-top:4px}.orange{background:#ff7a00;color:white}.green{background:#00d26a;color:white}.red{background:#ff3c00;color:white}
.auto{display:flex;align-items:center;gap:6px;font-size:11px;margin:3px 0;cursor:pointer}.sw{width:32px;height:18px;background:#333;border-radius:10px;position:relative}.sw.on{background:#00d26a}.sw i{position:absolute;top:2px;left:2px;width:14px;height:14px;background:white;border-radius:50%;transition:0.2s}.sw.on i{left:16px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.85);display:none;align-items:center;justify-content:center;z-index:99}.box{background:#1a2332;padding:20px;border-radius:12px;width:90%;max-width:360px}.box input{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:none}
</style></head><body>
<div class="top" id="history"></div>
<div class="main"><div class="center"><canvas id="c"></canvas><div id="plane">✈️</div><div class="mult" id="mult">1.00x</div></div></div>
<div class="controls">
<div class="betbox">
<div style="display:flex;justify-content:space-between;align-items:center"><span class="solde-badge" id="solde">1000F</span><span onclick="openDepot()" style="color:#ff7a00;font-weight:bold;font-size:12px">+ DEPOT</span></div>
<div class="row2"><div><label>Mise</label><input id="mise1" value="100" type="number"></div><div><label>Auto @</label><input id="auto1" value="2.00" type="number" step="0.1"></div></div>
<div class="auto" onclick="toggleAuto(1)"><div class="sw on" id="sw1"><i></i></div> Auto</div>
<button class="btn orange" id="btn1" onclick="parier(1)">PLACER UN PARI</button>
</div>
<div class="betbox">
<div style="display:flex;justify-content:space-between"><span style="font-size:11px;opacity:0.7">Pari 2</span><span style="font-size:11px;color:#00ff88" id="gain2"></span></div>
<div class="row2"><div><label>Mise</label><input id="mise2" value="100" type="number"></div><div><label>Auto @</label><input id="auto2" value="1.20" type="number" step="0.1"></div></div>
<div class="auto" onclick="toggleAuto(2)"><div class="sw on" id="sw2"><i></i></div> Auto</div>
<button class="btn green" id="btn2" onclick="parier(2)">PLACER UN PARI</button>
</div>
</div>
<div class="modal" id="modalDepot"><div class="box"><h3>Depot 92 72 70 34</h3><input id="depMontant" type="number" placeholder="Montant"><input id="depTel" placeholder="Numero"><input id="depId" placeholder="ID"><button class="btn green" onclick="envoyerDepot()">ENVOYER</button><button class="btn" style="background:#333;margin-top:8px" onclick="closeDepot()">FERMER</button></div></div>
<script>
let solde=1000,bet1=0,bet2=0,autoOn1=true,autoOn2=true,curMult=1,curElapsed=0;
let canvas=document.getElementById('c'),ctx=canvas.getContext('2d'),plane=document.getElementById('plane');
function resize(){let r=window.devicePixelRatio||1;canvas.width=canvas.clientWidth*r;canvas.height=canvas.clientHeight*r;ctx.setTransform(r,0,0,r,0,0);}resize();window.onresize=resize;
let multDiv=document.getElementById('mult');

function drawCurve(prog,W,H){
  let pts=[];
  for(let i=0;i<=80;i++){
    let t=i/80*prog; // 0 -> prog (0.9 max)
    let x=W*t;
    // NOUVELLE FORMULE COUCHEE : tres plate au debut, monte doucement
    let y=H - 25 - Math.pow(t,1.7)*H*0.75;
    pts.push([x,y]);
  }
  return pts;
}

async function poll(){
 let r=await fetch('/api/state');let e=await r.json();
 let W=canvas.clientWidth,H=canvas.clientHeight;
 ctx.clearRect(0,0,W,H);
 document.getElementById('history').innerHTML=e.history.map(v=>`<span style="background:${v<2?'#1e2a4a':v<5?'#1e3a2a':'#4a1e1e'};color:${v<2?'#7aa0ff':v<5?'#7aff7a':'#ff7a5a'}">${v.toFixed(2)}x</span>`).join('');

 if(e.phase=="waiting"){
   multDiv.innerHTML=`<span style="color:#ffaa00">EN ATTENTE</span><small>Prochain dans ${e.countdown.toFixed(1)}s</small>`;
   plane.style.display='none';
   document.getElementById('btn1').innerText='PLACER UN PARI';document.getElementById('btn1').className='btn orange';
   document.getElementById('btn2').innerText='PLACER UN PARI';document.getElementById('btn2').className='btn green';
 } else if(e.phase=="crashed"){
   multDiv.innerHTML=`<span style="color:#ff3c00">${e.crash.toFixed(2)}x</span><small>CRASHED</small>`;
   plane.style.display='none';
   let pts=drawCurve(Math.min(e.elapsed/10,0.9),W,H);
   ctx.beginPath();ctx.strokeStyle='#ff3c00';ctx.lineWidth=3;pts.forEach((p,i)=>{if(i==0)ctx.moveTo(p[0],p[1]);else ctx.lineTo(p[0],p[1]);});ctx.stroke();
   if(bet1>0||bet2>0){bet1=0;bet2=0;}
 } else {
   curMult=e.multiplier;curElapsed=e.elapsed;
   multDiv.innerHTML=`<span style="color:${curMult>=2?'#00ff88':'white'}">${curMult.toFixed(2)}x</span>`;
   let prog=Math.min(curElapsed/10,0.92);
   let pts=drawCurve(prog,W,H);
   ctx.beginPath();ctx.strokeStyle='#ff3c00';ctx.lineWidth=3.5;pts.forEach((p,i)=>{if(i==0)ctx.moveTo(p[0],p[1]);else ctx.lineTo(p[0],p[1]);});ctx.stroke();
   ctx.lineTo(pts[pts.length-1][0],H);ctx.lineTo(0,H);ctx.closePath();ctx.fillStyle='rgba(255,60,0,0.12)';ctx.fill();
   let last=pts[pts.length-1];
   plane.style.display='block';plane.style.left=last[0]+'px';plane.style.top=last[1]+'px';
   // rotation selon pente
   if(pts.length>5){let prev=pts[pts.length-6];let ang=Math.atan2(last[1]-prev[1],last[0]-prev[0]);plane.style.transform=`translate(-50%,-50%) rotate(${ang}deg)`;}

   if(bet1>0){let g=Math.floor(bet1*curMult);document.getElementById('btn1').innerText='CASHOUT '+g+'F';document.getElementById('btn1').className='btn red';
     if(autoOn1&&curMult>=parseFloat(document.getElementById('auto1').value)){solde=Math.floor(solde+bet1*curMult);document.getElementById('solde').innerText=solde+'F';bet1=0;}}
   if(bet2>0){let g=Math.floor(bet2*curMult);document.getElementById('btn2').innerText='CASHOUT '+g+'F';document.getElementById('btn2').className='btn red';
     if(autoOn2&&curMult>=parseFloat(document.getElementById('auto2').value)){solde=Math.floor(solde+bet2*curMult);document.getElementById('solde').innerText=solde+'F';bet2=0;}}
 }
}
setInterval(poll,60);

function toggleAuto(n){if(n==1){autoOn1=!autoOn1;document.getElementById('sw1').className='sw '+(autoOn1?'on':'');}else{autoOn2=!autoOn2;document.getElementById('sw2').className='sw '+(autoOn2?'on':'');}}
function parier(n){
  let mise=parseInt(document.getElementById('mise'+n).value);
  if(isNaN(mise)||mise<=0)return;
  if(n==1&&bet1==0){if(solde<mise){alert('Solde insuffisant - Fais DEPOT');return;}solde=Math.floor(solde-mise);bet1=mise;document.getElementById('solde').innerText=solde+'F';}
  else if(n==1&&bet1>0){solde=Math.floor(solde+bet1*curMult);bet1=0;document.getElementById('solde').innerText=solde+'F';document.getElementById('btn1').innerText='PLACER UN PARI';document.getElementById('btn1').className='btn orange';}
  if(n==2&&bet2==0){if(solde<mise){alert('Solde');return;}solde=Math.floor(solde-mise);bet2=mise;document.getElementById('solde').innerText=solde+'F';}
  else if(n==2&&bet2>0){solde=Math.floor(solde+bet2*curMult);bet2=0;document.getElementById('solde').innerText=solde+'F';document.getElementById('btn2').innerText='PLACER UN PARI';document.getElementById('btn2').className='btn green';}
}
function openDepot(){document.getElementById('modalDepot').style.display='flex';}
function closeDepot(){document.getElementById('modalDepot').style.display='none';}
async function envoyerDepot(){let m=document.getElementById('depMontant').value;let t=document.getElementById('depTel').value;let id=document.getElementById('depId').value;if(!m||!t||!id){alert('Remplis tout');return;}await fetch('/api/depot/demande',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({montant:m,telephone:t,id_transaction:id})});alert('Envoye');closeDepot();}
</script></body></html>""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
