import os
import smtplib
import secrets
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _load_env_file():
    """Load backend/.env variables into os.environ if present."""
    paths = [
        Path(__file__).resolve().parent.parent / ".env",
        Path("/opt/fleetcar/backend/.env"),
        Path("/etc/fleetcar.env")
    ]
    for env_path in paths:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k:
                                os.environ[k] = v
            except Exception:
                pass


_load_env_file()

APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://fleetrent.com.tr")



def generate_invitation_token() -> str:
    """Generate a secure hex token for invitation URL."""
    return secrets.token_urlsafe(32)


def send_supplier_invitation_email(recipient_email: str, supplier_name: str, token: str) -> dict:
    """
    Sends an invitation email to a supplier with a password setup link.
    Returns a dictionary with delivery status, SMTP configuration flag, and invite_url.
    """
    _load_env_file()
    app_base_url = os.environ.get("APP_BASE_URL", "https://fleetrent.com.tr").rstrip("/")
    invite_url = f"{app_base_url}/setup-password?token={token}"

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


def send_password_reset_email(recipient_email: str, recipient_name: str, token: str) -> dict:
    """
    Sends a password reset email with a secure token link.
    """
    _load_env_file()
    app_base_url = os.environ.get("APP_BASE_URL", "https://fleetrent.com.tr").rstrip("/")
    reset_url = f"{app_base_url}/reset-password?token={token}"

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_from = os.environ.get("SMTP_FROM", "info@fleetrent.com.tr").strip()

    is_smtp_configured = bool(smtp_host and smtp_user and smtp_pass)
    subject = "FleetRent — Şifre Sıfırlama Talebi"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
            .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 30px; text-align: center; color: #ffffff; }}
            .content {{ padding: 35px; color: #334155; line-height: 1.6; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff !important; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: bold; margin-top: 20px; box-shadow: 0 4px 15px rgba(37,99,235,0.3); }}
            .footer {{ background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 0.8rem; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0; font-size: 24px;">FleetRent Filo Yönetimi</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Şifre Sıfırlama Bilgilendirmesi</p>
            </div>
            <div class="content">
                <h2>Merhaba {recipient_name},</h2>
                <p>FleetRent hesabınız için bir şifre sıfırlama talebi aldık.</p>
                <p>Yeni şifrenizi oluşturmak için lütfen aşağıdaki butona tıklayın:</p>
                <div style="text-align: center;">
                    <a href="{reset_url}" class="btn">Şifremi Sıfırla ➔</a>
                </div>
                <p style="margin-top: 30px; font-size: 0.85rem; color: #64748b;">
                    Bu talebi siz yapmadıysanız bu e-postayı güvenle göz ardı edebilirsiniz. Şifreniz değişmeyecektir.<br><br>
                    Bağlantı adresi:<br>
                    <a href="{reset_url}" style="color: #2563eb;">{reset_url}</a>
                </p>
            </div>
            <div class="footer">
                © 2026 FleetRent Filo Yönetim Hizmetleri A.Ş. — Tüm hakları saklıdır.
            </div>
        </div>
    </body>
    </html>
    """

    print(f"\n[EMAIL RESET] To: {recipient_email} | Link: {reset_url}\n")

    if not is_smtp_configured:
        return {"email_sent": False, "smtp_configured": False, "reset_url": reset_url, "message": "SMTP yapılandırılmadı."}

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
        
        return {"email_sent": True, "smtp_configured": True, "reset_url": reset_url, "message": "Şifre sıfırlama e-postası gönderildi."}
    except Exception as e:
        print(f"[SMTP ERROR] Failed password reset email to {recipient_email}: {e}")
        return {"email_sent": False, "smtp_configured": True, "reset_url": reset_url, "message": f"SMTP hatası: {e}"}


def send_email_verification_email(recipient_email: str, recipient_name: str, token: str) -> dict:
    """
    Sends an email verification link to confirm user's email address upon registration.
    """
    _load_env_file()
    app_base_url = os.environ.get("APP_BASE_URL", "https://fleetrent.com.tr").rstrip("/")
    verify_url = f"{app_base_url}/verify-email?token={token}"

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_from = os.environ.get("SMTP_FROM", "info@fleetrent.com.tr").strip()

    is_smtp_configured = bool(smtp_host and smtp_user and smtp_pass)
    subject = "FleetRent — E-posta Adresinizi Doğrulayın"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
            .header {{ background: linear-gradient(135deg, #10b981, #059669); padding: 30px; text-align: center; color: #ffffff; }}
            .content {{ padding: 35px; color: #334155; line-height: 1.6; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: #ffffff !important; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: bold; margin-top: 20px; box-shadow: 0 4px 15px rgba(16,185,129,0.3); }}
            .footer {{ background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 0.8rem; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin:0; font-size: 24px;">FleetRent Filo Yönetimi</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">E-posta Doğrulama</p>
            </div>
            <div class="content">
                <h2>Aramıza Hoş Geldiniz, {recipient_name}!</h2>
                <p>FleetRent platformuna kaydınız başarıyla oluşturuldu.</p>
                <p>Hesabınızı aktifleştirmek ve sistemdeki tüm filo yönetimi işlemlerine erişmek için lütfen e-posta adresinizi doğrulayın:</p>
                <div style="text-align: center;">
                    <a href="{verify_url}" class="btn">E-postamı Doğrula ➔</a>
                </div>
                <p style="margin-top: 30px; font-size: 0.85rem; color: #64748b;">
                    Eğer buton çalışmıyorsa aşağıdaki adresi tarayıcınıza yapıştırabilirsiniz:<br>
                    <a href="{verify_url}" style="color: #10b981;">{verify_url}</a>
                </p>
            </div>
            <div class="footer">
                © 2026 FleetRent Filo Yönetim Hizmetleri A.Ş. — Tüm hakları saklıdır.
            </div>
        </div>
    </body>
    </html>
    """

    print(f"\n[EMAIL VERIFY] To: {recipient_email} | Link: {verify_url}\n")

    if not is_smtp_configured:
        return {"email_sent": False, "smtp_configured": False, "verify_url": verify_url, "message": "SMTP yapılandırılmadı."}

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
        
        return {"email_sent": True, "smtp_configured": True, "verify_url": verify_url, "message": "E-posta doğrulama bağlantısı gönderildi."}
    except Exception as e:
        print(f"[SMTP ERROR] Failed email verification to {recipient_email}: {e}")
        return {"email_sent": False, "smtp_configured": True, "verify_url": verify_url, "message": f"SMTP hatası: {e}"}

