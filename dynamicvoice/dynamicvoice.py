"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

# Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
# Essentials
import os
from random import choice
import asyncio
import logging
log = logging.getLogger('red.dynamicvoice')


class DynamicVoice:
    """Create dynamic voice channels for your server! Deal with the crowd, never run out of voice channels again!"""

    __author__ = "Kowlin"
    __version__ = "DV-V1.0a"

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/dynamicvoice/settings.json')
        self.namelist = open('data/dynamicvoice/names.txt', 'rt')
        self.namelist = self.namelist.readlines()

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(Manage_channels=True)
    async def dynamicvoice(self, ctx):
        """Settings for DynamicVoice"""
        server = ctx.message.server
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)
        if server.id not in self.settings:
            self.settings[server.id] = {'toggle': False,
                                        'count': 2,
                                        'position': -1,
                                        'channels': [],
                                        'cache': []
                                        }

    @dynamicvoice.command(pass_context=True, no_pm=True)
    async def toggle(self, ctx):
        """Toggle DynamicVoice for this server."""
        server = ctx.message.server
        perms = ctx.message.server.get_member(self.bot.user.id).server_permissions
        if perms.manage_channels is False:
            await self.bot.say('I cannot manage channels in this server. So I cannot enable DynamicVoice.\nAssign me manage channels.')
        elif self.settings[server.id]['toggle'] is False:
            self.settings[server.id]['toggle'] = True
            self.save_json()
            await self.bot.say('DynamicVoice is now enabled. Going to create the new dynamic channels!')
            await self._create_channels(server)
        else:
            self.settings[server.id]['toggle'] = False
            self.save_json()
            await self.bot.say('DynamicVoice is now disabled. Deleting the dynamic channels!')
            await self._delete_channels(server)

    @dynamicvoice.command(pass_context=True, no_pm=True)
    async def emptychannels(self, ctx, number: int):
        """Set the number of empty dynamic channels.
        These channels will always be topped up by the bot."""
        server = ctx.message.server
        if self.settings[server.id]['count'] > number:
            self.settings[server.id]['count'] = number
            self.save_json()
            await self._delete_channels(server)
            await self.bot.say('The new channel count is set. Deleting empty dynamic channels')
        elif self.settings[server.id]['count'] < number:
            self.settings[server.id]['count'] = number
            self.save_json()
            await self.bot.say('The new channel count is set. Adding new empty dynamic channels')
            await self._create_channels(server)
        else:
            await self.bot.say('The requested channel count is the same as the current one. Nothing changed.')

    @dynamicvoice.command(pass_context=True, no_pm=True)
    async def position(self, ctx, position: int):
        """Set the position of new voice channels created by DynamicVoice
        0 for the top, 1 for the one below that, ETC ETC.
        -1 to disable setting positions (Default Discord behavior)"""
        server = ctx.message.server
        if self.settings[server.id]['position'] == position:
            await self.bot.say('The position already is {}.'.format(position))
        else:
            self.settings[server.id]['position'] = position
            self.save_json()
            if position == -1:
                await self.bot.say('New channel positions are now disabled!')
            else:
                await self.bot.say('New channels will appear on position {} now.'.format(position))

    @dynamicvoice.command(pass_context=True, no_pm=True)
    async def flush(self, ctx):
        """Remove and recreate all dynamic channels!"""
        server = ctx.message.server
        for channel_id in self.settings[server.id]['channels']:
            try:
                channel = server.get_channel(channel_id)
                await asyncio.sleep(0.25)
                await self.bot.delete_channel(channel)
            except:
                pass
        self.settings[server.id]['channels'].clear()
        self.settings[server.id]['cache'].clear()
        await self._create_channels(server)

    def save_json(self):
        dataIO.save_json("data/dynamicvoice/settings.json", self.settings)

    async def _create_channels(self, server):
        """Create new dynamic channels"""
        if len(self.settings[server.id]['channels']) < self.settings[server.id]['count']:
            count = self.settings[server.id]['count'] - len(self.settings[server.id]['channels'])
            for i in range(count):
                name = choice(self.namelist)[:-1]
                await asyncio.sleep(0.25)  # Sleep to avoid the longest existing bug in d.py
                channel = await self.bot.create_channel(server, name.title(), type=discord.ChannelType.voice)
                self.settings[server.id]['channels'].append(channel.id)
                if self.settings[server.id]['position'] != -1:
                    await asyncio.sleep(0.25)
                    await self.bot.move_channel(channel, self.settings[server.id]['position'])
            self.save_json()

    async def _delete_channels(self, server):
        """Delete dynamic voice channels"""
        if len(self.settings[server.id]['channels']) > self.settings[server.id]['count']:
            count = len(self.settings[server.id]['channels']) - self.settings[server.id]['count']
            for i in range(count):
                await asyncio.sleep(0.25)
                try:
                    channel = discord.utils.get(server.channels, id=self.settings[server.id]['channels'][0])
                    await self.bot.delete_channel(channel)
                except:
                    pass
                del self.settings[server.id]['channels'][0]
            self.save_json()
        else:
            for c in self.settings[server.id]['channels']:
                try:
                    channel = discord.utils.get(server.channels, id=c)
                    await self.bot.delete_channel(channel)
                except:
                    pass
                self.settings[server.id]['channels'].remove(c)
            self.save_json()

    async def _name_channel(self, member):
        """Rename the channel with the game if the user has one"""
        game = member.game
        channel = member.voice.voice_channel
        if member.game is not None:
            await self.bot.edit_channel(channel, name="{} - {}".format(channel.name, game))

    async def _check_count(self, server):
        """Check voice channel count and create voice channels"""
        log.debug('--- START CHECK COUNT FUNCTION ---')
        empty = []
        used = []
        for channel in self.settings[server.id]['channels']:
            channel_obj = discord.utils.get(server.channels, id=channel)
            if channel_obj.voice_members != 0:
                used.append(channel)
            else:
                empty.append(channel)
        if len(empty) < self.settings[server.id]['count']:
            count = self.settings[server.id]['count'] - len(empty) - 1
            for c in range(count):
                name = choice(self.namelist)[:-1]
                channel = await self.bot.create_channel(server, name.title(), type=discord.ChannelType.voice)
                self.settings[server.id]['channels'].append(channel.id)
                if self.settings[server.id]['position'] != -1:
                    await asyncio.sleep(0.25)
                    await self.bot.move_channel(channel, self.settings[server.id]['position'])
            self.save_json()

    async def check_voice(self, memb_before, memb_after):
        """The core of this cog, building and deleting of voice channels.
        To do this in a dynamic way we have to build a cache that stored the correct channels
        So that we can remove them (and from the cache) once their done being used,

        cache = Dynamic voice channel pool (all current channels) - required empty (also known as channel count)
        """
        server = memb_after.server
        cache = self.settings[server.id]['cache']
        channels = self.settings[server.id]['channels']

        # Check if memb_after is in a voice channel (User joined voice channel or switched)
        log.debug('--- START JOIN FUNCTION ---')
        if memb_after.voice.voice_channel is not None:
            log.debug('User joined: {}'.format(memb_after.voice.voice_channel))
            channel = memb_after.voice.voice_channel
            if channel.id not in cache:
                if channel.id in channels:
                    log.debug('Passed check: Renaming Channel and adding in cache')
                    await self._name_channel(memb_after)
                    cache.append(channel.id)
                    await self._check_count(server)

        # Check if memb_after is not in a voice channel (User left voice channel)
        log.debug('--- START LEAVE FUNCTION ---')
        if len(memb_before.voice.voice_channel.voice_members) == 0:
            channel = memb_before.voice.voice_channel
            log.debug('User left: {}'.format(memb_before.voice.voice_channel))
            if channel.id in cache:
                log.debug('Channel in cache')
                if len(channel.voice_members) == 0:
                    log.debug('Channel is in cache. And its empty.')
                    await self.bot.delete_channel(channel)
                    cache.remove(channel.id)
                    channels.remove(channel.id)


def check_folder():
    f = 'data/dynamicvoice'
    if not os.path.exists(f):
        os.makedirs(f)


def check_file():
    f = 'data/dynamicvoice/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = DynamicVoice(bot)
    bot.add_listener(n.check_voice, 'on_voice_state_update')
    bot.add_cog(n)
