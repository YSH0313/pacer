# -*- coding: utf-8 -*-
import logging
import socket
from random import choice

log_path = ''

"""
format参数值说明：
%(name)s：   打印Logger的名字
%(levelno)s: 打印日志级别的数值
%(levelname)s: 打印日志级别名称
%(pathname)s: 打印当前执行程序的路径，其实就是sys.argv[0]
%(filename)s: 打印当前执行程序的文件名
%(funcName)s: 打印日志的当前函数
%(lineno)d:  打印日志的当前行号
%(asctime)s: 打印日志的时间
%(thread)d:  打印线程ID
%(threadName)s: 打印线程名称
%(process)d: 打印进程ID
%(message)s: 打印日志信息
"""


class NoParsingFilter(logging.Filter):
    def filter(self, record):
        if record.name.startswith('asyncio_config.manager'):
            return False
        return True


logging.getLogger("root").setLevel(logging.WARNING)
logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("root").setLevel(logging.WARNING)
logging.getLogger("kafka").setLevel(logging.WARNING)
logging.getLogger("pymysqlpool").setLevel(logging.WARNING)


class SpiderLog(object):
    def __init__(self):
        # self.logger = logging.getLogger("mainModule.sub")
        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False
        self.logger.addFilter(NoParsingFilter())
        if log_path:
            # print('有')
            logging.basicConfig(level=logging.DEBUG,
                                format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
                                datefmt="%Y-%m-%d %H:%M:%S",
                                filename=log_path)
            console = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                                          datefmt="%Y-%m-%d %H:%M:%S")
            console.setFormatter(formatter)
            self.logger.addHandler(console)
        else:
            # print('没有')
            logging.basicConfig(level=logging.DEBUG,
                                format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
                                datefmt="%Y-%m-%d %H:%M:%S")
            logging.getLogger("root").setLevel(logging.WARNING)

    def func(self):
        self.logger.info("Start print log")
        self.logger.info('这是一个测试')
        self.logger.debug("Do something")
        self.logger.warning("Something maybe fail.")
        # try:
        #     open("sklearn.txt", "rb")
        # except (SystemExit, KeyboardInterrupt):
        #     raise
        # except Exception:
        #     self.logger.error("Faild to open sklearn.txt from logger.error", exc_info=True)
        self.logger.info("Finish")


if __name__ == "__main__":
    spider_log = SpiderLog()
    spider_log.func()
