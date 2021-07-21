from random import Random, random
import unittest

import sys
from functools import partial, wraps

# sys.path.append("C:\\Users\\jbrizzy\\Desktop\\Discord_Bot")
# print(sys.path)
from cogs.utils.die_parser import RollParser
from unittest.mock import patch

unittest.TestLoader.sortTestMethodsUsing = None
# component testing


DIE_EXPRESSIONS = [
    "1d20",
    "d20",
    "&d20",
    "2d20 + 4",
    "1d20 + 1d6",
    "1d20 + 1 + 1d4",
    "(1d4)",
    "6*(4d6)",
    "(4d6)*6",
    "(1d20)*20",
    "2 * (1d6)",
    "(10d10) * 6",
    "6 * 1d20",
    "1d20 advantage",
    "1d20 disadvantage",
    "advantage 4d20",
    "1d20 advantage + 5 + 1 + 2",
    "6*(4d6 dl 1)",
    "( 4d6 dl1 )*6",
    "4d6 adv kh3",
    "1d10 dis + 1d4",
    "14d20 +2 disadvantage dl 6",
]


PARENTHESIS_EXPRESSIONS = [
    ("(1d20)", True),
    ("6*(6d4)", True),
    ("(((", False),
    ("))", False),
    ("()", True),
]


def for_each_roll(test_func):
    @wraps(test_func)
    def _wrapper(self):
        for exp in self.die_expressions:
            with self.subTest(expression=exp):
                test_func(self, exp)
        return _wrapper


"""
def _pseudo_length_check(func, results_arg):
    @wraps(func)
    def wrapper(*args, **kwargs):
        results_arg_set = results_arg or []
        if len(results_arg_set) == len(DIE_EXPRESSIONS):
            func(*args, **kwargs)
        else:
            raise ValueError("Mismatched results lengths")

    return wrapper


result_length_check = partial(_pseudo_length_check, results_arg=None)
# @result_length_check(results_arg=MULTIPLIER_TEST_LIST)
"""


class TestRollParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.random = Random(30)
        cls.die_expressions = []
        for exp in DIE_EXPRESSIONS:
            cls.die_expressions.append(RollParser(exp))

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.die_expressions

    def test_balanced_parenthesis(self):
        for (statement, expected_value) in PARENTHESIS_EXPRESSIONS:
            with self.subTest(paren_string=statement):
                self.assertEqual(
                    RollParser().balanced_parenthesis(statement), expected_value
                )

    MULTIPLIER_TEST_LIST = [
        (1, "1d20"),
        (1, "d20"),
        (1, "&d20"),
        (1, "2d20 + 4"),
        (1, "1d20 + 1d6"),
        (1, "1d20 + 1 + 1d4"),
        (1, "1d4"),
        (6, "4d6"),
        (6, "4d6"),
        (20, "1d20"),
        (2, "1d6"),
        (6, "10d10"),
        (1, "6 * 1d20"),
        (1, "1d20 advantage"),
        (1, "1d20 disadvantage"),
        (1, "advantage 4d20"),
        (1, "1d20 advantage + 5 + 1 + 2"),
        (6, "4d6 dl 1"),
        (6, " 4d6 dl1 "),
        (1, "4d6 adv kh3"),
        (1, "1d10 dis + 1d4"),
        (1, "14d20 +2 disadvantage dl 6"),
    ]
    MULTIPLIER_TEST_ITER = iter(MULTIPLIER_TEST_LIST)

    # ("(5d10)*21", 20, "5d10"),
    # ("(1d4)", 1, "1d4"),

    @for_each_roll
    def test_parse_multiplier(self, roll_exp):
        results = next(self.MULTIPLIER_TEST_ITER)
        multiplier, die_str = results
        parsed_multiplier = roll_exp.parse_multiplier()
        self.assertEqual(parsed_multiplier, multiplier)
        self.assertIsInstance(parsed_multiplier, int)
        self.assertEqual(roll_exp.roll_string, die_str)
        self.assertIsInstance(roll_exp.roll_string, str)

        # self.assertRaises(DiceSyntaxError, RollParser('6*()').parse_multiplier())
        # self.assertRaises(DiceSyntaxError, RollParser('()*3').parse_multiplier())
        # self.assertRaises(DiceSyntaxError, RollParser('6*').parse_multiplier())

    # fmt: off
    MODIFIER_TEST_RESULTS = iter(
        [
            ([0], [""], "1d20"),
            ([0], [""], "d20"),
            ([0], [""], "&d20"),
            ([4], ["+ 4 "], "2d20 + 4"),
            ([1, 6], ["+ 1d6 "], "1d20 "),
            ([1,], ["+ 1 ", "+ 1d4 "], "1d20 "),
            ([0], [""], "1d4"),
            ([0], [""], "4d6"),
            ([0], [""], "4d6"),
            ([0], [""], "1d20"),
            ([0], [""], "1d6"),
            ([0], [""], "10d10"),
            ([0], [""], "6 * 1d20"),
        ]
    )
    # fmt: on


