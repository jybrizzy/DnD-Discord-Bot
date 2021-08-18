import itertools
import re
from cogs.utils.errors import DiceSyntaxError
from functools import wraps


class Roll:
    MAX_DICE = 100
    MAX_SIDES = 1000

    def __init__(self, die: int, sides: int, sign: str = None) -> None:
        self.die = die
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

    def validate_roll(self) -> None:
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

    def validate_max_roll(self) -> set:
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


class RollValidation:
    @staticmethod
    def validate_max(value, var_name, max_value):
        warning = None
        if value > max_value:
            value = max_value
            warning = f"""Maximum number of {var_name}, {max_value}, exceeded.\n
                          Using {value} instead.\n"""
        return value, warning

    @staticmethod
    def validate_advantages(
        advantage: list, disadvantage: list, main_roll: Roll
    ) -> None:
        if advantage and disadvantage:
            raise DiceSyntaxError(
                "Invalid syntax. Cannot have advantage and disadvantage in the same roll.\n"
            )
        if len(disadvantage) > len(main_roll):
            raise DiceSyntaxError(
                "Invalid syntax. You cannot have more disadvantages than you have rolls.\n"
            )
        if len(advantage) > len(main_roll):
            raise DiceSyntaxError(
                "Invalid syntax. You cannot have more advantages than you have rolls.\n"
            )


class RollParser:
    MAX_MULTIPLIER = 20
    MAX_MODIFIER = 1000
    MAX_LEN_MODIFIERS = 100

    def __init__(self, roll_string: str = None, **kwargs) -> None:
        temp_roll_string = roll_string or "1d20"
        self.roll_string = temp_roll_string.lower().strip()
        syntax_error = ""
        try:
            self.multiplier = kwargs.get("multiplier", self.parse_multiplier())
            self.modifier = kwargs.get("modifier", self.parse_modifier())
            self.main_roll = kwargs.get("main_roll", self.parse_base_roll())
            self.advantages = kwargs.get("advantages", self.parse_advantages())
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
            new_roll_str += f" kh{self.main_roll.die - self.rolls_to_drop}"
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
        if paren_check[1]:
            self.roll_string = paren_check[1].strip()
        else:
            raise DiceSyntaxError(
                "Invalid format. Must include a dice roll to parse if including parenthesis.\n"
            )

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
                multiplier, warn = RollValidation.validate_max(
                    multiplier, "multiplier", self.MAX_MULTIPLIER
                )
                if warn:
                    self.warning.update(warn)
            except ValueError as mult_err:
                raise DiceSyntaxError(
                    "Invalid multiplier formatting. Multiplier must be a single positive integer.\n"
                ) from mult_err

        return multiplier

    def config_roll(self, die, sides, sign=None) -> Roll:
        try:
            die = int(die) if die else 1
            sides = int(sides)
            roll = Roll(die, sides, sign)
            warn = roll.validate_max_roll()
            if warn:
                self.warning.update(warn)
            roll.validate_roll()
        except ValueError as die_err:
            raise DiceSyntaxError("Invalid roll syntax.\n") from die_err

        return roll

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

                if mod_tuple[1]:
                    mod_die_str = mod_tuple[1] + mod_tuple[2]
                    mod_die, mod_sides = mod_die_str.split("d")
                    modifier = self.config_roll(mod_die, mod_sides, sign=sign)

                else:
                    try:
                        sign_multiple = (
                            1 if sign == "+" else -1 if sign == "-" else None
                        )
                        modifier = sign_multiple * int(mod_tuple[2])
                        modifier, warn = RollValidation.validate_max(
                            modifier, "modifier", self.MAX_MODIFIER
                        )
                        if warn:
                            self.warning.update(warn)
                    except ValueError as mod_int_err:
                        raise DiceSyntaxError(
                            "Invalid integer-type modifier format.\n"
                        ) from mod_int_err

                modifiers.append(modifier)

            if len(modifiers) > self.MAX_LEN_MODIFIERS:
                raise DiceSyntaxError(
                    f"Maximum number of modifiers, {self.MAX_LEN_MODIFIERS}, exceeded."
                )
        else:
            modifiers = [0]

        return modifiers

    def parse_base_roll(self) -> Roll:
        main_die_str = re.findall(r"(\d*[d]\d+)", self.roll_string)
        main_die_str = main_die_str[0]
        if main_die_str:
            die, sides = main_die_str.split("d")
            main_roll = self.config_roll(die, sides)
        else:
            main_roll = Roll(1, 20)
        return main_roll

    def parse_advantages(self) -> int:
        """Parses out advantage and disadvantage"""
        advantage = re.findall(
            r"(?<!dis)(?:\b|\d)(advantage|advan|adv|ad|a)", self.roll_string
        )
        disadvantage = re.findall(
            r"(?:\b|\d)(disadvantage|disadv|disv|dis|da)", self.roll_string
        )

        RollValidation.validate_advantages(
            advantage, disadvantage, self.main_roll
        )  # play with whether it is triggered when = to something
        advantage_indx = 1 if any(advantage) else -1 if any(disadvantage) else 0

        return advantage_indx

    def parse_drop_lowest(self) -> int:
        keep_drop = re.findall(r"(kh|dl)\s*?(\d+)", self.roll_string)
        keep_drop = list(itertools.chain(*keep_drop))
        if keep_drop:
            die = self.main_roll.die
            keep_drop_chc, parse_val = keep_drop[0], keep_drop[1]
            if int(parse_val) >= die:
                raise DiceSyntaxError(
                    "Invalid syntax. Cannot keep/drop more values than you rolled.\n"
                )
            if keep_drop_chc == "kh":
                drop_amnt = die - int(parse_val)
            if keep_drop_chc == "dl":
                drop_amnt = int(parse_val)
        else:
            drop_amnt = 0

        return drop_amnt


# print(RollParser("1d20").__dict__)  # parse_multiplier()
