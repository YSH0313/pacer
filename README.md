# 异步后端框架

## 初次拉代码，部署本地环境：
- 1、git clone https://github.com/YSH0313/pacer.git
- 2、settings.py中的MYSQL地址改为自己的

## 运行环境
- Python3.7.2及以上
- 安装requirements.txt依赖包

## 使用
- 使用pacer -p <project_name> 命令创建项目
- 使用production.py创建app
- application目录下存放创建的app项目
- 在创建的app中写视图函数
- app项目下的urls.py用于存放互相对应的视图和路由

## 启动服务
- 执行runner.py即可启动服务

## 生产环境启动服务
- 可使用docker启动或其它方式，推荐docker启动
- 可在项目根目录下执行docker-compose up -d
- 重启服务可直接执行reload_server.sh
- Dockerfile和docker-compose.yml参数可根据需要自行调整