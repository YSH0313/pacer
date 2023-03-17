# -*- coding: utf-8 -*-
from aiohttp import web
from middleware.connecter import Cluster


class First_app(Cluster):
    def __init__(self):
        super().__init__()

    async def get_result(self, fun_name, spider_name, spider_id):
        return {"code": "200", "msg": 'Successful!', 'data': [fun_name, spider_name, spider_id]}

    async def request_info(self, request):
        try:
            spider_name = request.rel_url.query.get('spider_name')
            spider_id = request.rel_url.query.get('spider_id')
            a = self.production_md5(spider_name)
            print(spider_name, spider_id, a)
            # spider_name = request.match_info.get('spider_name')
            # spider_id = request.match_info.get('spider_id')
            if spider_name:
                result = await self.get_result('request_info', spider_name, spider_id)
                print('返回值：' + str(result))
                print('获取数据成功')
                print('完成')
                return web.json_response(result)
        except:
            import traceback
            traceback.print_exc()
            return web.json_response({"code": "500", "msg": 'System anomaly'})

    async def post_info(self, request):
        try:
            spider_name = request.rel_url.query.get('spider_name')
            spider_id = request.rel_url.query.get('spider_id')
            print(spider_name, spider_id)
            # spider_name = request.match_info.get('spider_name')
            # spider_id = request.match_info.get('spider_id')
            if spider_name:
                result = await self.get_result('post_info', spider_name, spider_id)
                print('返回值：' + str(result))
                print('获取数据成功')
                print('完成')
                return web.json_response(result)
        except:
            import traceback
            traceback.print_exc()
            return web.json_response({"code": "500", "msg": 'System anomaly'})
