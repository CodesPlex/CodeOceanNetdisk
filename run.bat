@echo off

REM 安装Python的flask库
pip install flask

REM 打开默认ip和端口的网站(http://127.0.0.1:5000)
start http://127.0.0.1:5000

REM 运行Python项目
python app.py

REM 退出
pause