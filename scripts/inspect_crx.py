import struct
import sys
import os

def inspect_crx(filename):
    print(f"--- Inspecting {filename} ---")
    if not os.path.exists(filename):
        print("File not found.")
        return

    with open(filename, "rb") as f:
        magic = f.read(4)
        if magic != b"Cr24":
            print(f"Invalid Magic: {magic}")
            return
        
        version_bytes = f.read(4)
        version = struct.unpack("<I", version_bytes)[0]
        print(f"Version: {version}")
        
        if version == 2:
            pub_len = struct.unpack("<I", f.read(4))[0]
            sig_len = struct.unpack("<I", f.read(4))[0]
            print(f"CRX2 Header:")
            print(f"  PubKey Length: {pub_len}")
            print(f"  Sig Length: {sig_len}")
            
        elif version == 3:
            header_len = struct.unpack("<I", f.read(4))[0]
            print(f"CRX3 Header:")
            print(f"  Header Length: {header_len}")
            # Could try to parse protobuf but looking at raw bytes might be enough
            header_data = f.read(header_len)
            print(f"  Header Data (Hex prefix): {header_data[:32].hex()}...")
            
        else:
            print("Unknown Version")

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        inspect_crx(arg)
