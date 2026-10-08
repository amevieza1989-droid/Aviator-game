import os
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aviator-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

HTML = r'''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aviateur</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0f1e;color:white;font-family:Arial;overflow:hidden;height:100vh}
.top{text-align:center;padding:20px}
.game{position:relative;width:100%;height:60vh;background:#0b0f1e;overflow:hidden;border-top:1px solid #1e2a4a;border-bottom:1px solid #1e2a4a}
#plane{position:absolute;left:10%;bottom:20%;font-size:50px;transition:all 0.08s linear}
#multi{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:70px;font-weight:900;color:#2eff7a}
.crash{color:#ff3b3b !important}
.controls{display:flex;justify-content:center;gap:15px;padding:20px}
.btn{padding:14px 28px;border:none;border-radius:12px;font-weight:bold;cursor:pointer}
.bet{background:#22c55e;color:white}
.cash{background:#f59e0b;color:white}
.btn:disabled{opacity:0.5}
.stats{text-align:center;color:#8b9bb4}
.history{display:flex;gap:8px;justify-content:center;padding:10px;flex-wrap:wrap}
.hist{background:#1a233f;padding:5px 10px;border-radius:20px;font-size:13px}
</style>
</head>
<body>
<div class="top"><h1>✈️ AVIATEUR</h1></div>
<div class="game">
<div id="multi">1.00x</div>
<div id="plane">✈️</div>
</div>
<div class="controls">
<button class="btn bet" id="betBtn" onclick="placeBet()">PARIER 100</button>
<button class="btn cash" id="cashBtn" onclick="cashout()" disabled>RETRAIT</button>
</div>
<div class="stats" id="msg">En attente...</div>
<div class="history" id="history"></div>
<script>
let mult=1.00,flying=false,crashPoint=0,interval,betActive=false,betAmount=100;
const multiEl=document.getElementById('multi'),planeEl=document.getElementById('plane'),msgEl=document.getElementById('msg'),betBtn=document.getElementById('betBtn'),cashBtn=document.getElementById('cashBtn'),historyEl=document.getElementById('history');
function randomCrash(){let r=Math.random();if(r<0.1)return(Math.random()*1+1).toFixed(2);if(r<0.4)return(Math.random()*2+1).toFixed(2);if(r<0.75)return(Math.random()*4+2).toFixed(2);if(r<0.92)return(Math.random()*10+4).toFixed(2);return(Math.random()*50+10).toFixed(2);}
function startRound(){flying=true;mult=1.00;crashPoint=parseFloat(randomCrash());multiEl.classList.remove('crash');msgEl.textContent='Tour... crash prevu '+crashPoint+'x';betBtn.disabled=true;if(betActive)cashBtn.disabled=false;planeEl.style.left='10%';planeEl.style.bottom='20%';planeEl.style.opacity='1';clearInterval(interval);interval=setInterval(()=>{mult+=0.01+mult*0.008;if(mult>=crashPoint){doCrash();return;}multiEl.textContent=mult.toFixed(2)+'x';let p=Math.min(mult/crashPoint,1);planeEl.style.left=(10+p*75)+'%';planeEl.style.bottom=(20+p*60)+'%';planeEl.style.transform='rotate('+-p*30+'deg)';},70);}
function doCrash(){clearInterval(interval);flying=false;multiEl.textContent=crashPoint+'x';multiEl.classList.add('crash');msgEl.textContent='CRASH à '+crashPoint+'x !';planeEl.style.opacity='0';cashBtn.disabled=true;betActive=false;betBtn.disabled=false;let d=document.createElement('div');d.className='hist';d.style.color=crashPoint<2?'#8b9bb4':crashPoint<5?'#22c55e':'#f59e0b';d.textContent=crashPoint+'x';historyEl.prepend(d);if(historyEl.children.length>12)historyEl.lastChild.remove();setTimeout(startRound,3000);}
function placeBet(){betActive=true;betBtn.disabled=true;betBtn.textContent='PARIÉ '+betAmount;if(!flying)startRound();}
function cashout(){if(!flying||!betActive)return;let gain=Math.floor(betAmount*mult);msgEl.textContent='Gagné '+gain+' FCFA à '+mult.toFixed(2)+'x !';betActive=false;cashBtn.disabled=true;betBtn.disabled=false;}
setTimeout(startRound,1000);
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
