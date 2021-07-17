from random import Random
import unittest
import sys
from functools import partial, wraps

# sys.path.append("C:\\Users\\jbrizzy\\Desktop\\Discord_Bot")
print(sys.path)
from cogs.utils.die_parser import RollParser


DIE_EXPRESSIONS = [
    "1d20",
    "d20",
    "2d20 + 4",
    "1d20 + 1 + 1d4",
    "(1d4)",
    "6*(4d6)",
    "(4d6)*6",
    "(1d20)*20",
]
PARENTHESIS_EXPRESSIONS = [
    ("(1d20)", True),
    ("6*(6d4)", True),
    ("(((", False),
    ("))", False),
    ("()", True),
]


class TestRollParser(unittest.TestCase):
    def setUp(self):
        self.expressions = []
        for die_string in DIE_EXPRESSIONS:
            pass
            # self.expressions.append(RollParser(die_string))
        # self.for_each_roll = partial(self._each_expression, self.expressions)

    def tearDown(self):
        del self.expressions

    def for_each_roll(self, test_func):
        @wraps(test_func)
        def _decorator(self):
            for exp in self.expressions:
                with self.subTest(expression=exp):
                    test_func(self, exp)
            return _decorator

    def test_balanced_parenthesis(self):
        for (statement, expected_value) in PARENTHESIS_EXPRESSIONS:
            with self.subTest(paren_string=statement):
                self.assertEqual(
                    RollParser().balanced_parenthesis(statement), expected_value
                )

    def test_parse_multiplier(self):
        MULTIPLIER_TEST = [
            ("6*(4d6)", 6, "4d6"),
            ("(4d6)*6", 6, "4d6"),
            ("(1d20)*20", 20, "1d20"),
            ("2 * (1d6)", 2, "1d6"),
            ("(10d10) * 6", 6, "10d10"),
        ]

        # ("(5d10)*21", 20, "5d10"),
        # ("(1d4)", 1, "1d4"),
        for expression, multiplier, die_str in MULTIPLIER_TEST:
            with self.subTest(mult_string=expression):
                mult_exp = RollParser(expression)
                self.assertEqual(mult_exp.parse_multiplier(), multiplier)
                self.assertEqual(mult_exp.roll_string, die_str)

        for expression, multiplier, die_str in MULTIPLIER_TEST:
            with self.subTest(mult_string=expression):
                mult_exp = RollParser(expression)
                self.assertIsInstance(mult_exp.parse_multiplier(), int)
                self.assertIsInstance(mult_exp.roll_string, str)

        # self.assertRaises(DiceSyntaxError, RollParser('6*()').parse_multiplier())
        # self.assertRaises(DiceSyntaxError, RollParser('()*3').parse_multiplier())
        # self.assertRaises(DiceSyntaxError, RollParser('6*').parse_multiplier())


if __name__ == "__main__":
    unittest.main()