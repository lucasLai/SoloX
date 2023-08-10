from __future__ import absolute_import
import multiprocessing
import subprocess
import time
import os
import platform
import re
import webbrowser
import requests
import socket
import sys
from view.apis import api
from view.pages import page
from logzero import logger
from threading import Lock
from flask_socketio import SocketIO, disconnect
from flask import Flask
from pyfiglet import Figlet
from solox import __version__

app = Flask(__name__, template_folder='templates', static_folder='static')
app.register_blueprint(api)
app.register_blueprint(page)

socketio = SocketIO(app, cors_allowed_origins="*")
thread = True
thread_lock = Lock()


@socketio.on('connect', namespace='/logcat')
def connect():
    socketio.emit('start connect', {'data': 'Connected'}, namespace='/logcat')
    logDir = os.path.join(os.getcwd(),'adblog')
    if not os.path.exists(logDir):
        os.mkdir(logDir)
    global thread
    thread = True
    with thread_lock:
        if thread:
            thread = socketio.start_background_task(target=backgroundThread)


def backgroundThread():
    global thread
    try:
        # logger.info('Initializing adb environment ...')
        # os.system('adb kill-server')
        # os.system('adb start-server')
        current_time = time.strftime("%Y%m%d%H", time.localtime())
        logPath = os.path.join(os.getcwd(),'adblog',f'{current_time}.log')
        logcat = subprocess.Popen(f'adb logcat *:E > {logPath}', stdout=subprocess.PIPE,
                                  shell=True)
        with open(logPath, "r") as f:
            while thread:
                socketio.sleep(1)
                for line in f.readlines():
                    socketio.emit('message', {'data': line}, namespace='/logcat')
        if logcat.poll() == 0:
            thread = False
    except Exception:
        pass


@socketio.on('disconnect_request', namespace='/logcat')
def disconnect():
    global thread
    logger.warning('Logcat client disconnected')
    thread = False
    disconnect()

def ip() -> str:
    ip = socket.gethostbyname(socket.gethostname())
    return ip


def listen(port):
    if platform.system() != 'Windows':
        os.system("lsof -i:%s| grep LISTEN| awk '{print $2}'|xargs kill -9" % port)
    else:
        port_cmd = 'netstat -ano | findstr {}'.format(port)
        r = os.popen(port_cmd)
        r_data_list = r.readlines()
        if len(r_data_list) == 0:
            return
        else:
            pid_list = []
            for line in r_data_list:
                line = line.strip()
                pid = re.findall(r'[1-9]\d*', line)
                pid_list.append(pid[-1])
            pid_set = list(set(pid_list))[0]
            pid_cmd = 'taskkill -PID {} -F'.format(pid_set)
            os.system(pid_cmd)

def status(host: str, port: int):
    r = requests.get('http://{}:{}'.format(host, port), timeout=2.0)
    flag = (True, False)[r.status_code == 200]
    return flag


def open_url(host: str, port: int):
    flag = True
    while flag:
        logger.info('start solox server ...')
        f = Figlet(font="slant", width=300)
        print(f.renderText("SOLOX {}".format(__version__)))
        flag = status(host, port)
    webbrowser.open('http://{}:{}/?platform=Android&lan=en'.format(host, port), new=2)
    logger.info('Running on http://{}:{}/?platform=Android&lan=en (Press CTRL+C to quit)'.format(host, port))


def start(host: str, port: int):
    socketio.run(app, host=host, debug=False, port=port)

def main(host=ip(), port=50003):
    try:
        listen(port=port)
        pool = multiprocessing.Pool(processes=2)
        pool.apply_async(start, (host, port))
        pool.apply_async(open_url, (host, port))
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        logger.info('stop solox success')
        sys.exit()
    except Exception as e:
        logger.exception(e)            


if __name__ == '__main__':
    main()