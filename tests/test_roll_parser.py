import random
import unittest

import sys
from functools import wraps

# sys.path.append("C:\\Users\\jbrizzy\\Desktop\\Discord_Bot")
# print(sys.path)
from cogs.utils.roll_parser import RollParser
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
    "( 4d6 dl 1 )*6",
    "4d6 adv kh3",
    "1d10 dis + 1d4",
    "14d20 +2 disadvantage dl 6",
    "2d12 + 3 + 1d4 advan dl 1 + 2",
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
    def wrapper(self):
        # print(test_func.__name__)
        # print(self.__dict__)
        for exp in self.die_expressions:
            with self.subTest(expression=exp.roll_string):
                return test_func(self, exp)
            # print(self.__dict__)

    # wrapper.__name__ = test_func.__name__
    return wrapper


def result_length_check(results_arg):
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            results_arg_set = results_arg or []
            if len(results_arg_set) == len(DIE_EXPRESSIONS):
                print("List lengths checked")
                return test_func(*args, **kwargs)
            else:
                raise ValueError("Mismatched results lengths")

        return wrapper

    return decorator


class TestRollParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        random.seed(30)
        cls.die_expressions = []
        for exp in DIE_EXPRESSIONS:
            cls.die_expressions.append(RollParser(exp))
        print(cls.die_expressions[1].roll_string)

    @classmethod
    def tearDownClass(cls):
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
        (1, "4d6 adv kh3"),
        (1, "1d10 dis + 1d4"),
        (1, "14d20 +2 disadvantage dl 6"),
        (1, "2d12 + 3 + 1d4 advan dl 1 + 2"),
    ]
    MULTIPLIER_TEST_ITER = iter(MULTIPLIER_TEST_LIST)

    @result_length_check(MULTIPLIER_TEST_LIST)
    @for_each_roll
    def test_parse_multiplier(self, roll_exp) -> None:
        expected = next(self.MULTIPLIER_TEST_ITER)
        expected_multiplier, die_str = expected
        result_multiplier = roll_exp.parse_multiplier()
        self.assertEqual(result_multiplier, expected_multiplier)
        self.assertIsInstance(result_multiplier, int)
        self.assertEqual(roll_exp.roll_string, die_str)
        self.assertIsInstance(roll_exp.roll_string, str)

    # fmt: off
    MODIFIER_TEST_LIST = [
        ([0], [""], "1d20"),
        ([0], [""], "d20"),
        ([0], [""], "&d20"),
        ([4], ["+ 4 "], "2d20 + 4"),
        ([1, 6], ["+ 1d6 "], "1d20"),
        ([1, 1], ["+ 1 ", "+ 1d4 "], "1d20"),
        ([0], [""], "1d4"),
        ([0], [""], "4d6"),
        ([0], [""], "4d6"),
        ([0], [""], "1d20"),
        ([0], [""], "1d6"),
        ([0], [""], "10d10"),
        ([0], [""], "6 * 1d20"),
        ([0], [""], "1d20 advantage"),
        ([0], [""], "1d20 disadvantage"),
        ([0], [""], "advantage 4d20"),
        ([5, 1, 2], ["+ 5 ", "+ 1 ", "+ 2 "], "1d20 advantage"),
        ([0], [""], "4d6 dl 1"),
        ([0], [""], "4d6 adv kh3"),
        ([1], ["+ 1d4 "], "1d10 dis"),
        ([2], ["+ 2 "], "14d20 disadvantage dl 6"),
        ([3, 1, 2], ["+ 3 ", "+ 1d4 ", "+ 2 "], "2d12 advan dl 1"),
    ]

    # fmt: on
    MODIFIER_TEST_ITER = iter(MODIFIER_TEST_LIST)

    @result_length_check(MODIFIER_TEST_LIST)
    @for_each_roll
    def test_parse_modifier(self, roll_exp) -> None:
        expected = next(self.MODIFIER_TEST_ITER)
        modifier_result, modifier_str_result, die_str = expected
        with patch("random.randint", lambda: 1):
            modifier_list, modifier_str_list = roll_exp.parse_modifier()

        self.assertListEqual(modifier_list, modifier_result)
        self.assertIsInstance(modifier_list, list)
        self.assertEqual(modifier_str_list, modifier_str_result)
        self.assertEqual(roll_exp.roll_string, die_str)
        self.assertIsInstance(roll_exp.roll_string, str)

    BASE_ROLL_TEST_LIST = [
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
        ([{"dice": 1, "sides": 20}], "1d20 advantage"),
        ([{"dice": 1, "sides": 20}], "1d20 disadvantage"),
        ([{"dice": 4, "sides": 20}], "advantage 4d20"),
        ([{"dice": 1, "sides": 20}], "1d20 advantage"),
        ([{"dice": 4, "sides": 6}], "4d6 dl 1"),
        ([{"dice": 4, "sides": 6}], "4d6 adv kh3"),
        ([{"dice": 1, "sides": 10}], "1d10 dis"),
        ([{"dice": 14, "sides": 20}], "14d20 disadvantage dl 6"),
        ([{"dice": 2, "sides": 12}], "2d12 advan dl 1"),
    ]
    BASE_ROLL_TEST_ITER = iter(BASE_ROLL_TEST_LIST)

    @result_length_check(BASE_ROLL_TEST_LIST)
    @for_each_roll
    def test_parse_base_roll(self, roll_exp) -> None:
        expected = next(self.BASE_ROLL_TEST_ITER)
        expected_roll, _ = expected
        base_roll_list = roll_exp.parse_base_roll()

        self.assertCountEqual(base_roll_list, expected_roll)

    ADVANTAGE_DISADVANTAGE_TEST_LIST = [
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
        (True, False, "1d20 advantage"),
        (False, True, "1d20 disadvantage"),
        (True, False, "advantage 4d20"),
        (True, False, "1d20 advantage"),
        (False, False, "4d6 dl 1"),
        (True, False, "4d6 adv kh3"),
        (False, True, "1d10 dis"),
        (False, True, "14d20 disadvantage dl 6"),
        (False, True, "2d12 advan dl 1"),
    ]

    ADVANTAGE_DISADVANTAGE_TEST_ITER = iter(ADVANTAGE_DISADVANTAGE_TEST_LIST)

    @result_length_check(ADVANTAGE_DISADVANTAGE_TEST_LIST)
    @for_each_roll
    def test_parse_advantage_disadvantage(self, roll_exp) -> None:
        expected = next(self.ADVANTAGE_DISADVANTAGE_TEST_ITER)
        expected_advantage, expected_disadvantage, _ = expected
        result_advantage, result_disadvantage = roll_exp.parse_advantage_disadvantage()
        self.assertIs(result_advantage, expected_advantage)
        self.assertIs(result_disadvantage, expected_disadvantage)

    DROP_LOWEST_TEST_LIST = [
        (0, "1d20"),
        (0, "d20"),
        (0, "&d20"),
        (0, "2d20 + 4"),
        (0, "1d20 "),
        (0, "1d20 "),
        (0, "1d4"),
        (0, "4d6"),
        (0, "4d6"),
        (0, "1d20"),
        (0, "1d6"),
        (0, "10d10"),
        (0, "6 * 1d20"),
        (0, "1d20 advantage"),
        (0, "1d20 disadvantage"),
        (0, "advantage 4d20"),
        (0, "1d20 advantage"),
        (1, "4d6 dl 1"),
        (1, "4d6 adv kh3"),
        (0, "1d10 dis"),
        (6, "14d20 disadvantage dl 6"),
        (1, "2d12 advan dl 1"),
    ]

    DROP_LOWEST_TEST_ITER = iter(DROP_LOWEST_TEST_LIST)

    @result_length_check(DROP_LOWEST_TEST_LIST)
    @for_each_roll
    def test_parse_drop_lowest(self, roll_exp) -> None:
        expected = next(self.DROP_LOWEST_TEST_ITER)
        expected_parse_value, _ = expected
        result_parse_value = roll_exp.parse_drop_lowest()
        self.assertEqual(result_parse_value, expected_parse_value)


# ("(5d10)*21", 20, "5d10"),
# self.assertRaises(DiceSyntaxError, RollParser('6*()').parse_multiplier())
# self.assertRaises(DiceSyntaxError, RollParser('()*3').parse_multiplier())
# self.assertRaises(DiceSyntaxError, RollParser('6*').parse_multiplier())

if __name__ == "__main__":
    unittest.main()