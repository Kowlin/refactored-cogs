import discord
from discord.ext import commands
from .utils import checks
import asyncio
import logging
log = logging.getLogger('red.punish')


class Punish:
    """Adds the ability to punish users."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_server=True)
    async def punish(self, ctx, user: discord.Member):
        """Place a user in timeout, if the user is already in timeout, this will also remove him from it"""
        server = ctx.message.server
        # Check if timeout exists.
        if 'Timeout' not in [r.name for r in server.roles]:
            await self.bot.say("The Timeout role doesn't exist. Creating!")
            log.debug('Creating timeout role')
            try:
                perms = discord.Permissions.none()
                # toggle permissions you want, rest are false
                await self.bot.create_role(server, name="Timeout", permissions=perms)
                await self.bot.say("Role created! Setting channel permissions!\nPlease ensure that your moderator roles are ABOVE the timeout role!\nPlease wait until the user has been added to the Timeout role!")
                try:
                    for c in server.channels:
                        if c.type.name == 'text':
                            perms = discord.Permissions.none()
                            perms.send_messages = True
                            r = discord.utils.get(ctx.message.server.roles, name="Timeout")
                            await self.bot.edit_channel_permissions(c, r, deny=perms)
                        await asyncio.sleep(1.5)
                except discord.Forbidden:
                    await self.bot.say("A error occured while making channel permissions.\nPlease check your channel permissions for the Timeout role!")
            except discord.Forbidden:
                await self.bot.say("I cannot create a role. Please assign Manage Roles to me!")
        r = discord.utils.get(ctx.message.server.roles, name="Timeout")
        if 'Timeout' not in [r.name for r in user.roles]:
            await self.bot.add_roles(user, r)
            await self.bot.say("User is now in Timeout!")
            log.debug('UID {} in Timeout role'.format(user.id))
        else:
            await self.bot.remove_roles(user, r)
            await self.bot.say("User is now removed from Timeout!")
            log.debug('UID {} removed from Timeout role'.format(user.id))

        # Look for new channels, and slap the role in there face!
    async def new_channel(self, c):
        if 'Timeout' in [r.name for r in c.server.roles]:
            perms = discord.Permissions.none()
            perms.send_messages = True
            r = discord.utils.get(c.server.roles, name="Timeout")
            await self.bot.edit_channel_permissions(c, r, deny=perms)
            log.debug('Timeout role created on channel: {}'.format(c.id))


def setup(bot):
    n = Punish(bot)
    bot.add_listener(n.new_channel, 'on_channel_create')
    bot.add_cog(n)
