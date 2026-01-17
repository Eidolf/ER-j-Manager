import struct
import sys
import os
import hashlib
import binascii

def read_varint(data, offset):
    value = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise Exception("Varint overflow")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return value, offset

def analyze_header(data, indent=""):
    offset = 0
    while offset < len(data):
        # Read Tag (Field + WireType)
        if offset + 1 > len(data): break
        tag_val, offset = read_varint(data, offset)
        field_num = tag_val >> 3
        wire_type = tag_val & 7
        
        print(f"{indent}Field {field_num} (Wire {wire_type}): ", end="")
        
        if wire_type == 2: # Length Delimited
            length, offset = read_varint(data, offset)
            payload = data[offset:offset+length]
            offset += length
            
            # Known fields
            if field_num == 2 and indent == "": # sha256_with_rsa
                print(f"AsymmetricKeyProof (Len {length})")
                analyze_header(payload, indent + "  ")
            elif field_num == 10000 and indent == "": # signed_header_data
                print(f"SignedHeaderData (Len {length})")
                analyze_header(payload, indent + "  ")
            elif field_num == 1 and indent == "  ": # public_key or crx_id
                 if len(payload) == 16:
                     print(f"CRX ID: {payload.hex()}")
                 else:
                     # Calculate ID from key
                     sha = hashlib.sha256(payload).digest()
                     cid = sha[:16].hex()
                     print(f"Public Key (Len {len(payload)}) -> ID: {cid}")
            elif field_num == 2 and indent == "  ": # signature
                print(f"Signature (Len {len(payload)})")
            else:
                print(f"Bytes: {payload.hex()[:20]}...")
        elif wire_type == 0: # Varint
            val, offset = read_varint(data, offset)
            print(f"Value: {val}")
        else:
             print(f"Unknown WireType")
             return

def inspect_crx(filename):
    print(f"\n=== Inspecting {filename} ===")
    with open(filename, "rb") as f:
        magic = f.read(4)
        if magic != b"Cr24":
            print("Invalid Magic")
            return
        
        version_bytes = f.read(4)
        version = struct.unpack("<I", version_bytes)[0]
        print(f"Version: {version}")
        
        if version != 3:
            print("Not CRX3")
            return
            
        header_len = struct.unpack("<I", f.read(4))[0]
        print(f"Header Length: {header_len}")
        
        header_data = f.read(header_len)
        analyze_header(header_data)
        
        zip_start = f.tell()
        f.seek(0, 2)
        total_len = f.tell()
        zip_len = total_len - zip_start
        print(f"Zip Payload Length: {zip_len}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_crx.py file1 [file2 ...]")
    for f in sys.argv[1:]:
        inspect_crx(f)
