import re
import json
import time
import aiohttp
import asyncio
import logging
import pymysql
from middleware.pymysqlpool.pymysqlpool import ConnectionPool
from web_tools.spider_log import SpiderLog
from web_tools.tools import Tools_user
from setting import Mysql, REDIS_HOST_LISTS
import redis


ip_lists = []
update = time.time()


class MyResponse(object):
    def __init__(self, url=None, headers=None, data=None, cookies=None, meta=None, text=None, content=None,
                 status_code=None, request_info=None, proxy=None):
        self.url = url  # 返回请求的的url
        self.data = data  # 返回请求用的data参数信息
        self.headers = headers  # 返回请求的header信息
        self.cookies = cookies  # 返回请求的cookies信息
        self.meta = meta  # 返回请求带过来的参数和值
        self.text = text  # 返回网站的响应体，包括html和json以及其他的任何数据
        self.content = content  # 返回的字节流
        self.status_code = status_code  # 返回响应状态吗
        self.request_info = request_info  # 返回请求体
        self.proxy = proxy  # 返回请求使用的代理


sem = asyncio.Semaphore(500)


class RedisDb(SpiderLog):
    def __init__(self):
        super().__init__()
        self.redis_host = REDIS_HOST_LISTS['host']
        self.redis_port = REDIS_HOST_LISTS['port']
        self.redis_pass = REDIS_HOST_LISTS['password']
        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_pass, db=7,
                             socket_timeout=None, connection_pool=None, charset='utf8', errors='strict',
                             decode_responses=True, unix_socket_path=None)


