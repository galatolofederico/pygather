FROM python:3.6

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY server.py ./
COPY templates ./templates

EXPOSE 80
ENV FLASK_APP server.py
CMD flask run --port 80 --host 0.0.0.0

#CMD gunicorn --bind 0.0.0.0:80 server:app