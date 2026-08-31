import time
from pyngrok import ngrok

AUTH_TOKEN = "2xPVx5ZFeOjg2WfJtbD6dCCpsXw_4VzNUiuwAdr8jqJdpLvBJ"
PORT = 8001

def main():
    print("Connecting to Ngrok...")
    ngrok.set_auth_token(AUTH_TOKEN)
    tunnel = ngrok.connect(PORT, domain="beatriz-inattentive-malcolm.ngrok-free.app")
    print("\n" + "="*50)
    print(f"🎉 NGROK TUNNEL READY!")
    print(f"📌 Public URL: {tunnel.public_url}")
    print("="*50 + "\n")
    
    # Save URL to a text file for quick reference
    with open("ngrok_url.txt", "w") as f:
        f.write(tunnel.public_url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping Ngrok tunnel...")

if __name__ == "__main__":
    main()
