import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def create_test_email():
    """Helper function to create a test email with CC and BCC"""    
    # Create test email
    msg = MIMEMultipart()
    msg["From"] = "allencongregation@gmail.com"
    msg["To"] = "john.t.gruber@gmail.com"
    msg["CC"] = ""
    msg["BCC"] = ""
    msg["Subject"] = "Test Email with Gmail API"

    msg_plain = """
    This is a test email to demonstrate plain text.
    """

    msg_html = """
    <h2>This is a test email to demonstrate HTML test</h2>
    <pre>
    1. line 1
    2. line 2
    3. line 3
    </pre>
    """

    msg.attach(MIMEText(msg_plain, "plain"))
    msg.attach(MIMEText(msg_html, "html"))
    return msg


def send_test_email(host='localhost', port=8025):
    """Send a test email to the local SMTP server"""
    try:
        # Create and send test email
        msg = create_test_email()

        with smtplib.SMTP(host, port) as server:
            # Include all recipients (TO, CC, BCC)
            all_recipients = [
                "john.t.gruber@gmail.com"
            ]
            server.send_message(msg, to_addrs=all_recipients)
            print("📤 Test email sent!")

    except Exception as e:
        print(f"❌ Failed to send test email: {e}")



def test():
    send_test_email(host='localhost', port=8025)

if __name__ == "__main__":
    test()
