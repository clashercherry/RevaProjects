from io import BytesIO
from flask import Flask, render_template, url_for, request,session
from flask.helpers import send_file
from flask_mysqldb import MySQL
import MySQLdb
import os
import random
import string
from werkzeug.utils import redirect, secure_filename
from azure.storage.blob import BlockBlobService
import numpy as np
import os

# to activate the env--source env/bin/activate

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'cherry.mysql.pythonanywhere-services.com'
app.config['MYSQL_USER'] = 'cherry'
app.config['MYSQL_PASSWORD'] = 'cherrypassword'
app.config['MYSQL_DB'] = 'cherry$project'

app.config['UPLOAD_FOLDER'] = 'Uploads'


app.config['ACCOUNT'] = 'backendproject'
app.config['STORAGE_KEY'] = 'Ygxxs2zb94AuUfaLO549ActZSGtru2duXkphaJfqrS4UZfr8Xb/n+i+eiiy8+wR1YitzTyyok95Ks9zKSzRYAA=='
app.config['CONTAINER'] = 'files'


account = app.config['ACCOUNT']   # Azure account name
key = app.config['STORAGE_KEY']      # Azure Storage account access key
container = app.config['CONTAINER']


app.secret_key = "super secret key"

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def login():
    msg = ''
    if 'flag' in request.form:
        if request.method == 'POST' and 'username' in request.form and 'pass' in request.form:
            username = request.form['username']
            password = request.form['pass']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'SELECT * FROM users WHERE username = %s AND password = %s',(username, password,))
            account = cursor.fetchone()
            if account:
                session['username']=request.form['username']
                msg = 'Logged in successfully !'
                return search()
            else:
                msg = 'Incorrect username / password !'
        return render_template('index.html', msg=msg)
    else:
        return signup()
def signup():
    msg=''
    if request.method == 'POST' and 'username' in request.form and 'pass' in request.form:
        username = request.form['username']
        password = request.form['pass']
        password_check = request.form['passcheck']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if password == password_check:
            cursor.execute('SELECT * from users WHERE username = "%s"' % username)
            account1 =cursor.fetchone()
            if account1 :
                msg='Account already exists!'
                return render_template('index.html',signup_msg=msg)
            else:
                cursor.execute(
                'INSERT INTO users(username,password)values(%s,%s)', (username, password, ))
                cursor.connection.commit()
                msg = 'SignUp successfully ! Login'
                return render_template('index.html',signup_msg=msg)
        else:
             msg="password not match"   
             return render_template('index.html', signup_msg=msg)
    return render_template('index.html', signup_msg=msg)

# @app.route('/search', methods=['POST'])
# def upload_file():
#     f = request.files["filename"]
#     f.save(os.path.join(
#         app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
#     return render_template("search.html", msg=f.filename)

blob_service = BlockBlobService(
    account_name=account, account_key=key)

@app.route('/search')
def search():
    if 'username' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT title,Gname from proj')
        data = cursor.fetchall()
        cursor.connection.commit()
        return render_template("search.html",data=data)
    else:
        return redirect(url_for('index'))

reqfiles=''
@app.route('/download/<title>')
def download(title):
    global reqfiles
    if 'username' in session:
        filename=title
        print("working",filename)
        dir = 'static/files'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT UPfilename from proj WHERE title="%s"'%filename)
        data = cursor.fetchone()
        try:
            resName=data['UPfilename']
            print(resName)
            reqfiles=resName
            location="/home/cherry/RevaProjects/static/files/"+resName
            blob_service.get_blob_to_path(container,resName,location)
            #return send_file(location)
            return redirect(url_for('preview'))
        except:
            return redirect(url_for('preview'))
    else:
        return redirect(url_for('index'))
@app.route('/preview')
def preview():
    print("hii",reqfiles)
    return render_template("preview.html",data=reqfiles)
@app.route('/upload')
def upload():
    if 'username' in session:
        return render_template("upload.html")
    else:
        return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'username' in session:
        if request.method == 'POST':
            file = request.files['filename']
            title = request.form['title']
            GroupNo = request.form['GroupNo']
            year = request.form['year']
            Gname = request.form['Gname']
            filename = secure_filename(file.filename)
            fileextension = filename.rsplit('.', 1)[1]
            Randomfilename = id_generator()
            filename = Randomfilename + '.' + fileextension
            try:
                blob_service.create_blob_from_stream(container, filename, file)
                print("the username is")
                user_name = session['username']
                print("the username is",user_name)
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO proj(username,UPfilename,title,GroupNo,year,Gname) values(%s,%s,%s,%s,%s,%s)',(user_name,filename,title,GroupNo,year,Gname))
                cursor.connection.commit()
                return redirect(url_for('search'))
            except Exception as e :
                print(e,"errro")
            ref = 'http://' + account + '.blob.core.windows.net/' + container + '/' + filename
            data = blob_service.get_blob_to_bytes(container,filename)
            # x = np.fromstring(data.content, dtype='uint16')
            # img = cv2.imdecode(x, cv2.IMREAD_UNCHANGED)     
            # cv2.imwrite("temp.png", img)
            return render_template("search.html")
    else:
        return redirect(url_for('index'))

@app.route('/result',methods=['GET', 'POST'])
def result():
    if 'username' in session:
        if request.method == 'POST':
            reqtitle = "%"+request.form['reqtitle']+"%"
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT title,Gname from proj where title LIKE %s or Gname LIKE %s',(reqtitle,reqtitle))
            data = cursor.fetchall()
            cursor.connection.commit()
            return render_template("result.html",data=data)
    else:
        return redirect(url_for('index'))

   
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))
def id_generator(size=32, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


if __name__ == "__main__":
    app.run(debug=True)
