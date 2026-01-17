
import struct
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

def generate_key_if_missing(key_path: Path) -> rsa.RSAPrivateKey:
    if key_path.exists():
        with open(key_path, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
    else:
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        return key

def pack_crx2(zip_path: Path, key_path: Path, output_path: Path):
    """
    Pack a ZIP into a Chrome Extension (CRX2 format).
    Header: "Cr24" (4 bytes)
    Version: 2 (4 bytes)
    PubKey Length: 4 bytes
    Sig Length: 4 bytes
    Public Key
    Signature
    ZIP Data
    """
    private_key = generate_key_if_missing(key_path)
    
    # Get Public Key in DER format
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Read ZIP content
    with open(zip_path, "rb") as f:
        zip_data = f.read()
    
    # Sign ZIP data
    signature = private_key.sign(
        zip_data,
        padding.PKCS1v15(),
        hashes.SHA1()
    )
    
    # Header Construction
    magic = b'Cr24'
    version = struct.pack('<I', 2) # Version 2
    pub_len = struct.pack('<I', len(pub_bytes))
    sig_len = struct.pack('<I', len(signature))
    
    with open(output_path, "wb") as f:
        f.write(magic)
        f.write(version)
        f.write(pub_len)
        f.write(sig_len)
        f.write(pub_bytes)
        f.write(signature)
        f.write(zip_data)

    print(f"Packed CRX: {output_path} (Size: {output_path.stat().st_size} bytes)")
