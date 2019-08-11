FROM python:3.7

WORKDIR /usr/src/

COPY ./app app
RUN mkdir /usr/src/db
COPY ./wsgi.py ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["gunicorn", "-b 0.0.0.0:8080", "wsgi:app.app"]