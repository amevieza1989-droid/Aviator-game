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
<title>Aviator</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
body{background:#0a0e1f;color:#fff}
.top{display:flex;justify-content:space-between;padding:8px;background:#151a33}
.b1{background:#2a2f55;color:#8a90b0;border:none;padding:6px 14px;border-radius:6px;font-weight:700}
.b2{background:#ff7a00;color:#fff;border:none;padding:6px 14px;border-radius:6px;font-weight:700}
#game{position:relative;height:38vh;background:linear-gradient(180deg,#151a33,#0a0e1f);overflow:hidden}
#canvas{position:absolute;left:0;top:0;width:100%;height:100%}
#plane{position:absolute;left:10px;bottom:20px;font-size:26px;z-index:9}
#mult{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:52px;font-weight:900;z-index:8}
#cd{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:70px;font-weight:900;z-index:8}
.box{background:#1c2340;margin:6px;border-radius:8px;padding:8px;border:1px solid #2a3560}
.row{display:flex;gap:6px;align-items:center}
.inp{width:75px;background:#0f1429;border:1px solid #2a3560;color:#fff;padding:10px;border-radius:6px;text-align:center;font-weight:700}
.bx{flex:1;background:#2a3560;color:#8a90b0;border:none;padding:8px;border-radius:6px;font-size:10px;font-weight:700}
.bo{flex:1;background:#ff7a00;color:#fff;border:none;padding:10px;border-radius:6px;font-weight:900}
.bo.cash{background:#00c853}
.qrow{display:flex;gap:5px;margin-top:6px}
.qrow button{background:#2a3560;color:#c0c8e0;border:1px solid #3a4a70;border-radius:15px;padding:4px 10px;font-size:11px}
.stats{display:flex;justify-content:space-around;background:#151a33;padding:8px;text-align:center;border-top:1px solid #2a3560}
.stats small{color:#8a90b0;font-size:9px;display:block}
.stats b{color:#ff7a00;font-size:12px}
table{width:100%;font-size:11px;border-collapse:collapse}
th{background:#151a33;color:#8a90b0;padding:5px;font-size:9px}
td{padding:5px;border-bottom:1px solid #1c2340;text-align:center}
</style>
</head>
<body>
<div class="top"><button class="b1">Règles</button><button class="b2">HISTORIQUE</button></div>
<div id="game"><canvas id="canvas"></canvas><div id="plane">✈️</div><div id="mult"></div><div id="cd"></div></div>

<div class="box">
<div class="row"><input class="inp" id="a1" value="300"><span style="color:#8a90b0">X</span><button class="bx">ACTIVER LE JEU AUTOMATIQUE</button><button class="bo" id="b1" onclick="bet(0)">PLACER UN PARI</button></div>
<div class="qrow"><button onclick="setA(0,200)">200</button><button onclick="setA(0,700)">700</button><button onclick="setA(0,2000)">2000</button><button onclick="setA(0,6000)">6000</button><button onclick="setA(0,20000)">20000</button><button onclick="setA(0,70000)">70000</button></div>
</div>

<div class="box">
<div class="row"><input class="inp" id="a2" value="300"><span style="color:#8a90b0">X</span><button class="bx">ACTIVER LE JEU AUTOMATIQUE</button><button class="bo" id="b2" onclick="bet(1)">PLACER UN PARI</button></div>
<div class="qrow"><button onclick="setA(1,200)">200</button><button onclick="setA(1,700)">700</button><button onclick="setA(1,2000)">2000</button><button onclick="setA(1,6000)">6000</button><button onclick="setA(1,20000)">20000</button><button onclick="setA(1,70000)">70000</button></div>
</div>

<div class="stats"><div><small>Nombre de paris</small><b id="nb">0</b></div><div><small>Total des paris XOF</small><b id="tt">0</b></div><div><small>Gains totaux XOF</small><b id="gg">0</b></div></div>
<table id="tbl"><tr><th>NOM</th><th>COTE</th><th>PARI</th><th>GAIN</th></tr></table>

<script>
let canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d'),multE=document.getElementById('mult'),cdE=document.getElementById('cd'),plane=document.getElementById('plane');
let mult=1,crash=0,flying=false,timer,pts=[],bets=[{on:false,cash:false,amt:300},{on:false,cash:false,amt:300}],players=[];
function resize(){canvas.width=canvas.offsetWidth*2;canvas.height=canvas.offsetHeight*2;}window.onresize=resize;resize();
function rc(){let r=Math.random();if(r<0.3)return Math.random()*0.8+1;if(r<0.65)return Math.random()*1.5+1.1;if(r<0.88)return Math.random()*5+2.5;return Math.random()*30+6;}
function genP(){players=[];for(let i=0;i<8;i++){players.push({n:"****"+Math.floor(Math.random()*90+10),bet:Math.floor(Math.random()*8000+200),cash:0})}update();}
function update(){
 let html='<tr><th>NOM</th><th>COTE</th><th>PARI</th><th>GAIN</th></tr>',nb=players.length,tot=0,g=0;
 players.forEach(p=>{if(flying&&p.cash==0&&Math.random()<0.03){p.cash=mult}let c=p.cash>0?p.cash.toFixed(2)+'x':'x0';let gain=p.cash>0?Math.floor(p.bet*p.cash):0;tot+=p.bet;g+=gain;html+='<tr><td>'+p.n+'</td><td>'+c+'</td><td>'+p.bet+' XOF</td><td style="color:'+(gain>0?'#00ff7a':'')+'">'+gain+' XOF</td></tr>'});
 document.getElementById('nb').innerText=nb;document.getElementById('tt').innerText=tot;document.getElementById('gg').innerText=g;document.getElementById('tbl').innerHTML=html;
}
function countdown(){genP();cdE.style.display='block';multE.innerText='';pts=[];let c=5;cdE.innerText=c;let iv=setInterval(()=>{c--;if(c>0){cdE.innerText=c}else{clearInterval(iv);cdE.style.display='none';start()}},1000)}
function start(){
 flying=true;mult=1;crash=rc();pts=[{x:0,y:canvas.height-30}];
 bets.forEach((b,i)=>{let bt=document.getElementById('b'+(i+1));if(b.on){b.cash=false;bt.className='bo cash';bt.innerText='RETRAIT '+Math.floor(b.amt*mult)+' XOF'}});
 clearInterval(timer);
 timer=setInterval(()=>{
  mult+=0.01+mult*0.01;if(mult>=crash){crashNow();return;}
  multE.innerText=mult.toFixed(2)+'x';multE.style.color=mult<2?'#fff':'#00ff88';
  let w=canvas.width,h=canvas.height,p=mult/crash;
  let x=Math.pow(p,0.7)*(w*0.85),y=h-(Math.pow(p,1.15)*h*0.55+30);
  pts.push({x,y});if(pts.length>80)pts.shift();
  ctx.clearRect(0,0,w,h);ctx.beginPath();ctx.moveTo(0,h-30);pts.forEach(pt=>ctx.lineTo(pt.x,pt.y));ctx.strokeStyle='#ff3c00';ctx.lineWidth=4;ctx.stroke();ctx.lineTo(x,h-30);ctx.fillStyle='rgba(255,60,0,0.15)';ctx.fill();
  plane.style.left=(x/2-10)+'px';plane.style.top=(y/2-15)+'px';plane.style.transform='rotate('+(-15-p*15)+'deg)';
  bets.forEach((b,i)=>{if(b.on&&!b.cash){let bt=document.getElementById('b'+(i+1));bt.innerText=Math.floor(b.amt*mult)+' XOF'}});
  update();
 },60);
}
function crashNow(){
 clearInterval(timer);flying=false;multE.innerText=crash.toFixed(2)+'x';multE.style.color='#ff2a2a';plane.style.opacity='0.3';ctx.clearRect(0,0,canvas.width,canvas.height);
 bets.forEach((b,i)=>{let bt=document.getElementById('b'+(i+1));if(b.on&&!b.cash){bt.className='bo';bt.innerText='PLACER UN PARI';b.on=false}else if(b.on&&b.cash){bt.className='bo';bt.innerText='PLACER UN PARI';b.on=false}});
 setTimeout(()=>{plane.style.opacity='1';countdown()},3000);
}
function setA(i,v){document.getElementById('a'+(i+1)).value=v;bets[i].amt=v}
function bet(i){
 let amt=parseInt(document.getElementById('a'+(i+1)).value)||300,b=bets[i],bt=document.getElementById('b'+(i+1));
 if(!b.on){b.amt=amt;b.on=true;b.cash=false;bt.className='bo cash';bt.innerText=flying?'RETRAIT '+Math.floor(amt*mult)+' XOF':'PARI PLACE';if(!flying)bt.innerText='EN ATTENTE';}
 else{if(!flying||b.cash)return;let gain=Math.floor(b.amt*mult);b.cash=true;bt.className='bo';bt.innerText='GAGNE '+gain;setTimeout(()=>{b.on=false;bt.innerText='PLACER UN PARI'},1200)}
}
countdown();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
