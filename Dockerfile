FROM python:3.12.2-alpine

RUN mkdir /app
WORKDIR /app

COPY * /app
RUN pip install -r requirements.txt

ENTRYPOINT ["/app/run.sh"]