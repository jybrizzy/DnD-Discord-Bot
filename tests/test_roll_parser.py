import random
import unittest
from functools import wraps
from cogs.utils.roll_parser import Roll, RollParser, balanced_parenthesis
from cogs.utils.errors import DiceSyntaxError
from unittest.mock import patch

# component testing
unittest.TestLoader.sortTestMethodsUsing = None

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
                # print("List lengths checked")
                return test_func(*args, **kwargs)
            else:
                raise ValueError("Mismatched results lengths")

        return wrapper

    return decorator


class TestRollParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # random.seed(30)
        cls.die_expressions = []
        for exp in DIE_EXPRESSIONS:
            cls.die_expressions.append(RollParser(exp))

    @classmethod
    def tearDownClass(cls):
        del cls.die_expressions

    def test_balanced_parenthesis(self):
        for (statement, expected_value) in PARENTHESIS_EXPRESSIONS:
            with self.subTest(paren_string=statement):
                self.assertEqual(balanced_parenthesis(statement), expected_value)

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
        self.assertIsInstance(result_multiplier, int)
        self.assertEqual(result_multiplier, expected_multiplier)
        self.assertIsInstance(roll_exp.roll_string, str)
        self.assertEqual(roll_exp.roll_string, die_str)

    # fmt: off
    MODIFIER_TEST_LIST = [
        ([0], "1d20"),
        ([0], "d20"),
        ([0], "&d20"),
        ([4], "2d20 + 4"),
        ([Roll(1,6,'+')], "1d20"),
        ([1, Roll(1,6,'+')], "1d20"),
        ([0], "1d4"),
        ([0], "4d6"),
        ([0], "4d6"),
        ([0], "1d20"),
        ([0], "1d6"),
        ([0], "10d10"),
        ([0], "6 * 1d20"),
        ([0], "1d20 advantage"),
        ([0], "1d20 disadvantage"),
        ([0], "advantage 4d20"),
        ([5, 1, 2], "1d20 advantage"),
        ([0], "4d6 dl 1"),
        ([0], "4d6 adv kh3"),
        ([1], "1d10 dis"),
        ([2], "14d20 disadvantage dl 6"),
        ([3, Roll(1,4,'+'), 2], ["+ 3 ", "+ 1d4 ", "+ 2 "], "2d12 advan dl 1"),
    ]
    # fmt: on

    MODIFIER_TEST_ITER = iter(MODIFIER_TEST_LIST)

    @result_length_check(MODIFIER_TEST_LIST)
    @for_each_roll
    def test_parse_modifier(self, roll_exp) -> None:
        modifier_result, die_str = next(self.MODIFIER_TEST_ITER)
        # with patch("random.randint", lambda: 1):
        modifier_list = roll_exp.parse_modifier()
        self.assertIsInstance(modifier_list, list)
        self.assertListEqual(modifier_list, modifier_result)
        self.assertEqual(roll_exp.roll_string, die_str)
        self.assertIsInstance(roll_exp.roll_string, str)

    BASE_ROLL_TEST_LIST = [
        (Roll(1, 20), "1d20"),
        (Roll(1, 20), "d20"),
        (Roll(1, 20), "&d20"),
        (Roll(2, 20), "2d20"),
        (Roll(1, 20), "1d20 "),
        (Roll(1, 20), "1d20 "),
        (Roll(1, 4), "1d4"),
        (Roll(4, 6), "4d6"),
        (Roll(4, 6), "4d6"),
        (Roll(1, 20), "1d20"),
        (Roll(1, 6), "1d6"),
        (Roll(10, 10), "10d10"),
        (Roll(1, 20), "6 * 1d20"),
        (Roll(1, 20), "1d20 advantage"),
        (Roll(1, 20), "1d20 disadvantage"),
        (Roll(4, 20), "advantage 4d20"),
        (Roll(1, 20), "1d20 advantage"),
        (Roll(4, 6), "4d6 dl 1"),
        (Roll(4, 6), "4d6 adv kh3"),
        (Roll(1, 10), "1d10 dis"),
        (Roll(14, 20), "14d20 disadvantage dl 6"),
        (Roll(2, 12), "2d12 advan dl 1"),
    ]
    BASE_ROLL_TEST_ITER = iter(BASE_ROLL_TEST_LIST)

    @result_length_check(BASE_ROLL_TEST_LIST)
    @for_each_roll
    def test_parse_base_roll(self, roll_exp) -> None:
        expected = next(self.BASE_ROLL_TEST_ITER)
        expected_roll, _ = expected
        base_roll_list = roll_exp.parse_base_roll()

        self.assertEqual(base_roll_list, expected_roll)

    ADVANTAGE_DISADVANTAGE_TEST_LIST = [
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
        (1, "1d20 advantage"),
        (-1, "1d20 disadvantage"),
        (1, "advantage 4d20"),
        (1, "1d20 advantage"),
        (0, "4d6 dl 1"),
        (1, "4d6 adv kh3"),
        (-1, "1d10 dis"),
        (-1, "14d20 disadvantage dl 6"),
        (-1, "2d12 advan dl 1"),
    ]

    ADVANTAGE_DISADVANTAGE_TEST_ITER = iter(ADVANTAGE_DISADVANTAGE_TEST_LIST)

    @result_length_check(ADVANTAGE_DISADVANTAGE_TEST_LIST)
    @for_each_roll
    def test_parse_advantage_disadvantage(self, roll_exp) -> None:
        expected = next(self.ADVANTAGE_DISADVANTAGE_TEST_ITER)
        expected_advantages, _ = expected
        result_advantages = roll_exp.parse_advantages()
        self.assertEqual(result_advantages, expected_advantages)

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
        expected_parse_value, _ = next(self.DROP_LOWEST_TEST_ITER)
        result_parse_value = roll_exp.parse_drop_lowest()
        self.assertEqual(result_parse_value, expected_parse_value)


# ("(5d10)*21", 20, "5d10"),
# self.assertRaises(DiceSyntaxError, RollParser('6*()').parse_multiplier())
# self.assertRaises(DiceSyntaxError, RollParser('()*3').parse_multiplier())
# self.assertRaises(DiceSyntaxError, RollParser('6*').parse_multiplier())

if __name__ == "__main__":
    unittest.main()
