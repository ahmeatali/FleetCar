import os
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@fleetrent.com.tr")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://fleetrent.com.tr")


def generate_invitation_token() -> str:
    """Generate a secure hex token for invitation URL."""
    return secrets.token_urlsafe(32)


def send_supplier_invitation_email(recipient_email: str, supplier_name: str, token: str) -> bool:
    """
    Sends an invitation email to a supplier with a password setup link.
    If SMTP credentials are not configured, prints the invitation link to stdout/logs.
    """
    invite_url = f"{APP_BASE_URL}/setup-password?token={token}"

    subject = f"FleetCar — {supplier_name} Portal Davetiyeniz"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
            .header {{ background: linear-gradient(135deg, #7c3aed, #db2777); padding: 30px; text-align: center; color: #ffffff; }}
            .content {{ padding: 35px; color: #334155; line-height: 1.6; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #7c3aed, #db2777); color: #ffffff !important; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: bold; margin-top: 20px; box-shadow: 0 4px 15px rgba(124,58,237,0.3); }}
            .footer {{ background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 0.8rem; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0; font-size: 24px;">FleetCar Yönetici Portalı</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Tedarikçi & Servis Davetiyesi</p>
            </div>
            <div class="content">
                <h2>Merhaba {supplier_name},</h2>
                <p>FleetCar Filo Yönetim Platformu'nda şirketiniz adına bir tedarikçi/servis hesabı oluşturuldu.</p>
                <p>Tedarikçi portalına giriş yapabilmek ve hesabınızı aktifleştirmek için lütfen aşağıdaki butona tıklayarak şifrenizi belirleyin:</p>
                <div style="text-align: center;">
                    <a href="{invite_url}" class="btn">Şifremi Oluştur ve Giriş Yap ➔</a>
                </div>
                <p style="margin-top: 30px; font-size: 0.85rem; color: #64748b;">
                    Eğer buton çalışmıyorsa aşağıdaki bağlantıyı tarayıcınıza yapıştırabilirsiniz:<br>
                    <a href="{invite_url}" style="color: #7c3aed;">{invite_url}</a>
                </p>
            </div>
            <div class="footer">
                © 2026 FleetCar Filo Yönetim Hizmetleri A.Ş. — Tüm hakları saklıdır.
            </div>
        </div>
    </body>
    </html>
    """

    print(f"\n[EMAIL INVITE SENT] To: {recipient_email} | Supplier: {supplier_name} | Link: {invite_url}\n")

    if not SMTP_HOST or not SMTP_USER:
        print("[SMTP INFO] SMTP configuration missing. Email simulated and logged to stdout.")
        return True

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = recipient_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, [recipient_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[SMTP ERROR] Failed to send email to {recipient_email}: {e}")
        return False
