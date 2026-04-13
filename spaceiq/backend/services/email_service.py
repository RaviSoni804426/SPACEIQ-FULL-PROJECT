"""Email service for sending admin approval requests and notifications."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import parse, request
from config import settings
import logging

logger = logging.getLogger(__name__)


def _smtp_ready() -> tuple[bool, str]:
    if not settings.smtp_email:
        return False, "SMTP_EMAIL is missing"
    if not settings.smtp_password:
        return False, "SMTP_PASSWORD is missing"
    return True, "configured"


def _send_html_email(subject: str, recipient: str, html_body: str) -> tuple[bool, str]:
    ready, status = _smtp_ready()
    if not ready:
        logger.warning(f"SMTP not configured. {status}.")
        return False, status

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_email
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=20) as server:
            server.starttls()
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)
        return True, "sent"
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        return False, str(exc)


def _send_whatsapp_message(message: str) -> tuple[bool, str]:
    """Send WhatsApp message via Twilio when credentials are configured."""
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_whatsapp_from):
        logger.warning("Twilio WhatsApp not configured. Skipping WhatsApp notification.")
        return False, "Twilio credentials are missing"

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
        payload = parse.urlencode(
            {
                "From": settings.twilio_whatsapp_from,
                "To": f"whatsapp:+91{settings.owner_whatsapp_number}",
                "Body": message,
            }
        ).encode()
        req = request.Request(url, data=payload)
        credentials = f"{settings.twilio_account_sid}:{settings.twilio_auth_token}".encode()
        import base64
        req.add_header("Authorization", f"Basic {base64.b64encode(credentials).decode()}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with request.urlopen(req, timeout=10) as response:
            if 200 <= response.status < 300:
                return True, "sent"
        return False, f"Twilio returned status {response.status}"
    except Exception as exc:
        logger.error(f"Failed to send WhatsApp notification: {exc}")
        return False, str(exc)


def send_admin_request_email(user_name: str, user_email: str, user_id: str) -> tuple[bool, str]:
    """Send admin request notification to owner."""
    try:
        subject = f"🎯 Admin Access Request - {user_name}"
        
        whatsapp_link = f"https://wa.me/91{settings.owner_whatsapp_number}"
        body = f"""
<html>
<head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; color: #334155; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #fcfdfe; padding: 40px; border-radius: 12px; }}
        .header {{ color: #4f46e5; font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
        .info-box {{ background: white; border-left: 4px solid #4f46e5; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .button-group {{ text-align: center; margin: 30px 0; }}
        .btn {{ display: inline-block; padding: 12px 30px; margin: 0 10px; text-decoration: none; border-radius: 8px; font-weight: 600; }}
        .btn-approve {{ background: #10b981; color: white; }}
        .btn-reject {{ background: #ef4444; color: white; }}
        .footer {{ color: #94a3b8; font-size: 12px; margin-top: 30px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">👤 New Admin Access Request</div>
        
        <div class="info-box">
            <strong>User Name:</strong> {user_name}<br>
            <strong>User Email:</strong> {user_email}<br>
            <strong>Request ID:</strong> {user_id}
        </div>
        
        <p>A user has requested admin access to the SpaceIQ platform. Please review and approve or reject their request.</p>
        
        <div class="button-group">
            <a href="{settings.backend_url}/admin-dashboard?action=approve&user_id={user_id}" class="btn btn-approve">✓ Approve Admin Access</a>
            <a href="{settings.backend_url}/admin-dashboard?action=reject&user_id={user_id}" class="btn btn-reject">✗ Reject Request</a>
        </div>
        
        <div class="info-box" style="border-left-color: #94a3b8;">
            <strong>Or use the Admin Dashboard:</strong><br>
            Login at <a href="{settings.backend_url}">{settings.backend_url}</a> to manage requests
        </div>
        
        <div class="info-box" style="border-left-color: #22c55e;">
            <strong>Owner contact:</strong><br>
            Email: {settings.owner_email}<br>
            WhatsApp: <a href="{whatsapp_link}">+91 {settings.owner_whatsapp_number}</a>
        </div>
        
        <div class="footer">
            <p>SpaceIQ Admin System | Do not reply to this email</p>
        </div>
    </div>
</body>
</html>
        """
        
        sent, status = _send_html_email(subject, settings.owner_email, body)
        if sent:
            logger.info(f"Admin request email sent to {settings.owner_email} for user {user_email}")
        return sent, status
        
    except Exception as e:
        logger.error(f"Failed to send admin request email: {str(e)}")
        return False, str(e)


def send_admin_request_notifications(user_name: str, user_email: str, user_id: str) -> dict:
    """Send owner notifications by email and optional WhatsApp."""
    email_sent, email_status = send_admin_request_email(user_name, user_email, user_id)
    whatsapp_sent, whatsapp_status = _send_whatsapp_message(
        f"SpaceIQ admin request from {user_name} ({user_email}). Review user id: {user_id}"
    )
    return {
        "email_sent": email_sent,
        "whatsapp_sent": whatsapp_sent,
        "email_status": email_status,
        "whatsapp_status": whatsapp_status,
    }


def send_admin_approval_email(user_name: str, user_email: str) -> bool:
    """Send approval confirmation email to admin."""
    try:
        subject = "✨ You've Been Promoted to Admin - SpaceIQ"
        
        body = f"""
<html>
<head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; color: #334155; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #fcfdfe; padding: 40px; border-radius: 12px; }}
        .header {{ color: #4f46e5; font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
        .success-box {{ background: #d1fae5; border-left: 4px solid #10b981; padding: 20px; margin: 20px 0; border-radius: 8px; color: #047857; }}
        .button-group {{ text-align: center; margin: 30px 0; }}
        .btn {{ display: inline-block; padding: 12px 30px; background: #4f46e5; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; }}
        .footer {{ color: #94a3b8; font-size: 12px; margin-top: 30px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">🎉 Welcome to Admin Panel</div>
        
        <div class="success-box">
            <strong>Congratulations {user_name}!</strong><br>
            Your admin access request has been approved. You now have full administrative capabilities.
        </div>
        
        <p>You can now:</p>
        <ul>
            <li>View all bookings and analytics</li>
            <li>Manage users and admin requests</li>
            <li>Access the Executive Dashboard</li>
            <li>View demand forecasting and anomalies</li>
        </ul>
        
        <div class="button-group">
            <a href="{settings.backend_url}" class="btn">Access Admin Dashboard →</a>
        </div>
        
        <div class="footer">
            <p>SpaceIQ Admin System | Questions? Contact support</p>
        </div>
    </div>
</body>
</html>
        """
        
        sent, status = _send_html_email(subject, user_email, body)
        if sent:
            logger.info(f"Admin approval email sent to {user_email}")
        else:
            logger.warning(f"Admin approval email not sent to {user_email}. Reason: {status}")
        return sent
        
    except Exception as e:
        logger.error(f"Failed to send approval email: {str(e)}")
        return False
