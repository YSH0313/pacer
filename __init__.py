# # -*- coding: utf-8 -*-
# import numpy as np
# import pygsheets
# try:
#     client = pygsheets.authorize(service_file="client_secret.json")
#     # 根据key打开谷歌表格
#     sh = client.open_by_key('1sShMP6Z43N1Ij5j_whN-igjxRjjpsDXI6D_lU8aIbl8')
#     # 根据表名获取表格中的工作表
#     new_table = sh.worksheet_by_title('综合')
#     # # 遍历数据
#     zong_map = {}
#     for row in zong:
#         if row[1]:
#             zong = [row[0], row[5], row[6], row[7]]
#             zong_map[row[1]] = zong
#     data_list = []
#     for r in rengong:
#         data = [r[2], r[3], r[5], r[6]]
#         data_list.append(data)
#     # print(data_list)
#     for k, i in enumerate(data_list):
#         try:
#             # new_table.update_values(crange=f'A{k+1}:F{k+1}', values=np.array([i+zong_map[i[0]]]).tolist())
#             print('  '.join((i+zong_map[i[0]])))
#         except KeyError:
#             print('  '.join((i)))
# except Exception as e:
#     import traceback
#     traceback.print_exc()
