import discord
from discord.ext import commands


class GM_Role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def givethGMrole(self, ctx, game_master: discord.Member):
        await ctx.send(f"Show me what you got, {game_master}!")
        # guild = ctx.guild
        # await guild.create_role(name="role name")
        # user = ctx.message.author
        # await user.add_roles(role)
        game_master_role = discord.utils.get(ctx.guild.roles, name="Game Master")
        await game_master.add_roles(game_master_role)

    @commands.command()
    async def takethGMrole(self, ctx, game_master: discord.Member):
        await ctx.send(f"Get outta der, {game_master}!")
        noGMrole = discord.utils.get(ctx.guild.roles, name="Game Master")
        await game_master.remove_roles(noGMrole)


def setup(bot):
    bot.add_cog(GM_Role(bot))