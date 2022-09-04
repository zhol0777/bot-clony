'''
Method to warn users of impending eject/razer hate/etc
and track these warnings for mods/helpers
'''
import os

from discord.ext import commands
import discord

import db
import util

HELPER_CHAT = os.getenv('HELPER_CHAT')
HELPER_ROLE = os.getenv('HELPER_ROLE')
MOD_ROLE = os.getenv('MOD_ROLE')


class MemberWarning(commands.Cog):
    '''Warning cog'''
    def __init__(self, client):
        self.client = client

    @commands.group()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def ejectwarn(self, ctx: commands.Context):
        '''
        Usage: !ejectwarn [@ user tag] [reason...]
               [as message reply] !ejectwarn [reason...]
        Warn a user to stop being a punk, and track the warning
        '''
        if ctx.invoked_subcommand and \
                ctx.invoked_subcommand.name in ['list', 'delete']:
            return
        args = ctx.message.content.split()
        if ctx.message.reference is not None:
            # replying to someone who is about to be ejected
            reply_message = await util.get_reply_message(ctx, ctx.message)
            message_url = reply_message.jump_url
            original_msg = await ctx.fetch_message(
                id=ctx.message.reference.message_id)
            warning_reason = ' '.join(args[1:]) if len(args) >= 2 else ''
            user_id = original_msg.author.id
            with db.bot_db:
                db.WarningMemberReason.create(
                    user_id=user_id,
                    reason=warning_reason,
                    message_url=message_url,
                    for_eject=True,
                    for_ban=False
                )
            await ctx.channel.send("stop being a punk",
                                   reference=reply_message)
        else:
            user_id = util.get_id_from_tag(args[1])
            warning_reason = ' '.join(args[2:]) if len(args) >= 3 else ''
            with db.bot_db:
                db.WarningMemberReason.create(
                    user_id=user_id,
                    reason=warning_reason,
                    message_url=ctx.message.jump_url,
                    for_eject=True,
                    for_ban=False
                )
            await ctx.channel.send("stop being a punk")

    @ejectwarn.command()
    @commands.has_any_role(HELPER_ROLE, MOD_ROLE)
    async def list(self, ctx: commands.Context, user_id_tag: str):
        '''
        Usage: !ejectwarn list [@ user tag]
        list every warning given per some given user id
        '''
        channel = discord.utils.get(ctx.guild.channels,
                                    name=HELPER_CHAT)

        user_id = util.get_id_from_tag(user_id_tag)
        warnings = db.WarningMemberReason.select().where(
            db.WarningMemberReason.user_id == user_id
        )
        for warning in warnings:  # pylint: disable=not-an-iterable
            embed = discord.Embed(color=discord.Colour.orange())
            embed.set_author(name="Warning")
            embed.add_field(name="id", value=str(warning.id))
            embed.add_field(name="Reason", value=str(warning.reason))
            embed.add_field(name="Message link", value=str(warning.message_url))
            await channel.send(embed=embed)

    @ejectwarn.command()
    @commands.has_any_role(MOD_ROLE, HELPER_ROLE)
    async def delete(self, reason_id: int):
        '''
        Usage: !ejectwarn delete [warning reason ID]
        delete a warning from a user per reason_id
        '''
        warning_reason = db.WarningMemberReason.get_or_none(id=reason_id)
        if warning_reason:
            warning_reason.delete_instance()


def setup(client):
    '''setup'''
    client.add_cog(MemberWarning(client))
