import os
import re
from collections import Counter
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///loto.db').replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# TES LOTERIES - Tu peux ajouter d'autres pays ici
LOTERIES = {
    "TG": {"nom": "Togo LONATO", "max": 90, "flag": "🇹🇬"},
    "BJ": {"nom": "Bénin LNB", "max": 90, "flag": "🇧🇯"},
    "CI": {"nom": "Côte d'Ivoire LONACI", "max": 90, "flag": "🇨🇮"},
    "GH": {"nom": "Ghana NLA", "max": 90, "flag": "🇬🇭"},
    "SN": {"nom": "Sénégal LONASE", "max": 90, "flag": "🇸🇳"},
}

class Tirage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pays = db.Column(db.String(5), nullable=False)
    type_jeu = db.Column(db.String(50), nullable=False) # Ex: Matin 08h, Midi, Soir 18h
    numeros = db.Column(db.String(100), nullable=False) # Ex: "12,45,78,03,90"
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- LE CERVEAU DE LA V4 : CALCUL AUTO ---
def get_analyse(pays_code):
    tirages = Tirage.query.filter_by(pays=pays_code).order_by(Tirage.date.desc()).limit(100).all()
    if len(tirages) < 10: # Pas assez de données
        return None

    all_nums = []
    for t in tirages:
        try:
            nums = [int(x.strip()) for x in t.numeros.split(",") if x.strip().isdigit()]
            all_nums.extend(nums)
        except:
            continue

    if not all_nums:
        return None

    c = Counter(all_nums)
    conf = LOTERIES.get(pays_code, {"max": 90})

    # Chauds
    chauds_data = c.most_common(3)
    chauds = [{"num": n, "freq": f, "pct": round(f/len(tirages)*100,1)} for n, f in chauds_data]

    # Froids
    tous_possibles = list(range(1, conf["max"]+1))
    froids_tries = sorted(tous_possibles, key=lambda x: c.get(x,0))
    froids = [{"num": n, "freq": c.get(n,0)} for n in froids_tries[:3]]

    return {"chauds": chauds, "froids": froids, "total": len(tirages)}

# --- ROUTES ---
@app.route('/')
def index():
    analyses = {}
    derniers = {}
    for code in LOTERIES.keys():
        analyses[code] = get_analyse(code)
        derniers[code] = Tirage.query.filter_by(pays=code).order_by(Tirage.date.desc()).first()

    return render_template('index.html', loteries=LOTERIES, analyses=analyses, derniers=derniers)

@app.route('/admin/add', methods=['POST'])
def add_tirage():
    # Tu utilises ça pour ajouter les résultats: pays, type_jeu, numeros
    pays = request.form.get('pays')
    type_jeu = request.form.get('type_jeu')
    numeros = request.form.get('numeros')

    if pays and type_jeu and numeros:
        # Nettoyage
        numeros_clean = re.sub(r'[^0-9,]', '', numeros)
        t = Tirage(pays=pays, type_jeu=type_jeu, numeros=numeros_clean)
        db.session.add(t)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/api/analyse/<pays_code>')
def api_analyse(pays_code):
    data = get_analyse(pays_code)
    if not data:
        return jsonify({"error": "Pas assez de données"}), 404
    return jsonify(data)

# Création DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
