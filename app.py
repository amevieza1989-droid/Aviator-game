import random, time, threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# === ETAT DU JEU ===
game_state = {
    'multiplier': 1.0,
    'is_crashed': False,
    'history': [],
    'phase': 'waiting' # waiting, flying, crashed
}

def game_loop():
    while True:
        # Phase 1 : Attente 3 secondes
        game_state['phase'] = 'waiting'
        game_state['multiplier'] = 1.0
        game_state['is_crashed'] = False
        socketio.emit('waiting', {'time': 3})
        time.sleep(3)

        # Phase 2 : Vol
        game_state['phase'] = 'flying'
        game_state['multiplier'] = 1.0
        crash_point = random.uniform(1.1, 10.0)
        if random.random() < 0.15: # 15% de crash tot
            crash_point = random.uniform(1.0, 1.5)
        
        last_multiplier = 1.0
        
        while game_state['multiplier'] < crash_point:
            last_multiplier = game_state['multiplier']
            game_state['multiplier'] += 0.02 + (game_state['multiplier'] * 0.002)
            socketio.emit('update', {'multiplier': round(game_state['multiplier'], 2)})
            time.sleep(0.1)

        # Phase 3 : Crash - CORRECTION DU BUG 1.01x
        game_state['phase'] = 'crashed'
        game_state['is_crashed'] = True
        final_value = round(last_multiplier, 2)
        game_state['history'].insert(0, final_value)
        if len(game_state['history']) > 10:
            game_state['history'].pop()
        
        socketio.emit('crashed', {'multiplier': final_value, 'history': game_state['history']})
        print(f"CRASH a {final_value}x (pas 1.01x)")
        time.sleep(3)

HTML = """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
body{background:#0b0e1a;color:white;font-family:Arial;text-align:center;margin:0}
.history{display:flex;gap:5px;overflow-x:auto;padding:10px;background:#1a1e33}
.history span{padding:5px 10px;border-radius:15px;font-weight:bold}
.low{background:#ff3b3b} .high{background:#00d26a} .mid{background:#ffaa00}
#plane{font-size:80px;margin-top:40px;transition:0.1s}
#multiplier{font-size:60px;font-weight:bold;margin:20px}
.crashed{color:#ff3b3b}
</style>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
</head><body>
<div class="history" id="history"></div>
<div id="plane">✈️</div>
<div id="multiplier">1.00x</div>
<div id="status">En attente...</div>
<script>
var socket = io();
socket.on('update', (d)=>{
 document.getElementById('multiplier').innerText = d.multiplier.toFixed(2)+'x';
 document.getElementById('plane').style.transform = 'translateX('+(d.multiplier*10)+'px) translateY('+(-d.multiplier*2)+'px)';
});
socket.on('waiting', (d)=>{
 document.getElementById('status').innerText = 'Prochain tour dans '+d.time+'s';
 document.getElementById('multiplier').className='';
 document.getElementById('plane').style.transform='translateX(0) translateY(0)';
});
socket.on('crashed', (d)=>{
 document.getElementById('multiplier').innerText = d.multiplier.toFixed(2)+'x';
 document.getElementById('multiplier').className='crashed';
 document.getElementById('status').innerText = 'CRASH a '+d.multiplier+'x !';
 let h = document.getElementById('history'); h.innerHTML='';
 d.history.forEach(v=>{
  let cls = v<2?'low':v<5?'mid':'high';
  h.innerHTML += '<span class='+cls+'>'+v.toFixed(2)+'x</span>';
 });
});
</script></body></html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

threading.Thread(target=game_loop, daemon=True).start()

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
