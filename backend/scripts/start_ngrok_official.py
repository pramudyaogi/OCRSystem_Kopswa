import os
import sys
import time
import subprocess
import re
from pyngrok import ngrok, conf

AUTH_TOKEN = "2xPVx5ZFeOjg2WfJtbD6dCCpsXw_4VzNUiuwAdr8jqJdpLvBJ"
PORT = 8002

API_JS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "services", "api.js"))

def update_api_js(ngrok_url):
    if not os.path.exists(API_JS_PATH):
        print(f"File not found: {API_JS_PATH}")
        return
    with open(API_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    pattern = r"const defaultTunnelUrl = 'https://[^']+';"
    replacement = f"const defaultTunnelUrl = '{ngrok_url}';"
    
    new_content = re.sub(pattern, replacement, content)
    with open(API_JS_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ Updated api.js defaultTunnelUrl -> {ngrok_url}")

def build_and_push():
    print("🚀 Building frontend and pushing to GitHub/Vercel...")
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    subprocess.run("npm run build", shell=True, cwd=frontend_dir)
    subprocess.run("git add .", shell=True, cwd=root_dir)
    subprocess.run('git commit -m "Auto-update Ngrok URL"', shell=True, cwd=root_dir)
    subprocess.run("git push", shell=True, cwd=root_dir)
    print("🎉 Pushed to GitHub/Vercel successfully!")

def main():
    print("Starting Ngrok Tunnel with Authtoken...")
    ngrok.set_auth_token(AUTH_TOKEN)
    tunnel = ngrok.connect(PORT)
    public_url = tunnel.public_url.replace("http://", "https://")
    
    print("\n" + "="*50)
    print(f"🎉 NGROK TUNNEL ACTIVE!")
    print(f"📌 Public URL: {public_url}")
    print("="*50 + "\n")
    
    update_api_js(public_url)
    build_and_push()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping Ngrok...")

if __name__ == "__main__":
    main()