"""
    @for_each_roll
    def test_parse_modifier(self, roll_exp):
        results = next(self.MODIFIER_TEST_RESULTS)
        modifier_result, modifier_str_result, die_str = results
        modifier_list, modifier_str_list = roll_exp.parse_modifier()

        self.assertListEqual(modifier_list, modifier_result)
        self.assertIsInstance(modifier_list, list)
        self.assertEqual(modifier_str_list, modifier_str_result)
        self.assertEqual(roll_exp.roll_string, die_str)
        self.assertIsInstance(roll_exp.roll_string, str)
        # self.assertTrue(1 <= my_integer <= 6)

    BASE_ROLL_TEST_RESULTS = iter(
        [
            ([{"dice": 1, "sides": 20}], "1d20"),
            ([{"dice": 1, "sides": 20}], "d20"),
            ([{"dice": 1, "sides": 20}], "&d20"),
            ([{"dice": 2, "sides": 20}], "2d20"),
            ([{"dice": 1, "sides": 20}], "1d20 "),
            ([{"dice": 1, "sides": 20}], "1d20 "),
            ([{"dice": 1, "sides": 4}], "1d4"),
            ([{"dice": 4, "sides": 6}], "4d6"),
            ([{"dice": 4, "sides": 6}], "4d6"),
            ([{"dice": 1, "sides": 20}], "1d20"),
            ([{"dice": 1, "sides": 6}], "1d6"),
            ([{"dice": 10, "sides": 10}], "10d10"),
            ([{"dice": 1, "sides": 20}], "6 * 1d20"),
        ]
    )

    @for_each_roll
    def test_parse_base_roll(self, roll_exp):
        results = next(self.BASE_ROLL_TEST_RESULTS)
        expected_roll, _ = results
        base_roll_list = roll_exp.parse_base_roll()

        self.assertCountEqual(base_roll_list, expected_roll)

    MODIFIER_TEST_RESULTS = iter(
        [
            (False, False, "1d20"),
            (False, False, "d20"),
            (False, False, "&d20"),
            (False, False, "2d20 + 4"),
            (False, False, "1d20 "),
            (False, False, "1d20 "),
            (False, False, "1d4"),
            (False, False, "4d6"),
            (False, False, "4d6"),
            (False, False, "1d20"),
            (False, False, "1d6"),
            (False, False, "10d10"),
            (False, False, "6 * 1d20"),
        ]
    )

    @for_each_roll
    def test_parse_advantage_disadvantage(self, roll_exp):
        results = next(self.BASE_ROLL_TEST_RESULTS)
        expected_advantage, expected_disadvantage, _ = results
        adv_result, disadv_result = roll_exp.parse_advantage_disadvantage()
        self.assertIs(adv_result, expected_advantage)
        self.assertIs(disadv_result, expected_disadvantage)
"""

if __name__ == "__main__":
    unittest.main()