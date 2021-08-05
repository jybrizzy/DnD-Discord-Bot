from dataclasses import dataclass
from collections.abc import Callable

from .roll_parser import Roll, RollData, RollParser
from .roll_methods import RollMethods


@dataclass
class RollResults:
    def __init__(self) -> None:
        accepted: list[int]
        rejected: list[int] or list[None]
        pretotal: int
        total: int

    def set_index_to_keep(self, rolls2drp: int, dice_rolls: list[int]) -> list[int]:
        """Returns index ordered by roll result. Drops indices as prescribed by user."""
        amount2drop = rolls2drp  # self.roll_data.rolls_to_drop
        indices2keep = sorted(
            range(len(dice_rolls)),
            key=lambda x: dice_rolls[x],
        )[amount2drop:]
        return indices2keep

    def set_critical_values(self, d20_condition: bool) -> int:
        """Returns a mapping 0, 1, 2, or 3. Identifys 1's or 20's in d20 rolls."""
        if d20_condition:
            accpt = self.accepted
            critical_value = (
                3 if 1 and 20 in accpt else 2 if 20 in accpt else 1 if 1 in accpt else 0
            )
        else:
            critical_value = 0
        return critical_value


class RollCalculator(RollResults):
    def __init__(self, roll_data) -> None:
        # super().__init__(accepted, rejected, pretotal, total)
        self.roll_data = roll_data
        self.results = RollResults()

    def set_dice_rolls(self) -> tuple[list[int], list[int]]:
        roll_map = {
            -1: RollMethods.disadvantage,
            0: RollMethods.die_roller,
            1: RollMethods.advantage,
        }

        die, sides = self.roll_data.main_roll.die, self.roll_data.main_roll.sides
        accepted, *rejected = roll_map[self.roll_data.advantages](die, sides)
        rejected = rejected[0] if rejected else None
        self.results.accepted = accepted
        self.results.rejected = rejected
        return self

    def set_pretotal(self) -> None:
        ind2k = super().set_index_to_keep(self.results.accepted)
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
