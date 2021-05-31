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

        self.roll_str = self.roll_str.lower().strip()
            
        # Check for & parse parentheses and multiplier
        paren_check = re.findall(
            r"([0-9]{1,3})?\s*\*?\s*\((.*?)\)\s*\*?\s*([0-9]{1,3})?", self.roll_str
        ) 
        paren_check = list(itertools.chain(*paren_check)) #Removes tuple inside list
        if not paren_check[1]:
            raise ValueError("No dice string to parse!")
        elif paren_check[0] and paren_check[-1]:
            raise ValueError("You cannot have more than 1 multiplier")
        elif paren_check[0] or paren_check[-1]:
            multiplier_list = paren_check[::2]
            multiplier = int(list(filter(None, multiplier_list))[0])
            if yonot multiplier:
                raise ValueError('Invalid multiplier formatting')
            elif multiplier == 0:
                raise ValueError('Cannot have *0')
            else:
                self.roll["multiplier"] = multiplier
            self.roll_str = paren_check[1]
        else:
            self.roll_str = paren_check[1]

        

        # Find Base Roll
        main_die_list = re.findall(
            r"[^+|^-]\b(\d*[d]\d+)\b", self.roll_str
        )  
        if len(main_die_list) > self.max_rolls:
            raise ValueError("List is too long")
        raw_die_numbers = [
            tuple(die.split("d", 1)) for die in main_die_list
        ]  # ->[('',6),]
        main_die_tuples = []
        for dice, sides in raw_die_numbers:
            if not dice:
                dice = 1
            elif not sides:
                sides = 20
            elif (dice >= self.max_dice) and (sides >= self.max_sides):
                dice = self.max_dice
                sides = self.max_sides
                raise ValueError('Too many rolls/sides')
            elif (dice >= self.max_dice):
                dice = self.max_dice
            elif (sides >= self.max_sides):
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
                        modifier = RollCalculator().die_roller(
                            mod_dice, int(mod_tuple[2])
                        )
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
        advantage = re.findall('\s*(?<!dis)(advantage|advan|ad|a)\s*', self.roll_str, flags=re.IGNORECASE)
        disadvantage = re.findall('\s*(disadvantage|disadv|disv|dis|da)\s*', self.roll_str, flags=re.IGNORECASE)
        
        self.roll["advantage"] = any(advantage)
        self.roll['disadvantage'] = any(disadvantage)

        if self.roll["advantage"] and self.roll_dict["disadvantage"]:
            raise ValueError(
                "You cannot have advantage and disadvantage in the same roll"
            )

        elif len(disadvantage) > len(self.roll["main_roll"]) < len(advantage):
            raise ValueError("You cannot have more advantage/disadvantages than you have rolls")

        self.roll["main_roll"] = self.roll.get("main_roll", [(1, 20)])
        self.roll["modifier"] = self.roll.get("modifier", [0])
        self.roll["advantage"] = self.roll.get("advantage", False)
        self.roll["disadvantage"] = self.roll.get("disadvantage", False)
        self.roll["multiplier"] = self.roll.get("multiplier", 1)
        # adv_split_on = filter(lambda adv_item: adv_item in self.roll_str, adv_list)

        return self.roll


class RollCalculator:
    def __init__(self, roll_results=None):
        self.roll_string = roll_string
        if roll_results is None:
            self.roll_results = dict()
        else:
            self.roll_results = roll_results
        self.roll_data = None

    
    def die_roller(self, num_of_dice, type_of_die):
        return [randint(1, int(type_of_die)) for _ in range(int(num_of_dice))]

    def advantage(self,):
        [max(*rolls) for rolls in zip(roll1, roll2)]
    
    def disadvantage(self):
        [min(*rolls) for rolls in zip(roll1, roll2)]

    @property
    def get_roll_values(self, roll_string):
        self.roll_data = RollParser(roll_string).delineater
        return self.roll_data

    def calculate_results(self):

        if not self.roll_data:
            raise ValueError("Something went wrong in the parsing")
        else:
            if self.roll_data['advantage'] != 1:

            if self.roll_data['advantage'] or self.roll_data['disadvantage']:
                for dice, sides in self.roll_data['main roll']:
                
            for key, datum in self.self_roll_data.items():
                if key == 'main_roll':
                    for dice, sides in datum:
                        outcome = self.die_roller(dice,sides)


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