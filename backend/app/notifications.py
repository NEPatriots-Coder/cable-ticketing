from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime, timezone
from flask import current_app
from app.models import Notification
import requests
import boto3
from botocore.exceptions import ClientError

def send_sms(to_phone, message):
    """Send SMS via AWS SNS or Twilio"""
    try:
        # Try AWS SNS first (if configured)
        aws_key = current_app.config.get('AWS_ACCESS_KEY_ID')
        aws_secret = current_app.config.get('AWS_SECRET_ACCESS_KEY')
        aws_region = current_app.config.get('AWS_REGION', 'us-east-1')

        if aws_key and aws_secret:
            try:
                sns = boto3.client(
                    'sns',
                    aws_access_key_id=aws_key,
                    aws_secret_access_key=aws_secret,
                    region_name=aws_region
                )

                response = sns.publish(
                    PhoneNumber=to_phone,
                    Message=message,
                    MessageAttributes={
                        'AWS.SNS.SMS.SMSType': {
                            'DataType': 'String',
                            'StringValue': 'Transactional'
                        }
                    }
                )
                print(f"✅ SMS sent via AWS SNS: {response['MessageId']}")
                return True
            except ClientError as e:
                print(f"❌ AWS SNS error: {str(e)}")
                # Fall through to try Twilio

        # Fallback to Twilio
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        from_phone = current_app.config.get('TWILIO_PHONE_NUMBER')

        if not all([account_sid, auth_token, from_phone]):
            print("⚠️ No SMS service configured (AWS SNS or Twilio), skipping SMS")
            return False

        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_phone,
            to=to_phone
        )
        print(f"✅ SMS sent via Twilio: {msg.sid}")
        return True
    except Exception as e:
        print(f"❌ SMS error: {str(e)}")
        return False

def send_email(to_email, subject, html_content):
    """Send email via Resend or SendGrid"""
    try:
        # Try Resend first (simpler API)
        resend_key = current_app.config.get('RESEND_API_KEY')
        if resend_key:
            from_email = current_app.config.get('SENDGRID_FROM_EMAIL', 'onboarding@resend.dev')
            for attempt in range(1, 3):
                try:
                    response = requests.post(
                        'https://api.resend.com/emails',
                        headers={
                            'Authorization': f'Bearer {resend_key}',
                            'Content-Type': 'application/json'
                        },
                        json={
                            'from': from_email,
                            'to': [to_email],
                            'subject': subject,
                            'html': html_content
                        },
                        timeout=10,
                    )
                    if response.status_code in [200, 201]:
                        print(f"✅ Email sent via Resend: {response.status_code}")
                        return True
                    print(f"⚠️ Resend error on attempt {attempt}: {response.status_code} - {response.text}")
                except requests.RequestException as exc:
                    print(f"⚠️ Resend request failed on attempt {attempt}: {exc}")
            print("⚠️ Resend failed after retries, trying SendGrid...")

        # Fallback to SendGrid
        api_key = current_app.config.get('SENDGRID_API_KEY')
        from_email = current_app.config.get('SENDGRID_FROM_EMAIL')

        if not api_key:
            print("⚠️ No email service configured (Resend or SendGrid), skipping email")
            return False

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"✅ Email sent via SendGrid: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        return False

def notify_ticket_created(ticket):
    """Send notification when ticket is created"""
    app_url = current_app.config['APP_URL'].rstrip('/')
    assignee = ticket.assignee

    # Generate approval/rejection links
    approve_url = f"{app_url}/tickets/{ticket.id}/approve/{ticket.approval_token}"
    reject_url = f"{app_url}/tickets/{ticket.id}/reject/{ticket.approval_token}"

    # SMS message
    items_sms = "\n".join(
        f"Item {i+1}: {item['cable_type']} | {item['cable_length']} | Qty: {item['quantity']}"
        for i, item in enumerate(ticket.items)
    )
    sms_message = f"""
Cable Request from {ticket.creator.username}:

{items_sms}
Location: {ticket.location or 'N/A'}

Approve: {approve_url}
Reject: {reject_url}
""".strip()

    # Email HTML
    email_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #2563eb;">New Cable Request</h2>

        <p><strong>From:</strong> {ticket.creator.username}</p>

        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
            {''.join(f"<p><strong>Item {i+1}:</strong> {item['cable_type']} | {item['cable_length']} | Qty: {item['quantity']}</p>" for i, item in enumerate(ticket.items))}
            <p><strong>Location:</strong> {ticket.location or 'N/A'}</p>
            <p><strong>Notes:</strong> {ticket.notes or 'None'}</p>
        </div>

        <div style="margin: 30px 0; text-align: center;">
            <a href="{approve_url}"
               style="background-color: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 0 10px; display: inline-block;">
                ✅ Approve
            </a>
            <a href="{reject_url}"
               style="background-color: #ef4444; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 0 10px; display: inline-block;">
                ❌ Reject
            </a>
        </div>

        <p style="font-size: 12px; color: #666; margin-top: 30px;">
            Ticket ID: #{ticket.id} | Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}
        </p>
    </div>
</body>
</html>
"""

    # Send SMS
    sms_sent = send_sms(assignee.phone, sms_message)
    if sms_sent:
        Notification.create(
            ticket_id=ticket.id,
            recipient_user_id=assignee.id,
            notification_type='sms',
            status='sent',
            sent_at=datetime.now(timezone.utc)
        )

    # Send Email
    email_sent = send_email(assignee.email, f"Cable Request #{ticket.id}", email_html)
    if email_sent:
        Notification.create(
            ticket_id=ticket.id,
            recipient_user_id=assignee.id,
            notification_type='email',
            status='sent',
            sent_at=datetime.now(timezone.utc)
        )

def notify_status_change(ticket, new_status):
    """Send notification when ticket status changes"""
    creator = ticket.creator
    app_url = current_app.config['APP_URL'].rstrip('/')
    first_item = (ticket.items or [{}])[0]
    cable_type = first_item.get('cable_type', 'N/A')
    cable_length = first_item.get('cable_length', 'N/A')

    status_messages = {
        'approved': '✅ Your cable request has been APPROVED!',
        'rejected': '❌ Your cable request has been REJECTED',
        'fulfilled': '✅ Your cable request has been FULFILLED',
    }

    message = status_messages.get(new_status)
    if not message:
        return

    # SMS
    sms_message = f"""
{message}

Ticket #{ticket.id}
Type: {cable_type}
Length: {cable_length}

View: {app_url}/tickets/{ticket.id}
"""

    # Email
    email_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #2563eb;">Ticket Update</h2>
        <p style="font-size: 18px; font-weight: bold;">{message}</p>

        <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Ticket ID:</strong> #{ticket.id}</p>
            <p><strong>Cable Type:</strong> {cable_type}</p>
            <p><strong>Length:</strong> {cable_length}</p>
            <p><strong>Status:</strong> {new_status.upper()}</p>
            {f'<p><strong>Rejection Reason:</strong> {ticket.rejection_reason}</p>' if ticket.rejection_reason else ''}
        </div>

        <p><a href="{app_url}/tickets/{ticket.id}" style="color: #2563eb;">View Ticket Details</a></p>
    </div>
</body>
</html>
"""

    send_sms(creator.phone, sms_message.strip())
    send_email(creator.email, f"Ticket #{ticket.id} Update", email_html)
