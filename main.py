import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# 1. Web server configuration required for Render Free Tier
app = Flask('')

@app.route('/')
def home():
    return "Bot is functioning normally."

def run_web_server():
    # Render routes web traffic through port 10000 by default
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# 2. Discord Bot Configuration
class TicketBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(PersistentTicketView())
        await self.tree.sync()

bot = TicketBot()

class PersistentTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) 

    @discord.ui.button(label="📩 Open Support Ticket", style=discord.ButtonStyle.success, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }
        channel_name = f"ticket-{interaction.user.name.lower()}"
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        embed = discord.Embed(
            title="🎫 Ticket Created",
            description=f"Welcome {interaction.user.mention}, management will assist you shortly.",
            color=discord.Color.green()
        )
        await ticket_channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket created at {ticket_channel.mention}!", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚧 Deleting channel...")
        await interaction.channel.delete(delay=3.0)

@bot.tree.command(name="setup_tickets", description="Deploys ticket panel.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_tickets(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏢 Helpdesk Center",
        description="Click the button to open a support ticket.",
        color=discord.Color.blue()
    )
    await interaction.channel.send(embed=embed, view=PersistentTicketView())
    await interaction.response.send_message("Deployed!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"🤖 Connected as: {bot.user.name}")

if __name__ == "__main__":
    # Start the web server background thread before booting the bot
    keep_alive()
    
    # Safely pull token from Render Environment settings without files
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ Token Missing.")
