from abc import ABC, abstractmethod
from .roll_calculator import RollResults


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
        try:
            self.d20s = self.data.main_roll.sides == 20
            self.idx2keep = self.results.set_index_to_keep(self.results.accepted)
            self.crit_code = self.results.set_critical_values(self.d20s)
        except AttributeError as att_err:
            print(f"Attributes not recognized: {att_err}")

    def main_roll_result(self, ctx):
        if self.data.syntax_error:
            return self.data.syntax_error
        else:
            posted_text = (
                f"{ctx.author.mention} <:d20:849391713336426556>\n"
                f"{self.roll_string} "
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