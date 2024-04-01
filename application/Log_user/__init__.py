# import requests
# import json
#
# url = 'http://bailian-aliyun-crawler9.bl-ai.com:9999/weihuweb/login'
# data = {
#     'username': 'yuanshaohang',
#     'password': 'yhHoRatHtG8'
# }
#
# response = requests.post(url=url, json=data)
# print(response.cookies.get_dict())
# print(response.text)


# from aiohttp import web
# import time
# from authlib.jose import jwt
#
#
# async def login(request):
#     data = await request.post()
#     username = data['username']
#     password = data['password']
#
#     # 验证用户是否存在并密码是否正确
#     user = await db.get_user(username)
#     if user and check_password(user['password'], password):
#         # 生成 Token
#         payload = {'sub': user['id'], 'name': user['name'], 'iat': int(time.time())}
#         token = jwt.encode({'alg': 'HS256', 'typ': 'JWT'}, payload, 'secret')
#
#         # 将 Token 返回给客户端
#         return web.json_response({'token': token})
#     else:
#         return web.json_response({'error': 'Invalid username or password'})
