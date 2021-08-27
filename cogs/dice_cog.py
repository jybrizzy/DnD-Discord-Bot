import asyncio
import discord
from discord.ext import commands
from cogs.utils.roll_parser import Roll, RollParser
from cogs.utils.roll_calculator import RollResultIterator
from cogs.utils.roll_output import RollOutput


class DiceCog(commands.Cog):
    """Dice related commands"""

    def __init__(self, bot):
        self.bot = bot

    async def roll_pipeline(self, ctx, roll_data, roll_string=None):
        roll_results = iter(RollResultIterator(roll_data))
        roll_output = RollOutput(roll_data, roll_results, roll_string)
        await roll_output.main_roll_result(ctx)

    @commands.command(name="roll", aliases=("r", "d20", "1d20", "Roll", "ROLL"))
    async def roll_cmd(self, ctx, *, die_string=None):

        roll_data = RollParser(die_string)
        roll_string = self.roll_pipeline(ctx, roll_data)
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
                reroll_str = self.roll_pipeline(ctx, roll_data)
                await ctx.send(reroll_str)

    @commands.command(
        name="RollAbilities",
        aliases=(
            "roll_abilities",
            "rollabilities",
            "Roll_Abilities",
            "ra",
            "rollStats",
            "RollStats",
            "roll_stats",
        ),
    )
    async def roll_abilities_cmd(self, ctx):

        roll = {
            "main_roll": Roll(4, 6),
            "multiplier": 6,
            "rolls_to_drop": 1,
        }

        roll_data = RollParser(**roll)
        roll_string = self.roll_pipeline(
            ctx, roll_data, roll_string="Ability Score Rolls"
        )

        await ctx.send(roll_string)

        try:
            await ctx.message.delete()
        except Exception as e:
            print("Didn't delete message.", e)


def setup(bot):
    bot.add_cog(DiceCog(bot))
