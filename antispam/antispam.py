# Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
# Essentials
import os


class Antispam:
    """Advanced anti-spam controls"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/antispam/settings.json')

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(Administrator=True)
    async def antispamset(self, ctx):
        """Manage Antispam"""
        server = ctx.message.server
        if server.id not in self.settings:
            self.settings[server.id] = {}
            self.save_json()
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)


def check_folder():
    f = 'data/antispam'
    if not os.path.exists(f):
        os.makedirs(f)


def check_file():
    f = 'data/antispam/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = Antispam(bot)
    bot.add_cog(n)
