# -*- coding: utf-8 -*-
import logging
import asyncio
import argparse
import aiohttp_cors
from aiohttp import web
from web_tools.spider_log import SpiderLog
from urls import urlpatterns
from web_tools.tools import get_ip
from middleware.JWTfilter import LoginAuth
from setting import is_auth_required, login_name


class Router(SpiderLog):
    def __init__(self, app_name):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app_name = app_name
        if is_auth_required:
            self.auth_required = LoginAuth().auth_required


    async def make_router(self, url_patterns):
        url_patterns_map = {}
        for url_list in url_patterns:
            app_name = ''
            for method_info in url_list:
                app_name = method_info[2].__qualname__.split('.')[0]
            url_patterns_map[app_name] = url_list
        return url_patterns_map

    async def init(self, loop):
        app_server = argparse.ArgumentParser(description="服务启动中心")
        app_server.add_argument(
            "-d", "--app_name", help="启动指定的app服务 例 python -d <app_name>", metavar=""
        )
        args = app_server.parse_args()
        app = web.Application(loop=loop)
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        })
        url_patterns_map = await self.make_router(url_patterns=urlpatterns)
        if args.app_name or self.app_name:
            url_list = url_patterns_map[args.app_name if args.app_name else self.app_name]
            for method_info in url_list:
                method = method_info[2]
                router_method = self.auth_required(method) if is_auth_required and method.__name__ not in login_name else method
                app.router.add_route(method_info[0], method_info[1], router_method)
        else:
            for app_name, url_list in url_patterns_map.items():
                for method_info in url_list:
                    method = method_info[2]
                    router_method = self.auth_required(method) if is_auth_required and method.__name__ not in login_name else method
                    app.router.add_route(method_info[0], method_info[1], router_method)

        for route in list(app.router.routes()):
            cors.add(route)
        await loop.create_server(app.make_handler(), '0.0.0.0', 8889)
        self.logger.info(
            f'''===================={args.app_name if args.app_name else self.app_name}服务启动成功 http://{ get_ip() }:{8889} =====================''')


def start_server(app_name=''):
    router = Router(app_name=app_name)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(router.init(loop))
    loop.run_forever()


if __name__ == '__main__':
    router = Router('')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(router.init(loop))
    loop.run_forever()
