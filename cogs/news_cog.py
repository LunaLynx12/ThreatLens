"""
News and CVE commands cog.
Optimized for performance and stability with non-blocking operations.
"""

import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from lib.config import (
    DEFAULT_NEWS_LIMIT, MAX_NEWS_LIMIT, MIN_NEWS_LIMIT,
    EMBED_TITLE_MAX, EMBED_DESCRIPTION_MAX, RATE_LIMIT_DELAY,
    COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING
)
from lib.utils import truncate_text
from lib.news_fetcher import get_latest_news, get_cves_only

# Thread pool for running blocking news fetching
_news_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="news_worker")


def validate_news_limit(limit: int) -> int:
    """Validate and clamp news limit to allowed range."""
    return max(MIN_NEWS_LIMIT, min(MAX_NEWS_LIMIT, limit))


def _get_cve_color(cvss_score: Optional[float]) -> int:
    """Get color based on CVSS score."""
    if cvss_score is None:
        return COLOR_WARNING
    if cvss_score >= 9.0:
        return 0xFF0000  # Critical - Red
    elif cvss_score >= 7.0:
        return 0xFF6600  # High - Orange
    elif cvss_score >= 4.0:
        return 0xFFAA00  # Medium - Yellow
    else:
        return 0x00FF00  # Low - Green


def _create_article_embed(article: Dict, index: int, total: int) -> discord.Embed:
    """Create embed for an article efficiently."""
    is_cve = article.get('type') == 'CVE'
    color = _get_cve_color(article.get('cvss_score')) if is_cve else COLOR_SUCCESS
    
    embed = discord.Embed(
        title=truncate_text(article['title'], EMBED_TITLE_MAX),
        url=article['link'],
        description=truncate_text(article['summary'], EMBED_DESCRIPTION_MAX),
        color=color,
        timestamp=discord.utils.utcnow()
    )
    
    if is_cve:
        cve_id = article.get('cve_id')
        if cve_id:
            embed.add_field(name="🔖 CVE ID", value=cve_id, inline=True)
        
        cvss_score = article.get('cvss_score')
        if cvss_score is not None:
            embed.add_field(name="📊 CVSS Score", value=f"{cvss_score:.1f}", inline=True)
    
    embed.set_footer(text=f"Source: {article['source']} | {index}/{total}")
    return embed


async def send_news_articles(ctx_or_followup, articles: List[Dict], is_slash: bool = False) -> None:
    """
    Send news articles and CVEs as embeds efficiently.
    
    Args:
        ctx_or_followup: Context (prefix) or Followup (slash)
        articles: List of article/CVE dictionaries
        is_slash: Whether this is a slash command
    """
    if not articles:
        embed = discord.Embed(
            title="📰 No News Found",
            description="Could not fetch any news articles at this time.",
            color=COLOR_WARNING
        )
        await ctx_or_followup.send(embed=embed)
        return

    total = len(articles)
    
    # Send first article
    embed = _create_article_embed(articles[0], 1, total)
    await ctx_or_followup.send(embed=embed)
    
    # Send remaining articles with rate limiting
    if total > 1:
        for i, article in enumerate(articles[1:], start=2):
            embed = _create_article_embed(article, i, total)
            await ctx_or_followup.send(embed=embed)
            if i < total:  # Don't sleep after last article
                await asyncio.sleep(RATE_LIMIT_DELAY)


class NewsCog(commands.Cog):
    """Cog for news and CVE commands."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command(name='news')
    async def news_prefix(self, ctx: commands.Context, limit: int = DEFAULT_NEWS_LIMIT) -> None:
        """Fetches the latest cybersecurity news."""
        limit = validate_news_limit(limit)
        msg = await ctx.send("🔍 Fetching latest cybersecurity news...")
        
        try:
            # Run news fetching in executor to avoid blocking
            loop = asyncio.get_event_loop()
            articles = await loop.run_in_executor(
                _news_executor,
                get_latest_news,
                limit
            )
            await msg.delete()
            await send_news_articles(ctx, articles, is_slash=False)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await msg.edit(content=None, embed=error_embed)
    
    @commands.command(name='cve')
    async def cve_prefix(self, ctx: commands.Context, limit: int = DEFAULT_NEWS_LIMIT) -> None:
        """Fetches the latest CVE (Common Vulnerabilities and Exposures) information."""
        limit = validate_news_limit(limit)
        msg = await ctx.send("🔍 Fetching latest CVEs...")
        
        try:
            # Run CVE fetching in executor to avoid blocking
            loop = asyncio.get_event_loop()
            cves = await loop.run_in_executor(
                _news_executor,
                get_cves_only,
                limit
            )
            await msg.delete()
            await send_news_articles(ctx, cves, is_slash=False)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await msg.edit(content=None, embed=error_embed)
    
    @app_commands.command(name="news", description="Fetches the latest cybersecurity news")
    @app_commands.describe(limit="Number of articles to fetch (1-10)")
    async def news_slash(self, interaction: discord.Interaction, limit: int = DEFAULT_NEWS_LIMIT) -> None:
        """Slash command version of news."""
        limit = validate_news_limit(limit)
        await interaction.response.defer()
        
        try:
            # Run news fetching in executor to avoid blocking
            loop = asyncio.get_event_loop()
            articles = await loop.run_in_executor(
                _news_executor,
                get_latest_news,
                limit
            )
            await send_news_articles(interaction.followup, articles, is_slash=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=error_embed)
    
    @app_commands.command(name="cve", description="Fetches the latest CVE information")
    @app_commands.describe(limit="Number of CVEs to fetch (1-10)")
    async def cve_slash(self, interaction: discord.Interaction, limit: int = DEFAULT_NEWS_LIMIT) -> None:
        """Slash command version of CVE."""
        limit = validate_news_limit(limit)
        await interaction.response.defer()
        
        try:
            # Run CVE fetching in executor to avoid blocking
            loop = asyncio.get_event_loop()
            cves = await loop.run_in_executor(
                _news_executor,
                get_cves_only,
                limit
            )
            await send_news_articles(interaction.followup, cves, is_slash=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=error_embed)


async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(NewsCog(bot))
