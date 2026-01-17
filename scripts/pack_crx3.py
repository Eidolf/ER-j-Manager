import argparse
import os
import struct
import subprocess
import zipfile
import binascii

# CRX3 Header Magic: Cr24
# Version: 3
# Format:
#   Magic (4)
#   Version (4)
#   Header Length (4)
#   Header (Protobuf)
#   Archive (Zip)

# We need to construct a minimal protobuf header without 'google.protobuf' lib if possible,
# or assume 'protobuf' is installed? The environment is 'python:3.14-slim'.
# Installing 'protobuf' via pip is easy.
# BUT, we need to define the PROTO structure.
# Crx3 File Header Protobuf:
# message CrxFileHeader {
#   repeated AsymmetricKeyProof sha256_with_rsa = 2;
#   repeated AsymmetricKeyProof sha256_with_ecdsa = 3;
#   optional bytes signed_header_data = 10000;
# }
# message AsymmetricKeyProof {
#   optional bytes public_key = 1;
#   optional bytes signature = 2;
# }
# message SignedData {
#   optional bytes crx_id = 1;
# }

# Since we don't want to rely on compiling .proto files, we can construct the binary protobuf manually
# or use a pure-python minimal encoder for this specific structure.
# Field identifiers:
# sha256_with_rsa = 2 (WireType 2 -> Length Delimited)
#   public_key = 1 (WireType 2)
#   signature = 2 (WireType 2)
# signed_header_data = 10000 (WireType 2)
#   crx_id = 1 (WireType 2)

def varint(n):
    """Encode an integer as a varint."""
    data = []
    while True:
        towrite = n & 0x7f
        n >>= 7
        if n:
            data.append(towrite | 0x80)
        else:
            data.append(towrite)
            break
    return bytes(data)

def encode_field(field_number, wire_type, data):
    key = (field_number << 3) | wire_type
    return varint(key) + varint(len(data)) + data

def pack_crx3(extension_dir, output_file, private_key_file):
    # 1. Zip
    zip_path = output_file + ".zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(extension_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, extension_dir)
                
                # Create ZipInfo to set permissions manually
                # Python zipfile default permissions are sometimes 000
                zi = zipfile.ZipInfo.from_file(abs_path, rel_path)
                
                # Set permissions to 644 (rw-r--r--)
                # Use standard UNIX permission bitmask: (0o100000 | 0o644) << 16
                zi.external_attr = (0o100644) << 16
                
                with open(abs_path, "rb") as f:
                    zf.writestr(zi, f.read())
    
    with open(zip_path, "rb") as f:
        zip_data = f.read()
    os.remove(zip_path) # Cleanup zip immediately

    # 2. Key Generation / Reading
    if not os.path.exists(private_key_file):
        print("Generating key...")
        subprocess.check_call(["openssl", "genrsa", "-out", private_key_file, "2048"])
    
    # 3. Get Public Key (DER)
    # CRX3 uses SubjectPublicKeyInfo format
    pub_key_der = subprocess.check_output(
        ["openssl", "rsa", "-in", private_key_file, "-pubout", "-outform", "DER"]
    )

    # 4. Create Signed Header Data
    # Calculate CRX ID: First 16 bytes of SHA256 of Public Key
    # Actually CRX ID is usually from MP4/SHA256 of pubkey ?
    # Chrome extension ID is SHA256(pubkey) first 128 bits, hex encoded with a-p mapping.
    # But in the protobuf SignedData, it sends the raw bytes (16 bytes).
    import hashlib
    sha256 = hashlib.sha256(pub_key_der).digest()
    crx_id = sha256[:16]
    
    # SignedData { crx_id = 1 }
    signed_header_data_proto = encode_field(1, 2, crx_id)
    
    # 5. Sign the Signed Header Data + ZIP Data
    # Signature = SHA256 w/ RSA of (UTF8("CRX3 Signed Data") + 0x00 + signed_header_data_len (4 bytes LE) + signed_header_data + zip_data)
    
    prefix = b"CRX3 Signed Data\x00"
    signed_header_len_bytes = struct.pack("<I", len(signed_header_data_proto))
    data_to_sign = prefix + signed_header_len_bytes + signed_header_data_proto + zip_data
    
    # Sign with OpenSSL
    sig_input = "sig_input.dat"
    sig_output = "sig_output.dat"
    with open(sig_input, "wb") as f:
        f.write(data_to_sign)
        
    subprocess.check_call([
        "openssl", "dgst", "-sha256", "-sign", private_key_file, "-out", sig_output, sig_input
    ])
    
    with open(sig_output, "rb") as f:
        signature = f.read()
    
    os.remove(sig_input)
    os.remove(sig_output)

    # 6. Construct Final Header (CrxFileHeader)
    # AsymmetricKeyProof { public_key = 1, signature = 2 }
    proof_proto = encode_field(1, 2, pub_key_der) + encode_field(2, 2, signature)
    
    # CrxFileHeader { sha256_with_rsa = 2, signed_header_data = 10000 }
    # Note: sha256_with_rsa is repeated, usually one entry
    header_proto = encode_field(2, 2, proof_proto) + encode_field(10000, 2, signed_header_data_proto)

    # 7. Write CRX
    magic = b"Cr24"
    version = struct.pack("<I", 3)
    header_len = struct.pack("<I", len(header_proto))
    
    with open(output_file, "wb") as f:
        f.write(magic)
        f.write(version)
        f.write(header_len)
        f.write(header_proto)
        f.write(zip_data)
        
    print(f"CRX3 created: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dest")
    parser.add_argument("--key", default="extension.pem")
    args = parser.parse_args()
    
    pack_crx3(args.src, args.dest, args.key)
