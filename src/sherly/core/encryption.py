import base64

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    Fernet = None

class StorageEncryption:
    """
    Handles encrypted storage of sensitive data.
    """
    def __init__(self, secret_key: str = "sherly-default-key"):
        if Fernet is None:
            self.cipher = None
            return
            
        salt = b'sherly_salt' # In production, use a unique per-machine salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        if not self.cipher:
            return data.encode()
        return self.cipher.encrypt(data.encode())

    def decrypt(self, token: bytes) -> str:
        if not self.cipher:
            return token.decode()
        return self.cipher.decrypt(token).decode()

    def save_encrypted(self, path: str, data: str):
        encrypted = self.encrypt(data)
        with open(path, "wb") as f:
            f.write(encrypted)

    def load_encrypted(self, path: str) -> str:
        with open(path, "rb") as f:
            token = f.read()
        return self.decrypt(token)
