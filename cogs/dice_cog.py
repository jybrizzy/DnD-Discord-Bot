import asyncio
import discord
from discord.ext import commands
import itertools
import re
from random import randint


class RollParser:

    max_dice = 100
    max_sides = 1000
    max_multiplier = 10
    max_rolls = 10

    def __init__(self, roll_string, roll=None):
        self.roll_str = roll_string
        if roll is None:
            self.roll = {}
        else:
            self.roll = roll

    @property
    def delineater(self):

        # Check for & parse parentheses and multiplier
        paren_check = re.findall(
            r"([0-9]{1,3})?\s*\*?\s*\((.*?)\)\s*\*?\s*([0-9]{1,3})?", self.roll_str
        )
        paren_check = list(itertools.chain(*paren_check))
        self.roll_str = paren_check[1]
        if not self.roll_str:
            raise ValueError("No dice string to parse!")
        elif paren_check[0] and paren_check[-1]:
            raise ValueError("You cannot have more than 1 multiplier")

        # Find Base Roll
        main_die_list = re.findall(
            r"[^+|^-]\b(\d*[d]\d+)\b", self.roll_str
        )  # [a-c]{1, 100} <--this will allow any characters a through c to have a length of 1 to 100, so like "ccccccc" would be valid
        if len(main_die_list) > self.max_rolls:
            raise ValueError("List is too long")
        raw_die_numbers = [
            tuple(die.split("d", 1)) for die in main_die_list
        ]  # ->[('',6),]
        main_die_tuples = []
        for dice, sides in raw_die_numbers:
            if (not dice) or (not sides):
                dice = 1
                sides = 20
            elif (dice >= self.max_dice) or (sides >= self.max_sides):
                dice = self.max_dice
                sides = self.max_sides
            else:
                dice, sides = int(dice), int(sides)

            main_die_tuples.append((dice, sides))
        self.roll["main_roll"] = main_die_tuples

        # turn to integers
        # raw_rolls = [self.die_roller(dice, sides) for dice, sides in paired_die]
        # pretotals = [sum(x) for x in rolls_raw]

        # Find Modifiers
        # if there is +- signs but list is otherwise empty raise error
        raw_modifier = re.findall(r"([+|-])(\d*[d])?(\d+)", self.roll_str)
        modifier_list = []
        for mod_tuple in raw_modifier:
            if not mod_tuple[0]:
                modifier = 0
            else:
                sign = mod_tuple[0].strip()  # +/- sign
                sign = 1 if sign == "+" else -1 if sign == "-" else None

                if mod_tuple[1]:

                    mod_dice = [
                        int(dice) if dice else 1
                        for dice in re.findall(r"\d+", mod_tuple[1])
                    ]
                    try:
                        modifier = RollCalculator.die_roller(mod_dice, int(mod_tuple[2]))
                    except:
                        raise ValueError("Must assign # of sides to mod die")

                else:
                    try:
                        modifier = sign * int(mod_tuple[2])
                    except ValueError as verr:
                        print(
                            f"modifer was unable to parse modification string: {verr}"
                        )

            modifier_list.append(modifier)

        # Advantage or Disadvantage on Rolls

        adv_list = ["advantage", "adv", "ad", "a"]
        dis_list = ["disadvantage", "disadv", "disv", "dis", "da"]

        self.roll["advantage"] = any(a in self.roll_str for a in adv_list)
        self.roll["disadvantage"] = any(d in self.roll_str for d in dis_list)

        if self.roll["advantage"] and self.roll_dict["disadvantage"]:
            raise ValueError(
                "You cannot have advantage and disadvantage in the same roll"
            )

        self.roll["main_roll"] = self.roll.get("main_roll", [(1, 20)])
        self.roll["modifier"] = self.roll.get("modifier", [0])
        self.roll["advantage"] = self.roll.get("advantage", False)
        self.roll["disadvantage"] = self.roll.get("disadvantage", False)
        # adv_split_on = filter(lambda adv_item: adv_item in self.roll_str, adv_list)

        return self.roll


class RollCalculator:
    def __init__(self, roll_results=None):
        self.roll_string = roll_string
        if roll_results is None:
            self.roll_results = dict()
        else:
            self.roll_results = roll_results
        self.roll = None

    @staticmethod
    def die_roller(num_of_dice, type_of_die):
        return [randint(1, int(type_of_die)) for _ in range(int(num_of_dice))]

    
    def get_roll_values(self):
    @classmethod
    def from_string(cls, emp_str):
        first, last, pay = emp_str.split('-')
        return cls(first, last, pay)
        

class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=("r"))
    async def roll_cmd(self, ctx, *, die_string=None):

        roll_results = RollCalculator.die_results()

        roller = ctx.message.author.name
        msg = await ctx.send(string_value)

        await msg.add_reaction(":repeat:")

        while True:
            try:
                CHECK = (
                    lambda reaction, user: user == ctx.author
                    and str(reaction.emoji) == ":repeat:"
                )
                reaction, user = await self.bot.wait_for(
                    "reaction", check=CHECK, timeout=60.0
                )

            except asyncio.TimeoutError:
                await msg.clear_reactions()

            else:
                if reaction == ":repeat":
                    await self.roll_cmd()


def setup(bot):
    bot.add_cog(DiceCog(bot))