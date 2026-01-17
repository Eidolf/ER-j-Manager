import os
import struct
import subprocess
import sys
import shutil
import zipfile

def pack_crx(extension_dir, output_crx, private_key_path):
    # 1. Zip the extension directory
    zip_path = output_crx + ".zip"
    print(f"Zipping {extension_dir} to {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(extension_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, extension_dir)
                zf.write(abs_path, rel_path)

    # 2. Generate private key if not exists
    if not os.path.exists(private_key_path):
        print("Generating new private key...")
        subprocess.check_call(["openssl", "genrsa", "-out", private_key_path, "2048"])

    # 3. Extract public key
    pub_key_path = "pubkey.pem"
    subprocess.check_call(["openssl", "rsa", "-in", private_key_path, "-pubout", "-out", pub_key_path])

    # 4. Sign the zip
    sig_path = "signature.sig"
    subprocess.check_call(["openssl", "dgst", "-sha1", "-sign", private_key_path, "-out", sig_path, zip_path])

    # 5. Read Public Key and Signature
    # CRX2 format requires DER public key (not PEM)
    # Convert PEM pubkey to DER
    pub_key_der_path = "pubkey.der"
    # Removing header/footer and newlines manually or using openssl to convert
    subprocess.check_call(["openssl", "rsa", "-in", private_key_path, "-pubout", "-outform", "DER", "-out", pub_key_der_path])

    with open(pub_key_der_path, "rb") as f:
        pub_key = f.read()
    
    with open(sig_path, "rb") as f:
        signature = f.read()

    # 6. Construct CRX (Version 2)
    # Magic: Cr24
    # Version: 2
    # PubKey Len
    # Sig Len
    # PubKey
    # Sig
    # Zip Data

    magic = b"Cr24"
    version = struct.pack("<I", 2)
    pub_key_len = struct.pack("<I", len(pub_key))
    sig_len = struct.pack("<I", len(signature))

    print(f"Creating CRX: {output_crx}")
    with open(output_crx, "wb") as f:
        f.write(magic)
        f.write(version)
        f.write(pub_key_len)
        f.write(sig_len)
        f.write(pub_key)
        f.write(signature)
        with open(zip_path, "rb") as zf:
            f.write(zf.read())

    # Cleanup
    os.remove(zip_path)
    os.remove(pub_key_path)
    os.remove(pub_key_der_path)
    os.remove(sig_path)
    # Keep private key for future updates? Maybe.
    
    print("CRX successfully created.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pack_crx.py <extension_dir> <output_crx> [private_key]")
        sys.exit(1)
    
    ext_dir = sys.argv[1]
    out_crx = sys.argv[2]
    key = sys.argv[3] if len(sys.argv) > 3 else "extension.pem"
    
    pack_crx(ext_dir, out_crx, key)
