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
        self.accepted = list().copy()
        self.rejected = list().copy()
        self.pretotal = list().copy()
        self.total = list().copy()


class RollCalculator:
    def __init__(self, roll_data) -> None:
        self.roll_data = roll_data
        self.results = RollResults()

    def set_index_to_keep(self, dice_rolls: list[int]) -> list[int]:
        amount2drop = self.roll_data.rolls_to_drop
        indices2keep = sorted(
            range(len(dice_rolls)),
            key=lambda x: dice_rolls[x],
        )[amount2drop:]
        return indices2keep

    def set_dice_rolls(self, dice: int, sides: int) -> tuple[list[int], list[int]]:
        roll_map = {
            -1: RollMethods.disadvantage,
            0: RollMethods.die_roller,
            1: RollMethods.advantage,
        }

        accepted, *rejected = roll_map[self.roll_data.advantages](dice, sides)
        rejected = rejected[0] if rejected else None
        self.results.accepted = accepted
        self.results.rejected = rejected

    """
    def set_list_dice_rolls(self):
        die, sides = self.roll_data.main_roll.die, self.roll_data.main_roll.sides
        results_list = [
            self.set_dice_rolls(die, sides) for _ in range(self.roll_data.multiplier)
        ]
        accepted_list, rejected_list = list(zip(*results_list))
        self.results.accepted_rolls = accepted_list
        self.results.rejected_rolls = rejected_list
    """

    def set_pretotal(self) -> None:
        ind2k = self.set_index_to_keep(self.results.accepted)
        self.results.pretotal = sum([self.results.accepted[index] for index in ind2k])

    def set_modifier_total(self, modifiers: list) -> int:
        # static method?
        mod_values = []
        for modifier in modifiers:
            if isinstance(modifier, Roll):
                die, sides = modifier.die, modifier.sides
                mod_values.extend(RollMethods.die_roller(die, sides))
            elif isinstance(modifier, int):
                mod_values.append(modifier)
        return sum(mod_values)

    def set_total(self) -> None:
        mods = self.set_modifier_total(self.roll_data.modifier)
        self.results.total = self.results.pretotal + mods


class RollOutput:
    def __init__(self, roll_string: str = None, **kwargs):
        self.roll_string = roll_string or "1d20"
        self.roll_data = RollData(**kwargs) or RollParser(self.roll_string)
        self.rc = RollCalculator(self.roll_data)
        self.results = self.rc.results

    def initialize_results(self):
        self.rc.set_dice_rolls()
        self.rc.set_pretotal()
        self.rc.set_total()

    def string_constructor(self, ctx):
        posted_text = (
            f"{ctx.author.mention} <:d20:849391713336426556>\n" f"{self.roll_string} "
        )
        for iteration, roll in enumerate(accepted):
            if len(accepted) == 1:
                posted_text += f": [ {roll} ]\n"
                if self.roll_data.modifier:
                    posted_text += f"**Pretotal**: {pretotal}\n"

                posted_text += f"**Total** : {total}\n"
            else:
                if iteration == 0:
                    posted_text += "\n"
                posted_text += f"Roll {iteration+1} : [ {accepted} ]\n"
                if self.roll_data.modifier:
                    posted_text += f"**Pretotal**: {pretotal}\n"
                posted_text += f"**Total**: {total}\n"

    def d20_condition_check(self):
        d20s_condition = any(self.roll_data.main_roll.sides == 20)
        accpt = self.results.accepted_rolls
        if d20s_condition:
            critical_value = (
                3 if 1 and 20 in accpt else 2 if 20 in accpt else 1 if 1 in accpt else 0
            )
            crits_n_fails = re.compile(r"\b(20|1)\b")
            string_results = crits_n_fails.sub(r"**\1**", string_results)
        else:
            critical_value = 0
        return critical_value, string_results

    def accepted_roll(self, rejected_rolls):
        string_rejects = ", ".join(str(roll) for roll in rejected_rolls)
        if self.roll_data.advantages == 1:
            return (
                f"Rolled with Advantage\n" f"_Rejected Rolls_ : [ {string_rejects} ]\n"
            )
        if self.roll_data.advantages == -1:
            return (
                f"Rolled with Disadvantage\n"
                f"_Rejected Rolls_ : [ {stringified_roll.rejected} ]\n"
            )

    def string_d20_condition(self, string_results):
        crits_n_fails = re.compile(r"\b(20|1)\b")
        string_results = crits_n_fails.sub(
            r"**\1**", string_results
        )  # bold critical values
        if crit_code == 3:
            return f"Wow! You got a Critical Success and a Critical Failure!\n"
        elif crit_code == 2:
            return f"**Critical Success**! Roll again!\n"
        elif crit_code == 1:
            return f"**Critical Failure**! Await your fate!\n"

    def drop_lowest_condition(self):
        for index, value in enumerate(roll for roll in dice_rolls["accepted"]):
            if index not in indices2keep:
                string_dice_accepted[index] = f"~~{value}~~"
