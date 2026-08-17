'''
Cog for user data management: export, delete, opt-out, privacy policy
'''
import logging
import os

import discord
from discord.ext import commands

import db
import util

log = logging.getLogger(__name__)


PRIVACY_POLICY_URL = os.getenv('PRIVACY_POLICY_URL', '')
HELPER_CHAT_ID = int(os.getenv('HELPER_CHAT_ID', '0'))


class MyData(commands.Cog):
    '''Commands for users to manage their stored data'''

    def __init__(self, client):
        self.client = client

    @commands.group(name='mydata', invoke_without_command=True)
    async def mydata(self, ctx: commands.Context):
        '''Manage your data. Subcommands: export, delete, optout, optin, privacy'''
        await ctx.send("Usage: `!mydata export|delete|optout|optin|privacy`")

    @mydata.command()
    async def export(self, ctx: commands.Context):
        '''Show all data we have about you (sent via DM)'''
        user_id = ctx.author.id
        hashed = util.hash_user_id(user_id)
        lines = []

        with db.bot_db:
            reminders = db.Reminder.select().where(
                db.Reminder.user_id == user_id
            )
            r_count = reminders.count()
            if r_count:
                lines.append(f"**Reminders:** {r_count}")
                lines.extend(
                    f'  - "{r.reason}" (due <t:{r.reminder_epoch_time}:R>)' for r in reminders
                )

            eject = db.UnejectTime.get_or_none(user_id=user_id)
            if eject:
                lines.append(f"**Eject status:** Ejected until <t:{eject.uneject_epoch_time}:R>")

            queries = db.MechmarketQuery.select().where(
                db.MechmarketQuery.user_id == user_id
            )
            q_count = queries.count()
            if q_count:
                lines.append(f"**Mechmarket search queries:** {q_count}")
                lines.extend(
                    f'  - "{q.search_string}"' for q in queries
                )

            role_count = db.RoleAssignment.select().where(
                db.RoleAssignment.hashed_user_id == hashed
            ).count()
            lines.append(f"**Sticky role entries:** {role_count} "
                         "(stored as one-way hash — specific roles not listed)")

            opted_out = db.OptOut.get_or_none(hashed_user_id=hashed) is not None
            lines.append(f"**Opt-out status:** {'opted out' if opted_out else 'not opted out'}")

        embed = discord.Embed(
            title="Your Data",
            description="\n".join(lines) or "No data found.",
            color=discord.Color.blue()
        )
        await self._send_dm(ctx, embed=embed)

    @mydata.command()
    async def delete(self, ctx: commands.Context):
        '''Delete all your data from the bot (sent via DM)'''
        user_id = ctx.author.id
        hashed = util.hash_user_id(user_id)
        lines = []

        with db.bot_db:
            deleted_reminders = db.Reminder.delete().where(
                db.Reminder.user_id == user_id
            ).execute()
            if deleted_reminders:
                lines.append(f"Deleted {deleted_reminders} reminder(s)")

            deleted_eject = db.UnejectTime.delete().where(
                db.UnejectTime.user_id == user_id
            ).execute()
            if deleted_eject:
                lines.append("Deleted eject record")

            deleted_queries = db.MechmarketQuery.delete().where(
                db.MechmarketQuery.user_id == user_id
            ).execute()
            if deleted_queries:
                lines.append(f"Deleted {deleted_queries} mechmarket query(ies)")

            role_rows = db.RoleAssignment.select().where(
                db.RoleAssignment.hashed_user_id == hashed
            )
            role_names = [r.role_name for r in role_rows]
            deleted_roles = role_rows.delete().execute()
            if deleted_roles:
                lines.append(f"Deleted {deleted_roles} sticky role entry(ies)")

            db.OptOut.delete().where(
                db.OptOut.hashed_user_id == hashed
            ).execute()

        if deleted_roles:
            await self._notify_helper_of_role_shake(ctx, role_names)

        if not lines:
            lines.append("No data found to delete.")

        lines.append("")
        lines.append("> Spam hash entries (MessageIdentifier) auto-expire in 5 minutes "
                     "and are not stored long-term.")
        if deleted_roles:
            lines.append("> Sticky roles have been removed. If you leave and rejoin, "
                         "moderation roles will not auto-reapply.")
        lines.append("> If you had previously opted out, that preference has also been cleared.")

        embed = discord.Embed(
            title="Data Deleted",
            description="\n".join(lines),
            color=discord.Color.green()
        )
        await self._send_dm(ctx, embed=embed)

    @mydata.command()
    async def optout(self, ctx: commands.Context):
        '''Opt out of sticky role tracking'''
        hashed = util.hash_user_id(ctx.author.id)
        with db.bot_db:
            _, created = db.OptOut.get_or_create(hashed_user_id=hashed)
        if created:
            msg = ("You have opted out of sticky role tracking.\n"
                   "Sticky roles will not be applied when you rejoin the server.\n"
                   "Use `!mydata optin` to reverse this.")
        else:
            msg = "You are already opted out."
        await self._send_dm(ctx, text=msg)

    @mydata.command()
    async def optin(self, ctx: commands.Context):
        '''Re-enable sticky role tracking'''
        hashed = util.hash_user_id(ctx.author.id)
        with db.bot_db:
            deleted = db.OptOut.delete().where(
                db.OptOut.hashed_user_id == hashed
            ).execute()
        if deleted:
            msg = "You have opted back in. Sticky role tracking is re-enabled."
        else:
            msg = "You were not opted out."
        await self._send_dm(ctx, text=msg)

    @mydata.command()
    async def privacy(self, ctx: commands.Context):
        '''Link to the privacy policy'''
        if PRIVACY_POLICY_URL:
            await ctx.send(f"Privacy policy: {PRIVACY_POLICY_URL}")
        else:
            await ctx.send("A privacy policy URL has not been configured. "
                           "Contact the server moderators for information.")

    async def _notify_helper_of_role_shake(self, ctx: commands.Context, role_names: list[str]):
        '''Alert helpers when a user deletes sticky role entries, to flag possible role evasion.'''
        channel = self.client.get_channel(HELPER_CHAT_ID)
        if not channel:
            log.error("Helper Chat cannot be found (HELPER_CHAT_ID=%s); cannot notify of sticky role deletion",
                      HELPER_CHAT_ID)
            return

        role_list = "\n".join(f"- `{name}`" for name in role_names) or "- unknown"

        embed = discord.Embed(
            title="Sticky Roles Removed via !mydata delete",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="User",
            value=f"<@{ctx.author.id}> (`{ctx.author.id}`)",
            inline=False
        )
        embed.add_field(
            name="Roles being untracked",
            value=role_list,
            inline=False
        )
        embed.set_footer(
            text="They may be attempting to shake off moderation roles. "
                 "Re-apply roles manually if appropriate."
        )
        await channel.send(embed=embed)

    async def _send_dm(self, ctx: commands.Context, text: str = "",
                       embed: discord.Embed | None = None):
        '''Send a DM to the user. Falls back to a private channel message.'''
        try:
            if text:
                await ctx.author.send(text)
            if embed:
                await ctx.author.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I couldn't DM you. Please enable DMs and try again.",
                           delete_after=10)
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass


async def setup(client):
    '''setup'''
    await client.add_cog(MyData(client))
