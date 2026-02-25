import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

MAIL_SENDER = os.getenv("MAIL_SENDER")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def _send_email(to_email, subject, html_body, plain_body=None):
    if not MAIL_SENDER or not MAIL_PASSWORD:
        logging.warning("SMTP credentials not configured, skipping email")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = MAIL_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        if plain_body:
            msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(MAIL_SENDER, MAIL_PASSWORD)
            server.send_message(msg)
        logging.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logging.error(f"Email send failed to {to_email}: {e}")
        return False


def send_welcome_email(user_email, user_name, temp_password, login_url):
    subject = "Welcome to United Home Services"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Welcome to United Home Services</h2>
        <p>Hello {user_name},</p>
        <p>Your account has been created. Here are your login credentials:</p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Email:</strong> {user_email}</p>
            <p><strong>Temporary Password:</strong> {temp_password}</p>
        </div>
        <p>Please change your password after your first login.</p>
        <a href="{login_url}" style="display: inline-block; background: #3498db; color: white;
           padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0;">
            Login Now
        </a>
        <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
            If you did not expect this email, please disregard it.
        </p>
    </div>
    """
    _send_email(user_email, subject, html_body)


def send_password_reset_email(email, reset_link):
    subject = "Password Reset - United Home Services"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Password Reset</h2>
        <p>You requested a password reset. Click below to set a new password:</p>
        <a href="{reset_link}" style="display: inline-block; background: #3498db; color: white;
           padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0;">
            Reset Password
        </a>
        <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
            This link expires in 1 hour. If you did not request this, ignore this email.
        </p>
    </div>
    """
    _send_email(email, subject, html_body)


def send_booking_confirmation(customer_email, customer_name, technician_name,
                              service_type, start_time, address):
    subject = f"Appointment Confirmed - {service_type}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Appointment Confirmed</h2>
        <p>Hello {customer_name},</p>
        <p>Your appointment has been booked:</p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Service:</strong> {service_type}</p>
            <p><strong>Technician:</strong> {technician_name}</p>
            <p><strong>Date/Time:</strong> {start_time}</p>
            <p><strong>Address:</strong> {address}</p>
        </div>
        <p>If you need to reschedule or cancel, please contact us.</p>
    </div>
    """
    _send_email(customer_email, subject, html_body)


def send_technician_booking_notification(tech_email, tech_name, customer_name,
                                          service_type, start_time, address):
    subject = f"New Appointment - {service_type}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">New Appointment Assigned</h2>
        <p>Hello {tech_name},</p>
        <p>A new appointment has been booked for you:</p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Customer:</strong> {customer_name}</p>
            <p><strong>Service:</strong> {service_type}</p>
            <p><strong>Date/Time:</strong> {start_time}</p>
            <p><strong>Address:</strong> {address}</p>
        </div>
    </div>
    """
    _send_email(tech_email, subject, html_body)


def send_admin_booking_notification(customer_name, technician_name, service_type,
                                     start_time, address):
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        return
    subject = f"New Booking - {customer_name} - {service_type}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">New Appointment Booked</h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Customer:</strong> {customer_name}</p>
            <p><strong>Technician:</strong> {technician_name}</p>
            <p><strong>Service:</strong> {service_type}</p>
            <p><strong>Date/Time:</strong> {start_time}</p>
            <p><strong>Address:</strong> {address}</p>
        </div>
    </div>
    """
    _send_email(admin_email, subject, html_body)


def send_appointment_reminder(customer_email, customer_name, technician_name,
                               service_type, start_time, address):
    subject = f"Appointment Reminder - {service_type}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Appointment Reminder</h2>
        <p>Hello {customer_name},</p>
        <p>This is a reminder for your upcoming appointment:</p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Service:</strong> {service_type}</p>
            <p><strong>Technician:</strong> {technician_name}</p>
            <p><strong>Date/Time:</strong> {start_time}</p>
            <p><strong>Address:</strong> {address}</p>
        </div>
        <p>If you need to reschedule or cancel, please contact us as soon as possible.</p>
    </div>
    """
    _send_email(customer_email, subject, html_body)


def send_cancellation_email(customer_email, customer_name, service_type, start_time):
    subject = f"Appointment Cancelled - {service_type}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Appointment Cancelled</h2>
        <p>Hello {customer_name},</p>
        <p>Your appointment has been cancelled:</p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Service:</strong> {service_type}</p>
            <p><strong>Date/Time:</strong> {start_time}</p>
        </div>
        <p>If you would like to rebook, please contact us.</p>
    </div>
    """
    _send_email(customer_email, subject, html_body)


def send_technician_daily_schedule(tech_email, tech_name, schedule_date, appointments, schedule_url):
    """Send technician their next-day schedule at 6 PM ET."""
    subject = f"Your Schedule for {schedule_date} - United Home Services"

    if not appointments:
        appt_rows = "<tr><td colspan='4' style='padding: 12px; text-align: center; color: #7f8c8d;'>No appointments scheduled for tomorrow.</td></tr>"
    else:
        appt_rows = ""
        for i, appt in enumerate(appointments, 1):
            appt_rows += f"""
            <tr style="background: {'#f8f9fa' if i % 2 == 0 else '#ffffff'};">
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{appt.get('start_time', '')} - {appt.get('end_time', '')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{appt.get('service_type', '')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{appt.get('customer_name', '')}<br><small style="color:#7f8c8d;">{appt.get('customer_phone', '')}</small></td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{appt.get('address', '')}</td>
            </tr>"""

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">📋 Your Schedule for {schedule_date}</h2>
        <p>Hello {tech_name},</p>
        <p>Here is your schedule for <strong>{schedule_date}</strong>:</p>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; border: 1px solid #ddd; border-radius: 8px;">
            <thead>
                <tr style="background: #2c3e50; color: white;">
                    <th style="padding: 10px; text-align: left;">Time</th>
                    <th style="padding: 10px; text-align: left;">Service</th>
                    <th style="padding: 10px; text-align: left;">Customer</th>
                    <th style="padding: 10px; text-align: left;">Address</th>
                </tr>
            </thead>
            <tbody>
                {appt_rows}
            </tbody>
        </table>
        <p><strong>Total appointments: {len(appointments)}</strong></p>
        <a href="{schedule_url}" style="display: inline-block; background: #3498db; color: white;
           padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0;">
            View Full Schedule
        </a>
        <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
            This schedule was sent at 6:00 PM ET. If you have questions, contact your dispatcher.
        </p>
    </div>
    """
    _send_email(tech_email, subject, html_body)
