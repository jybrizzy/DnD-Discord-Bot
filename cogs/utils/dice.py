import asyncio
import itertools
import re
from random import randint
from collections import namedtuple
import sys

from cogs.utils.roll_parser import RollParser
from cogs.utils.roll_methods import RollMethods

# print(sys.path)


class RollCalculator:
    def __init__(self, roll_string=None, roll_data=None):
        self.roll_string = roll_string or "1d20"
        self.roll_data = roll_data or RollParser(self.roll_string).delineater
        self.roll_results = dict()

    def drop_lowest_generator(self, list_of_rolls):
        amount2drop = self.roll_data["rolls_to_drop"]
        for dice_rolls in list_of_rolls:
            indices2keep = sorted(
                range(len(dice_rolls["accepted"])),
                key=lambda x: dice_rolls["accepted"][x],
            )[amount2drop:]
            yield (indices2keep)

    @property
    def calculate_results(self):

        res_list = []
        for _ in range(self.roll_data["multiplier"]):
            for die_dict in self.roll_data["main_roll"]:
                dice, sides = die_dict["dice"], die_dict["sides"]
                results_dict = dict.fromkeys(["accepted", "rejected"])
                if self.roll_data["advantage"]:
                    (
                        results_dict["accepted"],
                        results_dict["rejected"],
                    ) = RollMethods.advantage(dice, sides)

                elif self.roll_data["disadvantage"]:
                    (
                        results_dict["accepted"],
                        results_dict["rejected"],
                    ) = RollMethods.disadvantage(dice, sides)

                else:
                    results_dict["accepted"] = RollMethods.die_roller(dice, sides)
                    results_dict["rejected"] = None

                res_list.append(results_dict)

        indices_to_keep = self.drop_lowest_generator(res_list)
        pretotal = []
        for dice_result in res_list:
            kept_dice = []
            ind2k = next(indices_to_keep)
            for index, rolls in enumerate(dice_result["accepted"]):
                if index in ind2k:
                    kept_dice.append(rolls)
                else:
                    continue
            pretotal.append(sum(kept_dice))

        mods = sum(self.roll_data["modifier"])

        self.roll_results["Results_Rejects"] = res_list
        self.roll_results["Pretotal"] = pretotal
        self.roll_results["Total"] = [
            pretot + mods for pretot in self.roll_results["Pretotal"]
        ]

        return self.roll_results

    def rollstr_from_rolldata(self):
        """Derives a new roll_string from roll_data"""
        new_roll_str = ""
        roll_dict = self.roll_data["main_roll"][0]
        new_roll_str += f'{roll_dict["dice"]}d{roll_dict["sides"]}'
        if any(self.roll_data["string_modifier"]):
            new_roll_str += " "
            new_roll_str += ", ".join(self.roll_data["string_modifier"])
        if self.roll_data["advantage"]:
            new_roll_str += " advantage"
        if self.roll_data["disadvantage"]:
            new_roll_str += " disadvantage"
        if self.roll_data["rolls_to_drop"] > 0:
            new_roll_str += f' kh{self.roll_data["rolls_to_drop"]}'
        if self.roll_data["multiplier"] > 1:
            new_roll_str = f'{self.roll_data["multiplier"]} * ({new_roll_str})'

        return new_roll_str

    def string_constructor(self, ctx):
        """Constructs string to be sent Discord side. Returns posted_text"""

        stringified_rolls = []
        _ = self.calculate_results
        String_Results = namedtuple(
            "String_Results", ["accepted", "rejected"]
        )  # class name in quotations
        list_o_indices = self.drop_lowest_generator(
            self.roll_results["Results_Rejects"]
        )
        for dice_rolls in self.roll_results["Results_Rejects"]:
            """Loops over dice multiples: most likely to be a single loop"""
            indices2keep = next(list_o_indices)
            if self.roll_data["rolls_to_drop"] > 0:
                string_dice_accepted = [str(roll) for roll in dice_rolls["accepted"]]
                for index, value in enumerate(roll for roll in dice_rolls["accepted"]):
                    if index not in indices2keep:
                        string_dice_accepted[index] = f"~~{value}~~"
                    else:
                        continue
            else:
                string_dice_accepted = [str(roll) for roll in dice_rolls["accepted"]]

            string_results = ", ".join(roll for roll in string_dice_accepted)
            if dice_rolls["rejected"] is not None:
                string_rejects = ", ".join(str(roll) for roll in dice_rolls["rejected"])
            else:
                string_rejects = None

            d20s_condition = any(
                [
                    roll["sides"]
                    for roll in self.roll_data["main_roll"]
                    if roll["sides"] == 20
                ]
            )

            if d20s_condition:
                crit_fail = True if 1 in dice_rolls["accepted"] else False
                crit_sucess = True if 20 in dice_rolls["accepted"] else False

                crits_n_fails = re.compile(r"\b(20|1)\b")
                string_results = crits_n_fails.sub(r"**\1**", string_results)
            else:
                crit_fail, crit_sucess = False, False

            stringified_result = String_Results(string_results, string_rejects)
            stringified_rolls.append(stringified_result)

        # need to put this under a conditional
        # ability_rolls_chk_dict = RollParser("6 * (4d6 dl1)").delineater
        # if self.roll_data == ability_rolls_chk_dict:
        # rolled_string = "Ability Score Rolls"
        # else:
        # rolled_string = self.roll_string.strip().lower()

        posted_text = (
            f"{ctx.author.mention} <:d20:849391713336426556>\n" f"{self.roll_string} "
        )
        for multiple, stringified_roll in enumerate(stringified_rolls):
            pretotal = self.roll_results["Pretotal"][multiple]
            total = self.roll_results["Total"][multiple]
            if self.roll_data["multiplier"] > 1:
                if multiple == 0:
                    posted_text += "\n"
                posted_text += (
                    f"Roll {multiple+1} : [ {stringified_roll.accepted} ]\n"
                    f"**Total**: {total}\n"
                )
            else:
                posted_text += f": [ {stringified_roll.accepted} ]\n"

                if len(self.roll_data["modifier"]) > 1:
                    posted_text += (
                        f"**Pretotal**: {pretotal}\n" f"**Total** : {total}\n"
                    )
                else:
                    posted_text += f"**Total** : {total}\n"

            if self.roll_data["advantage"]:
                posted_text += (
                    f"Rolled with Advantage\n"
                    f"_Rejected Rolls_ : [ {stringified_roll.rejected} ]\n"
                )
            if self.roll_data["disadvantage"]:
                posted_text += (
                    f"Rolled with Disadvantage\n"
                    f"_Rejected Rolls_ : [ {stringified_roll.rejected} ]\n"
                )
            if d20s_condition:
                if crit_fail and crit_sucess:
                    posted_text += (
                        f"Wow! You got a Critical Success and a Critical Failure!\n"
                    )
                elif crit_fail:
                    posted_text += f"**Critical Failure**! Await your fate!\n"
                elif d20s_condition and crit_sucess:
                    posted_text += f"**Critical Success**! Roll again!\n"

        return posted_text
