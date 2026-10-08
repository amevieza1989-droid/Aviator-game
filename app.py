import os
from flask import Flask
from flask_socketio import SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

HTML = r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Aviator Clean</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
body{background:#0a0e1f;color:#fff;overflow:hidden}
.top-hist{display:flex;gap:6px;padding:8px;background:#151a33;overflow-x:auto;border-bottom:1px solid #232a55}
.pill{padding:4px 10px;border-radius:15px;font-size:12px;font-weight:700;min-width:48px;text-align:center}
.pill.b{color:#8a90b0;background:#1e2445}
.pill.g{color:#00ff88;background:#0e2a1e}
.pill.o{color:#ff9a00;background:#2e1e0a}
.pill.p{color:#c47cff;background:#2a1450}
#game{position:relative;height:45vh;background:#0b0f25;overflow:hidden}
#cv{position:absolute;left:0;top:0;width:100%;height:100%}
#plane{position:absolute;left:0;bottom:10px;font-size:28px;z-index:10;will-change:left,top}
#mult{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:54px;font-weight:900;z-index:5}
#msg{position:absolute;left:50%;top:62%;transform:translate(-50%,-50%);font-size:14px;color:#8a90b0;z-index:5}
.box{background:#1c2340;margin:6px;border-radius:8px;padding:8px;border:1px solid #2a3560}
.row{display:flex;gap:6px;align-items:center}
.inp{width:80px;background:#0f1429;border:1px solid #2a3560;color:#fff;padding:10px;border-radius:6px;text-align:center;font-weight:700;font-size:16px}
.bx{flex:1;background:#2a3560;color:#8a90b0;border:none;padding:8px;border-radius:6px;font-size:10px;font-weight:700}
.bo{flex:1;background:#ff7a00;color:#fff;border:none;padding:11px;border-radius:6px;font-weight:900;font-size:13px}
.bo.cash{background:#00c853;animation:pulse 0.6s infinite}
@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.03)}100%{transform:scale(1)}}
.qrow{display:flex;gap:5px;margin-top:7px;flex-wrap:wrap}
.qrow button{background:#252e55;color:#c0c8e0;border:1px solid #33406e;border-radius:15px;padding:5px 12px;font-size:11px;font-weight:700}
</style>
</head>
<body>
<div class="top-hist" id="hist"></div>
<div id="game"><canvas id="cv"></canvas><div id="plane">✈️</div><div id="mult">1.00x</div><div id="msg">En attente du prochain tour</div></div>

<div class="box">
<div class="row"><input class="inp" id="a1" value="300"><span style="color:#8a90b0">X</span><button class="bx">AUTO</button><button class="bo" id="b1" onclick="doBet(0)">PLACER UN PARI</button></div>
<div class="qrow"><button onclick="setA(0,200)">200</button><button onclick="setA(0,700)">700</button><button onclick="setA(0,2000)">2000</button><button onclick="setA(0,6000)">6000</button><button onclick="setA(0,20000)">20000</button><button onclick="setA(0,70000)">70000</button></div>
</div>

<div class="box">
<div class="row"><input class="inp" id="a2" value="300"><span style="color:#8a90b0">X</span><button class="bx">AUTO</button><button class="bo" id="b2" onclick="doBet(1)">PLACER UN PARI</button></div>
<div class="qrow"><button onclick="setA(1,200)">200</button><button onclick="setA(1,700)">700</button><button onclick="setA(1,2000)">2000</button><button onclick="setA(1,6000)">6000</button><button onclick="setA(1,20000)">20000</button><button onclick="setA(1,70000)">70000</button></div>
</div>

<script>
let cv=document.getElementById('cv'),ctx=cv.getContext('2d'),hist=document.getElementById('hist'),multE=document.getElementById('mult'),msgE=document.getElementById('msg'),plane=document.getElementById('plane');
let mult=1,crash=0,flying=false,timer=null,pts=[],history=[],bets=[{on:false,cash:false,amt:300},{on:false,cash:false,amt:300}];

function resize(){cv.width=cv.offsetWidth*2;cv.height=cv.offsetHeight*2;}window.onresize=resize;resize();

function randCrash(){
 let r=Math.random();
 if(r<0.08) return +(Math.random()*0.3+1).toFixed(2);
 if(r<0.35) return +(Math.random()*0.9+1).toFixed(2);
 if(r<0.70) return +(Math.random()*2+1.5).toFixed(2);
 if(r<0.90) return +(Math.random()*6+3).toFixed(2);
 return +(Math.random()*50+8).toFixed(2);
}
function addHist(v){
 history.unshift(v); if(history.length>20) history.pop();
 hist.innerHTML='';
 history.forEach(val=>{
  let d=document.createElement('div'); let cls='b';
  if(val>=2 && val<10) cls='g'; else if(val>=10 && val<50) cls='o'; else if(val>=50) cls='p';
  d.className='pill '+cls; d.innerText=val.toFixed(2)+'x'; hist.appendChild(d);
 });
}

function startCountdown(){
 flying=false; mult=1; pts=[]; ctx.clearRect(0,0,cv.width,cv.height);
 plane.style.left='0px'; plane.style.bottom='10px'; plane.style.top='auto'; plane.style.opacity='1';
 multE.innerText='1.00x'; multE.style.color='#fff'; msgE.innerText='Prochain tour dans...';
 let c=3; multE.innerText=c+'s';
 let cd=setInterval(()=>{
  c--; if(c>0){multE.innerText=c+'s';} else {clearInterval(cd); msgE.innerText=''; launch();}
 },1000);
}

function launch(){
 flying=true; crash=randCrash(); pts=[{x:0,y:cv.height}]; // start at bottom left
 clearInterval(timer);
 timer=setInterval(()=>{
  mult+=0.01 + mult*0.011;
  if(mult>=crash){crashNow();return;}
  multE.innerText=mult.toFixed(2)+'x';
  if(mult>=1.5) multE.style.color='#00ff88'; else multE.style.color='#fff';

  let w=cv.width, h=cv.height;
  let prog=Math.min(mult/crash,1);
  let x = Math.pow(prog,0.8) * (w*0.88);
  let y = h - (Math.pow(prog,1.35) * h*0.75 + 20);
  pts.push({x,y}); if(pts.length>100) pts.shift();

  ctx.clearRect(0,0,w,h);
  ctx.beginPath(); ctx.moveTo(0,h);
  pts.forEach(p=>ctx.lineTo(p.x,p.y));
  ctx.strokeStyle='#ff3c00'; ctx.lineWidth=4; ctx.lineJoin='round'; ctx.stroke();
  ctx.lineTo(x,h); ctx.closePath(); ctx.fillStyle='rgba(255,60,0,0.18)'; ctx.fill();

  plane.style.left=(x/2)+'px';
  plane.style.top=(y/2)+'px';
  plane.style.bottom='auto';

  bets.forEach((b,i)=>{
   if(b.on &&!b.cash){
    let btn=document.getElementById('b'+(i+1));
    btn.innerText=Math.floor(b.amt*mult)+' XOF';
   }
  });
 },55);
}

function crashNow(){
 clearInterval(timer); flying=false;
 multE.innerText=crash.toFixed(2)+'x'; multE.style.color='#ff3b3b';
 msgE.innerText="S'EST ENVOLÉ!"; msgE.style.color='#ff3b3b';
 plane.style.opacity='0';
 addHist(crash);
 bets.forEach((b,i)=>{
  let btn=document.getElementById('b'+(i+1));
  if(b.on &&!b.cash){btn.className='bo'; btn.innerText='PLACER UN PARI'; b.on=false;}
  else if(b.on && b.cash){btn.className='bo'; btn.innerText='PLACER UN PARI'; b.on=false;}
 });
 setTimeout(startCountdown,2500);
}

function setA(i,v){document.getElementById('a'+(i+1)).value=v; bets[i].amt=v;}
function doBet(i){
 let amt=parseInt(document.getElementById('a'+(i+1)).value)||300;
 let b=bets[i], btn=document.getElementById('b'+(i+1));
 if(!b.on){
  b.amt=amt; b.on=true; b.cash=false;
  if(flying){btn.className='bo cash'; btn.innerText='RETRAIT '+Math.floor(amt*mult)+' XOF';}
  else{btn.className='bo'; btn.innerText='PARI PLACÉ - ATTENTE';}
 }else{
  if(!flying || b.cash) return;
  let gain=Math.floor(b.amt*mult);
  b.cash=true; btn.className='bo'; btn.innerText='GAGNÉ '+gain+' XOF';
 }
}

[1.42,2.31,1.08,5.22,1.93,12.4,3.11,1.05].forEach(v=>addHist(v));
startCountdown();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML

if __name__ == '__main__':
    port=int(os.environ.get('PORT',10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
