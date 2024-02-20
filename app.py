import os
import json
import shutil
import datetime
import re
import hashlib
from flask import *
from flask.logging import *

# pip install pymysql
# pyinstaller --onefile --add-data "templates/*;templates/" app.py

# md5加密方法
def md5(_str:str):
    hl = hashlib.md5()
    hl.update(_str.encode(encoding='utf-8'))
    return hl.hexdigest()

users_file = "configuration.json"
json_configuration = """{
    "IP":"127.0.0.1",
    "port":"5000"
}"""

if not os.path.exists(users_file):  
    with open(users_file, 'w') as f:  
        f.write(json_configuration)

with open("configuration.json", 'r') as f:
    data = json.load(f)

Ip = data['IP']  
port = data['port'] 

ip_ = Ip
numip = port

data_folder = "data"
# 检查文件夹是否存在  
if not os.path.exists(data_folder):  
    # 如果文件夹不存在，则创建它  
    os.makedirs(data_folder)

users_file = "users.json"
# 检查文件是否存在  
if not os.path.exists(users_file):  
    # 如果文件不存在，则创建它  
    with open(users_file, 'w') as f:  
        # 这里可以添加你想要写入文件的初始内容，例如一个空的JSON对象  
        f.write('{}')

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join('data')
users_file = os.path.join('users.json')
logs_dir = os.path.join('logs')

# 创建日志文件夹
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# 配置日志记录
log_file = os.path.join(logs_dir, f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建StreamHandler来将日志输出到终端
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# 创建Formatter并定义去除颜色代码的函数
class ColorFormatter(logging.Formatter):
    color_pattern = re.compile(r'\x1b[^m]*m')

    def format(self, record):
        message = super().format(record)
        return self.color_pattern.sub('', message)

formatter = ColorFormatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

logging.getLogger().addHandler(stream_handler)

# 404 页面
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'),404

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        password = md5(password)
        
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        if username in users and users[username] == password:
            session['username'] = username
            logging.info(f"User '{username}' logged in")
            return redirect('/')
        else:
            logging.warning(f"Failed login attempt for user '{username}'")
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        password = md5(password)

        username1 = username

        if username1 == " ":
            return render_template('register.html', error='用户名不可以为空格')
        
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        if username in users:
            logging.warning(f"Failed registration attempt. Username '{username}' already exists")
            return render_template('register.html', error='用户名已存在')
        
        users[username] = password
        
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=4)
        
        logging.info(f"New user registered. Username: '{username}'")
        return redirect('/login')
    
    return render_template('register.html')

# 登出
@app.route('/logout')
def logout():
    if 'username' in session:
        username = session['username']
        session.pop('username', None)
        logging.info(f"User '{username}' logged out")
    return redirect('/login')

# 主页
@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        user_dir = os.path.join(data_dir, username)
        
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        
        files = os.listdir(user_dir)
        return render_template('index.html', username=username, files=files)
    else:
        return redirect('/login')

# 上传文件
@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'username' in session:
            username = session['username']
            user_dir = os.path.join(data_dir, username)
            
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            
            file = request.files['file']
            filename = file.filename
            if filename != "":
                file.save(os.path.join(user_dir, filename))
                
                logging.info(f"File '{filename}' uploaded by user '{username}'")
        
        return redirect('/')
    except:
        data1 = "程序错误！"

@app.route('/downloads/<username>/<filename>')
def downloads(username, filename):
    if 'username' in session and session['username'] == username:

        user_dir = os.path.join(data_dir, username)
        file_path = os.path.join(user_dir, filename)
        
        if os.path.isfile(file_path):
            logging.info(f"File '{filename}' downloaded by user '{username}'")
            return send_from_directory(user_dir, filename, as_attachment=True)
        else:
            return render_template('file_does_not_exist.html')
    
    return redirect('/login')

# 在线浏览
@app.route('/viewer/<username>/<path:filename>')
def viewer(username,filename):
    # 检查文件类型
    # if filename.endswith(('.mp4', '.mp3', '.txt', '.pdf')):
    if filename.endswith(('.mp4', '.mp3', '.png', '.jpg',".ico",".avif",".svg")):
        # 返回在线浏览页面
        return render_template('viewer.html', username=username ,filename=filename)
    else:
        # 返回不支持在线浏览的提示信息
        return render_template('not_viewer.html')

"""多人在线浏览

# 多人在线浏览
@app.route('/viewers/<username>/<path:filename>')
def viewers(username, filename):
    # 检查文件类型
    # if filename.endswith(('.mp4', '.mp3', '.txt', '.pdf')):
    if filename.endswith(('.mp4', '.mp3', '.png', '.jpg', ".ico", ".avif", ".svg")):
        # 返回在线浏览页面
        return render_template('viewer.html', username=username, filename=filename)
    else:
        # 返回不支持在线浏览的提示信息
        return render_template('not_viewer.html')

@app.route('/downloads/<username>/<filename>')
def download2s(username, filename):
    user_dir = os.path.join(data_dir, username)
    file_path = os.path.join(user_dir, filename)

    if os.path.isfile(file_path):
        logging.info(f"File '{filename}' downloaded by user '{username}'")
        return send_from_directory(user_dir, filename, as_attachment=True)
    else:
        return render_template('file_does_not_exist.html')
"""

# 下载文件
@app.route('/download/<username>/<filename>')
def download(username, filename):
    try:
        if 'username' in session and session['username'] == username:

            # user_dir = os.path.join(data_dir, username)
            # file_path = os.path.join(user_dir, filename)

            user_dir = os.path.join(data_dir, username)
            file_path = os.path.join(user_dir, filename)

            if os.path.isfile(file_path):
                logging.info(f"File '{filename}' downloaded by user '{username}'")
                return send_from_directory(user_dir, filename, as_attachment=True)
            else:
                return render_template('file_does_not_exist.html')
        
        return redirect('/login')
    except:
        data1 = "程序错误！"

# 删除文件
@app.route('/delete/<username>/<path:file_path>')
def delete(username, file_path):
    if 'username' in session and session['username'] == username:
        user_dir = os.path.join(data_dir, username)
        abs_file_path = os.path.join(user_dir, file_path)
        
        if os.path.exists(abs_file_path):
            if os.path.isfile(abs_file_path):
                os.remove(abs_file_path)
                logging.info(f"File '{file_path}' deleted by user '{username}'")
            else:
                shutil.rmtree(abs_file_path)
                logging.info(f"Folder '{file_path}' deleted by user '{username}'")
    
    return redirect('/')

if __name__ == '__main__':
    app.run(ip_,numip)