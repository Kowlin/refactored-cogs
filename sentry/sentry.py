"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import discord
from discord.ext import commands
from .utils import checks
import logging
import os
from cogs.utils.dataIO import dataIO
import re
# Raven
from raven import Client
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler

log = logging.getLogger('red.sentry')


class Sentry:
    """Sentry Debugging"""

    __author__ = "Kowlin"
    __version__ = "S-V1.1"

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/sentry/settings.json')
        if self.settings['dsn'] is None:
            log.warning('Sentry: DSN key is not set. Not sending logs!')
        else:
            if self.settings['ssl'] is False:
                self.raven = Client(self.settings['dsn'] + '?verify_ssl=0')
            else:
                self.raven = Client(self.settings['dsn'])
            self.handler = SentryHandler(self.raven)
            self.handler.setLevel(self.settings['level'])
            self.logger = logging.getLogger("red").addHandler(self.handler)
            setup_logging(self.handler)
            # --- Raven settings
            self.raven.tags = self.settings['tags']
            if self.settings['name'] is not None:
                self.raven.name = self.settings['name']
            if self.settings['environment'] is not None:
                self.raven.environment = self.settings['environment']
            if self.settings.get('ignore'):
                self.raven.ignore = self.settings['ignore']

    def __unload(self):
            logging.getLogger("red").removeHandler(self.handler)

    @commands.group(pass_context=True)
    @checks.is_owner()
    async def sentry(self, ctx):
        """Manage Sentry logging"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @sentry.command(pass_context=True)
    async def dsn(self, ctx, dsn: str):
        """Set your DSN, Full private required. Recommended to do in DM"""
        if re.match('(https\:\/\/|http\:\/\/).*\:.*\@.*\/*[0-9]', dsn) is None:
            await self.bot.say('DSN key is not valid. Make sure its a full private key!')
        else:
            self.settings['dsn'] = dsn
            try:
                await self.bot.delete_message(ctx.message)
                await self.bot.say('DSN key set, removed your message for safety.\nReload the cog for the changes to have effect.\nTry the key with ``{}sentry test``'.format(ctx.prefix))
            except:
                await self.bot.say('DSN key set. Please remove your message for the safety of your logging operation.\nReload the cog for the changes to have effect.\nTry the key with ``{}sentry test``'.format(ctx.prefix))
            self.save_json()

    @sentry.command(pass_context=True)
    async def test(self, ctx, *, message="A test message to Sentry"):
        """Send a test message to the Sentry host."""
        try:
            self.raven.captureMessage(message)
            await self.bot.say('Test message should be send. Please check your Sentry instance.')
        except:
            await self.bot.say('Sentry client isn\'t setup. Please set a key and reload the cog.')

    @sentry.command(pass_context=True)
    async def name(self, ctx, name):
        """Set the "server_name" that appears in Sentry"""
        self.settings['name'] = name
        await self.bot.say('Name set,\nReload the cog for the changes to have effect.')
        self.save_json()

    @sentry.command(pass_context=True)
    async def environment(self, ctx, environment):
        """Set the environment that appears in Sentry"""
        self.settings['environment'] = environment
        await self.bot.say('Environment set,\nReload the cog for the changes to have effect.')

    @sentry.command(pass_context=True)
    async def level(self, ctx, level):
        """Set the logging level for Sentry

        The level can only be one of the following:
        critical, debug, error, fatal, notset, warn, warning
        Recommended: error"""
        log_list = ['CRITICAL', 'DEBUG', 'ERROR', 'FATAL', 'NOTSET', 'WARN', 'WARNING']
        if level.upper() in log_list:
            self.settings['level'] = level.upper()
            await self.bot.say('Log level now set to {}\nReload the cog for the changes to have effect.'.format(level))
            self.save_json()
        else:
            await self.bot.say('Invalid log level, please use one of the following:\ncritical, debug, error, fatal, notset, warn, warning')

    @sentry.command(pass_context=True)
    async def ssl(self, ctx):
        """Enable or disable SSL verification to the Sentry server."""
        if self.settings['ssl'] is True:
            self.settings['ssl'] = False
            await self.bot.say('SSL verification is disabled.\nReload the cog for the changes to have effect.')
        else:
            self.settings['ssl'] = True
            await self.bot.say('SSL verification is enabled\nReload the cog for the changes to have effect.')
        self.save_json()

    @sentry.group(pass_context=True)
    async def tags(self, ctx):
        """Manage tags for Sentry"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @tags.command(pass_context=True)
    async def add(self, ctx, tag, *, value):
        """Add/edit a tag with the set value."""
        self.settings['tags'][tag] = value
        await self.bot.say('Tag ``{}`` with value ``{}`` added.\nReload the cog for the changes to have effect.'.format(tag, value))
        self.save_json()

    @tags.command(pass_context=True)
    async def remove(self, ctx, tag):
        """Remove a tag"""
        if tag in self.settings['tags']:
            del self.settings['tags'][tag]
            await self.bot.say('Tag ``{}`` removed.\nReload the cog for the changes to have effect.'.format(tag))
            self.save_json()
        else:
            await self.bot.say('This tag doesn\'t exist')

    @tags.command(pass_context=True)
    async def list(self, ctx):
        """List all tags"""
        tag_list = ''
        for tag, value in self.settings['tags'].items():
            tag_list += '{}: {}\n'.format(tag, value)
        await self.bot.say("```\n{}\n```".format(tag_list))

    def save_json(self):
        dataIO.save_json('data/sentry/settings.json', self.settings)

    @sentry.group(pass_context=True)
    async def ignore(self, ctx):
        """Manage the ignored loggers for Sentry"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @ignore.command(pass_context=True, name='add')
    async def add_ignore(self, ctx, logger):
        """Add a logger to the ignore list"""
        if 'ignore' not in self.settings:
            self.settings['ignore'] = []
        if logger not in self.settings['ignore']:
            self.settings['ignore'].append(logger)
            self.save_json()
            await self.bot.say('``{}`` added to the ignore list.\nReload the cog for the changes to have effect.'.format(logger))
        else:
            await self.bot.say('``{}`` already in the ignore list.'.format(logger))

    @ignore.command(pass_context=True, name='remove')
    async def remove_ignore(self, ctx, logger):
        """Remove a logger from the ignore list"""
        if logger in self.settings['ignore']:
            del self.settings['ignore'][logger]
            self.save_json()
            await self.bot.say('``{}`` deleted from the ignore list.\nReload the cog for the changes to have effect.'.format(logger))
        else:
            await self.bot.say('``{}`` is not in the ignore list.'.format(logger))


def check_folder():
    if not os.path.exists('data/sentry'):
        os.makedirs('data/sentry')


def check_file():
    f = 'data/sentry/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {'dsn': None,
                             'tags': {},
                             'name': None,
                             'environment': None,
                             'ssl': True,
                             'level': 'ERROR',
                             'ignore': []
                             })
    f = 'data/sentry/settings.json'


def setup(bot):
    check_folder()
    check_file()
    n = Sentry(bot)
    bot.add_cog(n)
