import discord
from discord.ext import commands
from .utils import checks
from __main__ import send_cmd_help, settings
from cogs.utils.dataIO import dataIO
import os
import re
import asyncio


class Antiinvite:
    """Blocks discord invites from normal users.'"""

    def __init__(self, bot):
        self.bot = bot
        self.location = 'data/antiinvites/settings.json'
        self.json = dataIO.load_json(self.location)
        self.regex = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.gg|discordapp\.com\/invite)\b([-a-zA-Z0-9/]*)>?")
        self.regex_discordme = re.compile(r"<?(https?:\/\/)?(www\.)?(discord\.me\/)\b([-a-zA-Z0-9/]*)>?")

    @commands.group(pass_context=True, no_pm=True)
    async def antiinvite(self, ctx):
        """Antilink settings"""
        serverid = ctx.message.server.id
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
        if serverid not in self.json:
            self.json[serverid] = {'toggle': False, 'message': '', 'dm': False}

    @antiinvite.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def toggle(self, ctx):
        """Enable/disables antilink in your server"""
        serverid = ctx.message.server.id
        if self.json[serverid]['toggle'] is True:
            self.json[serverid]['toggle'] = False
            await self.bot.say('Antilink is now completly disabled on this server.')
        elif self.json[serverid]['toggle'] is False:
            self.json[serverid]['toggle'] = True
            await self.bot.say('Antilink is now fully enabled,👀 make sure to give "manage message" permission to the bot.')
        dataIO.save_json(self.location, self.json)

    @antiinvite.command(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def message(self, ctx, *, text):
        """Set the message when the user send invite links"""
        serverid = ctx.message.server.id
        self.json[serverid]['message'] = text
        dataIO.save_json(self.location, self.json)
        await self.bot.say('Message is set')
        if self.json[serverid]['dm'] is False:
            await self.bot.say('Remember: Direct Messages on removal is disabled!\nEnable it with ``antilinkset toggledm``')

    @antiinvite.command(pass_context=True, no_pm=True)
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
                if self.regex.search(message.content) is not None or self.regex_discordme.search(message.content) is not None:
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
    if not os.path.exists('data/antiinvites'):
        os.makedirs('data/antiinvites')


def check_file():
    f = 'data/antiinvites/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = antiinvites(bot)
    bot.add_cog(n)
    bot.add_listener(n._new_message, 'on_message')
