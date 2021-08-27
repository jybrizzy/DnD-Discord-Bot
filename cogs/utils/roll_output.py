from abc import ABC, abstractmethod
from cogs.utils.roll_calculator import RollCalculator, RollResults


class StringifyRoll(ABC):
    def __init__(self, data):
        self.data = data
        try:
            self.d20s = self.data.main_roll.sides == 20
            self.rlls2drp = self.data.rolls_to_drop
        except AttributeError as att_err:
            print(f"Attributes not recognized: {att_err}")

    def configure_roll_string(self, str_result: str, accpt_bool: bool = True):
        str_roll_lst = [str(result) for result in str_result]
        if accpt_bool:
            str_roll_lst = self.d20_formatter(str_roll_lst)
            str_roll_lst = self.drop_lowest_formatter(str_roll_lst)  # Need to fix
        str_roll = ", ".join(str_roll_lst)
        return str_roll

    def d20_formatter(self, str_roll):
        if self.d20s:
            ##Bold any 20's or 1's
            str_roll = [
                f"**{roll}**" if roll in ["20", "1"] else roll for roll in str_roll
            ]  # check if it highlights 10.
        return str_roll

    def drop_lowest_formatter(self, str_roll, accepted_results):
        if self.rlls2drp > 0:
            idx2keep = RollCalculator.set_index_to_keep(self.rlls2drp, accepted_results)
            str_roll = [
                f"~~{roll}~~" if idx not in idx2keep else roll
                for idx, roll in enumerate(str_roll)
            ]
        return str_roll

    @abstractmethod
    def configure_output(self, result: RollResults) -> str:
        pass

    def stringify_advantages(self, rejected_result):
        rejected = self.configure_roll_string(rejected_result, accpt_bool=False)
        if self.data.advantages == 1:
            return f"Rolled with Advantage\n" f"_Rejected Rolls_ : [ {rejected} ]\n"
        if self.data.advantages == -1:
            return f"Rolled with Disadvantage\n" f"_Rejected Rolls_ : [ {rejected} ]\n"

    def stringify_d20_crit_roll(self, accpted):
        crit_code_map = {
            3: "Wow! You got a Critical Success and a Critical Failure!\n",
            2: "**Critical Success**! Roll again!\n",
            1: "**Critical Failure**! Await your fate!\n",
            0: "",
        }

        if self.d20s:
            critical_value = (
                3
                if 1 and 20 in accpted
                else 2
                if 20 in accpted
                else 1
                if 1 in accpted
                else 0
            )
            return crit_code_map[critical_value]
        else:
            return crit_code_map[0]


class StringifyMultilplierRolls(StringifyRoll):
    def configure_output(self, result: RollResults, data) -> str:
        posted_text = "\n"
        for iteration in range(data.multiplier):
            rslt = next(result)  # Need to fix
            accepted = super().configure_roll_string(rslt.accepted)
            posted_text += f"Roll {iteration+1} : [ {accepted} ]\n"
            if len(data.modifier) > 1:
                posted_text += f"**Pretotal**: {rslt.pretotal}\n"
            posted_text += f"**Total**: {rslt.total}\n"
            if data.advantages != 0:
                posted_text += super().stringify_advantages(rslt.rejected)
            posted_text += super().stringify_d20_crit_roll(rslt.accepted)
        return posted_text


class StringifySingleRoll(StringifyRoll):
    def configure_output(self, result: RollResults, data) -> str:
        # Need to fix
        rslt = next(result)
        accepted = super().configure_roll_string(rslt.accepted)
        posted_text = f": [ {accepted} ]\n"
        if len(data.modifier) > 1:
            posted_text += f"**Pretotal**: {rslt.pretotal}\n"
        posted_text += f"**Total** : {rslt.total}\n"
        return posted_text


# class StringifyRejectedString(StringifyRoll):
#     def configure_output(self, result: RollResults) -> str:
#         rejected = super()
#         return rejected


class RollOutput:
    def __init__(self, roll_data, results, roll_string: str = None):
        self.data = roll_data
        self.roll_string = roll_string or str(self.data)
        self.results = results

    def main_roll_result(self, ctx):
        if self.data.syntax_error:
            return self.data.syntax_error
        else:
            posted_text = (
                f"{ctx.author.mention} <:d20:849391713336426556>\n"
                f"{self.roll_string} "
            )

            if self.data.multiplier > 1:
                str_inst = StringifyMultilplierRolls(self.data)
                posted_text += str_inst.configure_output(self.results, self.data)
            else:
                str_inst = StringifySingleRoll(self.data)
                posted_text += str_inst.configure_output(self.results)

            return posted_text
