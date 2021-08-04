from abc import ABC, abstractmethod
from dataclasses import dataclass

from cogs.utils.roll_parser import Roll, RollData, RollParser
from cogs.utils.roll_methods import RollMethods


@dataclass
class RollResults:

    accepted: list[int]
    rejected: list[int] or list[None]
    pretotal: int
    total: int

    def set_index_to_keep(self, rolls2drp, dice_rolls: list[int]) -> list[int]:
        amount2drop = rolls2drp
        indices2keep = sorted(
            range(len(dice_rolls)),
            key=lambda x: dice_rolls[x],
        )[amount2drop:]
        return indices2keep

    def set_critical_values(self, d20_condition: bool):
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
        ind2k = self.set_index_to_keep(self.results.accepted)
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


class StringifyRoll(ABC):
    def __init__(self, d20s=None, idx2keep=None):
        self.d20s = d20s
        self.idx2keep = idx2keep

    def configure_roll_string(self, str_result: str, accpt_bool: bool):
        str_roll = [str(result) for result in str_result]
        if accpt_bool:
            str_roll = self.d20_formatter(str_roll)
            str_roll = self.drop_lowest_formatter(str_roll)
        str_roll = ", ".join(str_result)
        return str_roll

    def d20_formatter(self, str_roll):
        if self.d20s:
            ##Bold any 20's or 1's
            str_roll = [
                f"**{roll}**" if roll in ["20", "1"] else roll for roll in str_roll
            ]
        return str_roll

    def drop_lowest_formatter(self, str_roll):
        if self.idx2keep:
            str_roll = [
                f"~~{roll}~~" if idx not in self.idx2keep else roll
                for idx, roll in enumerate(str_roll)
            ]
        return str_roll

    @abstractmethod
    def configure_output(self, result: RollResults) -> str:
        pass


class StringifyMultilplierRolls(StringifyRoll):
    def configure_output(self, result: RollResults, data) -> str:
        posted_text = "\n"
        for iteration in range(data.multiplier):
            accepted = super().configure_roll_string(result.accepted, accpt_bool=True)
            posted_text += f"Roll {iteration+1} : [ {accepted} ]\n"
            if data.modifier:
                posted_text += f"**Pretotal**: {result.pretotal}\n"
            posted_text += f"**Total**: {result.total}\n"
        return posted_text


class StringifySingleRoll(StringifyRoll):
    def configure_output(self, result: RollResults, data) -> str:
        accepted = super().configure_roll_string(result.accepted, accpt_bool=True)
        posted_text = f": [ {accepted} ]\n"
        if data.modifier:
            posted_text += f"**Pretotal**: {result.pretotal}\n"
        posted_text += f"**Total** : {result.total}\n"
        return posted_text


class StringifyRejectedString(StringifyRoll):
    def configure_output(self, result: RollResults) -> str:
        rejected = super().configure_roll_string(result.rejected, accpt_bool=False)
        return rejected


class RollOutput:
    def __init__(self, roll_data, results, roll_string: str):
        self.data = roll_data
        self.roll_string = roll_string or str(self.data)
        self.results = results
        self.d20s = self.data.main_roll.sides == 20
        self.idx2keep = self.results.set_index_to_keep(self.results.accepted)
        self.crit_code = self.results.set_critical_values(self.d20s)

    def main_roll_result(self, ctx):
        posted_text = (
            f"{ctx.author.mention} <:d20:849391713336426556>\n" f"{self.roll_string} "
        )

        if self.data.modifier > 1:
            str_inst = StringifyMultilplierRolls(self.d20s, self.idx2keep)
            posted_text += str_inst.configure_output(self.results, self.data)
        else:
            str_inst = StringifySingleRoll(self.d20s, self.idx2keep)
            posted_text += str_inst.configure_output(self.results, self.data)

        if self.data.advantages != 0:
            posted_text += self.stringify_advantages(self.results)
        if self.crit_code != 0:
            posted_text += RollOutput.d20_critical_roll(self.crit_code)

    def stringify_advantages(self, results):
        rejected = StringifyRejectedString().configure_output(results)
        if self.data.advantages == 1:
            return f"Rolled with Advantage\n" f"_Rejected Rolls_ : [ {rejected} ]\n"
        if self.data.advantages == -1:
            return f"Rolled with Disadvantage\n" f"_Rejected Rolls_ : [ {rejected} ]\n"

    @staticmethod
    def d20_critical_roll(crit_code):
        if crit_code == 3:
            return f"Wow! You got a Critical Success and a Critical Failure!\n"
        elif crit_code == 2:
            return f"**Critical Success**! Roll again!\n"
        elif crit_code == 1:
            return f"**Critical Failure**! Await your fate!\n"
