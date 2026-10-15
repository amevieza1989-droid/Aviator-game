from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="background:#111;color:gold;text-align:center;padding:50px;font-family:Arial">
        <h1>🏆 LOTO STATS PRO V4 EST LIVE !</h1>
        <p style="color:white;font-size:20px;">Serveur OK ✅</p>
        <p>Tu as réussi ! Le site est en ligne.</p>
    </body>
    </html>
    """

# C'est cette ligne qui manquait
if __name__ == "__main__":
    app.run()
