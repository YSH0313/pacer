# -*- coding: utf-8 -*-
# @Author: yuanshaohang
# @Date: 2023-02-17- 17:20:53
# @Version: 1.0.0
# @Description: 动态mysql查询工具类
import re
import time
from web_tools.tools import Tools_user

import pymysql
from pymysqlpool import ConnectionPool

Mysql = {
    'MYSQL_HOST': 'aliyun-rds-qdb.bl-ai.com',
    'MYSQL_DBNAME': 'spider_frame',
    'MYSQL_USER': 'yuanshaohang',
    'MYSQL_PASSWORD': 'yhHoRatHtG8',
    'PORT': 3306
}


class MysqlDB:
    def __init__(self):
        self.host = Mysql['MYSQL_HOST']
        self.port = Mysql['PORT']
        self.user = Mysql['MYSQL_USER']
        self.password = Mysql['MYSQL_PASSWORD']
        self.db = Mysql['MYSQL_DBNAME']
        # self.conn = None
        self.pool = self.create_pool()
        self.condition_re = re.compile('(.*?)\\(')
        self.params_re = re.compile('\\((.*?)\\)')

    def deal_re(self, demo, defult=None):  # 判断正则是否匹配到的是否为空
        if demo != None:
            data_tuple = demo.groups()
            lists = list(data_tuple)
            data = ''.join([i for i in lists if i != None])
            return data
        else:
            if defult:
                return defult
            return ''

    def create_pool(self):
        conn = ConnectionPool(
            pool_name='mypool',
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            autocommit=True
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
                print(f"Error while executing query: {e}")
                conn.rollback()
                attempts -= 1
                if attempts == 0:
                    raise Exception("Failed to execute query after 3 attempts")
            finally:
                if conn:
                    conn.close()

    def insert(self, table, data):
        columns = ', '.join([f"`{i}`" for i in data.keys()])
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT IGNORE INTO `{table}` ({columns}) VALUES ({placeholders});"

        update = ', '.join([f"`{key}` = %s" for key in data.keys()])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update}"
        print(sql % tuple([f"'{i}'" if i else i for i in data.values()]*2))

        print(query % tuple([f"'{i}'" if i else i for i in data.values()]))
        return self.execute(query, tuple(data.values()))

    def update(self, table, set_data, where=None):
        set_pairs = [f"`{column}`=%s" for column in set_data.keys()]
        query = f"UPDATE `{table}` SET {', '.join(set_pairs)}"
        parameters = tuple(set_data.values())
        if where:
            query += f" WHERE {where};"
        print(query % tuple([f"'{i}'" if i else i for i in parameters]))
        return self.execute(query, parameters)

    def delete(self, table, where=None):
        query = f"DELETE FROM `{table}`"
        if where:
            query += f" WHERE {where};"
        print(query)
        return self.execute(query)

    def get_condition(self, columns):
        condition_map = {'count': 'count', 'max': 'max', 'distinct': 'distinct'}
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
        print(query)
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


if __name__ == '__main__':
    my_db = MysqlDB()
    # for i in range(10):
    my_db.insert(table='db_base_test', data={'name': 'yuanshaohang', 'age': None, 'sex': '男'})  # 增

    # my_db.update(table='db_base_test', set_data={'name': '袁少航', 'age': 20, 'sex': '男'}, where="`name`='yuanshaohang'")  # 改
    #
    # my_db.delete(table='db_base_test', where="name='袁少航'")  # 删
    #
    # data_list = my_db.select(table='db_base_test', columns='name', where='`name` = "袁少航"')  # 查
    # print(data_list)