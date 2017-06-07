"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import discord
from discord.ext import commands
from .utils import checks
from __main__ import send_cmd_help, settings
from cogs.utils.dataIO import dataIO
import os
import re
import asyncio


class Antilink:
    """Blocks Discord invite links from users who don't have the permission 'Manage Messages'
    can optionally block all links not just invites"""

    __author__ = "Kowlin"
    __version__ = "AL-v1.1-LTS"



    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/antilink/settings.json'
        self.json = dataIO.load_json(self.location)
        self.regex = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.gg|discordapp\.com\/invite)\b([-a-zA-Z0-9/]*)>?")
        self.regex_discordme = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.me\/)\b([-a-zA-Z0-9/]*)>?")
        self.regex_url = re.compile(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))')

    @commands.group(pass_context=True, no_pm=True)
    async def antilinkset(self, ctx):
        """Manages the settings for antilink."""
        serverid = ctx.message.server.id
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
        if serverid not in self.json:
            self.json[serverid] = {'toggle': False, 'message': '', 'dm': False,
                                   'strict': False}

    @antilinkset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggle(self, ctx):
        """Enable/disables antilink in the server"""
        serverid = ctx.message.server.id
        if self.json[serverid]['toggle'] is True:
            self.json[serverid]['toggle'] = False
            await self.bot.say('Antilink is now disabled')
        elif self.json[serverid]['toggle'] is False:
            self.json[serverid]['toggle'] = True
            await self.bot.say('Antilink is now enabled')
        dataIO.save_json(self.location, self.json)

    @antilinkset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def togglestrict(self, ctx):
        """remove all the links"""
        serverid = ctx.message.server.id
        if self.json[serverid]['strict'] is True:
            self.json[serverid]['strict'] = False
            await self.bot.say('Strict mode is now disabled')
        elif self.json[serverid]['strict'] is False:
            self.json[serverid]['strict'] = True
            await self.bot.say('strictmode is now enabled')
        dataIO.save_json(self.location, self.json)

    @antilinkset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def message(self, ctx, *, text):
        """Set the message for when the user sends a illegal discord link"""
        serverid = ctx.message.server.id
        self.json[serverid]['message'] = text
        dataIO.save_json(self.location, self.json)
        await self.bot.say('Message is set')
        if self.json[serverid]['dm'] is False:
            await self.bot.say('Remember: Direct Messages on removal is disabled!\nEnable it with ``antilinkset toggledm``')

    @antilinkset.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggledm(self, ctx):
        serverid = ctx.message.server.id
        if self.json[serverid]['dm'] is False:
            self.json[serverid]['dm'] = True
            await self.bot.say('Enabled DMs on removal of invite links')
        elif self.json[serverid]['dm'] is True:
            self.json[serverid]['dm'] = False
            await self.bot.say('Disabled DMs on removal of invite links')
        dataIO.save_json(self.location, self.json)

    async def _new_message(self, message):
        """Finds the message and checks it for regex"""
        user = message.author
        if message.server is None:
            return
        if message.server.id in self.json:

            if self.json[message.server.id]['toggle'] is True:
                if self.regex.search(message.content) is not None or self.regex_discordme.search(message.content) is not None \
                    or self.regex_url.search(message.content)is not None and self.json[message.server.id]['strict']:

                    roles = [r.name for r in user.roles]
                    bot_admin = settings.get_server_admin(message.server)
                    bot_mod = settings.get_server_mod(message.server)
                    if user.id == settings.owner:
                        return
                    elif bot_admin in roles:
                        return
                    elif bot_mod in roles:
                        return
                    elif user.permissions_in(message.channel).manage_messages is True:
                        return
                    else:
                        asyncio.sleep(0.5)
                        await self.bot.delete_message(message)
                        if self.json[message.server.id]['dm'] is True:
                            await self.bot.send_message(message.author, self.json[message.server.id]['message'])


def check_folder():
    if not os.path.exists('data/antilink'):
        os.makedirs('data/antilink')


def check_file():
    f = 'data/antilink/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = Antilink(bot)
    bot.add_cog(n)
    bot.add_listener(n._new_message, 'on_message')
