import discord
from discord.ext import commands
from .utils import checks
import asyncio
import logging
# Data stuffies
from __main__ import send_cmd_help
from cogs.utils.dataIO import dataIO
import os
import time
# Tabulate, cause its tabulate
from tabulate import tabulate
log = logging.getLogger('red.punish')


class Punish:
    """Adds the ability to punish users."""

    # --- Format
    # {
    # Server : {
    #   UserIDs : {
    #       Until :
    #       Muted By :
    #       NumberOfSandwiches :
    #       }
    #    }
    # }
    # ---

    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/punish/settings.json'
        self.json = dataIO.load_json(self.location)
        self.min = ['m', 'min', 'mins', 'minutes', 'minute']
        self.hour = ['h', 'hour', 'hours']
        self.day = ['d', 'day', 'days']

    def _timestamp(self, t, unit):
        if unit in self.min:
            return t * 60 + int(time.time())
        elif unit in self.hour:
            return t * 60 * 60 + int(time.time())
        elif unit in self.day:
            return t * 60 * 60 * 24 + int(time.time())
        else:
            raise Exception('Invalid Unit')

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def punish(self, ctx, user: discord.Member, t: int=1, unit='hour'):
        """Places a user in timeout for a period of time.

        Valid unit of times are minutes, hours & days.
        Example usage: !punish @kowlin 3 hours"""
        server = ctx.message.server
        # --- CREATING ROLE ---
        if 'Punished' not in [r.name for r in server.roles]:
            await self.bot.say('The Punished role doesn\'t exist! Creating it now!')
            log.debug('Creating Punished role in {}'.format(server.id))
            try:
                perms = discord.Permissions.none()
                await self.bot.create_role(server, name='Punished', permissions=perms)
                await self.bot.say("Role created! Setting channel permissions!\nPlease ensure that your moderator roles are ABOVE the Punished role!\nPlease wait until the user has been added to the Timeout role!")
                try:
                    r = discord.utils.get(server.roles, name='Punished')
                    perms = discord.PermissionOverwrite()
                    perms.send_messages = False
                    for c in server.channels:
                        if c.type.name == 'text':
                            await self.bot.edit_channel_permissions(c, r, perms)
                            await asyncio.sleep(1.5)
                except discord.Forbidden:
                    await self.bot.say("A error occured while making channel permissions.\nPlease check your channel permissions for the Punished role!")
            except discord.Forbidden:
                await self.bot.say("I cannot create a role. Please assign Manage Roles to me!")
        role = discord.utils.get(server.roles, name='Punished')
        # --- DONE CREATING ROLE! ---
        # --- JSON SERVER LOGIC ---
        if server.id not in self.json:
            log.debug('Adding server({}) in Json'.format(server.id))
            self.json[server.id] = {}
            dataIO.save_json(self.location, self.json)
        # --- DONE JSON SERVER LOGIC! ---
        # --- ASSIGNING TIMESTAMPS AND ROLE ---
        try:
            if user.id not in self.json[server.id] and role not in user.roles:
                # USER NOT IN PUNISH, NO ROLE
                until = self._timestamp(t, unit)
                self.json[server.id][user.id] = {'until': until, 'givenby': ctx.message.author.display_name}
                dataIO.save_json(self.location, self.json)
                await self.bot.add_roles(user, role)
                await self.bot.say('``{}`` is now Punished for {} {} by ``{}``.'.format(user.display_name, str(t), unit, ctx.message.author.display_name))
            elif user.id in self.json[server.id] and role not in user.roles:
                # USER IN PUNISH, NO ROLE
                await self.bot.say('The user {} is still punished but doesn\' have the role. Do you want to reapply the role?\n*(Say "yes" in chat to confirm or "no" to remove the punishment)*'.format())
                answer = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)
                if answer is None:
                    await self.bot.say('You didn\'t respond in time. Doing nothing.')
                elif 'yes' in answer.content.lower():
                    await self.bot.add_roles(user, role)
                    await self.bot.say('Role reapplied on {}'.format(user.display_name))
                else:
                    await self.bot.remove_roles(user, role)
                    del self.json[server.id][user.id]
                    dataIO.save_json(self.location, self.json)
                    await self.bot.say('Alright, punishment is removed from the user.')
            elif user.id not in self.json[server.id] and role in user.roles:
                # USER NOT IN PUNISH, HAS ROLE
                await self.bot.say('{} already had the punished role. Setting the timer'.format(user.display_name))
                until = self._timestamp(t, unit)
                self.json[server.id][user.id] = {'until': until, 'givenby': ctx.message.author.display_name}
                dataIO.save_json(self.location, self.json)
                await self.bot.say('``{}`` is now Punished for {} {} by ``{}``.'.format(user.display_name, str(t), unit, ctx.message.author.display_name))
            else:
                # USER IN PUNISH, HAS ROLE
                await self.bot.say('{} is already punished. Do you want to remove the punishment?\n*(Say "yes" in chat to confirm or "no" to cancel)*'.format(user.display_name))
                answer = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)
                if answer is None:
                    await self.bot.say('You didn\'t respond in time. Doing nothing.')
                elif 'yes' in answer.content.lower():
                    await self.bot.remove_roles(user, role)
                    del self.json[server.id][user.id]
                    dataIO.save_json(self.location, self.json)
                    await self.bot.say('Punishment deleted on {}'.format(user.display_name))
                else:
                    await self.bot.say('Alright, doing nothing')
        except:
            await self.bot.say('Invalid unit')

            # Look for new channels, and slap the role in there face!
    async def new_channel(self, c):
        if 'Punished' in [r.name for r in c.server.roles]:
            if c.type.name == 'text':
                perms = discord.PermissionOverwrite()
                perms.send_messages = False
                r = discord.utils.get(c.server.roles, name='Punished')
                await self.bot.edit_channel_permissions(c, r, perms)
                log.debug('Punished role created on channel: {}'.format(c.id))

    async def check_time(self):
        while True:
            log.debug('Ohai first loop')
            await asyncio.sleep(120)
            log.debug('First Timer')
            for server in self.json:
                log.debug('Server Json')
                for user in self.json[server]:
                    log.debug('User Json')
                    if self.json[server][user]['until'] < int(time.time()):
                        log.debug('Deleting user({}) from server({}) punish list'.format(user, server))
                        try:
                            obj_server = discord.utils.get(self.bot.servers, id=server)
                            obj_user = discord.utils.get(obj_server.members, id=user)
                            obj_role = discord.utils.get(obj_server.roles, name='Punished')
                            del self.json[server][user]
                            dataIO.save_json(self.location, self.json)
                            await self.bot.remove_roles(obj_user, obj_role)
                            log.debug('Done')
                        except:
                            pass


def check_folder():
    if not os.path.exists('data/punish'):
        log.debug('Creating folder: data/punish')
        os.makedirs('data/punish')


def check_file():
    f = 'data/punish/settings.json'
    if dataIO.is_valid_json(f) is False:
        log.debug('Creating json: settings.json')
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = Punish(bot)
    bot.add_listener(n.check_time, 'on_ready')
    bot.add_listener(n.new_channel, 'on_channel_create')
    bot.add_cog(n)
