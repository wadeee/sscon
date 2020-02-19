from flask import Flask, request
from jinja2 import Environment, select_autoescape, FileSystemLoader
import os
import json
import re

app = Flask(__name__)
loader = FileSystemLoader('templates')
env = Environment(loader=loader, autoescape=select_autoescape(['html']))


@app.route('/')
def index():
    template = env.get_template('index.html')
    result = template.render()
    return result


@app.route('/ssinfo')
def ssinfo():
    ssconfiglist = []
    ssservices = os.popen('ls /etc/systemd/system | grep shadowsocks-').read().split('\n')
    for ssservice in ssservices:
        if re.search('(?<=shadowsocks-).*(?=\.service)', ssservice):
            servicestatus = os.popen('systemctl status ' + ssservice).read()
            with open('/etc/shadowsocks-' + re.search('(?<=shadowsocks-).*(?=\.service)', ssservice).group() + '.json',
                      'r') as f:
                ssconfig = json.load(f)
            activestatus = re.search('(?<=Active: )(active|inactive|failed)', servicestatus).group()
            ssconfiglist.append({
                'IP': '23.105.207.48',
                'port': ssconfig['server_port'],
                'password': ssconfig['password'],
                'encryption': ssconfig['method'],
                'status': activestatus,
            })

    return json.dumps(ssconfiglist)


@app.route('/addss', methods=['post'])
def addss():
    port = request.json.get('port')
    password = request.json.get('password')
    ssconfigfilepath = '/etc/shadowsocks-' + port + '.json'
    ssserviceconfigfilepath = '/etc/systemd/system/shadowsocks-' + port + '.service'

    ssconfig = {'server': "0.0.0.0",
                'server_port': port,
                'password': password,
                'timeout': 600,
                'method': "aes-256-cfb"}

    ssserviceconfig = [
        '[Unit]\n',
        'Description=Shadowsocks-' + port + '\n',
        '[Service]\n',
        'TimeoutStartSec=0\n',
        'ExecStart=/root/.pyenv/shims/ssserver -c ' + ssconfigfilepath + '\n',
        '[Install]\n',
        'WantedBy=multi-user.target\n'
    ]

    with open(ssconfigfilepath, 'w') as ssconfigfile, open(ssserviceconfigfilepath, 'w') as ssserviceconfigfile:
        ssconfigfile.writelines(json.dumps(ssconfig))
        ssserviceconfigfile.writelines(ssserviceconfig)

    os.system('systemctl enable shadowsocks-' + port)
    os.system('systemctl start shadowsocks-' + port)

    return ""


@app.route('/removess', methods=['post'])
def removess():
    port = str(request.json.get('port'))
    os.system('systemctl disable shadowsocks-' + port)
    os.system('systemctl stop shadowsocks-' + port)
    os.system('rm /etc/shadowsocks-' + port + '.json')
    os.system('rm /etc/systemd/system/shadowsocks-' + port + '.service')

    return ""


if __name__ == '__main__':
    app.run()
