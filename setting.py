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
    'host': 'yours',
    'port': 63791,
    'password': 'yours'
}

is_auth_required = False  # 是否要开启用户登录验证
login_whitelist = ['login']  # 用于给登录验证添加白名单，不进行验证登录