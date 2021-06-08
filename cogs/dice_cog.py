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

        """
        # Check for & parse parentheses and multiplier
        paren_check = re.findall(
            r"([0-9]{1,3})?\s*\*?\s*\((.*?)\)\s*\*?\s*([0-9]{1,3})?", self.roll_str
        )
        paren_check = list(itertools.chain(*paren_check))  # Removes tuple inside list
        if not paren_check[1]:
            raise ValueError("No dice string to parse!")
        elif paren_check[0] and paren_check[-1]:
            raise ValueError("You cannot have more than 1 multiplier")
        elif paren_check[0] or paren_check[-1]:
            multiplier_list = paren_check[::2]
            multiplier = int(list(filter(None, multiplier_list))[0])
            if not multiplier:
                raise ValueError("Invalid multiplier formatting")
            elif multiplier == 0:
                raise ValueError("Cannot have *0")
            else:
                self.roll["multiplier"] = multiplier
            self.roll_str = paren_check[1]
        else:
            self.roll_str = paren_check[1]
        """
        # Find Base Roll
        main_die_list = re.findall(r"(?<!\+|-)(\d*[d]\d+)", self.roll_str)
        if len(main_die_list) > self.max_rolls:
            raise ValueError("List is too long")
        raw_die_numbers = [
            tuple(die.split("d", 1)) for die in main_die_list
        ]  # ->[('',6),]
        main_die_tuples = []
        for dice, sides in raw_die_numbers:
            dice, sides = int(dice), int(sides)
            if not dice:
                dice = 1
            elif not sides:
                sides = 20
            elif (dice >= self.max_dice) and (sides >= self.max_sides):
                dice = self.max_dice
                sides = self.max_sides
                raise ValueError("Too many rolls/sides")
            elif dice >= self.max_dice:
                dice = self.max_dice
            elif sides >= self.max_sides:
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
        raw_modifier = re.findall(r"([\+-])\s*(\d*[d])?\s*(\d+)", self.roll_str)
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
                            mod_dice[0], int(mod_tuple[2])
                        )[0]
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

        self.roll["modifier"] = modifier_list
        # Advantage or Disadvantage on Rolls
        advantage = re.findall(
            r"\s*(?<!dis)(advantage|advan|ad|a)\s*", self.roll_str, flags=re.IGNORECASE
        )
        disadvantage = re.findall(
            r"\s*(disadvantage|disadv|disv|dis|da)\s*",
            self.roll_str,
            flags=re.IGNORECASE,
        )

        self.roll["advantage"] = any(advantage)
        self.roll["disadvantage"] = any(disadvantage)

        if self.roll["advantage"] and self.roll["disadvantage"]:
            raise ValueError(
                "You cannot have advantage and disadvantage in the same roll"
            )

        elif len(disadvantage) > len(self.roll["main_roll"]) < len(advantage):
            raise ValueError(
                "You cannot have more advantage/disadvantages than you have rolls"
            )

        self.roll["main_roll"] = self.roll.get("main_roll", [(1, 20)])
        self.roll["modifier"] = self.roll.get("modifier", [0])
        self.roll["advantage"] = self.roll.get("advantage", False)
        self.roll["disadvantage"] = self.roll.get("disadvantage", False)
        self.roll["multiplier"] = self.roll.get("multiplier", 1)
        # adv_split_on = filter(lambda adv_item: adv_item in self.roll_str, adv_list)

        return self.roll


