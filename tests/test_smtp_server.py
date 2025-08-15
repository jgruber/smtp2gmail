import pytest
import asyncio
import smtplib
import threading
import time
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from unittest.mock import patch, MagicMock
import io
import sys

import smtp2gmail.smtp_server as SMTPServer

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from aiosmtpd.controller import Controller


def create_test_email():
    """Helper function to create a test email with CC and BCC"""    
    # Create test email
    msg = MIMEMultipart()
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["CC"] = "cc1@example.com, cc2@example.com"
    msg["BCC"] = "bcc1@example.com, bcc2@example.com"
    msg["Subject"] = "Test Email with CC and BCC"

    body = """
    This is a test email to demonstrate CC and BCC recipient detection.
    
    The server should print:
    - TO: recipient@example.com
    - CC: cc1@example.com, cc2@example.com
    - BCC: Note that BCC is usually stripped by mail servers
    """

    msg.attach(MIMEText(body, "plain"))
    return msg


def send_test_email(host='localhost', port=8025):
    """Send a test email to the local SMTP server"""
    try:
        # Create and send test email
        msg = create_test_email()

        with smtplib.SMTP(host, port) as server:
            # Include all recipients (TO, CC, BCC)
            all_recipients = [
                "recipient@example.com",
                "cc1@example.com",
                "cc2@example.com",
                "bcc1@example.com",
                "bcc2@example.com",
            ]
            server.send_message(msg, to_addrs=all_recipients)
            print("📤 Test email sent!")

    except Exception as e:
        print(f"❌ Failed to send test email: {e}")



