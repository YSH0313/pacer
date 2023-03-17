# -*- coding: utf-8 -*-
from aiohttp import web
from functools import wraps
from middleware.connecter import Cluster
from ldap3 import ALL, Connection, Server
from aiohttp_session import get_session
from decorator import decorator
import json
from authlib.jose import jwt
from authlib.jose.errors import ExpiredTokenError
import time
from datetime import datetime, timedelta


class InvalidUserOrPasswordException(Exception):
    def __init__(self):
        self.message = '没有此用户'


class Log_user(Cluster):
    def __init__(self):
        super().__init__()
        self._SERVER = Server('ldap.bl-ai.com', get_info=ALL)
        self._BASE_DN_USER = 'ou=users,dc=bailian,dc=ai'

    async def login_success(self, username: str, password: str):
        user = f"cn={username},{self._BASE_DN_USER}"
        conn = Connection(self._SERVER, user=user, password=password)
        if not conn.bind():
            raise InvalidUserOrPasswordException()
        return True

    # # 登录视图函数
    async def login(self, request):
        info = await request.text()
        data = json.loads(info)
        # data = await request.post()
        username = data['username']
        password = data['password']

        # 验证用户是否存在并密码是否正确
        if await self.login_success(username, password):
            # 设置过期时间为 30 分钟
            expires_in = timedelta(minutes=525600)

            # 生成当前时间和过期时间
            now = datetime.utcnow()
            expires_at = now + expires_in

            # 生成 Token
            # payload = {'sub': username, 'username': username, 'iat': int(time.time())}
            payload = {
                'sub': username,
                'username': username,
                'iat': now,
                'exp': expires_at,
            }

            token = jwt.encode({'alg': 'HS256', 'typ': 'JWT'}, payload, 'yuanshaohang').decode('utf-8')
            self.r.set(username, token)
            # 将 Token 返回给客户端
            return web.json_response({'code': 200, 'message': '登录成功！', 'token': token})
        else:
            return web.json_response({'error': 'Invalid username or password'})
