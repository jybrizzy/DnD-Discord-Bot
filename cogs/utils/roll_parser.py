import itertools
import re
from cogs.utils.errors import DiceSyntaxError
from functools import wraps


class Roll:
    MAX_DICE = 100
    MAX_SIDES = 1000

    def __init__(self, die: int or None, sides: int, sign: str = None) -> None:
        self.die = die or 1
        self.sides = sides
        self.sign = sign
        self.warning = set()

    def __str__(self) -> str:
        die_str = f"{self.die}d{self.sides}"
        if self.sign:
            die_str = f"{self.sign.strip()} {die_str}"
        return die_str

    def __repr__(self) -> str:
        if self.sign:
            return f"Roll({self.die}, {self.sides}, '{self.sign}')"
        else:
            return f"Roll({self.die}, {self.sides})"

    def __len__(self) -> int:
        return 1

    def max_roll_check(self) -> set:
        if self.die > self.MAX_DICE:
            self.die = self.MAX_DICE
            self.warning.update(f"Maximum number of die, {self.MAX_DICE}, exceeded.\n")
        if self.sides > self.MAX_SIDES:
            self.sides = self.MAX_SIDES
            self.warning.update(
                f"Maximum number of sides, {self.MAX_SIDES}, exceeded.\n"
            )
        if self.warning:
            self.warning.update(f"Rolling {self.die}d{self.sides} instead.\n")
        return self.warning

    def invalid_roll_check(self) -> None:
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


def balanced_parenthesis(string2check: str) -> bool:
    """Check for balanced parenthesis. Used for syntax check."""
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


def parse_parenthesis(default_val):
    def _decorator(parse_mult):
        @wraps(parse_mult)
        def _wrapper(self):
            if re.search(r"\((.*?)\)", self.roll_string):
                return parse_mult(self)
            elif not balanced_parenthesis(self.roll_string):
                raise DiceSyntaxError("Incomplete parenthesis.\n")
            else:
                return default_val

        return _wrapper

    return _decorator


