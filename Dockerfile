FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV SMTP_HOSTNAME="localhost"
ENV SMTP_PORT="8025"
ENV SMTP_HANDLER="GMAIL_PROXY_HANDLER"

CMD ["python", "app.py"]
