# -*- coding: utf-8 -*-
from application.Log_user.Log_user import Log_user

Log_user = Log_user()

url_list = [
    ['POST', '/Log_user_index', Log_user.login]
]