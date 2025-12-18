"""
Ideas generation command cog.
Optimized for performance and stability with non-blocking AI calls.
"""

import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Union
from concurrent.futures import ThreadPoolExecutor

from lib.config import (
    DEFAULT_NEWS_LIMIT, EMBED_DESCRIPTION_MAX,
    COLOR_WARNING, COLOR_ERROR
)
from lib.utils import truncate_text, get_error_color
from lib.ui import IdeasPaginator
from lib.news_fetcher import get_latest_news
from lib.ai_insight import analyze_news_for_ideas
from lib.database import save_ideas

# Thread pool for running blocking AI calls
_ai_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ai_worker")


async def handle_ideas_command(
    ctx_or_followup: Union[discord.ext.commands.Context, discord.webhook.Webhook],
    author_id: int,
    is_slash: bool = False
) -> None:
    """
    Handle the ideas command logic efficiently with non-blocking AI calls.
    
    Args:
        ctx_or_followup: Context (prefix) or Followup (slash)
        author_id: ID of the user who invoked the command
        is_slash: Whether this is a slash command
    """
    # Fetch news first (this is fast, can be blocking)
    articles = get_latest_news(limit=DEFAULT_NEWS_LIMIT)
    if not articles:
        embed = discord.Embed(
            title="❌ No News Found",
            description="Could not fetch news to analyze.",
            color=COLOR_WARNING
        )
        if is_slash:
            await ctx_or_followup.send(embed=embed)
        else:
            await ctx_or_followup.edit(content=None, embed=embed)
        return
    
    # Run AI analysis in executor to avoid blocking event loop
    try:
        # Run the blocking AI call in a thread pool
        loop = asyncio.get_event_loop()
        ideas_list = await loop.run_in_executor(
            _ai_executor,
            analyze_news_for_ideas,
            articles
        )
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ AI Service Error",
            description=truncate_text(f"Failed to analyze news: {str(e)[:200]}", EMBED_DESCRIPTION_MAX),
            color=COLOR_ERROR
        )
        if is_slash:
            await ctx_or_followup.send(embed=error_embed)
        else:
            await ctx_or_followup.edit(content=None, embed=error_embed)
        return
    
    if isinstance(ideas_list, str):  # Error message
        error_embed = discord.Embed(
            title="🤖 AI Service Response",
            description=truncate_text(ideas_list, EMBED_DESCRIPTION_MAX),
            color=get_error_color(ideas_list)
        )
        error_embed.set_footer(text="Tip: Try again in a few moments if the service is overloaded")
        
        if is_slash:
            await ctx_or_followup.send(embed=error_embed)
        else:
            await ctx_or_followup.edit(content=None, embed=error_embed)
        return

    if not ideas_list:
        embed = discord.Embed(
            title="❌ No Ideas Generated",
            description="AI could not generate ideas from the news.",
            color=COLOR_WARNING
        )
        if is_slash:
            await ctx_or_followup.send(embed=embed)
        else:
            await ctx_or_followup.edit(content=None, embed=embed)
        return

    # Save ideas to database (non-blocking, errors are logged but don't stop execution)
    try:
        saved_ids = save_ideas(ideas_list)
        print(f"💾 Saved {len(saved_ids)} ideas to database (IDs: {saved_ids})")
    except Exception as e:
        print(f"⚠️ Warning: Failed to save ideas to database: {e}")
    
    # Start Paginator
    paginator = IdeasPaginator(ideas_list, author_id=author_id)
    first_embed = await paginator.get_page_embed()
    
    content = "**💡 Research Ideas based on current threats:**"
    
    if is_slash:
        await ctx_or_followup.send(
            content=content,
            embed=first_embed,
            view=paginator
        )
    else:
        await ctx_or_followup.edit(
            content=content,
            embed=first_embed,
            view=paginator
        )


class IdeasCog(commands.Cog):
    """Cog for ideas generation commands."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command(name='ideas')
    async def ideas_prefix(self, ctx: commands.Context) -> None:
        """Generates security project ideas based on latest news."""
        msg = await ctx.send("🤖 Analyzing latest news trends for research ideas...\n⏳ This may take a moment...")
        
        try:
            await handle_ideas_command(msg, author_id=ctx.author.id, is_slash=False)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await msg.edit(content=None, embed=error_embed)
    
    @app_commands.command(name="ideas", description="Generates security project ideas based on latest news")
    async def ideas_slash(self, interaction: discord.Interaction) -> None:
        """Slash command version of ideas."""
        await interaction.response.defer()
        
        try:
            await handle_ideas_command(interaction.followup, author_id=interaction.user.id, is_slash=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=error_embed)


async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(IdeasCog(bot))
