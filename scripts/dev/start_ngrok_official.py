import os
import sys
import time
import subprocess
import re
from dotenv import load_dotenv
from pyngrok import ngrok, conf

load_dotenv()

# Use ngrok binary inside workspace bin/ to bypass Windows Defender restriction
ngrok_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "bin", "ngrok.exe"))
if os.path.exists(ngrok_exe):
    conf.get_default().ngrok_path = ngrok_exe

AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN", "2xPVx5ZFeOjg2WfJtbD6dCCpsXw_4VzNUiuwAdr8jqJdpLvBJ")
PORT = int(os.getenv("PORT", 8001))

def main():
    print(f"Starting Ngrok Tunnel on Port {PORT}...")
    if AUTH_TOKEN:
        ngrok.set_auth_token(AUTH_TOKEN)
    tunnel = ngrok.connect(PORT, domain="beatriz-inattentive-malcolm.ngrok-free.app")
    public_url = tunnel.public_url.replace("http://", "https://")
    
    print("\n" + "="*50)
    print(f"🎉 NGROK TUNNEL ACTIVE!")
    print(f"📌 Public URL: {public_url}")
    print(f"💡 Set VITE_API_URL={public_url} in Vercel / frontend .env")
    print("="*50 + "\n")
    
    with open("ngrok_url.txt", "w", encoding="utf-8") as f:
        f.write(public_url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping Ngrok...")

if __name__ == "__main__":
    main()

