import subprocess
import re
import time
import os

API_JS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "services", "api.js"))

def update_api_js(tunnel_url):
    if not os.path.exists(API_JS_PATH):
        print(f"File not found: {API_JS_PATH}")
        return
    with open(API_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    pattern = r"const defaultTunnelUrl = 'https://[^']+';"
    replacement = f"const defaultTunnelUrl = '{tunnel_url}';"
    
    new_content = re.sub(pattern, replacement, content)
    with open(API_JS_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ Updated api.js defaultTunnelUrl -> {tunnel_url}")

def build_and_push():
    print("🚀 Building frontend and pushing to GitHub/Vercel...")
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    subprocess.run("npm run build", shell=True, cwd=frontend_dir)
    subprocess.run("git add .", shell=True, cwd=root_dir)
    subprocess.run('git commit -m "Auto-update backend tunnel URL"', shell=True, cwd=root_dir)
    subprocess.run("git push", shell=True, cwd=root_dir)
    print("🎉 Pushed to GitHub/Vercel successfully!")

def main():
    print("Launching Serveo SSH Tunnel...")
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=15", "-R", "80:127.0.0.1:8002", "serveo.net"]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    tunnel_url = None
    for line in iter(proc.stdout.readline, ''):
        print(line, end='')
        if "Forwarding HTTP traffic from" in line:
            match = re.search(r'https://[a-zA-Z0-9\.-]+', line)
            if match:
                tunnel_url = match.group(0)
                print(f"\n==========================================")
                print(f"🎉 TUNNEL ACTIVE AT: {tunnel_url}")
                print(f"==========================================\n")
                update_api_js(tunnel_url)
                build_and_push()
                break
                
    proc.wait()

if __name__ == "__main__":
    main()
