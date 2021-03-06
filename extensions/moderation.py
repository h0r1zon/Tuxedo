# MODERATION FOR TUXEDO
# (c) ry000001 2017
# This code will *only* work on Tuxedo Discord bot.
# This code is free and open source software. Feel free to leak.
import discord
from discord.ext import commands
from discord import utils as dutils
from utils import switches
import asyncio
import random
import unidecode
import rethinkdb as r
chars = '!#/()=%&'
dehoist_char = '𛲢' # special character, to be used for dehoisting

pingmods_disabled = [110373943822540800]

class Moderation:
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn
        self.mutes = {}

    def get_role(self, guild, id):
        for i in guild.roles:
            if i.id == id: return i
        return None

    @commands.command(aliases=['rb', 'toss'])
    async def roleban(self, ctx, member:discord.Member, *, reason:str=None):
        'Mutes a member. You can specify a reason.'
        g = ctx.guild
        perms = ctx.author.permissions_in(ctx.channel)
        if perms.manage_roles or perms.kick_members or perms.ban_members:
            exists = (lambda: list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
            if not exists:
                return
            # we know the guild has an entry in the settings
            settings = list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            if 'rolebanned_role' not in settings.keys():
                return await ctx.send(f':x: You haven\'t set up a rolebanned role. Please use `{ctx.prefix}set rolebanned_role <role name>`')
            role = self.get_role(ctx.guild, int(settings['rolebanned_role']))
            try:
                meme = self.mutes[member.id][ctx.guild.id]
                if meme != [] and meme != None:
                    return await ctx.send(':x: This member is already rolebanned.')
            except KeyError:
                pass
            self.mutes[member.id] = {}
            self.mutes[member.id][ctx.guild.id] = []
            try:
                for i in member.roles:
                    if i != g.default_role:
                        self.mutes[member.id][ctx.guild.id].append(i)
                        await member.remove_roles(i)
                await member.add_roles(role, reason=f'[{str(ctx.author)}] {reason}' if reason != None else f'[Roleban by {str(ctx.author)}]')
                prevroles = ', '.join([i.name for i in self.mutes[member.id][ctx.guild.id]])
                if prevroles == '': prevroles = 'None'
                await ctx.send(f'**{member.name}**#{member.discriminator} ({member.id}) has been rolebanned.\nPrevious roles: {prevroles}')
            except discord.Forbidden:
                return await ctx.send(':x: I don\'t have permission to do this. Give me Manage Roles or move my role higher.')
        else:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need either Manage Roles, Kick Members or Ban Members.')

    @commands.command(aliases=['urb', 'untoss'])
    async def unroleban(self, ctx, member:discord.Member, *, reason : str=None):
        'Unmutes a member. You can specify a reason.'
        g = ctx.guild
        perms = ctx.author.permissions_in(ctx.channel)
        if perms.manage_roles or perms.kick_members or perms.ban_members:
            exists = (lambda: list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn)) != [])()
            if not exists:
                return
            # we know the guild has an entry in the settings
            settings = list(r.table('settings').filter(
                lambda a: a['guild'] == str(g.id)).run(self.conn))[0]
            if 'rolebanned_role' not in settings.keys():
                return await ctx.send(f':x: You haven\'t set up a rolebanned role. Please use `{ctx.prefix}set rolebanned_role <role name>`')
            role = self.get_role(ctx.guild, int(settings['rolebanned_role']))
            try:
                meme = self.mutes[member.id][ctx.guild.id]
                if meme == None:
                    raise KeyError('is not moot, does not compute')
            except KeyError:
                return await ctx.send(':x: This member wasn\'t rolebanned.')
            try:
                roles = []
                for i in self.mutes[member.id][ctx.guild.id]:
                    if i != g.default_role:
                        roles.append(i)
                        await member.add_roles(i)
                await member.remove_roles(role, reason=f'[{str(ctx.author)}] {reason}' if reason != None else f'[Unroleban by {str(ctx.author)}]')
                prevroles = ', '.join([i.name for i in roles])
                if prevroles == '': prevroles = 'None'
                self.mutes[member.id][ctx.guild.id] = None
                await ctx.send(f'**{member.name}**#{member.discriminator} ({member.id}) has been unrolebanned.\nRoles restored: {prevroles}')
            except discord.Forbidden:
                return await ctx.send(':x: I don\'t have permission to do this. Give me Manage Roles or move my role higher.')
        else:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need either Manage Roles, Kick Members or Ban Members.')

    @commands.command()
    async def ban(self, ctx, member : discord.Member, *, reason : str = None):
        """Bans a member. You can specify a reason."""
        if ctx.author == member:
            return await ctx.send('Don\'t ban yourself, please.')
        if not ctx.author.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Ban Members.')
        if not ctx.me.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Grant the bot Ban Members before doing this.')
        if ctx.author.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: You can\'t ban someone with a higher role than you!')
        if ctx.me.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: I can\'t ban someone with a higher role than me!')
        await ctx.guild.ban(member, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Ban by {str(ctx.author)}', delete_message_days=7)
        msg = await ctx.send(':ok_hand:')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command()
    async def kick(self, ctx, member : discord.Member, *, reason : str = None):
        """Kicks a member. You can specify a reason."""
        if ctx.author == member:
            return await ctx.send('Don\'t kick yourself, please.')
        if not ctx.author.permissions_in(ctx.channel).kick_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Kick Members.')
        if not ctx.me.permissions_in(ctx.channel).kick_members:
            return await ctx.send(':no_entry_sign: Grant the bot Kick Members before doing this.')
        if ctx.author.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: You can\'t kick someone with a higher role than you!')
        if ctx.me.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: I can\'t kick someone with a higher role than me!')
        await ctx.guild.kick(member, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Kick by {str(ctx.author)}')
        msg = await ctx.send(':ok_hand:')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command()
    async def dehoist(self, ctx, member : discord.Member, *, flags : str = None):
        'Remove a hoisting member\'s hoist.'
        if not ctx.author.permissions_in(ctx.channel).manage_nicknames:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Manage Nicknames.')
        if not ctx.me.permissions_in(ctx.channel).manage_nicknames:
            return await ctx.send(':no_entry_sign: Grant the bot Manage Nicknames before doing this.')
        if ctx.author.top_role <= member.top_role or ctx.me.top_role <= member.top_role:
            return await ctx.send(':no_entry_sign: I can\'t dehoist a member with a higher role than you, and you can\'t dehoist someone with a higher role than you.')
        if ctx.author == member:
            return await ctx.send('Nope, can\'t do this.')
        name = member.nick if member.nick else member.name
        if name.startswith(tuple(chars)):
            try:
                await member.edit(nick=f'{dehoist_char}{name}')
            except discord.Forbidden:
                await ctx.send('Oops. I can\'t dehoist this member because my privilege is too low. Move my role higher.')
            else:
                await ctx.send(':ok_hand:')
        else:
            await ctx.send('I couldn\'t dehoist this member. Either they weren\'t hoisting or this character isn\'t supported yet.')

    def cleanformat(self, number):
        string = ""
        if number == 1:
            string = "deleted 1 message"
        if number == 0:
            string = "deleted no messages"
        else:
            string = "deleted {} messages".format(number)
        return "Bot cleanup successful, {} (Method A)".format(string)

    def pruneformat(self, number):
        string = ""
        if number == 1:
            string = "Deleted 1 message"
        if number == 0:
            string = "Deleted no messages"
        else:
            string = "Deleted {} messages".format(number)
        return string

    @commands.command(description="Clean up the bot's messages.")
    async def clean(self, ctx, amount : int=50):
        """Clean up the bot's messages."""
        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            delet = await ctx.channel.purge(limit=amount+1, check=lambda a: a.author == self.bot.user, bulk=True)
            eee = await ctx.send(self.cleanformat(len(delet)))
            await asyncio.sleep(3)
            return await eee.delete()
        else:
            async for i in ctx.channel.history(limit=amount): # bugg-o
                if i.author == self.bot.user:
                    await i.delete()
            
            uwu = await ctx.send("Bot cleanup successful (Method B)")
            await asyncio.sleep(3)
            return await uwu.delete()

    @commands.command(description="Purge messages in the channel.", aliases=["prune"])
    async def purge(self, ctx, amount : int=50, *flags):
        if not ctx.author.permissions_in(ctx.channel).manage_messages:
            return await ctx.send(":x: Not enough permissions.")

        if not ctx.me.permissions_in(ctx.channel).manage_messages:
            return await ctx.send(":x: I don't have enough permissions.")
        
        meme = switches.parse(' '.join(flags))
        bots = (lambda: 'bots' in meme[0].keys())()

        if not bots:
            await ctx.message.delete()

        delet = await ctx.channel.purge(limit=amount, check=lambda a: a.author.bot if bots else True, bulk=True) # why is it bugged  
        eee = await ctx.send(self.pruneformat(len(delet)))
        await asyncio.sleep(3)
        return await eee.delete()

    @commands.command(description="Ban a user, even when not in the server.", aliases=['shadowban', 'hban'])
    async def hackban(self, ctx, user : int, *, reason : str = None):
        'Ban someone, even when not in the server.'
        if not ctx.author.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Not enough permissions. You need Ban Members.')
        if not ctx.me.permissions_in(ctx.channel).ban_members:
            return await ctx.send(':no_entry_sign: Grant the bot Ban Members before doing this.')
        await ctx.bot.http.ban(user, ctx.guild.id, 7, reason=f'[{str(ctx.author)}] {reason}' if reason else f'Hackban by {str(ctx.author)}')
        msg = await ctx.send(':ok_hand:')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(description='Ping an online moderator.', aliases=['pingmod'])
    async def pingmods(self, ctx, *, reason : str = None):
        'Ping an online moderator.'
        if ctx.guild.id in pingmods_disabled:
            return await ctx.send(':x: This feature isn\'t available here.')
        mods = [i for i in ctx.guild.members if (i.permissions_in(ctx.channel).kick_members or i.permissions_in(ctx.channel).ban_members) and
                                                not i.bot and
                                                (i.status == discord.Status.online or i.status == 'online')]
        mod = random.choice(mods)
        reasonless_string = f'Mod Autoping: <@{mod.id}> (by **{ctx.author.name}**#{ctx.author.discriminator})'
        reason_string = f'Mod Autoping:\n**{reason}**\n<@{mod.id}> (by **{ctx.author.name}**#{ctx.author.discriminator})'
        await ctx.send(reason_string if reason != None else reasonless_string)

    @commands.command(description='Decancer a member.')
    async def decancer(self, ctx, member : discord.Member):
        '"Decancer" a member, or strip all the non-ASCII characters from their name. Useful to make your chat look good.'
        if ctx.me.permissions_in(ctx.channel).manage_nicknames and ctx.author.permissions_in(ctx.channel).manage_nicknames:
            cancer = member.display_name
            decancer = unidecode.unidecode_expect_nonascii(cancer)
            try:
                await member.edit(nick=decancer)
                await ctx.send(f'Successfully decancered {cancer} to ​`{decancer}​`.')
            except discord.Forbidden:
                await ctx.send('I couldn\'t decancer this member. Please move my role higher.')
        else:
            cancer = member.display_name
            decancer = unidecode.unidecode_expect_nonascii(cancer)
            await ctx.send(f'The decancered version of {cancer} is ​`{decancer}​`.')
        
def setup(bot):
    bot.add_cog(Moderation(bot))