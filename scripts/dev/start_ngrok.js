import ngrok from '@ngrok/ngrok';
import fs from 'fs';

async function start() {
  console.log("🚀 Starting Official Ngrok Tunnel via Node SDK...");
  try {
    const listener = await ngrok.forward({
      addr: 8001,
      authtoken: "2xPVx5ZFeOjg2WfJtbD6dCCpsXw_4VzNUiuwAdr8jqJdpLvBJ"
    });

    const url = listener.url();
    console.log("\n==========================================");
    console.log("🎉 NGROK TUNNEL IS ACTIVE!");
    console.log(`📌 Public URL: ${url}`);
    console.log(`💡 Set VITE_API_URL=${url} in Vercel / frontend .env`);
    console.log("==========================================\n");

    fs.writeFileSync("tunnel_url.txt", url, "utf-8");
  } catch (err) {
    console.error("Ngrok Tunnel Error:", err);
  }
}

start();
