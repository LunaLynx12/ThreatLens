"""
Main Discord bot application.
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from lib.config import COMMAND_PREFIX
from lib.database import init_database

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=intents,
    help_command=None
)


@bot.event
async def on_ready():
    """Called when bot is ready."""
    print(f'✅ {bot.user} has connected to Discord!')
    print(f'📊 Connected to {len(bot.guilds)} guild(s)')
    
    init_database()
    
    await load_cogs()
    
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="cybersecurity news | !help"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)
    
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Global error handler for commands."""
    if isinstance(error, commands.CommandNotFound):
        return
    
    from lib.config import COLOR_ERROR
    embed = discord.Embed(
        title="❌ Error",
        description=f"An error occurred: {str(error)[:1000]}",
        color=COLOR_ERROR
    )
    await ctx.send(embed=embed)


async def load_cogs():
    """Load all cogs."""
    cog_files = [
        'cogs.news_cog',
        'cogs.ideas_cog',
        'cogs.saved_cog',
        'cogs.help_cog'
    ]
    
    for cog_file in cog_files:
        try:
            await bot.load_extension(cog_file)
            print(f'✅ Loaded cog: {cog_file}')
        except Exception as e:
            print(f'❌ Failed to load cog {cog_file}: {e}')


if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in environment variables.")
    elif TOKEN == "your_token_here":
        print("❌ Error: DISCORD_TOKEN is default placeholder. Please set a real token.")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Error: Invalid Discord token.")
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
