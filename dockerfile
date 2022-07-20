
FROM python:3.8


LABEL coder1="Adina"
LABEL coder2="Zifeng"
LABEL description="DAMG 7245 Assignment 3"
LABEL version="beta-0.1"

WORKDIR /app


COPY . /app


RUN pip install --upgrade pip
RUN pip install -r requirements.txt


EXPOSE 8000

CMD ["gunicorn" ,"-w", "4", "-k", "uvicorn.workers.UvicornWorker" , "--bind", "0.0.0.0:8000", "main:app"]