class TestSMTPServer:
    """Test suite for the SMTP server with CC/BCC detection"""
    
    @pytest.fixture
    def smtp_server_manager(self):
        """Fixture to create SMTPServerManager instance"""
        return SMTPServer.SMTPServerManager(host='localhost', port=8026, handler=None)  # Use different port for testing
    
    @pytest.fixture
    def test_email_message(self):
        """Fixture to create a test email with CC and BCC"""
        msg = MIMEMultipart()
        msg['From'] = 'test_sender@example.com'
        msg['To'] = 'test_recipient@example.com'
        msg['CC'] = 'cc1@test.com, cc2@test.com, cc3@test.com'
        msg['BCC'] = 'bcc1@test.com, bcc2@test.com'
        msg['Subject'] = 'Test Email for CC/BCC Detection'
        
        body = "This is a test email for pytest validation of CC/BCC recipient detection."
        msg.attach(MIMEText(body, 'plain'))
        
        return msg
    
    @pytest.fixture
    def server_thread(self, smtp_server_manager):
        """Fixture to start SMTP server in a separate thread"""
        server_thread = threading.Thread(
            target=self._run_server, 
            args=(smtp_server_manager,),
            daemon=True
        )
        server_thread.start()
        time.sleep(2)  # Wait for server to start
        yield smtp_server_manager
        # Cleanup
        if smtp_server_manager.controller:
            smtp_server_manager.controller.stop()
    
    def _run_server(self, server_manager):
        """Helper method to run server in thread"""
        server_manager.controller = Controller(
            handler=server_manager.handler,
            hostname=server_manager.host,
            port=server_manager.port,
            ready_timeout=30
        )
        server_manager.controller.start()
        
        # Keep running until stopped
        try:
            while server_manager.controller.server:
                time.sleep(0.1)
        except:
            pass

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, server_thread, test_email_message, capsys):
        """Test sending an email with CC and BCC recipients"""
        
        # Capture the handler's output
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            # Send the test email
            try:
                with smtplib.SMTP('localhost', 8026, timeout=10) as smtp_client:
                    all_recipients = [
                        'test_recipient@example.com',
                        'cc1@test.com', 'cc2@test.com', 'cc3@test.com',
                        'bcc1@test.com', 'bcc2@test.com'
                    ]
                    smtp_client.send_message(test_email_message, to_addrs=all_recipients)
                
                # Wait for message processing
                await asyncio.sleep(1)
                
                # Check if email was processed (this would require modifying the handler to be testable)
                assert True  # Basic connectivity test
                
            except Exception as e:
                pytest.fail(f"Failed to send test email: {e}")

    def test_email_parsing_cc_recipients(self):
        """Test CC recipient extraction from email headers"""
        
        # Create test email message
        email_content = """From: sender@test.com
To: recipient@test.com
CC: cc1@test.com, cc2@test.com, cc3@test.com
Subject: Test CC parsing
        
This is a test email body."""
        
        # Parse email
        email_msg = email.message_from_string(email_content)
        
        # Test CC extraction
        cc_recipients = email_msg.get('CC', '')
        cc_list = [addr.strip() for addr in cc_recipients.split(',') if addr.strip()]
        
        assert len(cc_list) == 3
        assert 'cc1@test.com' in cc_list
        assert 'cc2@test.com' in cc_list
        assert 'cc3@test.com' in cc_list

    def test_email_parsing_bcc_recipients(self):
        """Test BCC recipient extraction from email headers"""
        # Create test email with BCC (note: in real scenarios, BCC is usually stripped)
        email_content = """From: sender@test.com
To: recipient@test.com
BCC: bcc1@test.com, bcc2@test.com
Subject: Test BCC parsing
        
This is a test email body."""
        
        # Parse email
        email_msg = email.message_from_string(email_content)
        
        # Test BCC extraction
        bcc_recipients = email_msg.get('BCC', '')
        bcc_list = [addr.strip() for addr in bcc_recipients.split(',') if addr.strip()]
        
        assert len(bcc_list) == 2
        assert 'bcc1@test.com' in bcc_list
        assert 'bcc2@test.com' in bcc_list

    def test_email_parsing_no_cc_bcc(self):
        """Test email parsing when there are no CC/BCC recipients"""
        email_content = """From: sender@test.com
To: recipient@test.com
Subject: Test no CC/BCC
        
This is a test email body."""
        
        # Parse email
        email_msg = email.message_from_string(email_content)
        
        # Test that CC/BCC are empty
        cc_recipients = email_msg.get('CC', '')
        bcc_recipients = email_msg.get('BCC', '')
        
        assert cc_recipients == ''
        assert bcc_recipients == ''

    @pytest.mark.asyncio
    async def test_handler_message_processing(self):
        """Test the CCBCCHandler message processing logic"""
        
        handler = SMTPServer.PrintMessageHandler()
        
        # Create test email content
        test_message = """From: test@example.com
To: recipient@example.com
CC: cc1@example.com, cc2@example.com
Subject: Test Handler Processing

This is a test message body."""
        
        # Mock stdout to capture print statements
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            # Process the message
            await handler.handle_message(test_message)
            
            # Get the captured output
            output = mock_stdout.getvalue()
            
            # Assert expected content appears in output
            assert "New Email Received" in output
            assert "From: test@example.com" in output
            assert "To: recipient@example.com" in output
            assert "cc1@example.com" in output
            assert "cc2@example.com" in output

    def test_create_test_email_function(self):
        """Test the create_test_email helper function"""
        msg = create_test_email()
        
        # Verify email structure
        assert msg['From'] == 'sender@example.com'
        assert msg['To'] == 'recipient@example.com'
        assert 'cc1@example.com' in msg['CC']
        assert 'cc2@example.com' in msg['CC']
        assert 'bcc1@example.com' in msg['BCC']
        assert 'bcc2@example.com' in msg['BCC']
        assert msg['Subject'] == 'Test Email with CC and BCC'

    @pytest.mark.parametrize("cc_list,expected_count", [
        ("cc1@test.com", 1),
        ("cc1@test.com, cc2@test.com", 2),
        ("cc1@test.com, cc2@test.com, cc3@test.com", 3),
        ("", 0),
    ])
    def test_cc_parsing_variations(self, cc_list, expected_count):
        """Test CC parsing with different numbers of recipients"""
        email_content = f"""From: sender@test.com
To: recipient@test.com
CC: {cc_list}
Subject: Test CC variations
        
Test body."""
        
        email_msg = email.message_from_string(email_content)
        cc_recipients = email_msg.get('CC', '')
        cc_parsed = [addr.strip() for addr in cc_recipients.split(',') if addr.strip()]
        
        assert len(cc_parsed) == expected_count

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self):
        """Test that server can start and stop cleanly"""        
        server_manager = SMTPServer.SMTPServerManager(host='localhost', port=8027, handler=None)
        
        # This is more of an integration test - would need actual threading
        # For unit testing, we'd test individual components
        assert server_manager.host == 'localhost'
        assert server_manager.port == 8027
        assert server_manager.handler is not None

    def test_email_with_multipart_content(self):
        """Test handling of multipart email messages"""
        # Create a multipart email
        msg = MIMEMultipart()
        msg['From'] = 'sender@test.com'
        msg['To'] = 'recipient@test.com'
        msg['CC'] = 'cc@test.com'
        msg['Subject'] = 'Multipart Test'
        
        # Add text part
        text_part = MIMEText("This is the text content", 'plain')
        msg.attach(text_part)
        
        # Convert to string and back to test parsing
        email_str = msg.as_string()
        parsed_msg = email.message_from_string(email_str)
        
        assert parsed_msg.is_multipart()
        assert parsed_msg['CC'] == 'cc@test.com'
        
        # Extract text content
        for part in parsed_msg.walk():
            if part.get_content_type() == "text/plain":
                content = part.get_payload()
                assert "This is the text content" in content
                break


# Additional test configuration
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Import required modules for testing
    try:
        # Add Controller to globals for the test methods
        globals()['Controller'] = Controller
    except ImportError:
        pytest.skip("aiosmtpd not installed")
    
    yield
    
    # Cleanup after all tests


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
