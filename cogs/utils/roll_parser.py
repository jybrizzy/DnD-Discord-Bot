import itertools
import re
from cogs.utils.errors import DiceSyntaxError
from cogs.utils.roll_methods import RollMethods


class Roll:
    MAX_DICE = 100
    MAX_SIDES = 1000

    def __init__(self, die, sides):
        self.die = die or 1
        self.sides = sides
        self.warning = ""

    def __str__(self):
        return f"{self.die}d{self.sides}"

    @property
    def max_roll_check(self):
        if self.die > self.MAX_DICE:
            self.die = self.MAX_DICE
            self.warning += f"Maximum number of die, {self.MAX_DICE}, exceeded.\n"
        if self.sides > self.MAX_SIDES:
            self.sides = self.MAX_SIDES
            self.warning += f"Maximum number of sides, {self.MAX_SIDES}, exceeded.\n"
        if self.warning:
            self.warning += f"Rolling {self.die}d{self.sides} instead.\n"
        return self.die, self.sides, self.warning

    @property
    def invalid_roll_check(self):
        if not self.sides:
            raise DiceSyntaxError(
                "Invalid number of sides. Must include number of sides.\n"
            )
        if self.die <= 0:
            raise DiceSyntaxError(
                "Invalid number of die, must be a positive integer.\n"
            )
        if self.sides <= 0:
            raise DiceSyntaxError(
                "Invalid number of sides, must be a positive integer.\n"
            )


class RollData:

    MAX_MULTIPLIER = 20
    MAX_MODIFIER = 1000

    def __init__(self, **kwargs):
        self.multiplier = kwargs["multiplier"] or 1
        self.modifier = kwargs["modifier"] or [0]
        self.string_modifier = kwargs["string_modifier"] or [""]
        self.main_roll = kwargs["main_roll"] or Roll(1, 20)
        self.advantage = kwargs["advantage"] or False
        self.disadvantage = kwargs["disadvantage"] or False
        self.rolls_to_drop = kwargs["rolls_to_drop"] or 0
        self.warning = kwargs["warning"] or set()

    def __str__(self):
        """roll_string from RollData"""
        new_roll_str = ""
        new_roll_str += str(self.main_roll)
        if any(self.string_modifier):
            new_roll_str += " "
            new_roll_str += ", ".join(self.string_modifier)
        if self.advantage:
            new_roll_str += " advantage"
        if self.disadvantage:
            new_roll_str += " disadvantage"
        if self.rolls_to_drop > 0:
            new_roll_str += f" kh{self.rolls_to_drop}"
        if self.multiplier > 1:
            new_roll_str = f"{self.multiplier} * ({new_roll_str})"

        return new_roll_str

    @property
    def max_multiplier_check(self):
        if self.multiplier > self.MAX_MULTIPLIER:
            multiplier = self.MAX_MULTIPLIER
            self.roll["warning"] += (
                f"Maximum number of multipliers, {self.MAX_MULTIPLIER}, exceeded.\n"
                f"Using {multiplier} instead.\n"
            )


