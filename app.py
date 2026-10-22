from flask import Flask
import os
app = Flask(__name__)
@app.route('/')
def home():
    return '<h1 style="color:gold;background:black;padding:20px">LOTO V19 OK - DEPLOY REUSSI</h1>'
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
