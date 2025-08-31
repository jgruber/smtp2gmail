import asyncio
import os
import smtplib

from smtp2gmail.smtp_server import SMTPServerManager
from smtp2gmail.smtp_server import PrintMessageHandler
from smtp2gmail.smtp_server import GmailProxyHandler

def main():
    # Create and start the SMTP server
    SMTP_HOSTNAME = os.getenv("SMTP_HOSTNAME", "localhost")
    SMTP_PORT = os.getenv("SMTP_PORT", "8025")
    SMTP_HANDLER = os.getenv("SMTP_HANDLER", "PRINT_HANDLER")
    CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "./client_secret.json")

    handler_impl = None

    try:
        SMTP_HOSTNAME = str(SMTP_HOSTNAME)
        SMTP_PORT = int(SMTP_PORT)
        handler_impl = None
        if str(SMTP_HANDLER).lower() == "print_handler":
            handler_impl = PrintMessageHandler()
        elif str(SMTP_HANDLER).lower() == "gmail_proxy_handler":
            handler_impl = GmailProxyHandler(client_secret_file=CLIENT_SECRET_FILE)
    except ValueError as ve:
        print(f"❌ Failed to start SMTP server with invalid environment settings: {ve}")

    server_manager = SMTPServerManager(
        host=SMTP_HOSTNAME, port=SMTP_PORT, handler=handler_impl
    )
    server_manager.start_server()


if __name__ == "__main__":
    main()
