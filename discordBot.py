# Setup ===========================================================================================

# Import
import datetime
import mainWebsite
import discord
from discord.ext import commands, ipc

LOG_TEXT_CHANNEL_ID = 821162538796187648

# Bot class
class WebsiteDiscordBot(commands.Bot):
    # Initialize
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create server bot
        with open ("secretKey.txt") as secret_key_text_file:
            secret_key = secret_key_text_file.read()
        self.ipc_server = ipc.Server(self, secret_key = f"{secret_key}")

    # Upon startup of bot
    async def on_ready(self):
        print(f"Discord bot for website is online at {datetime.datetime.utcnow()}")

        # Start website
        mainWebsite.run_website()

# Create bot
discord_bot = WebsiteDiscordBot(command_prefix="NoCommandPrefix")

# Send message upon form
@discord_bot.ipc_server.route()
async def send_log_message(message):
    # Get log channel
    log_channel = discord_bot.get_channel(LOG_TEXT_CHANNEL_ID)
    await log_channel.send(message)

# Run =============================================================================================
if __name__ == "__main__":
    
    # Get token
    with open ("token.txt") as token_text_file:
        token = token_text_file.read()

    # Run!
    discord_bot.ipc_server.start()
    discord_bot.run(token)