import discord
from discord.ext import tasks, commands
import os
from mcstatus import MCServer
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# 1. Background Web Server required for Render Free Tier
class SimpleWebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Stat Tracker is fully functional.")

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleWebServer)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# 2. Discord Stat Tracker Engine Configuration
class StatBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # No message content intent needed just to update a bot status profile!
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Start the background auto-refresh loop task
        self.update_status_loop.start()

    @tasks.loop(seconds=60)
    async def update_status_loop(self):
        # Fallback to a major public server if no IP is provided in environment variables
        server_ip = os.getenv("MINECRAFT_SERVER_IP", "play.hypixel.net")
        try:
            # Look up the target server data over the network
            server = MCServer.lookup(server_ip)
            status = await server.async_status()
            
            # Set the bot's status text to show live player metrics
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
    print(f"🤖 Stat Tracker online as: {bot.user.name}")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ CRITICAL ERROR: Environment variable 'DISCORD_TOKEN' missing.")
