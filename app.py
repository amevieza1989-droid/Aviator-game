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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aviator PRO</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
body{background:#0e121b;color:#fff;overflow:hidden;height:100vh;display:flex;flex-direction:column}
.top-bar{background:#1a202e;display:flex;gap:6px;padding:8px;overflow-x:auto;border-bottom:1px solid #2a3245}
.pill{padding:4px 10px;border-radius:20px;font-size:12px;font-weight:700;min-width:45px;text-align:center}
.pill.blue{background:#1a233f;color:#8b9bb4;border:1px solid #2a3a5a}
.pill.green{background:#0f2d1f;color:#22c55e}
.pill.orange{background:#3d2410;color:#f59e0b}
.pill.purple{background:#2a103d;color:#c084fc}
.game-wrap{flex:1;position:relative;background:#000;overflow:hidden}
canvas#grid{position:absolute;left:0;top:0;width:100%;height:100%}
#plane{position:absolute;left:0;top:0;font-size:32px;z-index:5;filter:drop-shadow(0 0 6px #fff)}
#center{position:absolute;left:50%;top:45%;transform:translate(-50%,-50%);text-align:center;z-index:4}
#mult{font-size:64px;font-weight:900}
#mult.fly{color:#22ff6e}
#mult.crash{color:#ff2a2a}
#msg{font-size:18px;font-weight:700;margin-top:8px;color:#a0aec0}
.bet-area{background:#1a202e;padding:10px;display:flex;gap:10px;border-top:1px solid #2a3245}
.bet-card{flex:1;background:#252f43;border-radius:12px;padding:10px;border:1px solid #323f59}
.input-box{flex:1;background:#0e121b;border:1px solid #323f59;border-radius:8px;display:flex;padding:6px 10px}
.input-box input{background:transparent;border:none;color:#fff;width:100%;font-weight:700;text-align:center;outline:none}
.small-btn{background:#323f59;color:#8b9bb4;border:none;border-radius:6px;padding:6px 8px;font-weight:700}
.bet-btn{width:100%;padding:14px;border:none;border-radius:10px;font-weight:900;font-size:16px;cursor:pointer;margin-top:8px}
.bet-btn.bet{background:#22c55e;color:#fff;box-shadow:0 4px 0 #15803d}
.bet-btn.cash{background:#f59e0b;color:#fff;animation:pulse 0.8s infinite}
@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.02)}100%{transform:scale(1)}}
</style>
</head>
<body>
<div class="top-bar" id="history"></div>
<div class="game-wrap" id="gameWrap">
<canvas id="grid"></canvas>
<svg id="curveSvg" style="position:absolute;width:100%;height:100%"><path id="curvePath" d="M0 350 L0 350" stroke="#ff2a2a" stroke-width="4" fill="rgba(255,42,42,0.15)"/></svg>
<div id="plane">✈️</div>
<div id="center"><div id="mult">1.00x</div><div id="msg">En attente</div></div>
</div>
<div class="bet-area">
<div class="bet-card">
<div style="display:flex;justify-content:space-between;font-size:11px;color:#8b9bb4"><span>PARI 1</span><span id="bal1">Solde: 10000</span></div>
<div style="display:flex;gap:6px;margin-top:8px"><button class="small-btn" onclick="changeBet(0,-10)">-</button><div class="input-box"><input id="betInput1" value="100"></div><button class="small-btn" onclick="changeBet(0,10)">+</button></div>
<button class="bet-btn bet" id="betBtn1" onclick="placeBet(0)">PARIER<br><small id="betLabel1">100 FCFA</small></button>
</div>
<div class="bet-card">
<div style="display:flex;justify-content:space-between;font-size:11px;color:#8b9bb4"><span>PARI 2</span><span>AUTO</span></div>
<div style="display:flex;gap:6px;margin-top:8px"><button class="small-btn" onclick="changeBet(1,-10)">-</button><div class="input-box"><input id="betInput2" value="200"></div><button class="small-btn" onclick="changeBet(1,10)">+</button></div>
<button class="bet-btn bet" id="betBtn2" onclick="placeBet(1)">PARIER<br><small id="betLabel2">200 FCFA</small></button>
</div>
</div>
<script>
const canvas=document.getElementById('grid'),ctx=canvas.getContext('2d');
function resize(){canvas.width=canvas.offsetWidth*2;canvas.height=canvas.offsetHeight*2;drawGrid()}
function drawGrid(){ctx.clearRect(0,0,canvas.width,canvas.height);ctx.strokeStyle='rgba(255,255,255,0.04)';for(let x=0;x<canvas.width;x+=80){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,canvas.height);ctx.stroke()}for(let y=0;y<canvas.height;y+=80){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(canvas.width,y);ctx.stroke()}}
window.addEventListener('resize',resize);resize();
const multEl=document.getElementById('mult'),msgEl=document.getElementById('msg'),planeEl=document.getElementById('plane'),pathEl=document.getElementById('curvePath'),historyEl=document.getElementById('history'),wrap=document.getElementById('gameWrap');
let mult=1,crashPoint=0,flying=false,timer=null,points=[],bet=[{active:false,amount:100,cashed:false},{active:false,amount:200,cashed:false}],balance=10000;
function randCrash(){let r=Math.random();if(r<0.15)return +(Math.random()*0.8+1).toFixed(2);if(r<0.55)return +(Math.random()*2.5+1.1).toFixed(2);if(r<0.85)return +(Math.random()*7+3).toFixed(2);if(r<0.96)return +(Math.random()*20+10).toFixed(2);return +(Math.random()*100+30).toFixed(2);}
function colorFor(v){if(v<2)return 'blue';if(v<10)return 'green';if(v<50)return 'orange';return 'purple';}
function addHist(v){let d=document.createElement('div');d.className='pill '+colorFor(v);d.textContent=v.toFixed(2)+'x';historyEl.prepend(d);if(historyEl.children.length>20)historyEl.lastChild.remove();}
function startRound(){flying=true;mult=1;points=[{x:0,y:350}];crashPoint=randCrash();multEl.textContent='1.00x';multEl.className='fly';msgEl.textContent='';planeEl.style.opacity='1';bet.forEach((b,i)=>{if(b.active){b.cashed=false;let btn=document.getElementById('betBtn'+(i+1));btn.className='bet-btn cash';btn.innerHTML='RETRAIT<br><small>'+Math.floor(b.amount*mult)+' FCFA</small>';}});clearInterval(timer);timer=setInterval(()=>{mult+=0.01+mult*0.012;if(mult>=crashPoint){doCrash();return;}multEl.textContent=mult.toFixed(2)+'x';bet.forEach((b,i)=>{if(b.active&&!b.cashed){let label=document.querySelector('#betBtn'+(i+1)+' small');if(label)label.textContent=Math.floor(b.amount*mult)+' FCFA';}});let p=mult/crashPoint;let w=wrap.offsetWidth,h=wrap.offsetHeight;let x=Math.pow(p,0.7)*(w*0.85);let y=h-(Math.pow(p,1.4)*h*0.7+50);points.push({x,y});if(points.length>80)points.shift();let s='M0 350';points.forEach(pt=>{s+=' L'+pt.x+' '+pt.y});pathEl.setAttribute('d',s);planeEl.style.left=(x-15)+'px';planeEl.style.top=(y-15)+'px';planeEl.style.transform='rotate('+( -20 - p*25)+'deg)';},70);}
function doCrash(){clearInterval(timer);flying=false;multEl.textContent=crashPoint.toFixed(2)+'x';multEl.className='crash';msgEl.textContent="S'EST ENVOLÉ!";planeEl.style.opacity='0';addHist(crashPoint);bet.forEach((b,i)=>{let btn=document.getElementById('betBtn'+(i+1));if(b.active&&!b.cashed){btn.className='bet-btn bet';btn.innerHTML='PARIER<br><small>'+b.amount+' FCFA</small>';b.active=false;}else if(b.active&&b.cashed){btn.className='bet-btn bet';btn.innerHTML='PARIER<br><small>'+b.amount+' FCFA</small>';b.active=false;}});document.getElementById('bal1').textContent='Solde: '+balance+' FCFA';setTimeout(startRound,3000);}
function placeBet(idx){let input=document.getElementById('betInput'+(idx+1));let amount=parseInt(input.value)||100;let btn=document.getElementById('betBtn'+(idx+1));let b=bet[idx];if(!b.active){if(amount>balance){msgEl.textContent='Solde insuffisant!';return;}b.amount=amount;balance-=amount;b.active=true;b.cashed=false;document.getElementById('bal1').textContent='Solde: '+balance+' FCFA';if(flying){btn.className='bet-btn cash';btn.innerHTML='RETRAIT<br><small>'+Math.floor(amount*mult)+' FCFA</small>';}else{btn.className='bet-btn bet';btn.innerHTML='ATTENTE<br><small>Prochain tour</small>';}}else{if(!flying||b.cashed)return;let gain=Math.floor(b.amount*mult);balance+=gain;b.cashed=true;btn.className='bet-btn bet';btn.innerHTML='GAGNÉ '+gain+'<br><small>'+mult.toFixed(2)+'x</small>';document.getElementById('bal1').textContent='Solde: '+balance+' FCFA';msgEl.textContent='Retrait à '+mult.toFixed(2)+'x! +'+gain;}}
function changeBet(idx,delta){let inp=document.getElementById('betInput'+(idx+1));let v=parseInt(inp.value)||100;v=Math.max(10,v+delta);inp.value=v;bet[idx].amount=v;}
for(let i=0;i<8;i++)addHist([1.23,2.45,1.05,8.3,3.12,1.89,12.5,4.2][i]);setTimeout(startRound,1200);
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return HTML

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
