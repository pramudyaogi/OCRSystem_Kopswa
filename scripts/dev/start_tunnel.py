import subprocess
import re
import time
import os

def main():
    print("Launching Serveo SSH Tunnel for FastAPI Backend (port 8001)...")
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=15", "-R", "80:127.0.0.1:8001", "serveo.net"]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    tunnel_url = None
    for line in iter(proc.stdout.readline, ''):
        print(line, end='')
        if "Forwarding HTTP traffic from" in line:
            match = re.search(r'https://[a-zA-Z0-9\.-]+', line)
            if match:
                tunnel_url = match.group(0)
                print(f"\n==========================================")
                print(f"TUNNEL ACTIVE AT: {tunnel_url}")
                print(f"Set VITE_API_URL={tunnel_url} in Vercel / frontend .env")
                print(f"==========================================\n")
                with open("tunnel_url.txt", "w", encoding="utf-8") as f:
                    f.write(tunnel_url)
                break
                
    proc.wait()

if __name__ == "__main__":
    main()

