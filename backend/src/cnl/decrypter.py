from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import binascii

class CNLDecrypter:
    @staticmethod
    def decrypt(crypted_data: str, key_hex: str) -> str:
        try:
            # key is assumed to be hex string usually 32 chars (16 bytes)
            key = binascii.unhexlify(key_hex)
            iv = key # CNL2 often uses key as IV

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # Data is base64 encoded
            ciphertext = base64.b64decode(crypted_data)
            
            decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding (PKCS7 or just null byte strip/newlines)
            # CNL links are separated by newlines or null bytes.
            # Usually we decode to utf-8 and split
            decrypted_text = decrypted_padded.decode('utf-8', errors='ignore')
            return decrypted_text.strip()
        except Exception as e:
            print(f"Decryption failed: {e}")
            return ""

    @staticmethod
    def extract_links(decrypted_text: str) -> list[str]:
        # Links are often separated by \r\n or \n
        return [l.strip() for l in decrypted_text.replace('\r', '\n').split('\n') if l.strip()]
