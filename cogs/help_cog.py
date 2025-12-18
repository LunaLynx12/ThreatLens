"""
Help command cog.
"""

import discord
from discord.ext import commands
from discord import app_commands

from lib.config import COLOR_INFO


class HelpCog(commands.Cog):
    """Cog for help command."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='help')
    async def help_prefix(self, ctx: commands.Context):
        """Help command (prefix version)."""
        embed = discord.Embed(
            title="🤖 Cybersecurity Bot Help",
            description="A modern Discord bot for cybersecurity news and AI-powered research ideas.",
            color=COLOR_INFO,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="📰 `!news [limit]`",
            value="Fetch the latest cybersecurity news articles and CVEs (1-10 items)",
            inline=False
        )
        
        embed.add_field(
            name="🔖 `!cve [limit]`",
            value="Fetch the latest CVE (Common Vulnerabilities and Exposures) information (1-10 items)",
            inline=False
        )
        
        embed.add_field(
            name="💡 `!ideas`",
            value="Generate security project ideas based on latest news using AI",
            inline=False
        )
        
        embed.add_field(
            name="💾 `!saved [limit]`",
            value="View saved project ideas from the database (1-10 items)",
            inline=False
        )
        
        embed.add_field(
            name="✅ `!implement <id>`",
            value="Mark an idea as implemented by its ID",
            inline=False
        )
        
        embed.set_footer(text="Powered by Gemini AI")
        await ctx.send(embed=embed)
    
    @app_commands.command(name="help", description="Shows available commands and bot information")
    async def help_slash(self, interaction: discord.Interaction):
        """Help command."""
        embed = discord.Embed(
            title="🤖 Cybersecurity Bot Help",
            description="A modern Discord bot for cybersecurity news and AI-powered research ideas.",
            color=COLOR_INFO,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="📰 `/news [limit]`",
            value="Fetch the latest cybersecurity news articles and CVEs (1-10 items)",
            inline=False
        )
        
        embed.add_field(
            name="🔖 `/cve [limit]`",
            value="Fetch the latest CVE (Common Vulnerabilities and Exposures) information (1-10 items)",
            inline=False
        )
        
        embed.add_field(
            name="💡 `/ideas`",
            value="Generate security project ideas based on latest news using AI",
            inline=False
        )
        
        embed.add_field(
            name="💾 `/saved [limit]`",
            value="View saved project ideas from the database (1-10 items)",
            inline=False
        )
        
        embed.add_field(
            name="✅ `/implement <id>`",
            value="Mark an idea as implemented by its ID",
            inline=False
        )
        
        embed.set_footer(text="Powered by Gemini AI")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(HelpCog(bot))

