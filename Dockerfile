FROM tiangolo/uwsgi-nginx-flask:flask-python3.5-index
MAINTAINER Matt Johnson "matjohn2+cisco.com"

COPY . /app/
RUN mkdir /app/config
RUN pip install -r requirements.txt
