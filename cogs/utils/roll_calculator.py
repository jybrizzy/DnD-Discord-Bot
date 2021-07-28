import asyncio
import itertools
import re
from random import randint
from collections import namedtuple
import sys

from cogs.utils.roll_parser import Roll, RollData, RollParser
from cogs.utils.roll_methods import RollMethods


class RollResults:
    def __init__(self):
        self.accepted_rolls = list().copy()
        self.rejected_rolls = list().copy()
        self.pretotal = list().copy()
        self.total = None


class RollCalculator:
    def __init__(self, roll_string=None, **kwargs):
        self.roll_string = roll_string or "1d20"
        self.roll_data = RollData(**kwargs) or RollParser(self.roll_string)
        self.results = RollResults()

    def drop_lowest_index(self, dice_rolls):
        amount2drop = self.roll_data.rolls_to_drop
        indices2keep = sorted(
            range(len(dice_rolls)),
            key=lambda x: dice_rolls[x],
        )[amount2drop:]
        return indices2keep

    def roll_die(self, dice, sides):
        if self.roll_data.advantages[0]:
            accepted, rejected = RollMethods.advantage(dice, sides)

        elif self.roll_data.advantages[1]:
            accepted, rejected = RollMethods.disadvantage(dice, sides)

        else:
            accepted = RollMethods.die_roller(dice, sides)
            rejected = None

        return accepted, rejected

    def calculate_modifier_total(self):
        mod_values = []
        for modifier in self.roll_data.modifier:
            if isinstance(modifier, Roll):
                die, sides = modifier.die, modifier.sides
                mod_values.extend(RollMethods.die_roller(die, sides))
            elif isinstance(modifier, int):
                mod_values.append(modifier)
        return sum(mod_values)

    def calculate_results(self):

        die, sides = self.roll_data.main_roll.die, self.roll_data.main_roll.sides
        for _ in range(self.roll_data.multiplier):
            accepted, rejected = self.roll_die(die, sides)
            ind2k = self.drop_lowest_index(accepted)
            pretotal_item = [accepted[index] for index in ind2k]
            self.results.accepted_rolls.append(accepted)
            self.results.rejected_rolls.append(rejected)
            self.results.pretotal.append(sum(pretotal_item))

        mods = self.calculate_modifier_total()

        self.results.total = [pretot + mods for pretot in self.results.pretotal]

        return self.results