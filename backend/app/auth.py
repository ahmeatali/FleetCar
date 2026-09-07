import hashlib
import secrets

def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 ile şifreleri güvenli şekilde hash'ler."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"pbkdf2_sha256$100000${salt}${key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Girilen şifrenin kayıtlı hash ile eşleşip eşleşmediğini kontrol eder."""
    try:
        parts = hashed.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_key_hex = parts[3]
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        return secrets.compare_digest(key.hex(), expected_key_hex)
    except Exception:
        return False
