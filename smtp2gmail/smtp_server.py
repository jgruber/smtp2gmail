import asyncio
import email

from simplegmail import Gmail

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import AsyncMessage

def process_mime_part(part, level=0, debug_print=False):
    indent = "  " * level
    content_type = part.get_content_type()
    if debug_print:
        print(f"{indent}Part: {content_type}")
        print(f"{indent}  Filename: {part.get_filename() or 'None'}")
        print(f"{indent}  Content-Disposition: {part.get('Content-Disposition', 'None')}")
    
    if part.is_multipart():
        if debug_print: print(f"{indent}  Multipart with {len(part.get_payload())} parts")
        # Recursively process each part
        payload = part.get_payload()
        for i, subpart in enumerate(payload):
            if debug_print: print(f"{indent}  Processing subpart {i + 1}:")
            process_mime_part(subpart, level + 1)
    else:
        # Handle non-multipart content
        try:
            content = part.get_payload(decode=True)
            part_plain = None
            part_html = None
            if isinstance(content, bytes):
                if content_type.startswith('text'):
                    full_content = content.decode('utf-8', errors='ignore')
                    if content_type == 'text/plain':
                        part_plain = full_content
                    if content_type == 'text/html':
                        part_html = full_content
                content_preview = content[:50].decode('utf-8', errors='ignore')
            else:
                content_preview = str(content)[:50]
            if debug_print: print(f"{indent}  Content preview: {content_preview}...")
            return(part_plain, part_html)
        except Exception as e:
            print(f"{indent}  Error reading content on Mime part {level} - {content[:30]}: {e}")


class GmailProxyHandler(AsyncMessage):

    def __init__(self):
        print("📝 Server will proxy emails through GMAIL API")
        self.gmail = Gmail(client_secret_file='client_secret.json', noauth_local_webserver=True)
        super().__init__()


    async def handle_message(self, message):
        """Handle incoming email messages"""
        try:
            # Parse the email message
            if isinstance(message, bytes):
                email_msg = email.message_from_bytes(message)
            else:
                email_msg = email.message_from_string(str(message))

            # Extract basic headers
            sender = email_msg.get("From", "Unknown")
            to_recipients = email_msg.get("To", "")
            cc_recipients = email_msg.get("CC", "")
            bcc_recipients = email_msg.get(
                "BCC", ""
            )  # Note: BCC usually stripped by mail servers
            subject = email_msg.get("Subject", "No Subject")


            # CC recipients
            cc_list = []
            if cc_recipients:
                cc_list = [
                    addr.strip() for addr in cc_recipients.split(",") if addr.strip()
                ]

            # BCC recipients (usually not available in headers)
            bcc_list = []
            if bcc_recipients:
                bcc_list = [
                    addr.strip() for addr in bcc_recipients.split(",") if addr.strip()
                ]

            msg_plain = ""
            msg_html = ""

            # Log message body preview (first 100 characters)
            if email_msg.is_multipart():
                for i, part in enumerate(message.get_payload()):
                    (part_plain, part_html) = process_mime_part(part)
                    if part_plain: 
                        msg_plain = part_plain
                    if part_html: 
                        msg_html = part_html
            # else:
                # TODO: HANDLE ATTACHMENTS INLINE IMAGES ETC..
            params = {
                "to": to_recipients,
                "sender": sender,
                "cc": cc_list,
                "bcc": bcc_list,
                "subject": subject,
                "msg_plain": msg_plain,
                "msg_html": msg_html,
                "signature": False
            }
            message = self.gmail.send_message(**params)

        except Exception as e:
            print(f"❌ Error processing message: {e}")


class PrintMessageHandler(AsyncMessage):
    """Custom SMTP handler that extracts and prints CC/BCC recipients"""

    def __init__(self):
        print("📝 Server will print email attributes to standard out")
        super().__init__()

    async def handle_message(self, message):
        """Handle incoming email messages"""
        try:
            # Parse the email message
            if isinstance(message, bytes):
                email_msg = email.message_from_bytes(message)
            else:
                email_msg = email.message_from_string(str(message))

            # Extract basic headers
            sender = email_msg.get("From", "Unknown")
            to_recipients = email_msg.get("To", "")
            cc_recipients = email_msg.get("CC", "")
            bcc_recipients = email_msg.get(
                "BCC", ""
            )  # Note: BCC usually stripped by mail servers
            subject = email_msg.get("Subject", "No Subject")

            print("\n" + "=" * 60)
            print(f"📧 New Email Received")
            print("=" * 60)
            print(f"From: {sender}")
            print(f"Subject: {subject}")
            print(f"To: {to_recipients}")

            # Print CC recipients
            if cc_recipients:
                cc_list = [
                    addr.strip() for addr in cc_recipients.split(",") if addr.strip()
                ]
                print(f"CC Recipients ({len(cc_list)}):")
                for i, cc_addr in enumerate(cc_list, 1):
                    print(f"  {i}. {cc_addr}")
            else:
                print("CC Recipients: None")

            # Print BCC recipients (usually not available in headers)
            if bcc_recipients:
                bcc_list = [
                    addr.strip() for addr in bcc_recipients.split(",") if addr.strip()
                ]
                print(f"BCC Recipients ({len(bcc_list)}):")
                for i, bcc_addr in enumerate(bcc_list, 1):
                    print(f"  {i}. {bcc_addr}")
            else:
                print("BCC Recipients: None (typically stripped by mail servers)")

            print("=" * 60)
            
            msg_plain = ""
            msg_html = ""

            # Log message body preview (first 100 characters)
            if email_msg.is_multipart():
                print(f"Root message is multipart with {len(message.get_payload())} parts")
                for i, part in enumerate(message.get_payload()):
                    print(f"\nProcessing root part {i + 1}:")
                    (part_plain, part_html) = process_mime_part(part)
                    if part_plain: 
                        msg_plain = part_plain
                    if part_html: 
                        msg_html = part_html
            else:
                msg_html = email_msg.get_payload(decode=True)
                if isinstance(msg_html, bytes):
                    msg_html = msg_html.decode("utf-8", errors="ignore")

            if msg_plain:
                print(f"Plain Message: {msg_plain}")

            if msg_html:
                print(f"HTML Message: {msg_html}")

            print("\n")

        except Exception as e:
            print(f"❌ Error processing message: {e}")


class SMTPServerManager:
    """Manager class for the SMTP server"""

    def __init__(self, host="localhost", port=8025, handler=None):
        self.host = host
        self.port = port
        if not handler:
            handler = PrintMessageHandler()
        self.handler = handler
        self.controller = None

    def start_server(self):
        """Start the SMTP server"""
        print(f"🚀 Starting SMTP server on {self.host}:{self.port}")
        print("⏹️  Press Ctrl+C to stop the server\n")

        self.controller = Controller(
            handler=self.handler, hostname=self.host, port=self.port, ready_timeout=300
        )

        try:
            self.controller.start()
            print(f"✅ SMTP Server running on {self.host}:{self.port}")

            # Keep the server running
            try:
                # Run forever
                asyncio.get_event_loop().run_forever()
            except KeyboardInterrupt:
                print("\n🛑 Shutting down server...")
            finally:
                self.controller.stop()
                print("✅ Server stopped")

        except Exception as e:
            print(f"❌ Failed to start server: {e}")