class RollParser:

    MAX_MULTIPLIER = 20
    MAX_MODIFIER = 1000

    def __init__(self, roll_string: str = None, **kwargs) -> None:
        temp_roll_string = roll_string or "1d20"
        self.roll_string = temp_roll_string.lower().strip()
        syntax_error = ""
        try:
            self.multiplier = kwargs.get("multiplier", self.parse_multiplier())
            self.modifier = kwargs.get("modifier", self.parse_modifier())
            self.main_roll = kwargs.get("main_roll", self.parse_base_roll())
            self.advantages = kwargs.get(
                "advantages", self.parse_advantage_disadvantage()
            )
            self.rolls_to_drop = kwargs.get("rolls_to_drop", self.parse_drop_lowest())
            self.warning = set()
        except DiceSyntaxError as die_err:
            syntax_error = str(die_err)
        finally:
            self.syntax_error = syntax_error

    def __str__(self) -> str:
        """roll string from roll data"""
        new_roll_str = f""
        new_roll_str += str(self.main_roll)
        if any(self.modifier):
            new_roll_str += f" "
            for mod in self.modifier:
                if isinstance(mod, Roll):
                    new_roll_str += f"{str(mod)} "
                elif isinstance(mod, int):
                    sign = "+" if mod >= 0 else "-"
                    new_roll_str += f"{sign} {abs(mod)} "
        if self.advantages == 1:
            new_roll_str += " advantage"
        if self.advantages == -1:
            new_roll_str += " disadvantage"
        if self.rolls_to_drop > 0:
            new_roll_str += f" kh{self.rolls_to_drop}"
        if self.multiplier > 1:
            new_roll_str = f"{self.multiplier} * ({new_roll_str})"

        return new_roll_str

    @parse_parenthesis(default_val=1)
    def parse_multiplier(self) -> int:
        """Searches dice text for parenthesis and multiplier (e.g. 6*(4d6)). Returns multiplier modifies dice text to what is in parens."""
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
                "Invalid format. Must include a dice roll to parse if including parenthesis.\n"
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

    def parse_modifier(self) -> list:
        """Compiles list of modifiers. List components are ints or Roll instances."""
        modifier_reg = r"([\+-])\s*(\d*[d])?\s*(\d+)\s*"
        raw_modifier = re.findall(modifier_reg, self.roll_string)
        # To not confuse parse_base_roll regex:
        self.roll_string = re.sub(modifier_reg, "", self.roll_string).strip()

        if any(raw_modifier):
            modifiers = []
            for mod_tuple in raw_modifier:
                # within mod tuple:
                # index 0 is sign
                # index 1 is the # of dice (may or may not be there)
                # index 2 is # dice of sides or integer modifier (dependent on index 1)
                sign = mod_tuple[0].strip()
                sign_multiple = 1 if sign == "+" else -1 if sign == "-" else None

                if mod_tuple[1]:
                    try:
                        mod_sides = int(mod_tuple[2])
                        mod_dice_strings = re.findall(r"\d+", mod_tuple[1])
                        # Set number of dice in modifier (1 if no number before d)
                        mod_dice = (
                            [int(dice) for dice in mod_dice_strings]
                            if mod_dice_strings
                            else [1]
                        )

                        modifier = Roll(mod_dice, mod_sides, sign=sign)
                        warning = modifier.max_roll_check()
                        if warning:
                            self.warning.update(warning)
                        modifier.invalid_roll_check()

                    except ValueError as mod_die_err:
                        raise DiceSyntaxError(
                            "Invalid die-type modifier format.\n"
                        ) from mod_die_err

                else:
                    try:
                        modifier = sign_multiple * int(mod_tuple[2])
                    except ValueError as mod_int_err:
                        raise DiceSyntaxError(
                            "Invalid integer-type modifier format.\n"
                        ) from mod_int_err

                modifiers.append(modifier)
        else:
            modifiers = [0]

        return modifiers

    def parse_base_roll(self) -> Roll:
        main_die = re.findall(r"(\d*[d]\d+)", self.roll_string)
        if main_die:
            raw_die_numbers = [tuple(map(int, die.split("d", 1))) for die in main_die]
            die, sides = raw_die_numbers[0]
            main_roll = Roll(die, sides)
            warning = main_roll.max_roll_check()
            if warning:
                self.warning.update(warning)
            main_roll.invalid_roll_check()
        else:
            main_roll = Roll(1, 20)
        return main_roll

    def parse_advantage_disadvantage(self) -> int:
        """Parses out advantage and disadvantage"""
        advantage = re.findall(
            r"(?<!dis)(?:\b|\d)(advantage|advan|adv|ad|a)", self.roll_string
        )
        disadvantage = re.findall(
            r"(?:\b|\d)(disadvantage|disadv|disv|dis|da)", self.roll_string
        )

        self.advantage_disadvantage_validation(advantage, disadvantage)
        advantage_indx = 1 if any(advantage) else -1 if any(disadvantage) else 0

        return advantage_indx

    def parse_drop_lowest(self) -> int:
        keep_drop = re.findall(r"(kh|dl)\s*?(\d+)", self.roll_string)
        keep_drop = list(itertools.chain(*keep_drop))
        if keep_drop:
            dice = self.main_roll.dice
            keep_drop_chc, parse_val = keep_drop[0], keep_drop[1]
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

    def max_multiplier_check(self) -> None:
        if self.multiplier > self.MAX_MULTIPLIER:
            multiplier = self.MAX_MULTIPLIER
            self.warning.update(
                f"Maximum number of multipliers, {self.MAX_MULTIPLIER}, exceeded.\n"
                f"Using {multiplier} instead.\n"
            )

    def advantage_disadvantage_validation(
        self, advantage: list, disadvantage: list
    ) -> None:
        if advantage and disadvantage:
            raise DiceSyntaxError(
                "Invalid syntax. Cannot have advantage and disadvantage in the same roll.\n"
            )
        if len(disadvantage) > len(self.main_roll):
            raise DiceSyntaxError(
                "Invalid syntax. You cannot have more disadvantages than you have rolls.\n"
            )
        if len(advantage) > len(self.main_roll):
            raise DiceSyntaxError(
                "Invalid syntax. You cannot have more advantages than you have rolls.\n"
            )


# print(RollParser("1d20").__dict__)  # parse_multiplier()
