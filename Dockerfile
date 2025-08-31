FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

VOLUME [ "/tokens" ]

ENV SMTP_HOSTNAME="localhost"
ENV SMTP_PORT="8025"
ENV SMTP_HANDLER="GMAIL_PROXY_HANDLER"
ENV CLIENT_SECRET_FILE="/tokens/client_secret.json"

CMD ["python", "app.py"]
