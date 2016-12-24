# Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
# Essentials
import os


class Antispam:
    """Advanced anti-spam controls"""

    reactions = ['off', 'remove', 'warning', 'kick', 'ban']

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
            # Threat for increasing a users Threat level on the Threat cog (Not
            # developed as of yet)
            escalations = {
                'remove': {},
                'warning': {'remove': 1},
                'kick': {'warning': 2},
                'ban': {'warning': 3, 'kick': 3}
            }
            # Escalations indicate the number of other reactions required to actually react with the
            # current action's state; any one of the prior reactions is enough to proceed, so given:
            # {'ban': {'warning': 3, 'kick': 3}}
            # either 3 warnings or 3 kicks will result in a ban.  All reactions are checked, even if
            # the escalation condition is already satisfied, to ensure all the expected reactions
            # take place.  Given the default settings of:
            # {
            #     'remove': {},
            #     'warning': {'remove': 1},
            #     'kick': {'warning': 2},
            #     'ban': {'warning': 3, 'kick': 3}
            # }
            # an action state of 'ban', and no prior infractions recorded for the given user:
            # check 'ban'
            #   need 3 'warning' or 3 'kick'
            #   check 'warning'
            #       need 1 'remove'
            #       check 'remove'
            #           nothing needed
            #           requirements met
            #           fire 'remove' (remove == 1)
            #       requirements met
            #       fire 'warning' (warning == 1)
            #   check 'kick'
            #       need 2 'warning'
            #       check already run
            #       requirements not met
            #       fire nothing ('kick' == 0)
            #   requirements not met
            #   fire nothing ('ban' == 0)
            # This ensures users can fire lesser reactions at the same time as the one set
            # for a given action.
            self.settings[server.id] = {'actions': actions, 'escalations': escalations, 'message': {
                'massmention': 'You have mentioned too many users in a single message.',
                'repeatmessage': 'You have sent the same message too many times.',
                'slowmode': 'You are sending messages too quickly.',
                'blockinvites': 'You cannot send Discord invites on this server.',
                'blocklinks': 'You cannot send that link on this server.'
            }}
            self.save_json()
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @antispamset.command(pass_context=True, no_pm=True)
    async def reaction(self, ctx, action, reaction):
        """Set the reaction of an action.

        The `action` can be one of the following:
        massmention, repeatmessage, slowmode, blockinvites, blocklinks

        The `reaction` can be one of the following:
        off, remove, warning, kick, ban"""
        server = ctx.message.server
        if action.lower() not in self.settings[server.id]['actions']:
            await self.bot.say('This action doesn\'t exist. Please see the help for accepted actions')
        elif reaction.lower() not in self.reactions:
            await self.bot.say('This reaction doesn\'t exist. Please see the help for accepted reactions')
        else:
            action = action.lower()
            reaction = reaction.lower()
            if reaction == 'off':
                reaction = False
            self.settings[server.id]['actions'][action]['state'] = reaction
            self.save_json()
            await self.bot.say('{} is now set to {}'.format(action, reaction))

    @antispamset.command(pass_context=True, no_pm=True)
    async def escalation(self, ctx, reaction, prereq, amount):
        """Set an escalation for a reaction.

        Both `reaction` and `prereq` are any valid reaction besides 'off':
        remove, warning, kick, ban

        `amount` is a positive integer, or 0 to remove the `prereq`

        When an action triggers `reaction`, trigger `prereq`, and only fire
        `reaction` if `prereq` has been fired at least `amount` times,
        counting this one. When multiple prereqs are set, all of them are
        triggered, but only one must reach `amount` to fire `reaction`"""
        server = ctx.message.server
        if reaction.lower() not in [react for react in self.reactions if react != 'off']:
            await self.bot.say('This reaction doesn\'t exist. Please see the help for accepted reactions')
        elif prereq.lower() not in [react for react in self.reactions if react != 'off']:
            await self.bot.say('This prereq doesn\'t exist. Please see the help for accepted reactions')
        # Basically the same as /[0-9]+/, but faster; ensures only digits 0-9
        elif not '{}'.format(amount).isdigit():
            await self.bot.say('The amount needs to be an integer >= 0. Please see the help.')
        else:
            reaction = reaction.lower()
            prereq = prereq.lower()
            if amount == 0:
                if prereq in self.settings[server.id]['escalations'][reaction]:
                    del self.settings[server.id]['escalations'][reaction][prereq]
            else:
                self.settings[server.id]['escalations'][reaction][prereq] = amount
            self.save_json()
            await self.bot.say('{} now requires {} {} to fire'.format(reaction, amount, prereq))

    async def _fire(self, ctx, action, reaction):
        server = ctx.message.server
        user = ctx.message.author
        tracking = dataIO.load_json('data/antispam/tracking-{}.json'.format(server.id))
        fires = self._trigger(self, ctx, tracking, reaction, [])
        if fires:
            asyncio.sleep(0.5)
            if 'remove' in fires:
                await self.bot.delete_message(ctx.message)
                tracking[user.id]['remove'] += 1
            if 'warning' in fires:
                await self.bot.send_message(user, self.settings[server.id]['message'][action])
                tracking[user.id]['warning'] += 1
            if 'kick' in fires:
                # Kick the user
                tracking[user.id]['kick'] += 1
            if 'ban' in fires:
                # Ban the user
                tracking[user.id]['ban'] += 1
            dataIO.save_json('data/antispam/tracking-{}.json'.format(server.id), tracking)

    async def _trigger(self, ctx, tracking, reaction, fires):
        server = ctx.message.server
        user = ctx.message.author
        if self.settings[server.id]['escalations'][reaction]:
            for prereq, amount in self.settings[server.id]['escalations'][reaction]:
                fires = self._trigger(self, ctx, tracking, prereq, fires)
                prefired = tracking[user.id][prereq] + (1 if prereq in fires else 0)
                if prefired >= amount:
                    fires.append(reaction)
        else:
            fires.append(reaction)
        return fires

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
