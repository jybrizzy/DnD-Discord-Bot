import asyncio
import itertools
import re
from random import randint
from collections import namedtuple


class RollParser:

    max_dice = 100
    max_sides = 1000
    max_multiplier = 10
    max_rolls = 10

    def __init__(self, roll_string):
        if roll_string is None:
            self.roll_string = "1d20"
        else:
            self.roll_str = roll_string.lower().strip()
        self.roll = {}

    @property
    def delineater(self):

        # Check for & parse parentheses and multiplier
        if re.search(r"\((.*?)\)", self.roll_str):
            paren_check = re.findall(
                r"([0-9]{1,3})?\s*\*?\s*\((.*?)\)\s*\*?\s*([0-9]{1,3})?", self.roll_str
            )
            paren_check = list(
                itertools.chain(*paren_check)
            )  # Removes tuple inside list
            if not paren_check[1]:
                raise ValueError("No dice string to parse!")
            elif paren_check[0] and paren_check[-1]:
                raise ValueError("You cannot have more than 1 multiplier")
            elif paren_check[0] or paren_check[-1]:
                multiplier_list = paren_check[::2]
                multiplier = int(list(filter(None, multiplier_list))[0])
                if not multiplier:
                    raise ValueError("Invalid multiplier formatting")
                elif multiplier <= 0:
                    raise ValueError("Cannot have *0 or negative values")
                else:
                    self.roll["multiplier"] = multiplier
                self.roll_str = paren_check[1]
            else:
                self.roll_str = paren_check[1]
        else:
            pass

        # Find Modifiers
        # if there is +- signs but list is otherwise empty raise error
        modifier_reg = r"([\+-])\s*(\d*[d])?\s*(\d+)\s*"
        raw_modifier = re.findall(modifier_reg, self.roll_str)
        modifier_list = []

        if not all(raw_modifier):
            modifier_list = [0]  # Set modifiers to 0 if regex query empty
        else:
            for mod_tuple in raw_modifier:
                # 0 is sign
                # 1 is the # of dice
                # 2 is dice type or integer modifier
                sign = mod_tuple[0].strip()  # +/- sign
                sign = 1 if sign == "+" else -1 if sign == "-" else None

                if mod_tuple[1]:

                    mod_dice = [
                        int(dice) if dice else 1
                        for dice in re.findall(r"\d+", mod_tuple[1])
                    ]
                    try:
                        modifier = RollCalculator.die_roller(
                            mod_dice[0], int(mod_tuple[2])
                        )[0]
                        modifier *= sign
                    except:
                        raise ValueError("Must assign # of sides to mod die")

                else:
                    try:
                        modifier = sign * int(mod_tuple[2])
                    except ValueError as verr:
                        print(
                            f"modifer was unable to parse modification string: {verr}"
                        )

                modifier_list.append(modifier)

        self.roll["modifier"] = modifier_list

        # Find Base Roll
        self.roll_str = re.sub(modifier_reg, "", self.roll_str)
        main_die_list = re.findall(r"(\d*[d]\d+)", self.roll_str)
        if len(main_die_list) > self.max_rolls:
            raise ValueError("List is too long")
        raw_die_numbers = [
            tuple(map(int, die.split("d", 1))) for die in main_die_list
        ]  # ->[('','6'),('1', '20')]

        main_die = []
        Dice_Sides = namedtuple("Dice_Sides", ["dice", "sides"])
        for dice, sides in raw_die_numbers:
            if not dice:
                dice = 1
            elif not sides:
                sides = 20
            elif dice >= self.max_dice and sides >= self.max_sides:
                dice = self.max_dice
                sides = self.max_sides
                raise ValueError("Too many rolls/sides")
            elif dice >= self.max_dice:
                dice = self.max_dice
            elif sides >= self.max_sides:
                sides = self.max_sides
            else:
                dice, sides = dice, sides

            main_die.append(Dice_Sides(dice, sides))

        self.roll["main_roll"] = main_die

        # Advantage or Disadvantage on Rolls
        advantage = re.findall(
            r"(?<!dis)(?:\b|\d)(advantage|advan|adv|ad|a)\b",
            self.roll_str,
            flags=re.IGNORECASE,
        )
        disadvantage = re.findall(
            r"(?:\b|\d)(disadvantage|disadv|disv|dis|da|d)\b",
            self.roll_str,
            flags=re.IGNORECASE,
        )

        if advantage and disadvantage:
            raise ValueError(
                "You cannot have advantage and disadvantage in the same roll"
            )

        elif len(disadvantage) > len(self.roll["main_roll"]) < len(advantage):
            raise ValueError(
                "You cannot have more advantage/disadvantages than you have rolls"
            )

        else:
            self.roll["advantage"] = any(advantage)
            self.roll["disadvantage"] = any(disadvantage)

        # keep highest/drop lowest
        keep_drop = re.findall(
            r"(kh|dl)(\d+)",
            self.roll_str,
        )
        if keep_drop:
            keep_drop_chc, parse_val = keep_drop[0][0], keep_drop[0][1]
            if int(parse_val) > dice:
                raise ValueError("Cannot keep/drop more values than you rolled.")
            elif keep_drop_chc == "kh":
                parse_value = int(parse_val)
            elif keep_drop_chc == "dl":
                parse_value = dice - int(parse_val)
            else:
                parse_value = 0
        else:
            parse_value = 0

        self.roll["retain_number"] = parse_value

        self.roll["main_roll"] = self.roll.get("main_roll", [Dice_Sides(1, 20)])
        self.roll["modifier"] = self.roll.get("modifier", [0])
        self.roll["advantage"] = self.roll.get("advantage", False)
        self.roll["disadvantage"] = self.roll.get("disadvantage", False)
        self.roll["multiplier"] = self.roll.get("multiplier", 1)
        self.roll["retain_number"] = self.roll.get("retain_number", 0)
        # adv_split_on = filter(lambda adv_item: adv_item in self.roll_str, adv_list)

        return self.roll


