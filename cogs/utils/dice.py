import asyncio
import itertools
import re
from random import randint
from collections import namedtuple


class RollParser:

    max_dice = 100
    max_sides = 1000
    max_multiplier = 20
    max_rolls = 10

    def __init__(self, roll_string=None):
        self.roll_string = roll_string or "1d20"
        self.roll = {}

    def max_roll_check(self, dice, sides):
        warning = ""
        if dice > self.max_dice:
            dice = self.max_dice
            warning += f"Maximum number of die, {self.max_dice}, exceeded.\n"
        if sides > self.max_sides:
            sides = self.max_sides
            warning += f"Maximum number of sides, {self.max_sides}, exceeded.\n"
        if warning:
            warning += f"Rolling {dice}d{sides} instead.\n"
        return dice, sides, warning

    def invalid_roll_check(self, dice, sides):
        warning = ""
        if not dice:
            dice = 1
        if not sides:
            warning += "Invalid number of sides.\n"
        if dice <= 0:
            warning += f"Invalid number of die, must be a positive integer.\n"
        if sides <= 0:
            warning += f"Invalid number of sides, must be a positive integer.\n"
        return dice, sides, warning

    def balanced_parenthesis(self, string2check):
        pairs = {"(": ")"}
        match_chk = []
        for char in string2check:
            if char in "(":
                match_chk.append(char)
            elif match_chk and char == pairs[match_chk[-1]]:
                match_chk.pop()
            else:
                return False
        return len(match_chk) == 0

    @property
    def delineater(self):
        self.roll_string = self.roll_string.lower().strip()
        # Check for & parse parentheses and multiplier
        if re.search(r"\((.*?)\)", self.roll_string):
            paren_check = re.findall(
                r"([0-9]{1,3})?\s*\*?\s*\((.*?)\)\s*\*?\s*([0-9]{1,3})?",
                self.roll_string,
            )
            # 0 is potential multiplier
            # 1 is content w/in parenthesis
            # 2 is potential multiplier

            # Removes tuple inside list [(1,2,3)] -> [1,2,3]
            paren_check = list(itertools.chain(*paren_check))
            if not paren_check[1]:
                return "Invalid format. Must include a dice roll to parse if including parentheses.\n"
            else:
                self.roll_string = paren_check[1].strip()

            multiplier_list = paren_check[::2]
            try:
                # have to apply int to list
                multiplier = int(list(filter(None, multiplier_list)))
            except TypeError as verr:
                print(f"Invalid multiplier formatting: {verr}")
                return "Invalid multiplier formatting. Multiplier must be a single positive integer.\n"
            if multiplier > self.max_multiplier:
                multiplier = self.max_multiplier
                self.roll["warning"] += (
                    f"Maximum number of multipliers, {self.max_multiplier}, exceeded.\n"
                    f"Using {multiplier} instead.\n"
                )
            if multiplier <= 0:
                return "Invalid multiplier. Multiplier cannot be less than 1.\n"

            self.roll["multiplier"] = multiplier

        elif self.balanced_parenthesis(self.roll_string):
            return "Incomplete parenthesis. Try again."
        else:
            self.roll["multiplier"] = 1

        # Find Modifiers
        # if there is +- signs but list is otherwise empty raise error
        modifier_reg = r"([\+-])\s*(\d*[d])?\s*(\d+)\s*"
        raw_modifier = re.findall(modifier_reg, self.roll_string)
        modifier_list = []
        modifier_str_list = []

        if not all(raw_modifier):
            modifier_list = [0]  # Set modifiers to 0 if regex query empty
        else:
            for mod_tuple in raw_modifier:
                # 0 is sign
                # 1 is the # of dice
                # 2 is dice type or integer modifier
                sign = mod_tuple[0].strip()  # +/- sign
                sign_multiple = 1 if sign == "+" else -1 if sign == "-" else None

                if mod_tuple[1]:

                    mod_dice_strings = re.findall(r"\d+", mod_tuple[1])
                    mod_dice = (
                        [int(dice) for dice in mod_dice_strings]
                        if mod_dice_strings
                        else [1]
                    )
                    mod_die, mod_sides, max_mod_warning = self.max_roll_check(
                        mod_dice[0], int(mod_tuple[2])
                    )
                    if max_mod_warning:
                        self.roll["warning"] += max_mod_warning
                    final_mod_string = f"{sign} {mod_die}d{mod_sides} "
                    try:
                        modifier = RollCalculator.die_roller(mod_die, mod_sides)[0]
                        modifier *= sign
                    except Exception as err:
                        # Deprecated: look into creating one
                        print(f"Modifier error: {err}")

                else:
                    try:
                        final_mod_string = f"{sign} {mod_tuple[2]} "
                        modifier = sign_multiple * int(mod_tuple[2])
                    except ValueError as verr:
                        print(
                            f"modifer was unable to parse modification string: {verr}"
                        )

                modifier_list.append(modifier)
                modifier_str_list.append(final_mod_string)

        self.roll["modifier"] = modifier_list
        self.roll["string_modifier"] = modifier_str_list

        # Find Base Roll
        self.roll_string = re.sub(modifier_reg, "", self.roll_string)
        main_die_list = re.findall(r"(\d*[d]\d+)", self.roll_string)
        if len(main_die_list) > self.max_rolls:
            raise ValueError("List is too long")
        raw_die_numbers = [
            tuple(map(int, die.split("d", 1))) for die in main_die_list
        ]  # ->[('','6'),('1', '20')]

        main_die = []
        for dice, sides in raw_die_numbers:
            dice, sides, mod_warning = self.max_roll_check(dice, sides)
            if mod_warning:
                return mod_warning

            main_die.append({"dice": dice, "sides": sides})

        self.roll["main_roll"] = main_die

        # Advantage or Disadvantage on Rolls
        advantage = re.findall(
            r"(?<!dis)(?:\b|\d)(advantage|advan|adv|ad|a)\b",
            self.roll_string,
            flags=re.IGNORECASE,
        )
        disadvantage = re.findall(
            r"(?:\b|\d)(disadvantage|disadv|disv|dis|da|d)\b",
            self.roll_string,
            flags=re.IGNORECASE,
        )

        if advantage and disadvantage:
            return "Invalid format. Cannot have advantage and disadvantage in the same roll"

        elif len(disadvantage) > len(self.roll["main_roll"]) < len(advantage):
            return "You cannot have more advantage/disadvantages than you have rolls"

        else:
            self.roll["advantage"] = any(advantage)
            self.roll["disadvantage"] = any(disadvantage)

        # keep highest/drop lowest
        keep_drop = re.findall(
            r"(kh|dl)\s*?(\d+)",
            self.roll_string,
        )
        if keep_drop:
            keep_drop_chc, parse_val = keep_drop[0][0], keep_drop[0][1]
            if int(parse_val) > dice:
                return "Cannot keep/drop more values than you rolled."
            elif keep_drop_chc == "kh":
                parse_value = dice - int(parse_val)
            elif keep_drop_chc == "dl":
                parse_value = int(parse_val)
            else:
                parse_value = 0
        else:
            parse_value = 0

        self.roll["rolls_to_drop"] = parse_value

        self.roll["main_roll"] = self.roll.get("main_roll", [{"dice": 1, "sides": 20}])
        self.roll["modifier"] = self.roll.get("modifier", [0])
        self.roll["string_modifier"] = self.roll.get("string_modifier", [""])
        self.roll["advantage"] = self.roll.get("advantage", False)
        self.roll["disadvantage"] = self.roll.get("disadvantage", False)
        self.roll["multiplier"] = self.roll.get("multiplier", 1)
        self.roll["rolls_to_drop"] = self.roll.get("rolls_to_drop", 0)
        self.roll["warning"] = self.roll.get("warning", "")
        # adv_split_on = filter(lambda adv_item: adv_item in self.roll_string, adv_list)

        return self.roll


