from random import randint


class RollMethods:
    @staticmethod
    def die_roller(num_of_dice, type_of_die):
        return [randint(1, int(type_of_die)) for _ in range(int(num_of_dice))]

    @staticmethod
    def advantage(num_of_dice, type_of_die):
        roll1, roll2 = (
            RollMethods.die_roller(num_of_dice, type_of_die),
            RollMethods.die_roller(num_of_dice, type_of_die),
        )
        advantage = [(max(*rolls), min(*rolls)) for rolls in zip(roll1, roll2)]
        return [accpt for accpt, _ in advantage], [rej for _, rej in advantage]

    @staticmethod
    def disadvantage(num_of_dice, type_of_die):
        roll1, roll2 = (
            RollMethods.die_roller(num_of_dice, type_of_die),
            RollMethods.die_roller(num_of_dice, type_of_die),
        )
        disadvantage = [(min(*rolls), max(*rolls)) for rolls in zip(roll1, roll2)]
        return [accpt for accpt, _ in disadvantage], [rej for _, rej in disadvantage]