class RollCalculator:
    def __init__(self, roll_string=None, roll_results=None):
        if roll_string is None:
            self.roll_string = "1d20"
        else:
            self.roll_string = roll_string.strip().lower()
        if roll_results is None:
            self.roll_results = dict()
        else:
            self.roll_results = roll_results
        self.roll_data = RollParser(roll_string).delineater

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

    def keep_highest_generator(self, list_of_rolls):
        amount2keep = -1 * self.roll_data["retain_number"]
        for dice_rolls in list_of_rolls:
            indices2keep = sorted(
                range(len(dice_rolls["accepted"])),
                key=lambda x: dice_rolls["accepted"][x],
            )[amount2keep:]
            yield (indices2keep)

    @property
    def calculate_results(self):

        res_list = []
        for _ in range(self.roll_data["multiplier"]):
            for dice, sides in self.roll_data["main_roll"]:
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

        indices_to_keep = self.keep_highest_generator(res_list)
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

    def string_constructor(self, ctx):
        """Constructs string to be sent Discord side. Returns posted_text"""

        stringified_rolls = []
        _ = self.calculate_results
        String_Results = namedtuple(
            "String_Results", ["accepted", "rejected"]
        )  # class name in quotations
        list_o_indices = self.keep_highest_generator(
            self.roll_results["Results_Rejects"]
        )
        for dice_rolls in self.roll_results["Results_Rejects"]:
            """Loops over dice multiples: most likely to be a single loop"""
            indices2keep = next(list_o_indices)
            if self.roll_data["retain_number"] > 0:
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
                [roll.sides for roll in self.roll_data["main_roll"] if roll.sides == 20]
            )

            if d20s_condition:
                if 1 in dice_rolls["accepted"]:
                    crit_fail = True
                else:
                    crit_fail = False
                if 20 in dice_rolls["accepted"]:
                    crit_sucess = True
                else:
                    crit_sucess = False

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
            rolled_string = self.roll_string

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