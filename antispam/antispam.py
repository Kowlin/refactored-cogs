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
            actions = {
                'massmention': {'state': False, 'maxmentions': 10},
                'repeatmessage': {'state': False, 'repeats': 3},
                'slowmode': {'state': False, 'slowtime': 60},
                'blockinvites': {'state': False},
                'blocklinks': {'state': False}
            }
            # States can either be False, Warning, Remove, Kick, Ban or Threat increase
            # False counting as off
            # Warning sending out a warning to the user by DM
            # Remove, by removing the action without any other action
            # Kick... Well... You know, kicking.
            # Ban. You know that one
            # Threat for increasing a users Threat level on the Threat cog (Not developed as of yet)
            self.settings[server.id] = {'actions': actions}
            self.save_json()
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @antispamset.command(pass_context=True, no_pm=True)
    async def reaction(self, ctx, action, reaction):
        """Set the reaction of a action.

        The actions can be one of the following:
        massmention, repeatmessage, slowmode, blockinvites, blocklinks

        The reactions can be one of the following:
        off, remove, warning, kick, ban"""
        reactions = ['off', 'remove', 'warning', 'kick', 'ban']
        server = ctx.message.server
        if action.lower() not in self.settings[server.id]['actions']:
            await self.bot.say('This action doesn\'t exist. Please see the help for accepted actions')
        elif reaction.lower() not in reactions:
            await self.bot.say('This reaction doesn\'t exist. Please see the help for accepted reactions')
        else:
            reaction = reaction.lower()
            if reaction == 'off':
                reaction = False
            self.settings[server.id]['actions'][action]['state'] = reaction
            self.save_json()
            await self.bot.say('{} is now set to {}'.format(action, reaction))

    def save_json(self):
        dataIO.save_json("data/antispam/settings.json", self.settings)


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
