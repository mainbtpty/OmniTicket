import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# Load configuration data safely
if os.path.exists("config.json"):
    with open("config.json", "r") as f:
        config = json.load(f)
else:
    config = {"TOKEN": "", "TICKET_CATEGORY_ID": 0, "STAFF_ROLE_ID": 0}

class TicketBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required for slash commands and interaction
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Adds the persistent ticket button view so it still works after a bot reboot
        self.add_view(PersistentTicketView())
        await self.tree.sync()
        print("Slash commands synced successfully.")

bot = TicketBot()

# View containing the long-term, interactive ticket creation button
class PersistentTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Crucial: None makes the button work forever

    @discord.ui.button(label="📩 Open Support Ticket", style=discord.ButtonStyle.success, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category_id = config.get("TICKET_CATEGORY_ID")
        category = discord.utils.get(guild.categories, id=category_id)
        
        # Define channel access: Hide from everyone, expose to the user and staff
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.get_role(config.get("STAFF_ROLE_ID")): discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Create the ticket text channel
        channel_name = f"ticket-{interaction.user.name.lower()}"
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        
        # Provide immediate confirmation feedback inside the ticket channel
        embed = discord.Embed(
            title="🎫 Ticket Created Successfully",
            description=f"Welcome {interaction.user.mention},\nOur support staff will be with you shortly. Use the button below to close this inquiry when resolved.",
            color=discord.Color.green()
        )
        await ticket_channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket created at {ticket_channel.mention}!", ephemeral=True)

# View attached to the active message inside an open ticket channel
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚧 This support channel will be permanently deleted in 5 seconds...")
        await interaction.channel.delete(delay=5.0)

# Setup administrator setup command
@bot.tree.command(name="setup_tickets", description="Deploys the main ticket interaction embed to a channel.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_tickets(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏢 Community Support Helpdesk",
        description="Need help with our gaming services? Click the green button below to initiate a private support channel with our management staff.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message("✅ Ticket interface deployed.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=PersistentTicketView())

@bot.event
async def on_ready():
    print(f"🤖 Bot launched successfully as: {bot.user.name}")

# Launch the application
if __name__ == "__main__":
    bot.run(config["TOKEN"])
