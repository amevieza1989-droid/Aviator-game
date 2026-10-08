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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aviator FINAL</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
body{background:#0a0e1f;color:#fff}
#hist{display:flex;gap:5px;padding:6px;background:#151a33;overflow-x:auto}
.pill{padding:3px 9px;border-radius:12px;font-size:11px;font-weight:700}
.b{color:#8a90b0;background:#1e2445}.g{color:#00ff88;background:#0e2a1e}.o{color:#ff9a00;background:#2e1e0a}.p{color:#c47cff;background:#2a1450}
#game{position:relative;height:46vh;background:#080d21}
#cv{width:100%;height:100%;display:block}
#center{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none}
#mult{font-size:48px;font-weight:900}#msg{font-size:12px;color:#8a90b0;margin-top:4px}
.box{background:#1c2340;margin:6px;border-radius:8px;padding:8px;border:1px solid #2a3560}
.row{display:flex;gap:6px;align-items:center}
.inp{width:75px;background:#0f1429;border:1px solid #2a3560;color:#fff;padding:9px;border-radius:6px;text-align:center;font-weight:700}
.bx{flex:1;background:#2a3560;color:#8a90b0;border:none;padding:8px;border-radius:6px;font-size:10px}
.bo{flex:1;background:#ff7a00;color:#fff;border:none;padding:11px;border-radius:6px;font-weight:900}
.bo.cash{background:#00c853}
.qrow{display:flex;gap:5px;margin-top:6px}
.qrow button{background:#252e55;color:#c0c8e0;border:1px solid #33406e;border-radius:15px;padding:4px 10px;font-size:11px}
</style>
</head>
<body>
<div id="hist"></div>
<div id="game"><canvas id="cv"></canvas><div id="center"><div id="mult">1.00x</div><div id="msg"></div></div></div>

<div class="box"><div class="row"><input class="inp" id="a1" value="300"><span>X</span><button class="bx">AUTO</button><button class="bo" id="b1" onclick="doBet(0)">PLACER UN PARI</button></div><div class="qrow"><button onclick="setA(0,200)">200</button><button onclick="setA(0,700)">700</button><button onclick="setA(0,2000)">2000</button><button onclick="setA(0,6000)">6000</button><button onclick="setA(0,20000)">20000</button><button onclick="setA(0,70000)">70000</button></div></div>
<div class="box"><div class="row"><input class="inp" id="a2" value="300"><span>X</span><button class="bx">AUTO</button><button class="bo" id="b2" onclick="doBet(1)">PLACER UN PARI</button></div><div class="qrow"><button onclick="setA(1,200)">200</button><button onclick="setA(1,700)">700</button><button onclick="setA(1,2000)">2000</button><button onclick="setA(1,6000)">6000</button><button onclick="setA(1,20000)">20000</button><button onclick="setA(1,70000)">70000</button></div></div>

<script>
let cv=document.getElementById('cv'),ctx=cv.getContext('2d'),histE=document.getElementById('hist'),multE=document.getElementById('mult'),msgE=document.getElementById('msg');
let W,H,mult=1,crash=2,flying=false,timer,pts=[],prog=0,history=[],bets=[{on:false,cash:false,amt:300},{on:false,cash:false,amt:300}];

function resize(){W=cv.width=cv.offsetWidth*2;H=cv.height=cv.offsetHeight*2;}window.onresize=resize;resize();
function randCrash(){let r=Math.random();if(r<0.15)return 1+Math.random()*0.3;if(r<0.5)return 1.1+Math.random()*1;if(r<0.8)return 2+Math.random()*4;return 6+Math.random()*40;}
function addHist(v){history.unshift(v);if(history.length>25)history.pop();histE.innerHTML='';history.forEach(val=>{let d=document.createElement('div');let cl='b';if(val>=2&&val<10)cl='g';else if(val>=10&&val<50)cl='o';else if(val>=50)cl='p';d.className='pill '+cl;d.innerText=val.toFixed(2)+'x';histE.appendChild(d);});}

function drawFrame(x,y){
 ctx.clearRect(0,0,W,H);
 // grid
 ctx.strokeStyle='rgba(255,255,255,0.04)';ctx.lineWidth=1;
 for(let gx=0;gx<W;gx+=100){ctx.beginPath();ctx.moveTo(gx,0);ctx.lineTo(gx,H);ctx.stroke();}
 for(let gy=0;gy<H;gy+=100){ctx.beginPath();ctx.moveTo(0,gy);ctx.lineTo(W,gy);ctx.stroke();}
 // curve
 if(pts.length>1){
  ctx.beginPath();ctx.moveTo(0,H-20);pts.forEach(p=>ctx.lineTo(p.x,p.y));
  ctx.strokeStyle='#ff3c00';ctx.lineWidth=6;ctx.lineJoin='round';ctx.lineCap='round';ctx.stroke();
  ctx.lineTo(x,H-20);ctx.closePath();ctx.fillStyle='rgba(255,60,0,0.18)';ctx.fill();
 }
 // plane - single
 if(flying){
  ctx.save();ctx.translate(x,y);ctx.rotate(-0.4 - prog*0.3);
  ctx.font='36px Arial';ctx.fillText('✈️',-18,-4);ctx.restore();
 }
}

function countdown(){
 flying=false;prog=0;pts=[];drawFrame(0,H-20);
 multE.innerText='';msgE.innerText='';
 let c=3;multE.innerText=c+'s';msgE.innerText='Prochain tour dans...';
 let cd=setInterval(()=>{c--;if(c>0)multE.innerText=c+'s';else{clearInterval(cd);launch();}},1000);
}
function launch(){
 flying=true;mult=1;crash=randCrash();prog=0;pts=[{x:0,y:H-20}];
 bets.forEach((b,i)=>{let btn=document.getElementById('b'+(i+1));if(b.on){b.cash=false;btn.className='bo cash';btn.innerText='RETRAIT '+Math.floor(b.amt*mult)+' XOF';}});
 clearInterval(timer);
 timer=setInterval(()=>{
  prog+=0.009;
  mult+=0.012 + mult*0.013;
  if(mult>=crash){crashNow();return;}
  multE.innerText=mult.toFixed(2)+'x';multE.style.color=mult<2?'#fff':'#00ff88';msgE.innerText='';
  let x=prog*W*0.88;
  let y=H-20 - Math.pow(prog,1.45)*H*0.78;
  if(y<20) y=20;
  pts.push({x,y});if(pts.length>120)pts.shift();
  drawFrame(x,y);
  bets.forEach((b,i)=>{if(b.on&&!b.cash){document.getElementById('b'+(i+1)).innerText=Math.floor(b.amt*mult)+' XOF';}});
 },45);
}
function crashNow(){
 clearInterval(timer);flying=false;
 multE.innerText=crash.toFixed(2)+'x';multE.style.color='#ff2a2a';msgE.innerText="S'EST ENVOLÉ!";
 drawFrame(0,0);addHist(crash);
 bets.forEach((b,i)=>{let btn=document.getElementById('b'+(i+1));if(b.on){btn.className='bo';btn.innerText='PLACER UN PARI';b.on=false;}});
 setTimeout(countdown,3000);
}
function setA(i,v){document.getElementById('a'+(i+1)).value=v;bets[i].amt=v;}
function doBet(i){
 let amt=parseInt(document.getElementById('a'+(i+1)).value)||300;let b=bets[i],btn=document.getElementById('b'+(i+1));
 if(!b.on){b.amt=amt;b.on=true;b.cash=false;if(flying){btn.className='bo cash';btn.innerText='RETRAIT '+Math.floor(amt*mult)+' XOF';}else{btn.innerText='PARI PLACÉ - ATTENTE';}}
 else{if(!flying||b.cash)return;let gain=Math.floor(b.amt*mult);b.cash=true;btn.className='bo';btn.innerText='GAGNÉ '+gain+' XOF';setTimeout(()=>{b.on=false;btn.innerText='PLACER UN PARI';},1200);}
}
[1.24,2.5,1.08,8.12,1.92,15.3,3.4,1.12].forEach(v=>addHist(v));
countdown();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML

if __name__=='__main__':
    port=int(os.environ.get('PORT',10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
