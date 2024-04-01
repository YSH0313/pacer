import re
import sys
import oss2
import html
import time
import json
import base64
import socket
import hashlib
import datetime
import dateparser
import dateutil.parser
from urllib import parse as pp
from dateutil.parser import parse
from importlib import import_module
from xml.sax.saxutils import unescape, escape
from setting import oss_config
from web_tools.file_tools.Stream_local import stream_type
from web_tools.file_tools.ocrutils_local import reco_url


class ImproperlyConfigured(Exception):
    """Django is somehow improperly configured"""
    pass


def include(arg, namespace=None):
    app_name = None
    if isinstance(arg, tuple):
        # Callable returning a namespace hint.
        try:
            urlconf_module, app_name = arg
        except ValueError:
            if namespace:
                raise ImproperlyConfigured(
                    'Cannot override the namespace for a dynamic module that '
                    'provides a namespace.'
                )
            raise ImproperlyConfigured(
                'Passing a %d-tuple to include() is not supported. Pass a '
                '2-tuple containing the list of patterns and app_name, and '
                'provide the namespace argument to include() instead.' % len(arg)
            )
    else:
        # No namespace hint - use manually provided namespace.
        urlconf_module = 'application.' + arg

    if isinstance(urlconf_module, str):
        urlconf_module = import_module(urlconf_module)
    patterns = getattr(urlconf_module, 'urlpatterns', urlconf_module)
    app_name = getattr(urlconf_module, 'app_name', app_name)
    if namespace and not app_name:
        raise ImproperlyConfigured(
            'Specifying a namespace in include() without providing an app_name '
            'is not supported. Set the app_name attribute in the included '
            'module, or pass a 2-tuple containing the list of patterns and '
            'app_name instead.',
        )
    namespace = namespace or app_name
    # Make sure the patterns can be iterated through (without this, some
    # testcases will break).
    if isinstance(patterns, (list, tuple)):
        for url_pattern in patterns:
            pattern = getattr(url_pattern, 'pattern', None)
    # return (urlconf_module, app_name, namespace)
    return urlconf_module


def get_ip():
    # 获取计算机名称
    hostname = socket.gethostname()
    # 获取本机IP
    ip = socket.gethostbyname(hostname)
    return ip


class Tools_user(object):

    def production_md5(self, str_data):  # 生成md5
        md5 = hashlib.md5(str_data.encode(encoding='UTF-8')).hexdigest()
        return md5

    def per_dic_plus(self, dic_data, key_list):
        data = ''
        for key in key_list:
            da = dic_data.get(key)
            if da:
                data = da
                break
        return data

    def d_deal(self, data):  # 一般数据处理
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

    def now_time(self, is_date=False):  # 获取现在时间
        if is_date == False:
            now_time = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            return now_time
        now_time = str(time.strftime("%Y-%m-%d", time.localtime()))
        return now_time

    def getYesterday(self, num=1):
        today = datetime.date.today()
        twoday = datetime.timedelta(days=num)
        yesterday = today - twoday
        return str(yesterday)

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

    def get_time(self, str_data):  # 提取时间
        if str_data:
            data = self.deal_re(re.search(
                r"(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})|(\d{4}年\d{1,2}月\d{1,2}日)|(\d{4}-\d{1,2}-\d{1,2})|(\d{4}\.\d{1,2}\.\d{1,2})",
                str_data, re.S))
        else:
            data = ''
        return data

    def date_format(self, str_date):
        try:
            new_date = dateparser.parse(str_date).strftime('%Y-%m-%d %H:%M:%S')
            return new_date
        except AttributeError:
            try:
                new_date = parse(str_date)
                return str(new_date)
            except dateutil.parser.ParserError:
                return None
        except:
            return None

    def base64_encode(self, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, int):
            data = str(data)
        data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        return data

    def base64_decode(self, data):
        data = base64.b64decode(data).decode('utf-8')
        return data

    def html_code(self, text, is_escape=False):
        data = text
        if is_escape:
            text = escape(text)
            if text == data:
                text = escape(text)
            else:
                return data
            return text
        else:
            text = unescape(text)
            if text == data.replace('amp;', '').replace('&gt;', '>'):
                text = html.unescape(text)
            else:
                return data
        return text

    def url_decode(self, chara, encoding='utf-8'):
        data = str(pp.unquote(chara, encoding=encoding))
        return data

    def get_nowtime(self):
        return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    async def get_file_length(self, file_bytes):
        content_length = len(file_bytes)
        mb = content_length / 1048576
        return int(mb)

    async def suc_rate(self, total_num, suc_num):
        rate = round(suc_num / total_num, 2)
        rate_baifen = f'{rate:.2%}'
        return rate_baifen

    async def get_bucket(self):
        access_key_id = oss_config['access_key_id']
        access_key_secret = oss_config['access_key_secret']
        endpoint = oss_config['endpoint'] if sys.platform != 'linux' else oss_config['endpoint_online']
        bucket_name = oss_config['bucket_name']
        return oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)

    async def oss_push_file(self, url, data, response=None, suffix='', custom=False, path=''):
        """
        :param url: 详情页链接
        :param data: 文件二进制数据流
        return: 对外能访问的图片URL
        """
        if len(data) < 10:
            return False
        oss_bucket = await self.get_bucket()
        stream = await stream_type(stream=data, response=response)
        if not stream and not custom:
            suffix_list = ['.doc', '.docx', '.xlr', '.xls', '.xlsx', '.pdf', '.txt', '.jpg', '.png', '.rar', '.zip']
            for i in suffix_list:
                if url.endswith(i):
                    suffix = i
            if not suffix.startswith('.'):
                suffix = '.' + suffix
        elif stream and not custom:
            suffix = '.' + stream
        else:
            if not suffix.startswith('.'):
                suffix = '.' + suffix
        if suffix:
            url_md5 = f'{path}{hashlib.sha1(url.encode()).hexdigest() + suffix}'
            oss_bucket.put_object(url_md5, data)
            oss_url = f'https://bid.snapshot.qudaobao.com.cn/{url_md5}'
            return oss_url

    async def ocr_result(self, file_bytes, key, response=None, host=None, is_update='2'):
        if len(file_bytes) > 10:
            stream = await stream_type(stream=file_bytes, response=response)
            result = []
            # if stream == 'pdf':
            #     result = await self.pdf2text(file_bytes)
            #     if not result:
            #         result = await reco_url(file_bytes, stream, key)
            # elif stream == 'jpg' or stream == 'png' or stream == 'doc' or stream == 'docx':
            #     result = await reco_url(file_bytes, stream, key, host=host)
            if stream == 'pdf' or stream == 'jpg' or stream == 'png' or stream == 'doc' or stream == 'docx':
                result = await reco_url(file_bytes, stream, key, host=host, is_update=is_update)
            return result
        else:
            return []

    async def get_small_file(self, file_bytes):
        fsize = len(file_bytes)
        print(fsize)
        if fsize <= 50 * 1024:
            return True


if __name__ == '__main__':
    # a = include('Time_controller.urls')
    # print(a.url_list)
    tool = Tools_user()
    a = tool.getYesterday()
    print(a)
