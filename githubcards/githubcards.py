# Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
# Essentials
import aiohttp
from fnmatch import fnmatch
import os


class GithubCards:
    """Embed GitHub issues and pull requests with a simple to use system!"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/githubcards/settings.json')

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(Administrator=True)
    async def githubcards(self, ctx):
        """Manage GitHub Cards"""
        server = ctx.message.server
        if server.id not in self.settings:
            self.settings[server.id] = {}
            self.save_json()
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @githubcards.command(pass_context=True, no_pm=True)
    async def add(self, ctx, prefix, github):
        """Add a new GitHub repo with the given prefix.

        Format for adding a new GitHub repo is \"Username/Repository\""""
        server = ctx.message.server
        prefix = prefix.lower()  # I'm Lazy okay :(
        if prefix in self.settings[server.id]:
            await self.bot.say('This prefix already exists in this server. Please use something else.')
        elif len(github.split('/')) != 2:
            await self.bot.say('Invalid format. Please use Username/Repository')
        else:
            # Confirm the User/Repo exits, We don't want to try and pull from a non existant repo
            async with aiohttp.get('https://api.github.com/repos/{}'.format(github)) as response:
                if response.status == 404:
                    await self.bot.say('The repository cannot be found.\nMake sure its a public repository.')
                else:
                    fields = {
                        'author': True,
                        'status': True,
                        'comments': True,
                        'description': True,
                        'mergestatus': True,
                        'labels': True,
                        'closedby': False,
                        'locked': False,
                        'assigned': False,
                        'createdat': False,
                        'milestone': False
                    }
                    self.settings[server.id][prefix] = {'gh': github, 'fields': fields}
                    self.save_json()
                    await self.bot.say('All done, you can now use "{}#issue number" to gather information of an issue\nOr use "githubcards edit"'.format(prefix))

    @githubcards.command(pass_context=True, no_pm=True)
    async def edit(self, ctx, prefix, field=None):
        """Edit the fields that show up on the embed.

        To see what fields are currently enabled use "githubcards edit <prefix>"
        The following options are valid:
        author, assigned, closedby, comments, createdat, description, labels, locked, mergestatus, milestone, status"""
        fieldlist = ['author', 'assigned', 'closedby', 'comments', 'createdat', 'description', 'labels', 'locked' 'mergestatus', 'milestone', 'status']
        if prefix not in self.settings[ctx.message.server.id]:
            await self.bot.say('This GitHub prefix doesn\'t exist.')
        elif field is None:
            templist = []
            for field, fset in self.settings[ctx.message.server.id][prefix]['fields'].items():
                if fset is True:
                    templist.append('{}: Enabled'.format(field.title()))
                else:
                    templist.append('{}: Disabled'.format(field.title()))
            await self.bot.say('```Fields for {}:\n{}```'.format(prefix, '\n'.join(sorted(templist))))
        elif field.lower() in fieldlist:
            if self.settings[ctx.message.server.id][prefix]['fields'][field.lower()] is True:
                self.settings[ctx.message.server.id][prefix]['fields'][field.lower()] = False
                self.save_json()
                await self.bot.say('{} is now disabled.'.format(field.title()))
            else:
                self.settings[ctx.message.server.id][prefix]['fields'][field.lower()] = True
                self.save_json()
                await self.bot.say('{} is now enabled.'.format(field.title()))
        else:
            await self.bot.say('The field is not valid, please use one of the following \n\n{}'.format(', '.join(fieldlist)))

    @githubcards.command(pass_context=True, no_pm=True)
    async def remove(self, ctx, prefix):
        """Remove a GitHub prefix"""
        if prefix.lower() in self.settings[ctx.message.server.id]:
            del self.settings[ctx.message.server.id][prefix.lower]
            self.save_json()
            await self.bot.say('Done, ~~it was about time.~~ This GitHub Prefix is now deleted.')
        else:
            await self.bot.say('This GitHub prefix doesn\'t exist.')

    async def get_issue(self, message):
        if message.server.id in self.settings and message.author.bot is False:
            for word in message.content.split(' '):
                for prefix in self.settings[message.server.id]:
                    if fnmatch(word.lower(), '{}#*'.format(prefix)):
                        split = word.split('#')
                        if split[1] is None:
                            break
                        api = 'https://api.github.com/repos/{}/issues/{}'.format(self.settings[message.server.id][prefix]['gh'], split[1])
                        async with aiohttp.get(api) as r:
                            if r.status != 404:
                                break
                            result = await r.json()
                            if self.settings[message.server.id][prefix]['fields']['description'] is True:
                                description = result['body']
                                embed_description = (description[:100] + '...') if len(description) > 100 else description
                                embed = discord.Embed(title='{} #{}'.format(result['title'], result['number']), description=embed_description, url=result['html_url'])
                            else:
                                embed = discord.Embed(title='{} #{}'.format(result['title'], result['number'], url=result['html_url']))
                            embed.add_field()
                            await self.bot.send_message(message.channel, embed=embed)

    def save_json(self):
        dataIO.save_json("data/githubcards/settings.json", self.settings)


def check_folder():
    f = 'data/githubcards'
    if not os.path.exists(f):
        os.makedirs(f)


def check_file():
    f = 'data/githubcards/settings.json'
    if dataIO.is_valid_json(f) is False:
        dataIO.save_json(f, {})


def setup(bot):
    check_folder()
    check_file()
    n = GithubCards(bot)
    bot.add_listener(n.get_issue, 'on_message')
    bot.add_cog(n)
