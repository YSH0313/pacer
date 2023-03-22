# mysql数据库连接
Mysql = {
    'MYSQL_HOST': 'yours',
    'MYSQL_DBNAME': 'yours',
    'MYSQL_USER': 'yours',
    'MYSQL_PASSWORD': 'yours',
    'PORT': 3306
}
# 连接redis数据库
REDIS_HOST_LISTS = {
    'host': 'bailian-aliyun-crawler7.bl-ai.com',
    'port': 63791,
    'password': 'dADM1QUHjD@'
}

is_auth_required = False  # 是否要开启用户登录验证
login_name = ['login']  # 登录视图方法名，用于给登录视图添加白名单，不验证登录