import os
from flask import Flask
from flask_socketio import SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

HTML = r'''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Aviator - Exact Clone</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial, sans-serif}
body{background:#0b0e1a;color:#fff;overflow-x:hidden}
.header{display:flex;justify-content:space-between;padding:8px 10px;background:#151a2e}
.btn-top{padding:6px 16px;border-radius:6px;border:none;font-size:12px;font-weight:700}
.btn-regles{background:#2a2f4a;color:#8b90a8}
.btn-hist{background:#ff7a00;color:#fff}
.game-area{position:relative;height:32vh;background:radial-gradient(at 50% 100%, #1a1f3d 0%, #0b0e1a 70%);overflow:hidden;border-bottom:1px solid #1f2340}
#canvas{position:absolute;left:0;top:0;width:100%;height:100%}
#plane{position:absolute;left:20px;bottom:30px;font-size:22px;z-index:5;transition:all 0.06s linear}
#mult{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:48px;font-weight:900;color:#fff;z-index:4}
#countdown{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:70px;font-weight:900;color:#fff}
.bet-box{background:#1c2340;margin:8px;border-radius:8px;padding:8px;border:1px solid #2a335a}
.bet-row{display:flex;gap:8px;align-items:center}
.input-montant{flex:1;background:#0f1429;border:1px solid #2a335a;color:#fff;padding:10px;border-radius:6px;font-weight:700;font-size:16px;text-align:center;width:70px}
.btn-x{background:transparent;border:none;color:#8b90a8;font-size:18px;padding:0 6px}
.btn-auto{flex:1;background:#2a335a;color:#8b90a8;border:1px solid #3a456a;border-radius:6px;padding:8px;font-size:10px;font-weight:700;text-align:center}
.btn-placer{flex:1;background:#ff7a00;color:#fff;border:none;border-radius:6px;padding:10px;font-weight:900;font-size:13px;box-shadow:0 3px 0 #cc6200}
.btn-placer.cash{background:#00c74d;box-shadow:0 3px 0 #00963a}
.quick-row{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.qbtn{background:#2a335a;color:#c0c6dc;border:1px solid #3a456a;border-radius:16px;padding:5px 14px;font-size:12px;font-weight:700}
.stats-bar{display:flex;justify-content:space-around;background:#151a2e;padding:10px 5px;border-top:1px solid #2a335a;border-bottom:1px solid #2a335a;text-align:center}
.stats-bar div{flex:1}
.stats-bar small{color:#8b90a8;font-size:10px;display:block}
.stats-bar b{color:#ff7a00;font-size:13px}
.table{width:100%;font-size:11px;border-collapse:collapse}
.table th{background:#151a2e;color:#8b90a8;padding:6px;font-size:9px}
.table td{padding:6px;border-bottom:1px solid #1c2340;text-align:center;color:#c0c6dc}
</style>
</head>
<body>
<div class="header"><button class="btn-top btn-regles">Règles</button><button class="btn-top btn-hist">HISTORIQUE</button></div>
<div class="game-area" id="game"><canvas id="canvas"></canvas><div id="plane">✈️</div><div id="mult"></div><div id="countdown"></div></div>

<div class="bet-box" id="box1">
<div class="bet-row"><input class="input-montant" id="amt1" value="300"><button class="btn-x">X</button><div class="btn-auto">ACTIVER LE JEU AUTOMATIQUE</div><button class="btn-placer" id="btn1" onclick="place(0)">PLACER UN PARI</button></div>
<div class="quick-row"><button class="qbtn" onclick="setAmt(0,200)">200</button><button class="qbtn" onclick="setAmt(0,700)">700</button><button class="qbtn" onclick="setAmt(0,2000)">2000</button><button class="qbtn" onclick="setAmt(0,6000)">6000</button><button class="qbtn" onclick="setAmt(0,20000)">20000</button><button class="qbtn" onclick="setAmt(0,70000)">70000</button></div>
</div>

<div class="bet-box" id="box2">
<div class="bet-row"><input class="input-montant" id="amt2" value="300"><button class="btn-x">X</button><div class="btn-auto">ACTIVER LE JEU AUTOMATIQUE</div><button class="btn-placer" id="btn2" onclick="place(1)">PLACER UN PARI</button></div>
<div class="quick-row"><button class="qbtn" onclick="setAmt(1,200)">200</button><button class="qbtn" onclick="setAmt(1,700)">700</button><button class="qbtn" onclick="setAmt(1,2000)">2000</button><button class="qbtn" onclick="setAmt(1,6000)">6000</button><button class="qbtn" onclick="setAmt(1,20000)">20000</button><button class="qbtn" onclick="setAmt(1,70000)">70000</button></div>
</div>

<div class="stats-bar">
<div><small>Nombre de paris</small><b id="nb">0</b></div>
<div><small>Total des paris XOF</small><b id="tot">0</b></div>
<div><small>Gains totaux XOF</small><b id="gain">0</b></div>
</div>
<table class="table" id="plist">
<tr><th>NOM D'UTILISATE...</th><th>COTE</th><th>PARI</th><th>GAIN</th></tr>
</table>

<script>
const canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d'),multEl=document.getElementById('mult'),cdEl=document.getElementById('countdown'),planeEl=document.getElementById('plane'),game=document.getElementById('game');
let mult=1,crash=0,flying=false,count=5,timer=null,pts=[],balance=100000;
let bets=[{active:false,cashed:false,amt:300},{active:false,cashed:false,amt:300}];
let fakePlayers=[];

function resize(){canvas.width=canvas.offsetWidth*2;canvas.height=canvas.offsetHeight*2;}window.addEventListener('resize',resize);resize();
function randCrash(){let r=Math.random();if(r<0.3)return +(Math.random()*0.5+1).toFixed(2);if(r<0.7)return +(Math.random()*1.5+1).toFixed(2);if(r<0.9)return +(Math.random()*5+2).toFixed(2);return +(Math.random()*20+5).toFixed(2);}
function genPlayers(){
  const names=["****12","****45","****78","****23","****91","****34","****56","****88"];
  fakePlayers=names.map(n=>({name:n,bet:Math.floor(Math.random()*10000+200),cash:0,active:true}));
  updateTable();
}
function updateTable(){
  let html='<tr><th>NOM D\'UTILISATE...</th><th>COTE</th><th>PARI</th><th>GAIN</th></tr>';
  let nb=fakePlayers.length, tot=0, gains=0;
  fakePlayers.forEach(p=>{
    let cote = flying? (p.cash>0? p.cash.toFixed(2)+'x' : 'x0') : 'x0';
    let gain = p.cash>0? Math.floor(p.bet*p.cash)+' XOF' : '0 XOF';
    if(flying && Math.random()<0.02 && p.cash==0){p.cash=mult; p.active=false;}
    tot+=p.bet; if(p.cash>0) gains+=Math.floor(p.bet*p.cash);
    html+=`<tr><td>${p.name}</td><td>${cote}</td><td>${p.bet} XOF</td><td style="color:${p.cash>0?'#00ff7a':''}">${gain}</td></tr>`;
  });
  document.getElementById('nb').textContent=nb;
  document.getElementById('tot').textContent=tot.toLocaleString();
  document.getElementById('gain').textContent=gains.toLocaleString();
  document.getElementById('plist').innerHTML=html;
}

function countdown(){
  genPlayers(); cdEl.style.display='block'; multEl.textContent=''; pts=[];
  count=5; cdEl.textContent=count;
  let cd=setInterval(()=>{
    count--; if(count>0){cdEl.textContent=count;} else {clearInterval(cd); cdEl.style.display='none'; startRound();}
  },1000);
}

function startRound(){
  flying=true; mult=1; crash=randCrash(); pts=[{x:0,y:canvas.height-40}];
  bets.forEach((b,i)=>{let btn=document.getElementById('btn'+(i+1)); if(b.active){btn.className='btn-placer cash'; btn.textContent='RETRAIT'; b.cashed=false;}});
  clearInterval(timer);
  timer=setInterval(()=>{
    mult+=0.008+mult*0.008;
    if(mult>=crash){doCrash();return;}
    multEl.textContent=mult.toFixed(2)+'x';
    multEl.style.color=mult<2?'#fff':'#00ff7a';
    let w=canvas.width,h=canvas.height; let p=mult/crash;
    let x=Math.pow(p,0.7)*(w*0.85); let y=h - (Math.pow(p,1.2)*h*0.6 + 40);
    pts.push({x,y}); if(pts.length>120)pts.shift();
    ctx.clearRect(0,0,w,h);
    ctx.beginPath(); ctx.moveTo(0,h-40);
    pts.forEach(pt=>ctx.lineTo(pt.x,pt.y));
    ctx.strokeStyle='#ff3b00'; ctx.lineWidth=5; ctx.lineCap='round'; ctx.stroke();
    ctx.lineTo(x,h-40); ctx.closePath(); ctx.fillStyle='rgba(255,90,0,0.15)'; ctx.fill();
    planeEl.style.left=(x/2-10)+'px'; planeEl.style.top=(y/2-20)+'px';
    planeEl.style.transform='rotate('+( -10 - p*20)+'deg)';
    bets.forEach((b,i)=>{if(b.active&&!b.cashed){let btn=document.getElementById('btn'+(i+1)); btn.textContent=(Math.floor(b.amt*mult))+' XOF');}});
    updateTable();
  },50);
}

function doCrash(){
  clearInterval(timer); flying=false;
  multEl.textContent=crash.toFixed(2)+'x'; multEl.style.color='#ff3b3b';
  planeEl.style.opacity='0.2';
  ctx.clearRect(0,0,canvas.width,canvas.height);
  bets.forEach((b,i)=>{let btn=document.getElementById('btn'+(i+1)); if(b.active&&!b.cashed){btn.className='btn-placer'; btn.textContent='PLACER UN PARI'; b.active=false;} else if(b.active&&b.cashed){btn.className='btn-placer'; btn.textContent='PLACER UN PARI'; b.active=false;}});
  setTimeout(()=>{planeEl.style.opacity='1'; countdown();},3000);
}

function setAmt(idx,val){document.getElementById('amt'+(idx+1)).value=val; bets[idx].amt=val;}
function place(idx){
  let amt=parseInt(document.getElementById('amt'+(idx+1)).value)||300;
  let b=bets[idx], btn=document.getElementById('btn'+(idx+1));
  if(!b.active){
    b.amt=amt; b.active=true; b.cashed=false; btn.className='btn-placer'; btn.textContent=flying?'EN ATTENTE...':'PARI PLACÉ'; if(flying){btn.className='btn-placer cash'; btn.textContent='RETRAIT';}
  }else{
    if(!flying||b.cashed)return; let gain=Math.floor(b.amt*mult); b.cashed=true; btn.className='btn-placer'; btn.textContent='GAGNÉ '+gain; setTimeout(()=>{b.active=false; btn.textContent='PLACER UN PARI';},1500);
  }
}
countdown();
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