class RollCalculator:
    def __init__(self, roll_string=None, roll_results=None):
        if roll_string is None:
            self.roll_string = "1d20"
        else:
            self.roll_string = roll_string.strip()
        if roll_results is None:
            self.roll_results = dict()
        else:
            self.roll_results = roll_results
        self.roll_data = None

    def die_roller(self, num_of_dice, type_of_die):
        return [randint(1, int(type_of_die)) for _ in range(int(num_of_dice))]

    def advantage(self, num_of_dice, type_of_die):
        roll1, roll2 = self.die_roller(num_of_dice, type_of_die), self.die_roller(
            num_of_dice, type_of_die
        )
        return [(max(*rolls), min(*rolls)) for rolls in zip(roll1, roll2)]

    def disadvantage(self, num_of_dice, type_of_die):
        roll1, roll2 = self.die_roller(num_of_dice, type_of_die), self.die_roller(
            num_of_dice, type_of_die
        )
        return [(min(*rolls), max(*rolls)) for rolls in zip(roll1, roll2)]

    def get_rolls(self, roll_string):
        self.roll_data = RollParser(roll_string).delineater
        return self.roll_data

    @property
    def calculate_results(self):

        res_list = []

        for _ in range(self.roll_data["multiplier"]):
            for dice, sides in self.roll_data["main_roll"]:
                if self.roll_data["advantage"]:
                    res_tup = self.advantage(dice, sides)
                    # res_tup, rej_tup = zip(*adv_list)
                elif self.roll_data["disadvantage"]:
                    res_tup = self.disadvantage(dice, sides)
                    # res_tup, rej_tup = zip(*dis_list)
                else:
                    res_tup = (self.die_roller(dice, sides), None)
                    # rej_list = ()

                res_list.append(res_tup)
                # rej_list.append(rej_tup)

        mods = sum(self.roll_data["modifier"])

        self.roll_results["Results_Rejects"] = res_list
        # self.roll_results['Rejects'] = rej_list
        self.roll_results["Pretotal"] = [sum(result[0]) for result in res_list][0]
        self.roll_results["Total"] = self.roll_results["Pretotal"] + mods

        return self.roll_results

    def string_constructor(self, ctx):
        _ = self.get_rolls(self.roll_string)
        _ = self.calculate_results
        if self.roll_data["multiplier"] == 1:
            dice_rolls = list(
                itertools.chain(*self.roll_results["Results_Rejects"])
            )  # [((1,5,10), (1,4,6))] -> [(1,5,10), (1,4,6)]
            stringified_rolls = []
            for res_rej in dice_rolls:
                if res_rej is not None:
                    stringified_roll = ", ".join(str(roll) for roll in res_rej)
                stringified_rolls.append(stringified_roll)
            d20s_condition = any(
                [roll for roll in self.roll_data["main_roll"] if roll[1] == 20]
            )
            if d20s_condition:
                if 1 in dice_rolls:
                    crit_fail = True
                else:
                    crit_fail = False
                if 20 in dice_rolls:
                    crit_sucess = True
                else:
                    crit_sucess = False

                crits_n_fails = re.compile(r"\b(20|1)\b")
                stringified_rolls[0] = crits_n_fails.sub(
                    r"**\1**", stringified_rolls[0]
                )
            else:
                crit_fail, crit_sucess = False, False

            pretotal = self.roll_results.get("Pretotal", 0)
            total = self.roll_results["Total"]
            # custom emoji
            posted_text = (
                f"{ctx.author.mention} <:d20:849391713336426556>\n"
                f"{self.roll_string}: [ {stringified_rolls[0]} ]\n"
                f"**Total**: {total}\n"
            )

            if self.roll_data["advantage"]:
                posted_text += (
                    f"Rolled with Advantage\n"
                    f"_Rejected Rolls_: [{stringified_rolls[1]}]\n"
                )
            elif self.roll_data["disadvantage"]:
                posted_text += (
                    f"Rolled with Disadvantage\n"
                    f"_Rejected Rolls_: [{stringified_rolls[1]}]\n"
                )
            else:
                pass
            if d20s_condition and crit_fail and crit_sucess:
                posted_text += (
                    f"Wow! You got a Critical Success and a Critical Failure!\n"
                )
            elif d20s_condition and crit_fail:
                posted_text += f"**Critical Failure**! Await your fate!\n"
            elif d20s_condition and crit_sucess:
                posted_text += f"**Critical Success**! Roll again!\n"
            else:
                pass

        else:
            pass
            # for roll_result in self.roll_results['Results_Rejects']:

        return posted_text


class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=("r",))
    async def roll_cmd(self, ctx, *, die_string=None):

        roll_results = RollCalculator(die_string)
        roll_string = roll_results.string_constructor(ctx)

        try:
            await ctx.message.delete()
        except discord.HTTPException:
            print("didn't happen")
        msg = await ctx.send(roll_string)
        repeat = "🔁"  # self.bot.get_emoji(850479576198414366)

        await msg.add_reaction(repeat)

        while True:
            try:
                CHECK = (
                    lambda reaction, user: user == ctx.author
                    and str(reaction.emoji) == repeat
                )
                reaction, user = await self.bot.wait_for(
                    "reaction", check=CHECK, timeout=60.0
                )
                if reaction == repeat:
                    roll_results = RollCalculator(die_string)
                    roll_string = roll_results.string_constructor(ctx)
                    await ctx.send(roll_string)

            except asyncio.TimeoutError:
                await msg.clear_reactions()


def setup(bot):
    bot.add_cog(DiceCog(bot))