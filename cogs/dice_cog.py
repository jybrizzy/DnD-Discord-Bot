import asyncio
import discord
from discord.ext import commands

from cogs.utils.dice import RollCalculator
import sys

print(sys.path)


class DiceCog(commands.Cog):
    """Dice related commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=("r", "d20"))
    async def roll_cmd(self, ctx, *, die_string=None):

        roll_results = RollCalculator(die_string)
        roll_string = roll_results.string_constructor(ctx)

        msg = await ctx.send(roll_string)

        repeat = "🔁"  # self.bot.get_emoji(850479576198414366)
        await msg.add_reaction(repeat)

        try:
            await ctx.message.delete()
        except Exception as e:
            print("didn't happen", e)

        while True:
            try:
                CHECK = (
                    lambda reaction, user: user == ctx.author
                    and str(reaction.emoji) == repeat
                    and user != self.bot.user
                    and reaction.message.id == msg.id
                )

                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=CHECK, timeout=60.0
                )

            except asyncio.TimeoutError:
                await msg.clear_reactions()
            else:
                await msg.remove_reaction(reaction, user)
                reroll = roll_results.string_constructor(ctx)
                await ctx.send(reroll)

    @commands.command(
        name="RollAbilities",
        aliases=(
            "roll_abilities",
            "rollabilities",
            "Roll_Abilities",
            "ra",
            "rollStats",
            "roll_stats",
        ),
    )
    async def roll_abilities_cmd(self, ctx):

        roll = {
            "main_roll": Roll(4, 6),
            "multiplier": 6,
            "rolls_to_drop": 3,
        }
        roll_results = RollCalculator(roll_string="Ability Score Rolls", roll_data=roll)
        roll_string = roll_results.string_constructor(ctx)

        await ctx.send(roll_string)

        try:
            await ctx.message.delete()
        except Exception as e:
            print("didn't happen", e)


def setup(bot):
    bot.add_cog(DiceCog(bot))