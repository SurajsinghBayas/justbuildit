import smtplib
import logging
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

logger = logging.getLogger("app.email")

async def send_email(subject: str, recipient: str, body_html: str):
    """
    Send an email using SMTP settings from config.
    Runs concurrently in a thread pool to avoid blocking the async event loop.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning(f"SMTP not configured. Email to {recipient} NOT sent. Subject: {subject}")
        return

    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    msg['To'] = recipient
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body_html, 'html'))
    
    def _send():
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                if settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"SMTP execution error sending to {recipient}: {e}")
            return False

    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=3) as pool:
            success = await loop.run_in_executor(pool, _send)
            if success:
                logger.info(f"Email sent successfully to {recipient}")
    except Exception as e:
        logger.error(f"Failed to dispatch email to {recipient}: {e}")

async def notify_added_to_org(recipient_email: str, org_name: str, inviter_name: str):
    subject = f"You've been added to {org_name} on JustBuildIt"
    body = f"""
    <html>
        <body>
            <h2>Welcome to {org_name}!</h2>
            <p>Hi there,</p>
            <p><b>{inviter_name}</b> has added you to their organization on <b>JustBuildIt</b>.</p>
            <p>You can now collaborate on projects and track tasks together.</p>
            <br/>
            <p>Happy Building!<br/>The JustBuildIt Team</p>
        </body>
    </html>
    """
    await send_email(subject, recipient_email, body)

async def notify_task_assigned(recipient_email: str, task_title: str, project_name: str, assigner_name: str):
    subject = f"New task assigned: {task_title}"
    body = f"""
    <html>
        <body>
            <h2>Task Assigned</h2>
            <p>Hi,</p>
            <p><b>{assigner_name}</b> has assigned a new task to you in <b>{project_name}</b>:</p>
            <p><b>Task:</b> {task_title}</p>
            <br/>
            <p>Log in to JustBuildIt to start working on it.</p>
        </body>
    </html>
    """
    await send_email(subject, recipient_email, body)

async def notify_project_created(recipient_emails: list[str], project_name: str, org_name: str, creator_name: str):
    subject = f"New project in {org_name}: {project_name}"
    body = f"""
    <html>
        <body>
            <h2>New Project Created</h2>
            <p>Hi team,</p>
            <p><b>{creator_name}</b> just created a new project <b>{project_name}</b> in the <b>{org_name}</b> organization.</p>
            <br/>
            <p>Check it out and start planning!</p>
        </body>
    </html>
    """
    for email in recipient_emails:
        await send_email(subject, email, body)
