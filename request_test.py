"""
pip install flask
python request_test.py

dann kann der bot getestet werden ohne dass die api läuft und irgendwas gespeichert wird
"""
from flask import Flask

app = Flask(__name__)

@app.route('/characters/create', methods=['GET', 'POST'])
def characters_create():
    return 'OK'

if __name__ == "__main__":
    app.run(port=8080)