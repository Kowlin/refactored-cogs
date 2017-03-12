"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import discord
from discord.ext import commands
from .utils import checks
import urllib


class SimplyGoogle:
    """A non sarcastic google command"""

    __author__ = "Kowlin"
    __version__ = "SG-v1.0-LTS"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    async def google(self, ctx, text):
        """Its google, you search with it.
        Example: google A french pug

        Special search options are avaiable; Image, Maps
        Example: google image You know, for kids!
        Another example: google maps New York"""
        search_type = ctx.message.content[len(ctx.prefix + ctx.command.name) + 1:].lower().split(" ")
        # Start of Image
        if search_type[0] == "image":
            search_valid = str(ctx.message.content[len(ctx.prefix + ctx.command.name) + 1:].lower())
            if search_valid == "image":
                await self.bot.say("Please actually search something")
            else:
                uri = "https://www.google.com/search?tbm=isch&q="
                quary = str(ctx.message.content[len(ctx.prefix + ctx.command.name) + 7:].lower())
                encode = urllib.parse.quote_plus(quary, encoding='utf-8', errors='replace')
                await self.bot.say(uri + encode)
            # End of Image
        # Start of Maps
        elif search_type[0] == "maps":
            search_valid = str(ctx.message.content[len(ctx.prefix + ctx.command.name) + 1:].lower())
            if search_valid == "maps":
                await self.bot.say("Please actually search something")
            else:
                uri = "https://www.google.com/maps/search/"
                quary = str(ctx.message.content[len(ctx.prefix + ctx.command.name) + 6:].lower())
                encode = urllib.parse.quote_plus(quary, encoding='utf-8', errors='replace')
                await self.bot.say(uri + encode)
            # End of Maps
        # Start of generic search
        else:
            uri = "https://www.google.com/search?q="
            quary = str(ctx.message.content[len(ctx.prefix + ctx.command.name) + 1:])
            encode = urllib.parse.quote_plus(quary, encoding='utf-8', errors='replace')
            await self.bot.say(uri + encode)
            # End of generic search


def setup(bot):
    n = SimplyGoogle(bot)
    bot.add_cog(n)