class RollParser:
    def __init__(self, roll_string=None):
        temp_roll_string = roll_string or "1d20"
        self.roll_string = temp_roll_string.lower().strip()
        self.main_die = None

    def balanced_parenthesis(self, string2check):
        pairs = {"(": ")"}
        match_chk = []
        for char in string2check:
            if char == "(":
                match_chk.append(char)
            elif match_chk and char == pairs[match_chk[-1]]:
                match_chk.pop()
            elif char == ")":
                return False
            else:
                continue
        return len(match_chk) == 0

    def parse_multiplier(self):
        if re.search(r"\((.*?)\)", self.roll_string):
            paren_check = re.findall(
                r"(\d+)?\s*\*?\s*\((.*?)\)\s*\*?\s*(\d+)?",
                self.roll_string,
            )
            # index 0 is potential multiplier
            # index 1 is content w/in parenthesis
            # index 2 is potential multiplier

            # Removes tuple inside list [(1,2,3)] -> [1,2,3]
            paren_check = list(itertools.chain(*paren_check))
            if not paren_check[1]:
                raise DiceSyntaxError(
                    "Invalid format. Must include a dice roll to parse if including parentheses.\n"
                )
            else:
                self.roll_string = paren_check[1].strip()

            multiplier_list = paren_check[::2]
            if not any(item for item in multiplier_list):
                multiplier = 1
            else:
                try:
                    parsed_multiplier = list(filter(None, multiplier_list))
                    if len(parsed_multiplier) == 1:
                        multiplier = int(parsed_multiplier[0])
                    else:
                        raise ValueError(
                            f"Too many multipliers were parsed: {parsed_multiplier}"
                        )
                except ValueError as mult_err:
                    raise DiceSyntaxError(
                        "Invalid multiplier formatting. Multiplier must be a single positive integer.\n"
                    ) from mult_err

            return multiplier

        elif not self.balanced_parenthesis(self.roll_string):
            raise DiceSyntaxError("Incomplete parenthesis.\n")

        else:
            return 1

    def parse_modifier(self):
        # if there is +- signs but list is otherwise empty raise error
        modifier_reg = r"([\+-])\s*(\d*[d])?\s*(\d+)\s*"
        raw_modifier = re.findall(modifier_reg, self.roll_string)
        self.roll_string = re.sub(modifier_reg, "", self.roll_string)
        self.roll_string = self.roll_string.strip()
        modifier_list = []
        modifier_str_list = []

        if any(raw_modifier):
            for mod_tuple in raw_modifier:
                # within mod tuple:
                # index 0 is sign
                # index 1 is the # of dice (may or may not be there)
                # index 2 is dice type or integer modifier
                sign = mod_tuple[0].strip()  # +/- sign
                sign_multiple = 1 if sign == "+" else -1 if sign == "-" else None

                if mod_tuple[1]:

                    mod_dice_strings = re.findall(r"\d+", mod_tuple[1])
                    mod_dice = (
                        [int(dice) for dice in mod_dice_strings]
                        if mod_dice_strings
                        else [1]
                    )  # Set number of modifier dice

                    try:
                        mod_die, mod_sides, max_mod_warning = self.max_roll_check(
                            mod_dice[0], int(mod_tuple[2])
                        )
                        if max_mod_warning:
                            self.roll["warning"] += max_mod_warning
                        final_mod_string = f"{sign} {mod_die}d{mod_sides} "
                        modifier = RollMethods.die_roller(mod_die, mod_sides)[0]
                        modifier *= sign_multiple
                    except ValueError as mod_die_err:
                        raise DiceSyntaxError(
                            "Invalid die-type modifier format.\n"
                        ) from mod_die_err

                else:
                    try:
                        final_mod_string = f"{sign} {mod_tuple[2]} "
                        modifier = sign_multiple * int(mod_tuple[2])
                    except ValueError as mod_int_err:
                        raise DiceSyntaxError(
                            "Invalid integer-type modifier format.\n"
                        ) from mod_int_err

                modifier_list.append(modifier)
                modifier_str_list.append(final_mod_string)
        else:
            modifier_list = [0]
            modifier_str_list = [""]

        return modifier_list, modifier_str_list

    def parse_base_roll(self):
        main_die_list = re.findall(r"(\d*[d]\d+)", self.roll_string)
        raw_die_numbers = [
            tuple(map(int, die.split("d", 1))) for die in main_die_list
        ]  # ->[('',6),(1, 20)]

        self.main_die = []
        for dice, sides in raw_die_numbers:
            die_instance = Roll(dice, sides)
            _ = self.main_die.max_roll_check
            _ = self.main_die.invalid_roll_check

            self.main_die.append(die_instance)

        return self.main_die

    def parse_advantage_disadvantage(self):
        advantage = re.findall(
            r"(?<!dis)(?:\b|\d)(advantage|advan|adv|ad|a)",
            self.roll_string,
        )
        disadvantage = re.findall(
            r"(?:\b|\d)(disadvantage|disadv|disv|dis|da)", self.roll_string
        )
        if advantage and disadvantage:
            raise DiceSyntaxError(
                "Invalid syntax. Cannot have advantage and disadvantage in the same roll.\n"
            )
        if len(disadvantage) > len(self.roll["main_roll"]):
            raise DiceSyntaxError(
                "Invalid syntax. You cannot have more disadvantages than you have rolls.\n"
            )
        if len(advantage) > len(self.roll["main_roll"]):
            raise DiceSyntaxError(
                "Invalid syntax. You cannot have more advantages than you have rolls.\n"
            )

        return any(advantage), any(disadvantage)

    def parse_drop_lowest(self):
        keep_drop = re.findall(
            r"(kh|dl)\s*?(\d+)",
            self.roll_string,
        )
        if keep_drop:
            dice = self.main_die[0].dice
            keep_drop_chc, parse_val = keep_drop[0][0], keep_drop[0][1]
            if int(parse_val) >= dice:
                raise DiceSyntaxError(
                    "Invalid syntax. Cannot keep/drop more values than you rolled.\n"
                )
            if keep_drop_chc == "kh":
                parse_value = dice - int(parse_val)
            if keep_drop_chc == "dl":
                parse_value = int(parse_val)
        else:
            parse_value = 0

        return parse_value

    @property
    def create_roll_data(self):
        try:
            mod, string_mod = self.parse_modifier()
            adv, disadv = self.parse_advantage_disadvantage()
            roll_inputs = {
                "multiplier": self.parse_multiplier(),
                "modifier": mod,
                "string_modifier": string_mod,
                "main_roll": self.parse_base_roll(),
                "advantage": adv,
                "disadvantage": disadv,
                "rolls_to_drop": self.parse_drop_lowest(),
                "warning": self.roll.get("warning", ""),
            }

        except DiceSyntaxError as die_err:
            # die_err.__cause__ would reveal ValueErrors
            return str(die_err)
        else:
            return self.roll


# print(RollParser("1d20").__dict__)  # parse_multiplier()
