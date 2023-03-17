# -*- coding: utf-8 -*-
from application.First_app.first_app import First_app

first_app = First_app()

url_list = [
    ['GET', '/request_info', first_app.request_info],
    ['GET', '/post_info', first_app.post_info],
]
