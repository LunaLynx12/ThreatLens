"""
Saved ideas and implementation commands cog.
Optimized for performance and stability.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from lib.config import (
    MIN_NEWS_LIMIT, MAX_NEWS_LIMIT,
    EMBED_DESCRIPTION_MAX, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING
)
from lib.utils import truncate_text, can_mark_implemented, get_allowed_implement_users
from lib.ui import SavedIdeasPaginator
from lib.database import (
    get_all_ideas, get_idea_by_id,
    mark_idea_implemented, get_idea_count
)


def _validate_limit(limit: int) -> int:
    """Validate and clamp limit to allowed range."""
    return max(MIN_NEWS_LIMIT, min(MAX_NEWS_LIMIT, limit))


def _check_implement_permission(user_id: int, user_roles: list, bot_owner_id: Optional[int]) -> bool:
    """Check if user has permission to mark ideas as implemented."""
    allowed_users = get_allowed_implement_users()
    is_owner = user_id == bot_owner_id if bot_owner_id else False
    return can_mark_implemented(user_id, user_roles) or is_owner or (allowed_users and user_id in allowed_users)


class SavedCog(commands.Cog):
    """Cog for saved ideas and implementation commands."""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command(name='saved')
    async def saved_prefix(self, ctx: commands.Context, limit: int = 10) -> None:
        """View saved project ideas from the database."""
        limit = _validate_limit(limit)
        msg = await ctx.send("🔍 Loading saved ideas...")
        
        try:
            ideas = get_all_ideas(limit=limit, implemented_only=False)
            
            if not ideas:
                embed = discord.Embed(
                    title="📚 No Saved Ideas",
                    description="You don't have any saved ideas yet. Use `!ideas` to generate some!",
                    color=COLOR_WARNING
                )
                await msg.edit(content=None, embed=embed)
                return
            
            stats = get_idea_count()
            allowed_users = get_allowed_implement_users() or ([self.bot.owner_id] if self.bot.owner_id else [])
            
            paginator = SavedIdeasPaginator(
                ideas, 
                author_id=ctx.author.id,
                allowed_user_ids=allowed_users
            )
            first_embed = await paginator.get_page_embed()
            
            content = f"**💾 Saved Ideas** ({stats['total']} total, {stats['implemented']} implemented, {stats['unimplemented']} pending)"
            await msg.edit(content=content, embed=first_embed, view=paginator)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await msg.edit(content=None, embed=error_embed)
    
    @commands.command(name='implement')
    async def implement_prefix(self, ctx: commands.Context, idea_id: int) -> None:
        """Mark an idea as implemented by ID."""
        user_roles = [role.name for role in ctx.author.roles] if hasattr(ctx.author, 'roles') else []
        
        if not _check_implement_permission(ctx.author.id, user_roles, self.bot.owner_id):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to mark ideas as implemented. Only authorized users can use this command.",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        try:
            success = mark_idea_implemented(idea_id)
            
            if success:
                idea = get_idea_by_id(idea_id)
                embed = discord.Embed(
                    title="✅ Idea Marked as Implemented",
                    description=f"**{idea['title']}**\n\nID: #{idea_id}",
                    color=COLOR_SUCCESS,
                    timestamp=discord.utils.utcnow()
                )
                if idea.get('implemented_at'):
                    embed.add_field(name="📅 Implemented At", value=idea['implemented_at'], inline=False)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Idea with ID #{idea_id} not found.",
                    color=COLOR_ERROR
                )
                await ctx.send(embed=embed)
        except ValueError:
            embed = discord.Embed(
                title="❌ Error",
                description="Please provide a valid idea ID (number).",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await ctx.send(embed=error_embed)
    
    @app_commands.command(name="saved", description="View saved project ideas from the database")
    @app_commands.describe(limit="Number of ideas to show (1-10)")
    async def saved_slash(self, interaction: discord.Interaction, limit: int = 10) -> None:
        """Slash command version of saved."""
        limit = _validate_limit(limit)
        await interaction.response.defer()
        
        try:
            ideas = get_all_ideas(limit=limit, implemented_only=False)
            
            if not ideas:
                embed = discord.Embed(
                    title="📚 No Saved Ideas",
                    description="You don't have any saved ideas yet. Use `/ideas` to generate some!",
                    color=COLOR_WARNING
                )
                await interaction.followup.send(embed=embed)
                return
            
            stats = get_idea_count()
            allowed_users = get_allowed_implement_users() or ([self.bot.owner_id] if self.bot.owner_id else [])
            
            paginator = SavedIdeasPaginator(
                ideas,
                author_id=interaction.user.id,
                allowed_user_ids=allowed_users
            )
            first_embed = await paginator.get_page_embed()
            
            content = f"**💾 Saved Ideas** ({stats['total']} total, {stats['implemented']} implemented, {stats['unimplemented']} pending)"
            await interaction.followup.send(content=content, embed=first_embed, view=paginator)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=error_embed)
    
    @app_commands.command(name="implement", description="Mark an idea as implemented by ID")
    @app_commands.describe(idea_id="The ID of the idea to mark as implemented")
    async def implement_slash(self, interaction: discord.Interaction, idea_id: int) -> None:
        """Slash command version of implement."""
        await interaction.response.defer()
        
        user_roles = [role.name for role in interaction.user.roles] if hasattr(interaction.user, 'roles') else []
        
        if not _check_implement_permission(interaction.user.id, user_roles, self.bot.owner_id):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to mark ideas as implemented. Only authorized users can use this command.",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed)
            return
        
        try:
            success = mark_idea_implemented(idea_id)
            
            if success:
                idea = get_idea_by_id(idea_id)
                embed = discord.Embed(
                    title="✅ Idea Marked as Implemented",
                    description=f"**{idea['title']}**\n\nID: #{idea_id}",
                    color=COLOR_SUCCESS,
                    timestamp=discord.utils.utcnow()
                )
                if idea.get('implemented_at'):
                    embed.add_field(name="📅 Implemented At", value=idea['implemented_at'], inline=False)
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Idea with ID #{idea_id} not found.",
                    color=COLOR_ERROR
                )
                await interaction.followup.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=truncate_text(str(e), EMBED_DESCRIPTION_MAX),
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=error_embed)


async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(SavedCog(bot))