class Cluster(Tools_user, RedisDb):

    def __init__(self):
        Tools_user.__init__(self)
        RedisDb.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.success_count = 0
        self.error_count = 0
        self.url = 'http://8.140.146.196:9090/qdb/get_proxy'
        self.charset_code = re.compile(r'charset=(.*?)"|charset=(.*?)>|charset="(.*?)"', re.S)
        # self.db = pymysql.connect(host=Mysql['MYSQL_HOST'], user=Mysql['MYSQL_USER'], password=Mysql['MYSQL_PASSWORD'],
        #                           port=Mysql['PORT'], db=Mysql['MYSQL_DBNAME'], charset='utf8', use_unicode=True)
        # self.cursor = self.db.cursor()
        # self.other_db = pymysql.connect(host=Mysql['MYSQL_HOST'], user=Mysql['MYSQL_USER'], password=Mysql['MYSQL_PASSWORD'],
        #                                 port=Mysql['PORT'], db=Mysql['MYSQL_DBNAME'], charset='utf8', use_unicode=True)
        # self.other_cursor = self.other_db.cursor()

        self.host = Mysql['MYSQL_HOST']
        self.port = Mysql['PORT']
        self.user = Mysql['MYSQL_USER']
        self.password = Mysql['MYSQL_PASSWORD']
        self.db = Mysql['MYSQL_DBNAME']
        # self.conn = None
        self.pool = self.create_pool()
        self.condition_re = re.compile('(.*?)\\(')
        self.params_re = re.compile('\\((.*?)\\)')

    def on_send_success(self, *args, **kwargs):
        self.success_count += 1

    def on_send_error(self, *args, **kwargs):
        self.error_count += 1

    def prints(self, item, is_replace=True):
        item_last = {}
        for k, v in item.items():
            if (v == None) or (v == 'None') or (v == ''):
                continue
            elif (('time' not in k) or ('Time' not in k) or ('updated' not in k) or ('date' not in k)) and (
                    isinstance(v, dict) == False):
                if is_replace:
                    item_last[k] = self.d_deal(v)
                else:
                    item_last[k] = v
            elif isinstance(v, dict):
                item_last[k] = str(v)
            elif k == 'body':
                item_last[k] = """{body}""".format(body=v)
            elif ('time' in k) or ('Time' in k) or ('updated' in k) or ('date' in k) or (k.endswith('T') == True):
                item_last[k] = v
        # print(json.dumps(item_last, indent=2, ensure_ascii=False))
        self.logger.info('\r\n' + json.dumps(item_last, indent=2, ensure_ascii=False))
        return item_last

    def send_where(self, dic_str):
        where = ''
        for key, value in dic_str.items():
            if len(value) > 1:
                for v in value:
                    where += '`' + key + '`="' + v + '" or '
            elif len(value) == 1:
                where += '`' + key + '`="' + str(value[0]) + '" and '
        # where = where.rstrip(' and ')
        where = where.rstrip(' or ')
        return where

    def create_pool(self):
        conn = ConnectionPool(
            pool_name='mypool',
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            autocommit=False
        )
        return conn

    def execute(self, query, parameters=None, many=False):
        attempts = 3  # allow 3 attempts to execute the query
        while attempts > 0:
            conn = self.pool.borrow_connection()
            try:
                with conn.cursor() as cursor:
                    if many:
                        cursor.executemany(query, parameters)
                    else:
                        cursor.execute(query, parameters)
                    conn.commit()
                    if cursor.lastrowid:
                        return cursor.lastrowid
                    else:
                        return cursor.rowcount
            except pymysql.OperationalError as e:
                if e.args[0] in (2006, 2013):  # MySQL server has gone away
                    self.pool.close()
                    self.pool = self.create_pool()
                    attempts -= 1
                else:
                    raise
            except Exception as e:
                self.logger.error(f"Error while executing query: {e}")
                conn.rollback()
                attempts -= 1
                if attempts == 0:
                    raise Exception("Failed to execute query after 3 attempts")
            finally:
                self.pool.return_connection(conn)

                # if conn:
                #     conn.close()

    def insert(self, table, data, if_update=False):
        columns = ', '.join([f"`{i}`" for i in data.keys()])
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT IGNORE INTO `{table}` ({columns}) VALUES ({placeholders});"
        sql = query % tuple([f"'{i}'" if i else i for i in data.values()])
        if if_update:
            update = ', '.join([f"`{key}` = %s" for key in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update}"
            sql = query % tuple([f"'{i}'" if i else i for i in data.values()] * 2)
        self.logger.info(sql)
        return self.execute(query, tuple(data.values()))

    def update(self, table, set_data, where=None):
        set_pairs = [f"`{column}`=%s" for column in set_data.keys()]
        query = f"UPDATE `{table}` SET {', '.join(set_pairs)}"
        parameters = tuple(set_data.values())
        if where:
            query += f" WHERE {where}"
        ssql = query % tuple([f"'{i}'" if i else i for i in parameters])
        self.logger.info(ssql)
        return self.execute(query, parameters)

    def delete(self, table, where=None):
        query = f"DELETE FROM `{table}`"
        if where:
            query += f" WHERE {where}"
        self.logger.info(query)
        return self.execute(query)

    def trucate(self, table):
        sql = f"""TRUNCATE `{table}`;"""
        return self.execute(sql)

    def get_condition(self, columns):
        condition_map = {'count': 'count', 'max': 'max', 'min': 'min', 'sum': 'sum', 'avg': 'avg',
                         'distinct': 'distinct'}
        condition = ''
        if isinstance(columns, list):
            columns = ', '.join([f"`{i}`" for i in columns])
        elif isinstance(columns, str):
            condition = self.deal_re(self.condition_re.search(columns))
            condition_exis = True if [True for i in condition_map.keys() if i.upper() in columns.upper()] else False
            if not condition_exis:
                columns = ', '.join(f'`{i.strip(" ")}`' for i in columns.split(','))
        return condition_map, condition, columns

    def select(self, table, columns='*', where=None, order_by=None, limit=None, offset=None):
        condition_map, condition, columns = self.get_condition(columns)
        query = f"SELECT {columns} FROM `{table}`"
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        self.logger.info('查询字段：' + query)
        self.logger.info('===========================================================')
        with self.pool.cursor() as cursor:
            cursor.execute(query)
            data = cursor.fetchall()
            if self.judge_er(condition):
                condition_map = [i.upper() for i in condition_map.keys()]
            if f'{condition}' in condition_map:
                data = data[0].get(columns)
            return data

    def judge_er(self, str_data):
        if str_data.isupper():
            return True
        else:
            return False

    # def re_connet(self, if_other_db=False):
    #     if if_other_db:
    #         self.other_db = pymysql.connect(host=Mysql['MYSQL_HOST'], user=Mysql['MYSQL_USER'],
    #                                         password=Mysql['MYSQL_PASSWORD'], port=Mysql['PORT'],
    #                                         db=Mysql['MYSQL_DBNAME'], charset='utf8', use_unicode=True)
    #         self.other_cursor = self.other_db.cursor()
    #     else:
    #         self.db = pymysql.connect(host=Mysql['MYSQL_HOST'], user=Mysql['MYSQL_USER'],
    #                                   password=Mysql['MYSQL_PASSWORD'], port=Mysql['PORT'], db=Mysql['MYSQL_DBNAME'],
    #                                   charset='utf8', use_unicode=True)
    #         self.cursor = self.db.cursor()
    #
    # def trucate_sql(self, table, db_name=None, OTHER_INSERT=False):
    #     sql = """TRUNCATE `{db_name}`.`{table_name}`""".format(db_name=db_name, table_name=table)
    #     while 1:
    #         if OTHER_INSERT:
    #             try:
    #                 self.other_cursor.execute(sql)
    #                 self.other_db.commit()
    #                 break
    #             except pymysql.err.OperationalError:
    #                 self.re_connet(if_other_db=True)
    #         else:
    #             try:
    #                 self.cursor.execute(sql)
    #                 self.db.commit()
    #             except pymysql.err.OperationalError:
    #                 self.re_connet()
    #             break
    #
    # def insert(self, item, table, db_name=None, OTHER_INSERT=False, is_update=False, is_replace=True):
    #     item = self.prints(item, is_replace=is_replace)
    #     field_lists = []
    #     value_lists = []
    #     field_num = []
    #     for k, v in dict(item).items():
    #         if (v == None) or (v == 'None') or (v == ''):
    #             continue
    #         elif ('{' and '}') in v:
    #             field_lists.append("`" + str(k) + "`")
    #             value_lists.append(str(v))
    #         else:
    #             field_lists.append("`" + str(k) + "`")
    #             value_lists.append(str(v))
    #     [field_num.append('%s') for i in range(1, len(field_lists) + 1)]
    #     if db_name and is_update:
    #         new_values = []
    #         for i in value_lists:
    #             if i.isdigit():
    #                 new_values.append(i)
    #             else:
    #                 new_values.append("'" + i + "'")
    #         sql = """INSERT INTO `{db_name}`.`{table_name}`({fields}) VALUES({value_lists}) ON DUPLICATE KEY UPDATE {update_lists}""".format(
    #             db_name=db_name, table_name=table, fields=','.join(field_lists), value_lists=','.join(new_values),
    #             update_lists=','.join(self.update_item(item, is_insert=True, is_replace=is_replace)))
    #     elif db_name and is_update == False:
    #         sql = """INSERT IGNORE INTO `{db_name}`.`{table}` ({fields}) VALUES ({fields_num});""".format(
    #             db_name=db_name, table=table, fields=','.join(field_lists), fields_num=','.join(field_num))
    #     else:
    #         sql = """INSERT IGNORE INTO `{db_name}`.`{table}` ({fields}) VALUES ({fields_num});""".format(
    #             db_name=Mysql['MYSQL_DBNAME'], table=table, fields=','.join(field_lists),
    #             fields_num=','.join(field_num))
    #     while 1:
    #         if OTHER_INSERT:
    #             try:
    #                 if is_update:
    #                     self.other_cursor.execute(sql)
    #                     self.other_db.commit()
    #                 else:
    #                     self.other_cursor.execute(sql, tuple(value_lists))
    #                     self.other_db.commit()
    #                 break
    #             except pymysql.err.OperationalError:
    #                 self.re_connet(if_other_db=True)
    #         else:
    #             try:
    #                 if is_update:
    #                     self.cursor.execute(sql)
    #                     self.db.commit()
    #                 else:
    #                     self.cursor.execute(sql, tuple(value_lists))
    #                     self.db.commit()
    #                 break
    #             except pymysql.err.OperationalError:
    #                 self.re_connet()
    #     # print('===========================================================')
    #     self.logger.info('===========================================================')
    #
    # def select_data(self, field_lists=None, db_name=None, table=None, condition=None, where=0, num_id=0, min_id=0,
    #                 max_id=0, cond=None, OTHER_INSERT=False, if_dic=False):
    #     field_lists_last = []
    #     if field_lists:
    #         for i in field_lists:
    #             field_lists_last.append("`" + str(i) + "`")
    #     sq1_all = ''
    #     if (num_id == 0) and (where == 0):
    #         sq1_all = """SELECT {field_lists} FROM `{db}`.`{table}`;""".format(db=db_name,
    #                                                                            field_lists=','.join(field_lists_last),
    #                                                                            table=table)
    #     if cond != None:
    #         sq1_all = """SELECT {field_lists} FROM `{db}`.`{table}` {cond};""".format(db=db_name, field_lists=','.join(
    #             field_lists_last), table=table, cond=cond)
    #     if (num_id == 0) and (where != 0):
    #         sq1_all = """SELECT {field_lists} FROM `{db}`.`{table}` WHERE {where};""".format(db=db_name,
    #                                                                                          field_lists=','.join(
    #                                                                                              field_lists_last),
    #                                                                                          table=table, where=where)
    #     if num_id != 0:
    #         sq1_all = """SELECT {field_lists} FROM `{db}`.`{table}` WHERE `wid` = {id};""".format(db=db_name,
    #                                                                                               field_lists=','.join(
    #                                                                                                   field_lists_last),
    #                                                                                               table=table,
    #                                                                                               id=num_id)
    #     if (min_id == 0) and (max_id == 0):
    #         pass
    #     if (max_id != 0):
    #         sq1_all = """SELECT {field_lists} FROM `{db}`.`{table}` WHERE (`id` >= {min}) AND (`id` <= {max});""".format(
    #             db=db_name, field_lists=','.join(field_lists_last), table=table, min=min_id, max=max_id)
    #     if condition:
    #         sq1_all = """SELECT {condition} {field_lists} FROM `{db}`.`{table}`;""".format(condition=condition,
    #                                                                                        field_lists=','.join(
    #                                                                                            field_lists_last),
    #                                                                                        db=db_name, table=table)
    #     if condition and cond:
    #         sq1_all = """SELECT {condition} {field_lists} FROM `{db}`.`{table}` {cond};""".format(condition=condition,
    #                                                                                               field_lists=','.join(
    #                                                                                                   field_lists_last),
    #                                                                                               db=db_name,
    #                                                                                               table=table,
    #                                                                                               cond=cond)
    #     if condition and where:
    #         sq1_all = """SELECT {condition} {field_lists} FROM `{db}`.`{table}` WHERE {where};""".format(condition=condition,
    #                                                                                               field_lists=','.join(
    #                                                                                                   field_lists_last),
    #                                                                                               db=db_name,
    #                                                                                               table=table,
    #                                                                                               where=where)
    #     # print('\033[1;31;0m{tt}查询字段：\033[0m'.format(tt=str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))), sq1_all)
    #     self.logger.info('查询字段：' + sq1_all)
    #     self.logger.info('===========================================================')
    #     # print('===========================================================')
    #     while 1:
    #         if OTHER_INSERT:
    #             try:
    #                 self.other_cursor.execute(sq1_all)
    #                 self.other_db.commit()
    #                 data_all = self.other_cursor.fetchall()
    #                 dic_data_all = []
    #                 if if_dic:
    #                     for i in data_all:
    #                         dic_data = dict(zip(field_lists, i))
    #                         dic_data_all.append(dic_data)
    #                     return dic_data_all
    #                 return data_all
    #             except pymysql.err.OperationalError:
    #                 self.re_connet(if_other_db=True)
    #         else:
    #             try:
    #                 self.cursor.execute(sq1_all)
    #                 self.db.commit()
    #                 data_all = self.cursor.fetchall()
    #                 dic_data_all = []
    #                 if if_dic:
    #                     for i in data_all:
    #                         dic_data = dict(zip(field_lists, i))
    #                         dic_data_all.append(dic_data)
    #                     return dic_data_all
    #                 return data_all
    #             except pymysql.err.OperationalError:
    #                 self.re_connet()
    #
    # def delete_sql(self, db_name, table_name, where, OTHER_INSERT=False):
    #     sql = f"""delete from `{db_name}`.`{table_name}` where {where}"""
    #     self.logger.info('查询字段：' + sql)
    #     self.logger.info('===========================================================')
    #     while 1:
    #         if OTHER_INSERT:
    #             try:
    #                 self.other_cursor.execute(sql)
    #                 self.other_db.commit()
    #                 break
    #             except pymysql.err.OperationalError:
    #                 self.re_connet(if_other_db=True)
    #         else:
    #             try:
    #                 self.cursor.execute(sql)
    #                 self.db.commit()
    #                 break
    #             except pymysql.err.OperationalError:
    #                 self.re_connet()
    #
    # def update_item(self, item, is_insert=False, is_replace=True):
    #     field_lists_last = []
    #     for k, v in item.items():
    #         if ('time' in k) or ('Time' in k) or (k.endswith('T') == True):
    #             data = "`" + str(k) + "`" + "='{values}'".format(values=pymysql.converters.escape_string(str(v)))
    #         elif str(v).isdigit() and is_insert:
    #             data = "`" + str(k) + "`" + "={values}".format(values=v)
    #         elif (v == '') or (v == None):
    #             data = "`" + str(k) + "`" + "=NULL".format(values=v)
    #         else:
    #             if is_replace:
    #                 data = "`" + str(k) + "`" + "='{values}'".format(values=pymysql.converters.escape_string(str(self.d_deal(v))))
    #             else:
    #                 data = "`" + str(k) + "`" + "='{values}'".format(values=pymysql.converters.escape_string(str(v)))
    #         field_lists_last.append(data)
    #     # if is_insert == False:
    #     # print(json.dumps(field_lists_last, indent=2, ensure_ascii=False))
    #     # self.logger.info('\r\n'+json.dumps(field_lists_last, indent=2, ensure_ascii=False))
    #     return field_lists_last
    #
    # def update_data(self, item, db_name, table, where=0, OTHER_INSERT=False, is_replace=True):
    #     # print('\033[1;31;0m{tt}更新字段：\033[0m'.format(tt=str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))))
    #     # self.logger.info('更新字段：')
    #     item = self.update_item(item, is_replace=is_replace)
    #     update_sql = """UPDATE `{db}`.`{table_name}` SET {field_lists} WHERE {where}""".format(db=db_name,
    #                                                                                            table_name=table,
    #                                                                                            field_lists=','.join(
    #                                                                                                item), where=where)
    #     while 1:
    #         self.logger.info(update_sql)
    #         if OTHER_INSERT:
    #             try:
    #                 self.other_cursor.execute(update_sql)
    #                 self.other_db.commit()
    #                 break
    #             except pymysql.err.OperationalError:
    #                 self.re_connet(if_other_db=True)
    #         else:
    #             try:
    #                 self.cursor.execute(update_sql)
    #                 self.db.commit()
    #             except pymysql.err.OperationalError:
    #                 self.re_connet()
    #             break
    #         # print(update_sql)
    #         # self.logger.info('\r\n' + update_sql)

    async def data_deal(self, data):  # 一般数据处理
        if (data == None) or (data == ''):
            data_last = ''
            return data_last
        elif isinstance(data, dict):
            return json.loads(data)
        else:
            sin_list = ['\r', '\n', '\xa0', '\u3000', '\\u3000', '\t', ' ', '&nbsp;', '\\r', '\\n', ',,']
            for i in sin_list:
                data = str(data).replace(i, '')
            return data

    async def deal_json(self, response):
        ippool = json.loads(response)['http']
        ip_lists.append(ippool)

    async def asy_rand_choi_pool_response(self):  # 适用于aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.get(url=self.url)
                res = await response.read()
                return res.decode('utf-8')
        except Exception as e:
            self.logger.debug(str(e))
            return False

    async def asy_rand_choi_pool(self):
        global ip_lists
        global update
        if (len(ip_lists) == 0) or (time.time() - update >= 60):
            response = await self.asy_rand_choi_pool_response()
            while response == False:
                response = await self.asy_rand_choi_pool_response()
            try:
                await self.deal_json(response=response)
            except:
                while len(ip_lists) == 0:
                    try:
                        response = await self.asy_rand_choi_pool_response()
                        await self.deal_json(response=response)
                    except:
                        ip_lists = ip_lists
        if len(ip_lists) != 0:
            proxy = ip_lists.pop()
            return proxy

    async def deal_code(self, res):
        import chardet  # 字符集检测
        charset_code = chardet.detect(res[0:1])['encoding']
        # charset_code = self.deal_re(self.charset_code.search(str(res)))
        if charset_code:
            try:
                text = res.decode(charset_code)
                return text
            except (UnicodeDecodeError, TypeError, LookupError):
                text = await self.cycle_charset(res)
                return text
            except Exception as e:
                self.logger.error('Decoding error', exc_info=True)
        else:
            text = await self.cycle_charset(res)
            return text

    async def cycle_charset(self, res):  # 异常编码处理函数
        charset_code_list = ['utf-8', 'gbk', 'gb2312']
        for code in charset_code_list:
            try:
                text = res.decode(code)
                return text
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.error('Decoding error again', exc_info=True)

    async def try_get_request(self, url, callback=None, headers=None, meta=None, timeout=10):
        async with sem:
            try:
                async with aiohttp.ClientSession(headers=headers, conn_timeout=timeout) as session:
                    async with session.get(url=url, headers=headers, proxy=await self.asy_rand_choi_pool(),
                                           timeout=timeout) as response:
                        res = await response.read()
                        if callback != None:
                            if ('img_' in callback.__name__):
                                response_last = MyResponse(url=url, headers=headers, cookies=response.cookies,
                                                           meta=meta, text='这是一张图片',
                                                           content=res, status_code=response.status)
                                return response_last
                        else:
                            text = await self.deal_code(res=res)
                            response_last = MyResponse(url=url, headers=headers, cookies=response.cookies, meta=meta,
                                                       text=text, content=res, status_code=response.status)
                            return response_last
            except Exception as e:
                return False

    async def get_request(self, url, callback=None, headers=None, meta=None, timeout=10):
        response = await self.try_get_request(url=url, callback=callback, headers=headers, meta=meta, timeout=timeout)
        while response == False:
            response = await self.try_get_request(url=url, callback=callback, headers=headers, meta=meta,
                                                  timeout=timeout)

        if (callback == None):
            return response
        else:
            await self.__getattribute__(callback.__name__)(response=response)

    async def try_post_request(self, url, headers=None, meta=None, timeout=10, data=None):
        async with sem:
            try:
                async with aiohttp.ClientSession(headers=headers, conn_timeout=timeout) as session:
                    if '127.0.0.1' in url:
                        async with session.post(url=url, headers=headers, data=data, timeout=timeout) as response:
                            res = await response.read()
                    else:
                        async with session.post(url=url, headers=headers, data=data,
                                                proxy=await self.asy_rand_choi_pool(), timeout=timeout) as response:
                            res = await response.read()
                    text = await self.deal_code(res=res)
                    response_last = MyResponse(url=url, headers=headers, data=data, cookies=response.cookies, meta=meta,
                                               text=text, content=res, status_code=response.status)
                    return response_last
            except:
                return False

    async def post_request(self, url, callback=None, headers=None, meta=None, timeout=10, data=None):
        response = await self.try_post_request(url=url, headers=headers, meta=meta, timeout=timeout, data=data)
        while response == False:
            response = await self.try_post_request(url=url, headers=headers, meta=meta, timeout=timeout, data=data)

        if (callback == None):
            return response
        else:
            await self.__getattribute__(callback.__name__)(response=response)

    def url_code(self, chara, encoding='utf-8'):
        from urllib import parse
        data = str(parse.quote(chara, encoding=encoding))
        return data

    def filters_value(self, dic_data):
        for i in dic_data:
            if i['status'] == 0:
                i['status'] = '缺少'
            elif i['status'] == 1:
                i['status'] = '多出'
            elif i['status'] == 2:
                i['status'] = '重合'
            else:
                i['status'] = '未知'
        return dic_data


if __name__ == '__main__':
    cl = Cluster()
    cl.trucate(table='rizhi_shixin_real_time_page')
    cl.trucate(table='rizhi_shixin_real_time')
