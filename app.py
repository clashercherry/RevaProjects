
from flask import Flask, render_template, url_for, request,session
from flask.helpers import send_file
from flask_mysqldb import MySQL

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
