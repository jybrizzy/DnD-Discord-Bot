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
    def __init__(self, roll_string: str = None, **kwargs) -> None:
        self.roll_string = roll_string or "1d20"
        self.roll_data = RollData(**kwargs) or RollParser(self.roll_string)
        self.results = RollResults()

    def get_index_to_keep(self, dice_rolls: list) -> list:
        amount2drop = self.roll_data.rolls_to_drop
        indices2keep = sorted(
            range(len(dice_rolls)),
            key=lambda x: dice_rolls[x],
        )[amount2drop:]
        return indices2keep

    def get_dice_rolls(self, dice, sides):
        roll_map = {
            -1: RollMethods.disadvantage,
            0: RollMethods.die_roller,
            1: RollMethods.advantage,
        }

        results = roll_map[self.advantages](dice, sides)
        for acpt, *rjct in results:
            accepted = acpt
            rejected = rjct if rjct else None

        return accepted, rejected

    def calculate_modifier_total(self) -> int:
        mod_values = []
        for modifier in self.roll_data.modifier:
            if isinstance(modifier, Roll):
                die, sides = modifier.die, modifier.sides
                mod_values.extend(RollMethods.die_roller(die, sides))
            elif isinstance(modifier, int):
                mod_values.append(modifier)
        return sum(mod_values)

    def calculate_results(self) -> RollResults:

        die, sides = self.roll_data.main_roll.die, self.roll_data.main_roll.sides
        for _ in range(self.roll_data.multiplier):
            accepted, rejected = self.get_dice_rolls(die, sides)
            ind2k = self.get_index_to_keep(accepted)
            pretotal_item = [accepted[index] for index in ind2k]
            self.results.accepted_rolls.append(accepted)
            self.results.rejected_rolls.append(rejected)
            self.results.pretotal.append(sum(pretotal_item))

        mods = self.calculate_modifier_total()
        self.results.total = [pretot + mods for pretot in self.results.pretotal]

        return self.results


class RollOutput:
    pass
