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
<meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>Aviator TOGO PRO</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Inter,Arial}
body{background:#0a0c1e;color:#fff}
#header{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:#141937;border-bottom:1px solid #252a50;position:sticky;top:0;z-index:10}
.logo{font-weight:900;color:#ff3c00}
#bal{color:#00ff88;font-weight:900;font-size:13px;background:#101432;padding:5px 10px;border-radius:20px;border:1px solid #2a3560}
.btn-d{padding:6px 12px;border-radius:20px;border:none;font-weight:800;font-size:11px}
.depot{background:#00c853;color:#fff}.retrait{background:#ff7a00;color:#fff}
#main{display:flex;height:calc(100vh - 45px)}
#left{width:300px;background:#12152e;border-right:1px solid #1e244a;overflow-y:auto}
.tab{display:flex;background:#0e1130}.tab div{flex:1;text-align:center;padding:8px;font-size:11px;font-weight:700;color:#8a90b0;border-bottom:2px solid transparent}
.tab div.active{color:#fff;border-color:#ff3c00}
.p-row{display:flex;justify-content:space-between;padding:6px 10px;font-size:11px;border-bottom:1px solid #1c2142}
#center{flex:1;display:flex;flex-direction:column;overflow:hidden}
#hist{display:flex;gap:5px;padding:6px;background:#151a33;overflow-x:auto}
.pill{padding:4px 9px;border-radius:15px;font-size:11px;font-weight:800;white-space:nowrap}
.b{color:#8a90b0;background:#1e2445}.g{color:#00ff88;background:#0e2a1e}.o{color:#ff9a00;background:#2e1e0a}.p{color:#c47cff;background:#2a1450}.r{color:#ff3b3b;background:#3a1520}
#game{position:relative;flex:1;background:radial-gradient(120% 100% at 0% 100%,#1a2048 0%,#0a0e1f 60%);min-height:280px}
#cv{width:100%;height:100%;display:block}
#centerM{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none}
#mult{font-size:48px;font-weight:900}#msg{font-size:11px;color:#8a90b0;font-weight:700}
#right-panels{padding:6px;background:#0a0c1e}
.panel{background:#1b213f;border-radius:12px;padding:10px;border:1px solid #2a3560;margin-bottom:6px}
.row{display:flex;gap:6px}.mise-box{flex:1;background:#101530;border:1px solid #2a3560;border-radius:8px;padding:6px;display:flex;align-items:center;gap:4px}
.mise-box input{flex:1;background:transparent;border:none;color:#fff;font-weight:800;font-size:16px;text-align:center;outline:none}
.mise-box button{background:#252e55;color:#fff;border:none;width:28px;height:28px;border-radius:50%;font-weight:900}
.bet-btn{flex:1.2;background:linear-gradient(#ff7a00,#ff5500);color:#fff;border:none;border-radius:8px;font-weight:900;font-size:13px;cursor:pointer}
.bet-btn.cash{background:linear-gradient(#00d26a,#00a854)}.bet-btn.wait{background:#3a415f;color:#a0a8c0}
.qrow{display:flex;gap:5px;margin-top:6px;flex-wrap:wrap}.qrow button{background:#252e55;color:#c0c8e0;border:1px solid #33406e;border-radius:20px;padding:4px 10px;font-size:10px;font-weight:700}
.auto-row{display:flex;gap:6px;margin-top:6px;align-items:center;background:#131a36;border-radius:6px;padding:5px 8px;font-size:11px}
.auto-row input{width:60px;background:#0f1429;border:1px solid #33406e;color:#fff;border-radius:4px;padding:3px;text-align:center}
#modalWrap{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:100;padding:15px}
.mBox{background:#1b213f;border:1px solid #2a3560;border-radius:14px;padding:18px;width:100%;max-width:360px}
.mBox h3{font-size:16px}.op{display:flex;gap:8px;margin:12px 0}.op div{flex:1;padding:10px;border-radius:8px;border:2px solid #2a3560;text-align:center;font-weight:800;font-size:12px;cursor:pointer}
.op div.sel{border-color:#00c853;background:#0e2a1e}
.mBox input{width:100%;padding:12px;background:#101530;border:1px solid #33406e;border-radius:8px;color:#fff;margin:6px 0;font-size:14px}
.mBox button{width:100%;padding:12px;border:none;border-radius:8px;font-weight:900;margin-top:8px;font-size:13px}
@media(max-width:800px){#left{display:none}}
</style>
</head>
<body>
<div id="header"><div class="logo">✈️ AVIATOR TG</div><div style="display:flex;gap:6px;align-items:center"><div id="bal">50 000 XOF</div><button class="btn-d depot" onclick="openDeposit()">DÉPÔT</button><button class="btn-d retrait" onclick="openRetrait()">RETRAIT</button></div></div>
<div id="main">
<div id="left"><div class="tab"><div class="active">Tous</div></div><div id="players"></div></div>
<div id="center">
<div id="hist"></div>
<div id="game"><canvas id="cv"></canvas><div id="centerM"><div id="mult">1.00x</div><div id="msg">En attente</div></div></div>
<div id="right-panels">
<div class="panel">
<div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:10px;color:#8a90b0"><span>PARI 1</span><label><input type="checkbox" id="auto0"> AUTO</label><label><input type="checkbox" id="ac0" checked> AUTO CASH</label></div>
<div class="row"><div class="mise-box"><button onclick="chg(0,-100)">-</button><input id="a0" value="300" type="number"><button onclick="chg(0,100)">+</button></div><button class="bet-btn" id="b0" onclick="clickBet(0)">PLACER UN PARI</button></div>
<div class="auto-row"><span>Cashout à</span><input id="acv0" value="2.00" type="number" step="0.1"><span>x</span></div>
<div class="qrow"><button onclick="setA(0,200)">200</button><button onclick="setA(0,500)">500</button><button onclick="setA(0,1000)">1K</button><button onclick="setA(0,2000)">2K</button><button onclick="setA(0,5000)">5K</button></div>
</div>
<div class="panel">
<div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:10px;color:#8a90b0"><span>PARI 2</span><label><input type="checkbox" id="auto1"> AUTO</label><label><input type="checkbox" id="ac1"> AUTO CASH</label></div>
<div class="row"><div class="mise-box"><button onclick="chg(1,-100)">-</button><input id="a1" value="300" type="number"><button onclick="chg(1,100)">+</button></div><button class="bet-btn" id="b1" onclick="clickBet(1)">PLACER UN PARI</button></div>
<div class="auto-row"><span>Cashout à</span><input id="acv1" value="3.50" type="number" step="0.1"><span>x</span></div>
<div class="qrow"><button onclick="setA(1,200)">200</button><button onclick="setA(1,500)">500</button><button onclick="setA(1,1000)">1K</button><button onclick="setA(1,2000)">2K</button><button onclick="setA(1,5000)">5K</button></div>
</div>
</div>
</div>
</div>

<div id="modalWrap"><div class="mBox">
<h3 id="mTitle">Dépôt Togo</h3>
<p style="font-size:11px;color:#8a90b0;margin-top:4px">Choisis ton opérateur</p>
<div class="op"><div id="opMixx" class="sel" onclick="selOp('mixx')">Mixx by Yas<br><span style="font-size:9px">*145#</span></div><div id="opFlooz" onclick="selOp('flooz')">Flooz<br><span style="font-size:9px">*155#</span></div></div>
<input id="phone" placeholder="Numéro: 90 12 34 56" type="tel">
<input id="amount" placeholder="Montant XOF" type="number" value="1000">
<div id="payInfo" style="background:#101432;border-radius:6px;padding:8px;font-size:10px;color:#c0c8e0;margin:6px 0;line-height:1.4">
Pour payer: <b id="ussd">*145*3*1#</b> puis suivez instructions. Numéro marchand: <b>90 00 00 00</b>
</div>
<button id="mBtn" style="background:#00c853;color:#fff" onclick="confirmPay()">CONFIRMER DÉPÔT MIXX</button>
<button style="background:#252e5a;color:#fff" onclick="closeM()">FERMER</button>
<p style="font-size:9px;color:#6b7280;margin-top:8px">Mode démo: le solde s'ajoute automatiquement. Pour vrai paiement, connecte PayGate / CinetPay API.</p>
</div></div>

<script>
let cv=document.getElementById('cv'),ctx=cv.getContext('2d'),histE=document.getElementById('hist'),multE=document.getElementById('mult'),msgE=document.getElementById('msg'),balE=document.getElementById('bal'),playersE=document.getElementById('players');
let W,H,mult=1,crash=2,flying=false,timer,pts=[],prog=0,history=[],bal=50000;
let bets=[{on:false,cash:false,amt:300},{on:false,cash:false,amt:300}];
let curPay='mixx',curMode='depot';
function resize(){W=cv.width=cv.offsetWidth*2;H=cv.height=cv.offsetHeight*2;}window.onresize=resize;resize();
function randCrash(){let r=Math.random();if(r<0.12)return 1+Math.random()*0.25;if(r<0.45)return 1+Math.random()*1;if(r<0.75)return 2+Math.random()*3;if(r<0.92)return 5+Math.random()*15;return 20+Math.random()*80;}
function addHist(v){history.unshift(v);if(history.length>35)history.pop();histE.innerHTML='';history.forEach(val=>{let d=document.createElement('div');let cl='b';if(val<1.2)cl='r';else if(val>=2&&val<10)cl='g';else if(val>=10&&val<50)cl='o';else if(val>=50)cl='p';d.className='pill '+cl;d.innerText=val.toFixed(2)+'x';histE.appendChild(d);});}
function draw(x,y){ctx.clearRect(0,0,W,H);ctx.strokeStyle='rgba(255,255,255,0.04)';for(let i=0;i<W;i+=100){ctx.beginPath();ctx.moveTo(i,0);ctx.lineTo(i,H);ctx.stroke();}for(let j=0;j<H;j+=100){ctx.beginPath();ctx.moveTo(0,j);ctx.lineTo(W,j);ctx.stroke();}
if(pts.length>1){ctx.beginPath();ctx.moveTo(0,H-24);pts.forEach(p=>ctx.lineTo(p.x,p.y));ctx.strokeStyle='#ff3c00';ctx.lineWidth=6;ctx.lineJoin='round';ctx.lineCap='round';ctx.stroke();ctx.lineTo(x,H-24);ctx.closePath();ctx.fillStyle='rgba(255,60,0,0.18)';ctx.fill();}
if(flying){ctx.save();ctx.translate(x,y);ctx.rotate(-0.45-prog*0.25);ctx.font='38px Arial';ctx.fillText('✈️',-20,-6);ctx.restore();}}
function countdown(){flying=false;prog=0;pts=[];draw(0,H-24);let c=7;multE.innerText=c+'s';multE.style.color='#fff';msgE.innerText='PROCHAIN TOUR';let cd=setInterval(()=>{c--;if(c>0)multE.innerText=c+'s';else{clearInterval(cd);launch();}},1000);bets.forEach((b,i)=>{if(document.getElementById('auto'+i).checked &&!b.on)setTimeout(()=>placeBet(i),400);});genPlayers();}
function launch(){flying=true;mult=1;crash=randCrash();prog=0;pts=[{x:0,y:H-24}];msgE.innerText='';bets.forEach((b,i)=>{if(b.on){let btn=document.getElementById('b'+i);b.cash=false;btn.className='bet-btn cash';btn.innerText='RETRAIT '+Math.floor(b.amt*mult)+' XOF';}});clearInterval(timer);timer=setInterval(()=>{prog+=0.008;mult+=0.01+mult*0.012;if(mult>=crash){crashNow();return;}multE.innerText=mult.toFixed(2)+'x';multE.style.color=mult<2?'#fff':'#00ff88';let x=prog*W*0.90;let y=H-24 - Math.pow(prog,1.45)*H*0.78;if(y<20)y=20;pts.push({x,y});if(pts.length>130)pts.shift();draw(x,y);bets.forEach((b,i)=>{if(b.on&&!b.cash){let btn=document.getElementById('b'+i);btn.innerText='RETRAIT '+Math.floor(b.amt*mult)+' XOF';let acOn=document.getElementById('ac'+i).checked;let acVal=parseFloat(document.getElementById('acv'+i).value)||2;if(acOn&&mult>=acVal)cashOut(i);}});},42);}
function crashNow(){clearInterval(timer);flying=false;multE.innerText=crash.toFixed(2)+'x';multE.style.color='#ff2a2a';msgE.innerText="S'EST ENVOLÉ!";draw(0,0);addHist(crash);bets.forEach((b,i)=>{let btn=document.getElementById('b'+i);if(b.on&&!b.cash){btn.className='bet-btn wait';btn.innerText='PERDU';}if(b.on)setTimeout(()=>{b.on=false;b.cash=false;btn.className='bet-btn';btn.innerText='PLACER UN PARI';},1200);});setTimeout(countdown,7000);}
function placeBet(i){let amt=parseInt(document.getElementById('a'+i).value)||0;let btn=document.getElementById('b'+i);let b=bets[i];if(b.on)return;if(amt<100){alert('Mise min 100 XOF');return;}if(bal<amt){alert('Solde insuffisant. Recharge via Mixx/Flooz');openDeposit();return;}b.amt=amt;b.on=true;b.cash=false;bal-=amt;balE.innerText=bal.toLocaleString()+' XOF';if(flying){btn.className='bet-btn cash';btn.innerText='RETRAIT '+Math.floor(amt*mult)+' XOF';}else{btn.className='bet-btn wait';btn.innerText='PARI PLACÉ - '+amt+' XOF';}}
function cashOut(i){let b=bets[i],btn=document.getElementById('b'+i);if(!b.on||b.cash||!flying)return;let gain=Math.floor(b.amt*mult);b.cash=true;bal+=gain;balE.innerText=bal.toLocaleString()+' XOF';btn.className='bet-btn';btn.innerText='GAGNÉ '+gain+' XOF';setTimeout(()=>{b.on=false;b.cash=false;btn.innerText='PLACER UN PARI';},1500);}
function clickBet(i){let b=bets[i];if(b.on&&!b.cash&&flying)cashOut(i);else if(!b.on)placeBet(i);}
function setA(i,v){document.getElementById('a'+i).value=v;}function chg(i,d){let el=document.getElementById('a'+i);let v=parseInt(el.value)||0;v=Math.max(100,v+d);el.value=v;}

// Players fake
let names=["Koffi","Moussa","Aminata","Joel","Fatou","Ibrahim","Seydou","Mariam","Abou","Kwame","Aicha","Emmanuel","Lamine","Ousmane","Yas Togo","Flooz TG"];
function genPlayers(){playersE.innerHTML='';for(let i=0;i<16;i++){let n=names[Math.floor(Math.random()*names.length)]+' '+(Math.floor(Math.random()*90)+10);let amt=[200,300,500,1000,2000,5000][Math.floor(Math.random()*6)];let cash=(Math.random()*5+1.1).toFixed(2);let win=Math.floor(amt*cash);let d=document.createElement('div');d.className='p-row';d.innerHTML=`<span>${n} • ${amt} XOF</span><span style="color:#00ff88"><b>${win} XOF</b> @${cash}x</span>`;playersE.appendChild(d);}}

function selOp(op){curPay=op;document.getElementById('opMixx').className=op==='mixx'?'sel':'';document.getElementById('opFlooz').className=op==='flooz'?'sel':'';document.getElementById('ussd').innerText=op==='mixx'?'*145*3*1#':'*155*3*1#';document.getElementById('mBtn').innerText=(curMode==='depot'?'CONFIRMER DÉPÔT ':'CONFIRMER RETRAIT ')+(op==='mixx'?'MIXX':'FLOOZ');}
function openDeposit(){curMode='depot';document.getElementById('mTitle').innerText='Dépôt Mixx / Flooz Togo';document.getElementById('modalWrap').style.display='flex';selOp(curPay);}
function openRetrait(){curMode='retrait';document.getElementById('mTitle').innerText='Retrait Mixx / Flooz Togo';document.getElementById('modalWrap').style.display='flex';selOp(curPay);}
function closeM(){document.getElementById('modalWrap').style.display='none';}
function confirmPay(){
 let phone=document.getElementById('phone').value.trim();
 let amt=parseInt(document.getElementById('amount').value)||0;
 if(phone.length<8){alert('Entre ton numéro Mixx/Flooz (ex: 90123456)');return;}
 if(amt<100){alert('Montant minimum 100 XOF');return;}
 if(curMode==='depot'){
   bal+=amt;balE.innerText=bal.toLocaleString()+' XOF';
   alert('✅ Dépôt '+amt+' XOF ('+(curPay==='mixx'?'Mixx by Yas':'Flooz')+' '+phone+') ajouté! Solde: '+bal+' XOF\\n\\nMODE DÉMO: Branche PayGate API pour vrai paiement Togo.');
 }else{
   if(bal<amt){alert('Solde insuffisant');return;}
   bal-=amt;balE.innerText=bal.toLocaleString()+' XOF';
   alert('✅ Retrait '+amt+' XOF vers '+(curPay==='mixx'?'Mixx':'Flooz')+' '+phone+' demandé!');
 }
 closeM();
}
[1.24,2.5,1.08,8.12,1.92,15.3,3.4,1.12].forEach(v=>addHist(v));genPlayers();countdown();
</script>
</body>
</html>
"""

@app.route('/')
def index(): return HTML
if __name__=='__main__':
    port=int(os.environ.get('PORT',10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
