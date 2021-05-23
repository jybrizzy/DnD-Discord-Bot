import discord
from discord.ext import commands
import re
from random import randint


class RollParser:
    def __init__(self, roll_string):
        self.roll_str = roll_string
        self.roll_dict = {}
        self.max_sides = 1000
        self.max_rolls = 10
        self.max_dice = 100

    def die_roller(self, num_of_dice=1, type_of_die=20):
        return [randint(1, int(type_of_die)) for _ in range(int(num_of_dice))]

    def delineater(self):

        # Find Base Roll
        main_die_list = re.findall(r"[^+|^-]\b(\d*[d]\d+)\b", self.roll_str)
        paired_die = [tuple(i.split("d", 1)) for i in main_die_list if i]
        raw_rolls = [self.die_roller(dice, sides) for dice, sides in paired_die]
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
                    mod_dice = [int(dice) for dice in re.findall(r"\d+", mod_tuple[1])]
                    modifier = self.die_roller(mod_dice, int(mod_tuple[2]))

                else:
                    try:
                        modifier = sign * int(mod_tuple[2])
                    except ValueError as verr:
                        print(
                            f"mod_tuple was unable to convert it's contents to a tuple: {verr}"
                        )

            modifier_list.append(modifier)

        # Advantage or Disadvantage on Rolls

        adv_list = ["advantage", "adv", "ad", "a"]
        dis_list = ["disadvantage", "disadv", "disv", "dis", "da"]

        self.roll_dict["advantage"] = any(a in self.roll_str for a in adv_list)
        self.roll_dict["disadvantage"] = any(d in self.roll_str for d in dis_list)

        if self.roll_dict["advantage"] and self.roll_dict["disadvantage"]:
            raise ValueError(
                "You cannot have advantage and disadvantage in the same roll"
            )
        # adv_split_on = filter(lambda adv_item: adv_item in self.roll_str, adv_list)
