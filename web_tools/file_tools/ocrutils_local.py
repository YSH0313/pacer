import io
import gc
import re
import asyncio
import aiohttp
import async_timeout
import threading
import pdfminer.psparser
import pdfplumber
import requests
import json
from aiohttp import FormData
import logging

logger = logging.getLogger(__name__)

# from config.settings import ocr_url as URL


# class RecoBase():
#
#     async def __init__(filename, is_merge=True):
#         self.filename = filename
#         self.is_merge = is_merge # 多页合并
#
#         self.__files__ = {}

is_merge = True  # 多页合并

__files__ = {}


def start_loop(loop):
    # 一个在后台永远运行的事件循环
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_loop():
    loop = asyncio.new_event_loop()
    # 定义一个线程，运行一个事件循环对象，用于实时接收新任务
    loop_thread = threading.Thread(target=start_loop, args=(loop,))
    # self.loop_thread.setDaemon(True)  # 守护进程，开启后随主线程一起退出
    loop_thread.start()
    return loop


async def __get_file__(File_bytes, file_type):
    # __files__["file"] = (f'filename.{file_type}', File_bytes)
    # return __files__
    data = FormData()
    data.add_field('file',
                   File_bytes,
                   filename=f'filename.{file_type}',
                   content_type=f'application/{file_type}')
    return data


async def __close_file__(self):
    for k, v in __files__.items():
        v.close()


# async def __req__(File_bytes, file_type):
#     try:
#         resp = requests.post(URL, files=__get_file__(File_bytes, file_type))
#         # await __close_file__()
#         jdata = json.loads(resp.text)
#         result = jdata.get("data").get("ocrInfo")
#         return result
#     except Exception as e:
#         return None

async def __req__(File_bytes, file_type, key, host=None, is_update='2'):
    try:
        # URL = "https://api.bltools.bailian-ai.com/getOcrOriginData?ocrType=2"
        # URL = f"https://api-bltools.bl-ai.com/getOcrOriginData?ocrType=2&id={key}"
        URL = f"https://api-bltools.bl-ai.com/v1/parse?service={is_update}&id={key}"
        if host:
            URL = f"http://{host}:8100/getOcrOriginData?ocrType=2&id={key}"
            # URL = f"http://gpu6.bl-ai.com:8100/getOcrOriginData?ocrType=2&id={key}"
        # print(host, URL)
        with async_timeout.timeout(timeout=60):
            async with aiohttp.ClientSession(conn_timeout=60) as session:
                async with session.post(url=URL, data=await __get_file__(File_bytes, file_type), timeout=60, verify_ssl=False) as response:
                    del File_bytes
                    gc.collect()
                    resp = await response.read()
                    # print(resp)
                    jdata = json.loads(resp)
                    result = jdata.get("data")
                    return result
    except Exception as e:
        logger.info(f'发送ocr服务失败,{e}')
        return None


async def __fill_black__(pre_end_pos, curr_pos):
    if pre_end_pos == 0:
        return ""
    width = curr_pos - pre_end_pos
    if width < 20:
        return ""
    return " " * int(width / 20)


async def reco(File_bytes, file_type, key, host=None):
    # ocr_info_dict = await __req__(File_bytes, file_type)
    ocr_info_dict = await __req__(File_bytes, file_type, key, host)
    if not ocr_info_dict:
        return []

    result_list = []
    for k, v in sorted(ocr_info_dict.items(), key=lambda k: k[0]):
        page = []
        for lines in v:
            row = ""
            pre_end_pos = 0
            for c in lines:
                curr_pos = c.get("left")
                fill = await __fill_black__(pre_end_pos, curr_pos)
                row += fill + c.get("words")
                pre_end_pos = curr_pos + c.get("width")
            page.append(row)
        result_list.append(page)

    if is_merge:
        merge_list = []
        for page in result_list:
            merge_list += page
        return merge_list
    return result_list


async def reco_url(file_bytes, file_type, key, is_merge=True, host=None, is_update='2'):
    File_bytes = io.BytesIO(file_bytes)
    if file_type == 'pdf':
        try:
            pdf = pdfplumber.open(File_bytes)
            if len(pdf.pages) > 50:
                return []
            pdf.close()
        except:
            pass

    File_bytes = io.BytesIO(file_bytes)
    del file_bytes
    gc.collect()
    f1 = io.BufferedReader(File_bytes)
    # result = await reco(f1, file_type, key, host)
    result = await __req__(f1, file_type, key, host, is_update=is_update)
    # print(result)
    return result


if __name__ == '__main__':
    import time
    start = time.time()
    url = 'http://cdn.jihui88.com/upload//s//s5//syxt//picture//2022//07//04/%E9%99%84%E4%BB%B61%EF%BC%9A%E5%85%B3%E4%BA%8E%E9%87%87%E8%B4%AD%E4%B8%89%E4%BA%9A%E5%B8%82%E7%94%B5%E5%AD%90%E6%94%BF%E5%8A%A1%E5%A4%96%E7%BD%91%E5%8F%8A%E9%93%BE%E8%B7%AF%E5%A7%94%E6%89%98%E8%BF%90%E7%BB%B4%E7%AE%A1%E7%90%86%E6%9C%8D%E5%8A%A1%E9%A1%B9%E7%9B%AE%EF%BC%882022%E5%B9%B4%E5%BA%A6%E7%AC%AC%E4%BA%8C%E6%89%B9%E9%98%B2%E7%81%AB%E5%A2%99%EF%BC%89%E9%87%87%E8%B4%AD%E9%9C%80%E6%B1%82%E6%96%87%E4%BB%B6.pdf'
    # url = 'http://img1.jihui88.com/upload/s/s5/syxt/picture/2022/07/01/12fb5f62-6aef-43e7-93dc-0894bd3ef1a0.png'

    resp = requests.get(url, stream=True)
    lo = asyncio.get_event_loop()
    result = lo.run_until_complete(reco_url(resp.content, 'pdf', key='ceshiceshi'))

    end = time.time()
    total_time = end - start
    print(f'共用时:{total_time}')
    print(result)
    # RecoFactory.show(result)
