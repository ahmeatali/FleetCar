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


def send_supplier_invitation_email(recipient_email: str, supplier_name: str, token: str) -> dict:
    """
    Sends an invitation email to a supplier with a password setup link.
    Returns a dictionary with delivery status, SMTP configuration flag, and invite_url.
    """
    invite_url = f"{APP_BASE_URL}/setup-password?token={token}"

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_from = os.environ.get("SMTP_FROM", "noreply@fleetrent.com.tr").strip()

    is_smtp_configured = bool(smtp_host and smtp_user and smtp_pass)

    subject = f"FleetRent — {supplier_name} Portal Davetiyeniz"
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
                <h1 style="margin:0; font-size: 24px;">FleetRent Yönetici Portalı</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Tedarikçi & Servis Davetiyesi</p>
            </div>
            <div class="content">
                <h2>Merhaba {supplier_name},</h2>
                <p>FleetRent Filo Yönetim Platformu'nda şirketiniz adına bir tedarikçi/servis hesabı oluşturuldu.</p>
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
                © 2026 FleetRent Filo Yönetim Hizmetleri A.Ş. — Tüm hakları saklıdır.
            </div>
        </div>
    </body>
    </html>
    """

    print(f"\n[EMAIL INVITE] To: {recipient_email} | Supplier: {supplier_name} | Link: {invite_url}\n")

    if not is_smtp_configured:
        print("[SMTP INFO] SMTP credentials missing in environment. Email simulated.")
        return {
            "email_sent": False,
            "smtp_configured": False,
            "invite_url": invite_url,
            "message": "SMTP e-posta sunucusu henüz yapılandırılmadı. Davet bağlantısı aşağıdan kopyalanabilir."
        }

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_from
        msg['To'] = recipient_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [recipient_email], msg.as_string())
        
        return {
            "email_sent": True,
            "smtp_configured": True,
            "invite_url": invite_url,
            "message": f"Davet e-postası [{recipient_email}] adresine başarıyla gönderildi."
        }
    except Exception as e:
        err_msg = str(e)
        print(f"[SMTP ERROR] Failed to send email to {recipient_email}: {err_msg}")
        return {
            "email_sent": False,
            "smtp_configured": True,
            "invite_url": invite_url,
            "message": f"SMTP hatası: {err_msg}"
        }
