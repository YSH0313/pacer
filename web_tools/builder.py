import os
import sys
import time
import socket
import random
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def re_name(str_data):
    new_name = ''.join([i.capitalize() for i in str_data.split('_')])
    return new_name


urls_py = """# -*- coding: utf-8 -*-
from application.{app_dir}.{app_name} import {app_class}

{app_name} = {app_class}()

url_list = [
    ['GET', '/{app_name}_index', {app_name}.index]
]
"""


def creat_urls(app_name):
    app_dir = app_name.capitalize()
    app_class = app_dir
    urls_model = urls_py.format(app_dir=app_dir, app_name=app_name, app_class=app_class)
    return urls_model


app_py = """# -*- coding: utf-8 -*-
from aiohttp import web
from middleware.connecter import Cluster


class {app_class}(Cluster):
    def __init__(self):
        super().__init__()

    async def index(self, request):
        return web.Response(text='Hello World!')
"""


def creat_app(app_name):
    app_class = app_name.capitalize()
    app_model = app_py.format(app_class=app_class)
    return app_model


def creat_file(path, app_name=None):
    init_file = open(f'{path}/__init__.py', 'w')
    init_file.close()
    with open(f'{path}/urls.py', 'wb') as u:
        url_model = creat_urls(app_name)
        u.write(url_model.encode('utf-8'))
    with open(f'{path}/{app_name}.py', 'wb') as a:
        app_model = creat_app(app_name)
        a.write(app_model.encode('utf-8'))
    return


def production(app_name):
    sys.argv.pop(0)
    current_path = os.getcwd()
    if len(sys.argv) != 0:
        current_path = current_path
    else:
        current_path = f'{os.getcwd()}/application/{app_name.capitalize()}'  # 应用路径

    flag = os.path.exists(current_path)
    if not flag:  # 不存在即创建
        os.makedirs(current_path)
        creat_file(path=current_path, app_name=app_name)
        print(f'{app_name.capitalize()}应用创建成功')
    elif flag:  # 如果存在，人工判断是否覆盖
        print(f'\033[1;31;0m名称为：{app_name.capitalize()}的应用已经存在\033[0m')
        while 1:
            judge = input('是否覆盖(y/n)?')
            if judge == 'y':
                creat_file(path=current_path, app_name=app_name)
                print('已覆盖')
                break
            if judge == 'n':
                pass
                break
            else:
                pass


if __name__ == '__main__':
    production('ceshi_app')
