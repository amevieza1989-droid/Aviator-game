import os
import random
import time
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aviator-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Variables du jeu
game_state = {
    'multiplier': 1.0,
    'is_flying': False,
    'crashed': False,
    'players': {}
}

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Aviator Game</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<style>
body{background:#0f172a;color:white;font-family:Arial;text-align:center;padding:20px}
#plane{font-size:80px;transition:all 0.1s}
#multiplier{font-size:60px;color:#22c55e;font-weight:bold;margin:20px}
button{padding:15px 40px;font-size:20px;background:#22c55e;border:none;border-radius:10px;color:white;cursor:pointer;margin:10px}
button:disabled{background:gray}
#crashed{color:#ef4444;font-size:40px;display:none}
</style>
</head>
<body>
<h1>✈️ AVIATOR</h1>
<div id="plane">✈️</div>
<div id="multiplier">1.00x</div>
<div id="crashed">💥 CRASHED!</div>
<button id="betBtn" onclick="placeBet()">PARIER 100</button>
<button id="cashBtn" onclick="cashOut()" disabled>CASH OUT</button>
<div id="info"></div>
<script>
var socket = io();
var hasBet = false;
var cashed = false;
var currentMult = 1.0;

socket.on('game_update', function(data){
    currentMult = data.multiplier;
    document.getElementById('multiplier').innerText = data.multiplier.toFixed(2) + 'x';
    document.getElementById('plane').style.transform = 'translateX('+(data.multiplier*20)+'px) translateY(-'+(data.multiplier*5)+'px)';
    if(data.crashed){
        document.getElementById('crashed').style.display='block';
        document.getElementById('multiplier').style.color='#ef4444';
        hasBet=false;
        document.getElementById('betBtn').disabled=false;
        document.getElementById('cashBtn').disabled=true;
    } else {
        document.getElementById('crashed').style.display='none';
        document.getElementById('multiplier').style.color='#22c55e';
    }
});

function placeBet(){
    hasBet=true;
    cashed=false;
    document.getElementById('betBtn').disabled=true;
    document.getElementById('cashBtn').disabled=false;
    document.getElementById('info').innerText='Pari placé! Attends le cash out';
}
function cashOut(){
    if(hasBet && !cashed){
        cashed=true;
        var win = (100 * currentMult).toFixed(0);
        document.getElementById('info').innerText='GAGNÉ: '+win+' ! à '+currentMult.toFixed(2)+'x';
        document.getElementById('cashBtn').disabled=true;
        document.getElementById('betBtn').disabled=false;
        hasBet=false;
    }
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

def game_loop():
    while True:
        # Nouveau tour
        game_state['multiplier'] = 1.0
        game_state['is_flying'] = True
        game_state['crashed'] = False
        crash_point = random.uniform(1.1, 10.0)
        # Si random < 0.1 crash instant
        if random.random() < 0.1:
            crash_point = random.uniform(1.0, 1.2)
        
        while game_state['multiplier'] < crash_point and game_state['is_flying']:
            game_state['multiplier'] += 0.05
            socketio.emit('game_update', {'multiplier': game_state['multiplier'], 'crashed': False})
            time.sleep(0.1)
        
        # Crash
        game_state['crashed'] = True
        game_state['is_flying'] = False
        socketio.emit('game_update', {'multiplier': game_state['multiplier'], 'crashed': True})
        time.sleep(5)

threading.Thread(target=game_loop, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
