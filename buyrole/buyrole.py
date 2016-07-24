import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
import logging
from tabulate import tabulate
from .utils import checks
from __main__ import send_cmd_help
import os
log = logging.getLogger('red.buyrole')


class Buyrole:
    """Allows the user to buy a role with economy balance"""

    # --- Format
    # {
    # Server : {
    #   Toggle: True/False
    #   Roles : {
    #       Price :
    #       Name :
    #       }
    #    }
    # }
    # ---
    def __init__(self, bot):
        self.bot = bot
        self.json = {}
        self.location = 'data/buyrole/settings.json'
        self.json = dataIO.load_json(self.location)

    @commands.command(pass_context=True, no_pm=True)
    async def buyrole(self, ctx, role: discord.Role=None):
        """Buy a role of your chooise with your hard earned balance

        To buy a role with a space in it, use qoutes"""
        economy = self.bot.get_cog('Economy').bank
        server = ctx.message.server.id
        author = ctx.message.author
        if server not in self.json:
            await self.bot.say(':warning: Buyrole isn\'t setup yet. Please ask your admin to set it up.')
        elif self.json[server]['toggle'] is False:
            await self.bot.say(':warning: Buyrole is disabled on this server.')
        else:
            if role is None:
                table = []
                for key, role in self.json[server].items():
                    try:
                        temp = []
                        temp.append(self.json[server][key]['name'])
                        temp.append(self.json[server][key]['price'])
                        table.append(temp)  # Past the list into a new list, thats a collection of lists.
                    except:
                        pass
                    header = ['Role', 'Price']
                if not table:
                    await self.bot.say(':warning: No roles are setup yet.')
                else:
                    await self.bot.say('```\n{}```'.format(tabulate(table, headers=header, tablefmt='simple')))
            else:
                if role.id in self.json[server]:
                    if role in author.roles:
                        await self.bot.say(':warning: {}, you already own this role!'.format(author.display_name))
                    elif economy.can_spend(author, int(self.json[server][role.id]['price'])):
                        msg = 'This role costs {}.\nAre you sure you want to buy this role?\nType *"Yes"* to confirm.'
                        log.debug('Starting check on UserID({})'.format(author.id))
                        await self.bot.say(msg.format(self.json[server][role.id]['price']))
                        answer = await self.bot.wait_for_message(timeout=15, author=author)
                        if answer is None:
                            await self.bot.say(':warning: {}, you didn\'t respond in time.'.format(author.display_name))
                            log.debug('Killing check on UserID({}) (Timeout)'.format(author.id))
                        elif 'yes' in answer.content.lower() and role.id in self.json[server]:
                            try:
                                economy.withdraw_credits(author, int(self.json[server][role.id]['price']))
                                await self.bot.add_roles(author, role)
                                await self.bot.say(':white_check_mark: Done! You\'re now the proud owner of {}'.format(self.json[server][role.id]['name']))
                                log.debug('Killing check on UserID({}) (Complete)'.format(author.id))
                            except discord.Forbidden:
                                await self.bot.say(":warning: I cannot manage server roles, or the role/user is higher then my role.\nPlease check the server roles to solve this.")
                        else:
                            await self.bot.say(':warning: {}, ok you can try again later.'.format(author.display_name))
                    else:
                        await self.bot.say(':warning: Sorry {}, you don\'t have enough credits to buy {}'.format(author.display_name, self.json[server][role.id]['name']))
                else:
                    await self.bot.say(':warning: {}, you cannot buy this role!'.format(role.name))

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def buyroleset(self, ctx):
        """Manage the settings for buyrole"""
        server = ctx.message.server.id
        if server not in self.json:  # Setup the server in the dict, failur rate 0%. For now
            self.json[server] = {'toggle': True}
            dataIO.save_json(self.location, self.json)
            log.debug('Wrote server ID({})'.format(server))
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @buyroleset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def add(self, ctx, role: discord.Role, price):
        """Adds a role for users to buy

        To edit a role, use this command again,
        To add a role with a space in it put it in qoutes,\"Role name\""""
        server = ctx.message.server.id
        self.json[server][role.id] = {'price': price, 'name': role.name}
        dataIO.save_json(self.location, self.json)
        log.debug('Wrote role ID({}) in server ID({})'.format(role.id, server))
        await self.bot.say(':white_check_mark: Added {} to the buy list for {}'.format(role.name, price))

    @buyroleset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def remove(self, ctx, role: discord.Role):
        """Removes a role for users to buy"""
        server = ctx.message.server.id
        try:
            del self.json[server][role.id]
            dataIO.save_json(self.location, self.json)
            log.debug('deleted role ID({}) in server ID({})'.format(role.id, server))
            await self.bot.say(':white_check_mark: Done! Removed the role')
        except:
            await self.bot.say(':warning: {} isn\'t in the list.'.format(role.name))

    @buyroleset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggle(self, ctx):
        """Enables or disables buying roles in the server"""
        server = ctx.message.server.id
        if self.json[server]['toggle'] is True:
            self.json[server]['toggle'] = False
            await self.bot.say(':white_check_mark: Toggle disabled! You can no longer buy roles on this server')
        else:
            self.json[server]['toggle'] = True
            await self.bot.say(':white_check_mark: Toggle enabled! You can buy roles on this server now!')
        log.debug('Wrote toggle to {} in server ID({})'.format(self.json[server]['toggle'], server))
        dataIO.save_json(self.location, self.json)

    @buyroleset.command(hidden=True, pass_context=True)
    @checks.admin_or_permissions(administrator=True)
    async def dicts(self, ctx):
        """Dicks"""
        await self.bot.say('All the dicks!')

    async def _update_name(self, old, new):  # Change the 'name' variable in the role ID. Since we don't pull names dynamicly in the table
        if new.server.id in self.json:
            if old.name != new.name:
                if new.id in self.json[new.server.id]:
                    self.json[new.server.id][new.id]['name'] = new.name
                    log.debug('Written new name to {}'.format(new.id))
                    dataIO.save_json(self.location, self.json)


def check_folder():
    if not os.path.exists('data/buyrole'):
        log.debug('Creating folder: data/buyrole')
        os.makedirs('data/buyrole')


def check_file():
    f = 'data/buyrole/settings.json'
    if dataIO.is_valid_json(f) is False:
        log.debug('Creating json: settings.json')
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = Buyrole(bot)
    bot.add_listener(n._update_name, 'on_server_role_update')
    bot.add_cog(n)
