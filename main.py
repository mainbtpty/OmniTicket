import discord
from discord.ext import tasks, commands
import os
from mcstatus import MCServer
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# 1. Advanced Web Server to handle Render's HEAD health checks without crashing
class SimpleWebServer(BaseHTTPRequestHandler):
    def do_HEAD(self):
        # Respond instantly to Render's system ping to confirm we are online
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Stat Tracker is fully functional.")

def run_server():
    # Render routes incoming free web service traffic via port 10000
    server = HTTPServer(('0.0.0.0', 10000), SimpleWebServer)
    server.serve_forever()

# Start web listener in a separate background thread
threading.Thread(target=run_server, daemon=True).start()

# 2. Complete Discord Stat Tracker Engine Configuration
class StatBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # Explicitly turn off message content since this bot doesn't use chat commands
        intents.message_content = False  
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.update_status_loop.start()

    @tasks.loop(seconds=60)
    async def update_status_loop(self):
        server_ip = os.getenv("MINECRAFT_SERVER_IP", "2b2t.org")
        try:
            server = MCServer.lookup(server_ip)
            status = await server.async_status()
            
            status_text = f"🎮 {status.players.online}/{status.players.max} players on {server_ip}"
            await self.change_presence(activity=discord.Game(name=status_text))
            print(f"📊 Status updated successfully: {status_text}")
            
        except Exception as e:
            await self.change_presence(activity=discord.Game(name="⚠️ Server Offline"))
            print(f"❌ Failed to reach Minecraft server: {e}")

    @update_status_loop.before_loop
    async def before_update_loop(self):
        await self.wait_until_ready()

bot = StatBot()

@bot.event
async def on_ready():
    print(f"🤖 Connected as: {bot.user.name}")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ CRITICAL ERROR: Environment variable 'DISCORD_TOKEN' missing.")
