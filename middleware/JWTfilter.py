# -*- coding: utf-8 -*-
# @Author: yuanshaohang
# @Date: 2023-03-22- 14:13:39
# @Version: 1.0.0
# @Description: TODO
from connecter import RedisDb
import logging
from aiohttp import web
from functools import wraps
from authlib.jose import jwt
from authlib.jose.errors import ExpiredTokenError


class LoginAuth(RedisDb):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    # 登录注册装饰器
    def auth_required(self, func):
        @wraps(func)
        async def wrapped(request, *args, **kwargs):
            if not request.headers.get('Authorization'):
                self.logger.info('用户未登录')
                return web.json_response({'code': 401, 'message': '用户未登录'})
            else:
                Authorization = request.headers.get('Authorization')
                try:
                    user_info = jwt.decode(Authorization, 'yuanshaohang')
                    user_info.validate()
                    if self.r.get(user_info.get('username')):
                        return await func(request, *args, **kwargs)
                    else:
                        return web.json_response({'code': 401, 'message': '登录失效'})
                except ExpiredTokenError:
                    return web.json_response({'code': 401, 'message': '登录失效'})

        return wrapped
