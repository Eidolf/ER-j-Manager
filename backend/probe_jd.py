
import socket
import struct

def scan_myjd_connections():
    print("[18] Checking MyJD TCP Connections")
    
    # 1. Resolve Domains
    domains = ["api.jdownloader.org", "my.jdownloader.org"]
    target_ips = set()
    
    for d in domains:
        try:
            # We might get multiple IPs
            # getaddrinfo returns list of (family, socktype, proto, canonname, sockaddr)
            result = socket.getaddrinfo(d, 443)
            for item in result:
                ip = item[4][0]
                target_ips.add(ip)
                print(f"  Resolved {d} -> {ip}")
        except Exception as e:
            print(f"  Failed to resolve {d}: {e}")
            
    if not target_ips:
        print("  No IPs resolved. Cannot verify.")
        return

    # 2. Scan /proc/net/tcp
    # Convert IP string to Hex for matching
    # e.g. 176.9.1.2 -> B0090102 (Little Endian?)
    # /proc/net/tcp stores IP as little-endian hex integer.
    
    def ip_to_hex(ip_str):
        try:
            packed = socket.inet_aton(ip_str)
            # unpack as little endian integer? No, formatted as struct.
            # actually /proc/net/tcp is usually machine native, but often little endian for x86.
            # let's just convert both ways to be safe.
            return struct.unpack("<I", packed)[0] # Little Endian Integer
        except:
             return None
        
    target_hexes = set()
    for ip in target_ips:
        h = ip_to_hex(ip)
        if h: 
            # Format as 8-char hex string
            target_hexes.add(f"{h:08X}")
            
    print(f"  Target Hexes: {target_hexes}")

    try:
        with open("/proc/net/tcp", "r") as f:
            lines = f.readlines()
            found = False
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                
                remote_hex = parts[2].split(":")[0]
                rem_port_hex = parts[2].split(":")[1]
                state = parts[3]
                
                if state == "01" and rem_port_hex == "01BB": # Established to 443
                    if remote_hex in target_hexes:
                        print(f"  MATCH: {remote_hex} (MyJD)")
                        found = True
                    else:
                        # Optional: Print non-matches to debug
                        # print(f"  Ignored: {remote_hex}")
                        pass
                        
            if found:
                print("  STATUS: CONNECTED")
            else:
                print("  STATUS: DISCONNECTED")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_myjd_connections()
