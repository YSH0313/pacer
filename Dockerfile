FROM python:3.7.2
ENV PYTHONUNBUFFERED 1
RUN mkdir /code && pip install --upgrade pip
WORKDIR /code
ADD requirements.txt /code/
COPY requirements.txt requirements.txt
RUN pip install -i https://pypi.douban.com/simple  -r requirements.txt
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN echo 'Asia/Shanghai' >/etc/timezone
ADD . /code/
CMD ["python", "runner.py"]
