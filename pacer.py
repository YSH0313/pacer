# -*- coding: utf-8 -*-
# @Author: yuanshaohang
# @Date: 2023-03-24 16:33:05
# @Version: 1.0.0
# @Description: 创建pacer项目工程

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import argparse
import shutil
from web_tools.builder import creat_file


def main():
    parser = argparse.ArgumentParser(description='Command parameters related to creating a pacer_builder project project')
    parser.add_argument('-p', '--projectName', help='Name of the project to be created', required=True)
    parser.add_argument('-a', '--appName', help='Name of the prepared application', required=False)
    parser.add_argument('-t', '--projectPath', help='Prepare the path for creating the project', required=False)
    args = vars(parser.parse_args())

    projectName = args['projectName']
    appName = args['appName']
    projectPath = args['projectPath']

    # print(f"projectPath: {projectPath}")

    def ignore_txt_files(dirname, filenames):
        return [filename for filename in filenames if filename.endswith('.txt') or filename == 'pacer_builder.py']

    project_path = os.path.dirname(os.path.abspath(__file__))
    # print(f'项目路径：{project_path}')

    if projectName:
        print(f"projectName: {projectName}")
        print(f'当前目录：{os.getcwd()}')
        craete_path = os.path.join(os.getcwd(), projectName) if not projectPath else project_path
        print(f'创建路径：{craete_path}')
        shutil.copytree(project_path, craete_path, ignore=ignore_txt_files, ignore_dangling_symlinks=True)
        if appName:
            app_path = f'{craete_path}/application/{appName.capitalize()}'
            os.makedirs(app_path)
            creat_file(path=app_path, app_name=appName)
            print(f'{appName.capitalize()}应用创建成功')


if __name__ == '__main__':
    main()
