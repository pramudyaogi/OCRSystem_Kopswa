import subprocess
import re

proc = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no', '-R', '80:127.0.0.1:8002', 'serveo.net'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

for line in iter(proc.stdout.readline, ''):
    print(line.strip())
    if "Forwarding HTTP traffic from" in line:
        match = re.search(r'https://[a-zA-Z0-9\.-]+', line)
        if match:
            url = match.group(0)
            print("\n*** LIVE_URL ***:", url)
            with open("live_url.txt", "w") as f:
                f.write(url)
            break
