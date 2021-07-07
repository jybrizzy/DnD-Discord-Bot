from random import Random
import unittest
import sys

# sys.path.append("c:\\Users\\jbrizzy\\Desktop\\Discord_Bot")
print(sys.path)
from cogs.utils.dice import RollCalculator, RollParser

DIE_EXPRESSIONS = [
    "1d20",
    "d20",
    "2d20 + 4",
    "1d20 + 1 + 1d4",
    "(1d4)",
    "6*(4d6)",
]
PARENTHESIS_EXPRESSIONS = [
    ("(1d20)", True),
    ("6*(6d4)", True),
    ("(((", False),
    ("))", False),
    ("()", True),
]


class TestRollParser(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_balanced_parenthesis(self):
        # for (statement, expected_value) in PARENTHESIS_EXPRESSIONS:
        self.assertEqual(RollParser().balanced_parenthesis("(1d20)"), True)


if __name__ == "__main__":
    unittest.main()