class RollCalculator:
    def __init__(self, roll_string=None, roll_data=None):
        self.roll_string = roll_string or "1d20"
        self.roll_data = roll_data or RollParser(self.roll_string).delineater
        self.roll_results = dict()

    @staticmethod
    def die_roller(num_of_dice, type_of_die):
        return [randint(1, int(type_of_die)) for _ in range(int(num_of_dice))]

    @staticmethod
    def advantage(num_of_dice, type_of_die):
        roll1, roll2 = (
            RollCalculator.die_roller(num_of_dice, type_of_die),
            RollCalculator.die_roller(num_of_dice, type_of_die),
        )
        advantage = [(max(*rolls), min(*rolls)) for rolls in zip(roll1, roll2)]
        return [accpt for accpt, _ in advantage], [rej for _, rej in advantage]

    @staticmethod
    def disadvantage(num_of_dice, type_of_die):
        roll1, roll2 = (
            RollCalculator.die_roller(num_of_dice, type_of_die),
            RollCalculator.die_roller(num_of_dice, type_of_die),
        )
        disadvantage = [(min(*rolls), max(*rolls)) for rolls in zip(roll1, roll2)]
        return [accpt for accpt, _ in disadvantage], [rej for _, rej in disadvantage]

    def drop_lowest_generator(self, list_of_rolls):
        # needs fixing
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
                    ) = RollCalculator.advantage(dice, sides)

                elif self.roll_data["disadvantage"]:
                    (
                        results_dict["accepted"],
                        results_dict["rejected"],
                    ) = RollCalculator.disadvantage(dice, sides)

                else:
                    results_dict["accepted"] = RollCalculator.die_roller(dice, sides)
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
        """method that modifies string to account for any changes made to the user input string
        Returns: new_roll_str (used in string_constructor method for output compiling)"""
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

        ability_rolls_chk_dict = RollParser("6 * (4d6 dl1)").delineater
        if self.roll_data == ability_rolls_chk_dict:
            rolled_string = "Ability Score Rolls"
        else:
            rolled_string = self.roll_string.strip().lower()

        posted_text = (
            f"{ctx.author.mention} <:d20:849391713336426556>\n" f"{rolled_string} "
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
            elif self.roll_data["disadvantage"]:
                posted_text += (
                    f"Rolled with Disadvantage\n"
                    f"_Rejected Rolls_ : [ {stringified_roll.rejected} ]\n"
                )
            else:
                pass
            if d20s_condition and crit_fail and crit_sucess:
                posted_text += (
                    f"Wow! You got a Critical Success and a Critical Failure!\n"
                )
            elif d20s_condition and crit_fail:
                posted_text += f"**Critical Failure**! Await your fate!\n"
            elif d20s_condition and crit_sucess:
                posted_text += f"**Critical Success**! Roll again!\n"
            else:
                pass

        return posted_text
