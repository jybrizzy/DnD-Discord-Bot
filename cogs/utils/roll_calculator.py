from dataclasses import dataclass
from collections.abc import Callable

from cogs.utils.roll_parser import Roll
from cogs.utils.roll_methods import RollMethods


class RollResults:
    def __init__(self, **kwargs):
        self.accepted = kwargs.get("accepted", list().copy())
        self.rejected = kwargs.get("rejected", list().copy())
        self.pretotal = kwargs.get("pretotal", None)
        self.total = kwargs.get("total", None)


class RollCalculator:
    def __init__(self, roll_data) -> None:
        self.roll_data = roll_data
        self.results = RollResults()

    def set_dice_rolls(self) -> tuple[list[int], list[int]]:
        roll_map = {
            -1: RollMethods.disadvantage,
            0: RollMethods.die_roller,
            1: RollMethods.advantage,
        }

        die, sides = self.roll_data.main_roll.die, self.roll_data.main_roll.sides
        results = roll_map[self.roll_data.advantages](die, sides)
        if any(isinstance(rest, list) for rest in results):
            self.results.accepted, *rejected = results
            self.results.rejected = rejected[0]
        else:
            self.results.accepted = results
            self.results.rejected = None

        return self

    @staticmethod
    def set_index_to_keep(rolls2drp: int, dice_rolls: list[int]) -> list[int]:
        """Returns index ordered by roll result. Drops indices as prescribed by user."""
        amount2drop = rolls2drp  # self.roll_data.rolls_to_drop
        indices2keep = sorted(
            range(len(dice_rolls)),
            key=lambda x: dice_rolls[x],
        )[amount2drop:]
        return indices2keep

    def set_pretotal(self) -> None:
        ind2k = RollCalculator.set_index_to_keep(
            self.roll_data.rolls_to_drop, self.results.accepted
        )
        self.results.pretotal = sum([self.results.accepted[index] for index in ind2k])
        return self

    def set_modifier_total(self) -> int:
        mod_values = []
        for modifier in self.roll_data.modifier:
            if isinstance(modifier, Roll):
                die, sides = modifier.die, modifier.sides
                mod_values.extend(RollMethods.die_roller(die, sides))
            elif isinstance(modifier, int):
                mod_values.append(modifier)
        return sum(mod_values)

    def set_total(self) -> None:
        mods = self.set_modifier_total()
        self.results.total = self.results.pretotal + mods
        return self
